"""Focused synthetic tests for PURGE-AUDIT-001."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from seqlogad.evaluation import purge_audit
from seqlogad.evaluation.purge_audit import (
    LabelLoadResult,
    PurgeAuditError,
    compare_audit_artifacts,
    load_purged_components,
    load_hdfs_label_file,
    map_labels_to_components,
    newcombe_wilson_difference_interval,
    prevalence_ratio,
    scientific_payload_sha256,
    validate_audit_artifact,
)
from seqlogad.ingestion.raw_metadata import (
    HdfsComponentIndex,
    HdfsComponentMetadata,
    build_hdfs_component_id,
    normalize_hdfs_block_id,
)


FINGERPRINT = purge_audit.EXPECTED_DATASET_FINGERPRINT
SOURCE_ID = "META-SOURCE-" + "a" * 64


def _component(*blocks: str, start: int) -> HdfsComponentMetadata:
    block_ids = tuple(blocks)
    return HdfsComponentMetadata(
        source_id=SOURCE_ID,
        dataset_fingerprint=FINGERPRINT,
        component_id=build_hdfs_component_id(block_ids),
        block_ids=block_ids,
        chronological_start=start - 1,
        source_line_start=start,
    )


def _index() -> HdfsComponentIndex:
    first = _component("blk_1", start=1)
    second = _component("blk_2", "blk_3", start=3)
    return HdfsComponentIndex(
        block_to_component={
            "blk_1": first.component_id,
            "blk_2": second.component_id,
            "blk_3": second.component_id,
        },
        components=(first, second),
        lines_scanned=4,
        complete=True,
    )


def _artifact(payload: dict) -> dict:
    return {
        "artifact_schema_version": "1.0",
        "artifact_type": "PURGE_REPRESENTATIVENESS_AUDIT",
        "scientific_payload": payload,
        "audit_payload_sha256": scientific_payload_sha256(payload),
        "generation": {"generated_at_utc": "volatile"},
    }


def _minimal_payload() -> dict:
    return {
        "audit_id": "PURGE-AUDIT-001",
        "audit_version": "1.0",
        "frozen_identity": {
            "dataset_fingerprint": purge_audit.EXPECTED_DATASET_FINGERPRINT,
            "split_payload_hash": purge_audit.EXPECTED_SPLIT_PAYLOAD_HASH,
        },
        "evidence_classification": [
            {"claim": "fixture", "classification": "ENGINEERING_DECISION"}
        ],
        "final_classification": "PURGE_REPRESENTATIVENESS_INCONCLUSIVE",
    }


def test_meta_normalization_is_reused_for_label_ids() -> None:
    assert normalize_hdfs_block_id(" blk_0002 ") == "blk_2"
    assert normalize_hdfs_block_id("blk_-0002") == "blk_-2"
    with pytest.raises(ValueError):
        normalize_hdfs_block_id("block_2")


def test_duplicate_equal_labels_are_counted_and_conflicts_rejected(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.csv"
    duplicate.write_text("BlockId,Label\nblk_1,Normal\nblk_01,Normal\n", encoding="utf-8")
    result = load_hdfs_label_file(duplicate)
    assert result.rows == 2
    assert result.duplicate_rows == 1
    assert result.labels == {"blk_1": False}

    conflict = tmp_path / "conflict.csv"
    conflict.write_text("BlockId,Label\nblk_1,Normal\nblk_01,Anomaly\n", encoding="utf-8")
    with pytest.raises(PurgeAuditError, match="LABEL_MAPPING_INCOMPLETE"):
        load_hdfs_label_file(conflict)


def test_missing_and_unknown_labels_fail_closed() -> None:
    with pytest.raises(PurgeAuditError, match="LABEL_MAPPING_INCOMPLETE"):
        map_labels_to_components(
            _index(),
            LabelLoadResult(labels={"blk_1": False, "blk_2": True, "blk_99": False}, rows=3, duplicate_rows=0),
        )


def test_conflicting_labels_inside_component_hard_stop() -> None:
    with pytest.raises(PurgeAuditError, match="LABEL_COMPONENT_CONFLICT"):
        map_labels_to_components(
            _index(),
            LabelLoadResult(
                labels={"blk_1": False, "blk_2": True, "blk_3": False},
                rows=3,
                duplicate_rows=0,
            ),
        )


def test_complete_component_mapping_is_deterministic() -> None:
    labels = LabelLoadResult(
        labels={"blk_3": True, "blk_1": False, "blk_2": True},
        rows=3,
        duplicate_rows=0,
    )
    first = map_labels_to_components(_index(), labels)
    second = map_labels_to_components(_index(), labels)
    assert first == second
    assert first.component_labels == (False, True)
    assert first.multi_block_components == 1


def test_purged_set_and_retained_complement_are_deterministic_and_read_only(
    tmp_path: Path,
) -> None:
    index = _index()
    first_component = index.components[0]
    record = {
        "disposition": "PURGED_BOUNDARY",
        "component_id": first_component.component_id,
        "block_ids_canonical_order": list(first_component.block_ids),
        "eligible_ranks_increasing": [1, 2],
        "raw_chronological_indices_increasing": [0, 2],
    }
    path = tmp_path / "exclusions.jsonl"
    path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    original = path.read_bytes()
    boundaries = (0, 2, 2, 3, 3, 4)

    first_purged, first_stats = load_purged_components(path, index, boundaries)
    second_purged, second_stats = load_purged_components(path, index, boundaries)
    retained = {item.component_id for item in index.components} - first_purged

    assert first_purged == second_purged == {first_component.component_id}
    assert first_stats == second_stats
    assert retained == {index.components[1].component_id}
    assert path.read_bytes() == original


def test_newcombe_interval_controlled_fixture_and_ratio_zero_handling() -> None:
    low, high = newcombe_wilson_difference_interval(30, 100, 10, 100)
    assert low == pytest.approx(0.0900021, abs=1e-6)
    assert high == pytest.approx(0.3057893, abs=1e-6)
    assert low < 0.2 < high
    assert prevalence_ratio(0.2, 0.1) == {"value": 2.0, "status": "DEFINED"}
    assert prevalence_ratio(0.2, 0.0) == {
        "value": None,
        "status": "UNDEFINED_ZERO_RETAINED_PREVALENCE",
    }


def test_scientific_payload_hash_ignores_volatile_wrapper_metadata(tmp_path: Path) -> None:
    payload = _minimal_payload()
    first = _artifact(payload)
    second = _artifact(payload)
    first["generation"] = {"generated_at_utc": "one"}
    second["generation"] = {"generated_at_utc": "two"}
    first_path, second_path = tmp_path / "one.json", tmp_path / "two.json"
    first_path.write_text(json.dumps(first), encoding="utf-8")
    second_path.write_text(json.dumps(second), encoding="utf-8")
    assert validate_audit_artifact(first_path)["valid"] is True
    assert compare_audit_artifacts(first_path, second_path)["deterministic"] is True


def test_fingerprint_split_mismatch_and_test_specific_output_are_rejected(tmp_path: Path) -> None:
    for key, value in (
        ("dataset_fingerprint", "0" * 64),
        ("split_payload_hash", "0" * 64),
    ):
        payload = _minimal_payload()
        payload["frozen_identity"][key] = value
        path = tmp_path / f"{key}.json"
        path.write_text(json.dumps(_artifact(payload)), encoding="utf-8")
        with pytest.raises(PurgeAuditError, match="FROZEN_IDENTITY_MISMATCH"):
            validate_audit_artifact(path)

    payload = _minimal_payload()
    payload["test_anomaly_prevalence"] = 0.1
    path = tmp_path / "unsafe.json"
    path.write_text(json.dumps(_artifact(payload)), encoding="utf-8")
    with pytest.raises(PurgeAuditError, match="TEST_BOUNDARY_CONFLICT"):
        validate_audit_artifact(path)


def test_invalid_final_or_evidence_classification_is_rejected(tmp_path: Path) -> None:
    payload = _minimal_payload()
    payload["final_classification"] = "ACCEPTABLE_WITHOUT_HUMAN_THRESHOLD"
    path = tmp_path / "bad-final.json"
    path.write_text(json.dumps(_artifact(payload)), encoding="utf-8")
    with pytest.raises(PurgeAuditError, match="AUDIT_ARTIFACT_INVALID"):
        validate_audit_artifact(path)

    payload = _minimal_payload()
    payload["evidence_classification"][0]["classification"] = "MADE_UP_CLASS"
    path = tmp_path / "bad-evidence.json"
    path.write_text(json.dumps(_artifact(payload)), encoding="utf-8")
    with pytest.raises(PurgeAuditError, match="AUDIT_ARTIFACT_INVALID"):
        validate_audit_artifact(path)


def test_audit_module_has_no_split_mutation_parser_model_or_test_unlock_dependency() -> None:
    source = inspect.getsource(purge_audit)
    assert "generate_split_artifact" not in source
    assert "iter_final_test_assignments" not in source
    assert "consume_human_test_grant" not in source
    assert "seqlogad.parsing" not in source
    assert "seqlogad.models" not in source
    assert "sealed/TEST.jsonl" not in source
    assert "partition_membership_read_by_audit\": False" in source
