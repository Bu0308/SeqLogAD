"""Synthetic-only PARSE-001 Drain3 fit, freeze, and restore tests."""

from __future__ import annotations

import dataclasses
import json
import shutil
from pathlib import Path

import pytest

from seqlogad.common.schemas.events import ScientificPartition, UNSEEN_EVENT_ID
from seqlogad.parsing.drain_parser import (
    ParserContractError,
    compare_fit_identities,
    fit_and_freeze_parser,
    load_frozen_parser,
    load_frozen_parser_contract,
    parser_config_sha256,
    validate_parser_artifact,
)
from seqlogad.parsing.normal_pool import select_hdfs_normal_membership


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = PROJECT_ROOT / "configs/parsing/drain3-v1.yaml"


def _manifest() -> dict:
    return {
        "dataset": {
            "key": "hdfs",
            "dataset_fingerprint": "a" * 64,
            "source_file": "data/raw/hdfs/synthetic/HDFS.log",
            "source_file_sha256": "b" * 64,
        },
        "identity": {
            "split_payload_hash": "c" * 64,
            "partition_hashes": {"BASE_TRAIN": "d" * 64},
        },
    }


def _pool(tmp_path: Path):
    source = tmp_path / "HDFS.log"
    source.write_bytes(
        b"081109 203518 1 INFO dfs.DataNode: Received block blk_1 from 10.0.0.1:50010\n"
        b"081109 203519 1 INFO dfs.DataNode: Received block blk_2 from 10.0.0.2:50010\n"
        b"081109 203520 1 INFO dfs.DataNode: Deleted block blk_1\n"
        b"081109 203521 1 INFO dfs.DataNode: Deleted block blk_2\n"
    )
    assignment = {
        "unit_kind": "HDFS_COMPONENT",
        "partition_or_null": "BASE_TRAIN",
        "disposition": "ASSIGNED",
        "component_id": "CMP-1",
        "block_ids_canonical_order": ["blk_1", "blk_2"],
        "raw_chronological_indices_increasing": [0, 1, 2, 3],
    }
    return select_hdfs_normal_membership(
        assignments=[assignment],
        scoped_labels={"blk_1": "Normal", "blk_2": "Normal"},
        total_raw_lines=4,
        manifest=_manifest(),
        source_path=source,
    )


def _fit(pool, output: Path) -> dict:
    return fit_and_freeze_parser(
        pool=pool,
        contract_path=CONTRACT,
        output_directory=output,
        generated_at_utc="2026-08-23T00:00:00Z",
    )


def test_frozen_config_identity_is_stable_and_version_locked() -> None:
    first = load_frozen_parser_contract(CONTRACT)
    second = load_frozen_parser_contract(CONTRACT)
    assert parser_config_sha256(first) == parser_config_sha256(second)
    assert first["software"] == {"package": "drain3", "version": "0.9.11"}
    assert first["drain"]["similarity_threshold"] == 0.4
    assert first["drain"]["depth"] == 4
    assert first["drain"]["frozen_match_full_search_strategy"] == "fallback"


def test_fit_is_deterministic_and_restore_is_immutable(tmp_path: Path) -> None:
    pool = _pool(tmp_path)
    first = _fit(pool, tmp_path / "first")
    second = _fit(pool, tmp_path / "second")

    assert compare_fit_identities(first, second) == {
        "deterministic": True,
        "mismatches": [],
    }
    assert first["input_record_count"] == 4
    assert first["cluster_count"] > 0
    assert first["restore_status"] == "PASS"
    assert first["frozen_transform_status"] == "PASS"

    parser = load_frozen_parser(tmp_path / "first")
    assert not hasattr(parser, "add_log_message")
    known_one = parser.transform(
        "Received block blk_999 from 10.1.2.3:1234",
        partition=ScientificPartition.VAL_EXPERT,
    )
    known_two = parser.transform(
        "Received block blk_999 from 10.1.2.3:1234",
        partition=ScientificPartition.VAL_EXPERT,
    )
    assert known_one == known_two
    assert known_one.matched is True
    assert known_one.event_id != UNSEEN_EVENT_ID

    unknown = parser.transform(
        "one two three four five six seven eight nine ten eleven twelve",
        partition=ScientificPartition.VAL_FUSION,
    )
    assert unknown.matched is False
    assert unknown.event_id == UNSEEN_EVENT_ID

    with pytest.raises(ParserContractError, match="TEST"):
        parser.transform(
            "Received block blk_7 from 10.0.0.7:1234",
            partition=ScientificPartition.TEST,
        )

    batch = parser.transform_batch(
        [
            "Received block blk_999 from 10.1.2.3:1234",
            "one two three four five six seven eight nine ten eleven twelve",
        ],
        partition=ScientificPartition.VAL_EXPERT,
    )
    assert batch == (known_one, unknown)
    with pytest.raises(ParserContractError, match="TEST"):
        parser.transform_batch(
            ["Received block blk_7 from 10.0.0.7:1234"],
            partition=ScientificPartition.TEST,
        )
    with pytest.raises(ParserContractError, match="NUL-free"):
        parser.transform_batch(
            ["message containing a source NUL \x00 byte"],
            partition=ScientificPartition.VAL_FUSION,
        )


def test_fit_refuses_nonbase_pool_and_output_overwrite(tmp_path: Path) -> None:
    pool = _pool(tmp_path)
    unsafe = dataclasses.replace(pool, fit_partition=ScientificPartition.VAL_EXPERT)
    with pytest.raises(ParserContractError, match="BASE_TRAIN"):
        _fit(unsafe, tmp_path / "unsafe")

    output = tmp_path / "parser"
    _fit(pool, output)
    with pytest.raises(ParserContractError, match="already exists"):
        _fit(pool, output)


def test_labels_do_not_enter_parser_inputs_or_registry(tmp_path: Path) -> None:
    pool = _pool(tmp_path)
    output = tmp_path / "parser"
    _fit(pool, output)
    pool_summary = json.loads((output / "normal-pool-summary.json").read_text())
    registry_text = (output / "template-registry.json").read_text()

    assert pool_summary["labels_persisted"] is False
    assert pool_summary["raw_messages_persisted"] is False
    assert "Anomaly" not in registry_text
    assert '"Normal"' not in registry_text


def test_corrupted_state_or_registry_fails_independent_validation(
    tmp_path: Path,
) -> None:
    pool = _pool(tmp_path)
    original = tmp_path / "parser"
    _fit(pool, original)

    corrupt_state = tmp_path / "corrupt-state"
    shutil.copytree(original, corrupt_state)
    with (corrupt_state / "drain3-state.bin").open("ab") as handle:
        handle.write(b"corruption")
    with pytest.raises(ParserContractError, match="integrity mismatch"):
        validate_parser_artifact(corrupt_state)

    corrupt_registry = tmp_path / "corrupt-registry"
    shutil.copytree(original, corrupt_registry)
    registry_path = corrupt_registry / "template-registry.json"
    registry = json.loads(registry_path.read_text())
    registry["cluster_to_event_id"] = {}
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    with pytest.raises(ParserContractError, match="integrity mismatch"):
        validate_parser_artifact(corrupt_registry)
