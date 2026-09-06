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
