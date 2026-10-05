"""Contract tests for the v2 process-evidence collection layer."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from seqlogad.collection import (
    ArchitectureRecord,
    DatasetSnapshotRecord,
    EventSchemaRecord,
    CollectionError,
    append_record,
    initialize_collection,
    validate_collection,
)


NOW = datetime(2026, 8, 29, tzinfo=timezone.utc)


def _architecture() -> ArchitectureRecord:
    return ArchitectureRecord(
        created_at_utc=NOW,
        recorder="test",
        architecture_id="arch-a-v1",
        title="Synthetic source architecture",
        mechanism_summary="test mechanism",
    )


def _event_schema() -> EventSchemaRecord:
    return EventSchemaRecord(
        created_at_utc=NOW,
        recorder="test",
        event_schema_id="events-v1",
        timestamp_field="ts",
        timezone_policy="UTC",
        source_id_field="source",
        event_type_field="template",
        message_storage="hash_only",
        missing_field_policy="record_missingness",
        late_event_policy="retain_and_flag",
        clock_skew_policy="record_skew",
    )


def _dataset() -> DatasetSnapshotRecord:
    return DatasetSnapshotRecord(
        created_at_utc=NOW,
        recorder="test",
        dataset_id="dataset-a-v1",
        source_systems=("source-a",),
        collection_start_utc=NOW,
        collection_end_utc=NOW,
        event_count=1,
        source_count=1,
        privacy_class="restricted",
        license_or_permission="local-permission",
        event_schema_id="events-v1",
        transform_id="transform-a-v1",
    )


def test_initialize_is_idempotent_and_creates_append_only_contract(tmp_path: Path) -> None:
    first = initialize_collection(tmp_path)
    second = initialize_collection(tmp_path)
    assert first["status"] == second["status"] == "READY"
    assert len(first["created_files"]) == 14
    assert second["created_files"] == []


def test_append_serializes_jsonl_and_rejects_duplicate_ids(tmp_path: Path) -> None:
    initialize_collection(tmp_path)
    record = _architecture()
    result = append_record(tmp_path, "architecture", record)
    assert result["status"] == "APPENDED"
    payload = (tmp_path / "research_records/architectures.jsonl").read_text()
    assert json.loads(payload)["architecture_id"] == "arch-a-v1"
    with pytest.raises(CollectionError, match="duplicate"):
        append_record(tmp_path, "architecture", record)


def test_validate_checks_core_references_and_portable_paths(tmp_path: Path) -> None:
    initialize_collection(tmp_path)
    append_record(tmp_path, "architecture", _architecture())
    append_record(tmp_path, "event_schema", _event_schema())
    # The dataset points at a transform that has not been recorded yet.
    append_record(tmp_path, "dataset", _dataset())
    report = validate_collection(tmp_path)
    assert report["status"] == "FAIL"
    assert any("orphan reference dataset.transform_id" in error for error in report["duplicate_or_parse_errors"])


def test_append_rejects_absolute_or_parent_paths(tmp_path: Path) -> None:
    initialize_collection(tmp_path)
    record = _architecture().model_copy(update={"decision_evidence": ("../secret.json",)})
    with pytest.raises(CollectionError, match="relative POSIX"):
        append_record(tmp_path, "architecture", record)


def test_empty_store_is_not_a_ready_package(tmp_path):
    report = validate_collection(tmp_path)
    assert report["status"] == "INCOMPLETE"
    assert report["structural_status"] == "PASS"
    assert report["handoff_status"] == "NOT_READY"
    initialize_collection(tmp_path)
    assert validate_collection(tmp_path)["status"] == "INCOMPLETE"


def test_two_variants_share_architecture_without_duplicate_identity(tmp_path):
    from seqlogad.collection.models import VariantRecord
    from hashlib import sha256
    (tmp_path / "config.json").write_text("{}")
    append_record(tmp_path, "architecture", _architecture())
    for number in (1, 2):
        variant = VariantRecord(
            created_at_utc=NOW, recorder="test", variant_id=f"var-{number}",
            architecture_id="arch-a-v1", change_reason="test",
            config_path="config.json", config_sha256=sha256(b"{}").hexdigest(),
        )
        assert append_record(tmp_path, "variant", variant)["record_id"] == f"var-{number}"
    assert validate_collection(tmp_path)["duplicate_or_parse_errors"] == []
    with pytest.raises(CollectionError, match="duplicate"):
        append_record(tmp_path, "variant", variant)


def _artifact(path="evidence.bin", digest="a" * 64, status="included"):
    from seqlogad.collection.models import ArtifactManifestRecord
    return ArtifactManifestRecord(
        created_at_utc=NOW, recorder="test", artifact_manifest_id="art-1",
        availability_verified_at_utc=NOW, verified_by="test",
        items=[dict(role="test", path=path, sha256=digest, size_bytes=3,
                    content_archived=True, archive_class="restricted",
                    availability_status=status)],
    )


@pytest.mark.parametrize("path", ["/private/file", "../file", "C:/file", "a\\b", "a\nfile"])
def test_nested_artifact_path_rejected(tmp_path, path):
    with pytest.raises(CollectionError, match="relative POSIX"):
        append_record(tmp_path, "artifact_manifest", _artifact(path=path))


def test_invalid_hash_and_changed_bytes_rejected(tmp_path):
    from hashlib import sha256
    with pytest.raises(CollectionError, match="SHA-256"):
        append_record(tmp_path, "artifact_manifest", _artifact(digest="bad"))
    (tmp_path / "evidence.bin").write_bytes(b"abc")
    append_record(tmp_path, "artifact_manifest", _artifact(digest=sha256(b"abc").hexdigest()))
    assert validate_collection(tmp_path)["structural_status"] == "PASS"
    (tmp_path / "evidence.bin").write_bytes(b"xyz")
    assert any("checksum mismatch" in e for e in validate_collection(tmp_path)["duplicate_or_parse_errors"])


def test_missing_included_bytes_fail_but_declared_missing_remains(tmp_path):
    append_record(tmp_path, "artifact_manifest", _artifact())
    assert validate_collection(tmp_path)["status"] == "FAIL"
    other = tmp_path / "declared"
    append_record(other, "artifact_manifest", _artifact(status="missing"))
    assert validate_collection(other)["structural_status"] == "PASS"


def test_symlink_cannot_escape_evidence_root(tmp_path):
    outside = tmp_path / "outside"
    outside.write_bytes(b"abc")
    root = tmp_path / "project"
    root.mkdir()
    (root / "evidence.bin").symlink_to(outside)
    append_record(root, "artifact_manifest", _artifact())
    assert any("escapes" in e for e in validate_collection(root)["duplicate_or_parse_errors"])


def test_lineage_endpoints_must_exist(tmp_path):
    from seqlogad.collection.models import LineageEdgeRecord
    edge = LineageEdgeRecord(created_at_utc=NOW, recorder="test", edge_id="edge-1",
                             subject_id="missing", predicate="USES", object_id="also-missing",
                             evidence_paths=())
    append_record(tmp_path, "lineage_edge", edge)
    assert any("orphan lineage" in e for e in validate_collection(tmp_path)["duplicate_or_parse_errors"])


def test_every_record_type_uses_its_own_id_not_a_foreign_key():
    from seqlogad.collection.models import RECORD_FILES
    from seqlogad.collection.validation import ID_FIELDS, record_id
    for kind, (_, model) in RECORD_FILES.items():
        values = {field: "foreign-id" for field in model.model_fields if field.endswith("_id")}
        values[ID_FIELDS[kind]] = f"primary-{kind}"
        record = model.model_construct(**values)
        assert record_id(record) == f"primary-{kind}"


def test_lineage_hashes_cannot_be_omitted(tmp_path):
    from seqlogad.collection.models import LineageEdgeRecord
    edge = LineageEdgeRecord(created_at_utc=NOW, recorder="test", edge_id="edge-1",
                             subject_id="a", predicate="USES", object_id="b",
                             evidence_paths=("source.json",))
    with pytest.raises(CollectionError, match="one hash"):
        append_record(tmp_path, "lineage_edge", edge)
