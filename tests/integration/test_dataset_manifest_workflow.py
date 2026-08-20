"""Offline end-to-end test for the Day 2 dataset integrity workflow."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from seqlogad.ingestion.dataset_config import DatasetDefinition
from seqlogad.ingestion.dataset_manifest import (
    build_dataset_manifest,
    verify_dataset_manifest,
    write_dataset_manifest,
)


ProjectFactory = Callable[[str], tuple[Path, DatasetDefinition]]


def test_fixture_manifest_build_verify_and_mutation_detection(
    make_dataset_project: ProjectFactory,
) -> None:
    root, config = make_dataset_project("complete_dataset")
    manifest = build_dataset_manifest(config, project_root=root)
    write_dataset_manifest(manifest, root / config.manifest_path)

    initial = verify_dataset_manifest(config, project_root=root)
    assert initial.valid is True
    assert initial.fingerprint_matches is True

    (root / config.raw_dir / "labels.csv").write_text(
        "trace_id,label\nsynthetic-001,anomaly\n",
        encoding="utf-8",
    )
    modified = verify_dataset_manifest(config, project_root=root)
    assert modified.valid is False
    assert modified.checksum_mismatches == ["data/raw/sample/labels.csv"]
