"""Unit tests for deterministic manifests and content verification."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from src.ingestion.dataset_config import DatasetDefinition
from src.ingestion.dataset_manifest import (
    build_dataset_manifest,
    dataset_fingerprint,
    manifest_json,
    verify_dataset_manifest,
    write_dataset_manifest,
)


ProjectFactory = Callable[[str], tuple[Path, DatasetDefinition]]


def test_manifest_generation_captures_required_metadata(
    make_dataset_project: ProjectFactory,
) -> None:
    root, config = make_dataset_project("complete_dataset")
    manifest = build_dataset_manifest(config, project_root=root)
    assert manifest.schema_version == "1.0"
    assert manifest.integrity.all_required_files_present is True
    assert manifest.statistics.file_count == 2
    assert all(not item.path.startswith("/") for item in manifest.files)
    assert all(len(item.sha256) == 64 for item in manifest.files)
    assert all(item.encoding_status == "UTF8_COMPATIBLE" for item in manifest.files)


def test_manifest_file_order_and_json_are_deterministic(
    make_dataset_project: ProjectFactory,
) -> None:
    root, config = make_dataset_project("complete_dataset")
    first = build_dataset_manifest(config, project_root=root)
    second = build_dataset_manifest(config, project_root=root)
    assert [item.path for item in first.files] == sorted(item.path for item in first.files)
    assert manifest_json(first) == manifest_json(second)


def test_fingerprint_is_order_independent_but_content_sensitive(
    make_dataset_project: ProjectFactory,
) -> None:
    root, config = make_dataset_project("complete_dataset")
    manifest = build_dataset_manifest(config, project_root=root)
    assert dataset_fingerprint(manifest.files) == dataset_fingerprint(list(reversed(manifest.files)))
    changed = manifest.files[0].model_copy(update={"sha256": "0" * 64})
    assert dataset_fingerprint([changed, *manifest.files[1:]]) != manifest.dataset_fingerprint


def test_manifest_serialization_contains_no_runtime_timestamp(
    make_dataset_project: ProjectFactory,
) -> None:
    root, config = make_dataset_project("complete_dataset")
    payload = json.loads(manifest_json(build_dataset_manifest(config, project_root=root)))
    assert "generated_at_utc" not in payload
    assert payload["source"]["acquired_at_utc"] is None


def test_manifest_verifier_passes_then_detects_modified_raw_file(
    make_dataset_project: ProjectFactory,
) -> None:
    root, config = make_dataset_project("complete_dataset")
    manifest = build_dataset_manifest(config, project_root=root)
    manifest_path = root / config.manifest_path
    write_dataset_manifest(manifest, manifest_path)
    assert verify_dataset_manifest(config, project_root=root).valid is True

    (root / config.raw_dir / "sample.log").write_text("modified\n", encoding="utf-8")
    report = verify_dataset_manifest(config, project_root=root)
    assert report.valid is False
    assert report.checksum_mismatches == ["data/raw/sample/sample.log"]
    assert report.fingerprint_matches is False


def test_incomplete_dataset_manifest_marks_integrity_false(
    make_dataset_project: ProjectFactory,
) -> None:
    root, config = make_dataset_project("partial_dataset")
    manifest = build_dataset_manifest(config, project_root=root)
    assert manifest.integrity.all_required_files_present is False
