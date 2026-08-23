"""Synthetic-only PARSE-001 normal-pool scope and identity tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from seqlogad.common.schemas.events import ScientificPartition
from seqlogad.parsing import normal_pool as normal_pool_module
from seqlogad.parsing.normal_pool import (
    NormalPoolError,
    select_bgl_normal_membership,
    select_hdfs_normal_membership,
)
from seqlogad.parsing.normalization import (
    BGL_EMPTY_CONTENT_SENTINEL,
    MessageExtractionError,
    extract_bgl_record,
    extract_hdfs_message,
)


def _manifest(dataset: str) -> dict:
    return {
        "dataset": {
            "key": dataset,
            "dataset_fingerprint": "a" * 64,
            "source_file": f"data/raw/{dataset}/source.log",
            "source_file_sha256": "b" * 64,
        },
        "identity": {
            "split_payload_hash": "c" * 64,
            "partition_hashes": {"BASE_TRAIN": "d" * 64},
        },
    }


def _hdfs_assignment(
    component: str,
    block_ids: list[str],
    indices: list[int],
    *,
    partition: str = "BASE_TRAIN",
) -> dict:
    return {
        "unit_kind": "HDFS_COMPONENT",
        "partition_or_null": partition,
        "disposition": "ASSIGNED",
        "component_id": component,
        "block_ids_canonical_order": block_ids,
        "raw_chronological_indices_increasing": indices,
    }


def _bgl_assignment(start: int, *, partition: str = "BASE_TRAIN") -> dict:
    return {
        "unit_kind": "BGL_PARENT_WINDOW",
        "partition_or_null": partition,
        "disposition": "ASSIGNED",
        "raw_rank_start_inclusive": start,
        "raw_rank_end_exclusive": start + 100,
    }


def _bgl_line(label: str, index: int, message: str | None = None) -> bytes:
    content = message or f"kernel event {index}"
    return (
        f"{label} {1117838570 + index} 2005.06.03 R02-M0-N0-C:J12-U11 "
        f"2005-06-03-15.42.50.000000 R02-M0-N0-C:J12-U11 RAS KERNEL INFO "
        f"{content}\n"
    ).encode()


def test_source_normalization_is_label_isolating_and_strict() -> None:
    hdfs = b"081109 203518 143 INFO dfs.DataNode: Received block blk_7\n"
    assert extract_hdfs_message(hdfs) == "Received block blk_7"

    bgl = extract_bgl_record(_bgl_line("KERNDTLB", 0, "message only"))
    assert bgl.label_marker == "KERNDTLB"
    assert bgl.message == "message only"
    assert "KERNDTLB" not in bgl.message
    empty = extract_bgl_record(
        b"- 1120866514 2005.07.08 NODE TIME NODE RAS KERNEL FATAL\n"
    )
    assert empty.message == BGL_EMPTY_CONTENT_SENTINEL

    with pytest.raises(MessageExtractionError):
        extract_hdfs_message(b"not the frozen format\n")
    with pytest.raises(MessageExtractionError):
        extract_bgl_record(b"too few fields\n")


def test_hdfs_selection_keeps_only_whole_all_normal_base_components(
    tmp_path: Path,
) -> None:
    source = tmp_path / "HDFS.log"
    source.write_bytes(
        b"081109 203518 1 INFO dfs.DataNode: a blk_1\n"
        b"081109 203519 1 INFO dfs.DataNode: b blk_2\n"
        b"081109 203520 1 INFO dfs.DataNode: c blk_3\n"
        b"081109 203521 1 INFO dfs.DataNode: d blk_4\n"
        b"081109 203522 1 INFO dfs.DataNode: e blk_5\n"
    )
    assignments = [
        _hdfs_assignment("CMP-1", ["blk_1", "blk_2"], [0, 1]),
        _hdfs_assignment("CMP-2", ["blk_3"], [2]),
        _hdfs_assignment("CMP-3", ["blk_4", "blk_5"], [3, 4]),
    ]
    labels = {
        "blk_1": "Normal",
        "blk_2": "Normal",
        "blk_3": "Anomaly",
        "blk_4": "Normal",
        "blk_5": "Anomaly",
    }

    pool = select_hdfs_normal_membership(
        assignments=assignments,
        scoped_labels=labels,
        total_raw_lines=5,
        manifest=_manifest("hdfs"),
        source_path=source,
    )

    assert pool.fit_partition is ScientificPartition.BASE_TRAIN
    assert list(pool.iter_source_indices()) == [0, 1]
    assert [message for _, message in pool.iter_messages()] == ["a blk_1", "b blk_2"]
    assert pool.selected_unit_count == 1
    assert pool.excluded_unit_count == 2
    assert pool.mixed_unit_count == 1
    assert pool.summary()["labels_persisted"] is False
    assert pool.summary()["test_accessed"] is False


def test_hdfs_pool_identity_is_deterministic_and_label_scope_fails_closed(
    tmp_path: Path,
) -> None:
    source = tmp_path / "HDFS.log"
    source.write_bytes(b"081109 203518 1 INFO dfs.DataNode: a blk_1\n")
    assignment = [_hdfs_assignment("CMP-1", ["blk_1"], [0])]
    kwargs = {
        "assignments": assignment,
        "scoped_labels": {"blk_1": "Normal"},
        "total_raw_lines": 1,
        "manifest": _manifest("hdfs"),
        "source_path": source,
    }
    first = select_hdfs_normal_membership(**kwargs)
    second = select_hdfs_normal_membership(**kwargs)
    assert first.normal_pool_hash == second.normal_pool_hash

    with pytest.raises(NormalPoolError):
        select_hdfs_normal_membership(
            **{**kwargs, "scoped_labels": {}},
        )
    with pytest.raises(NormalPoolError):
        select_hdfs_normal_membership(
            **{
                **kwargs,
                "assignments": [
                    _hdfs_assignment(
                        "CMP-X", ["blk_1"], [0], partition="VAL_EXPERT"
                    )
                ],
            }
        )
    with pytest.raises(NormalPoolError):
        select_hdfs_normal_membership(
            **{
                **kwargs,
                "assignments": [
                    _hdfs_assignment("CMP-X", ["blk_1"], [0], partition="TEST")
                ],
            }
        )


def test_hdfs_storage_scan_exposes_only_allowed_base_labels(tmp_path: Path) -> None:
    """A monolithic source CSV cannot expose or retain non-BASE labels."""

    labels = tmp_path / "anomaly_label.csv"
    labels.write_text(
        "BlockId,Label\nblk_base,Normal\nblk_other,Anomaly\n",
        encoding="utf-8",
    )
    first = normal_pool_module._read_scoped_hdfs_labels(labels, {"blk_base"})

    labels.write_text(
        "BlockId,Label\nblk_base,Normal\nblk_other,Normal\n",
        encoding="utf-8",
    )
    second = normal_pool_module._read_scoped_hdfs_labels(labels, {"blk_base"})

    assert first == second == {"blk_base": "Normal"}


def test_bgl_selection_reads_labels_only_for_complete_base_windows(
    tmp_path: Path,
) -> None:
    source = tmp_path / "BGL.log"
    base = [_bgl_line("-" if index != 9 else "KERNDTLB", index) for index in range(100)]
    forbidden_tail = [_bgl_line("SHOULD_NOT_BE_READ", index) for index in range(100, 200)]
    source.write_bytes(b"".join(base + forbidden_tail))

    def bounded_lines():
        for index, line in enumerate(base + forbidden_tail):
            if index >= 100:
                raise AssertionError("selector inspected a non-BASE label")
            yield line

    first = select_bgl_normal_membership(
        assignments=[_bgl_assignment(0)],
        raw_lines=bounded_lines(),
        total_raw_lines=200,
        manifest=_manifest("bgl"),
        source_path=source,
    )
    second = select_bgl_normal_membership(
        assignments=[_bgl_assignment(0)],
        raw_lines=iter(base),
        total_raw_lines=200,
        manifest=_manifest("bgl"),
        source_path=source,
    )

    assert first.fit_partition is ScientificPartition.BASE_TRAIN
    assert first.selected_record_count == 99
    assert first.excluded_unit_count == 1
    assert not first.contains(9)
    assert first.normal_pool_hash == second.normal_pool_hash
    messages = list(first.iter_messages())
    assert len(messages) == 99
    assert all("KERNDTLB" not in message for _, message in messages)


def test_bgl_selection_rejects_nonbase_and_malformed_windows(tmp_path: Path) -> None:
    source = tmp_path / "BGL.log"
    lines = [_bgl_line("-", index) for index in range(100)]
    source.write_bytes(b"".join(lines))
    common = {
        "raw_lines": iter(lines),
        "total_raw_lines": 100,
        "manifest": _manifest("bgl"),
        "source_path": source,
    }
    with pytest.raises(NormalPoolError):
        select_bgl_normal_membership(
            assignments=[_bgl_assignment(0, partition="VAL_FUSION")],
            **common,
        )
    with pytest.raises(NormalPoolError):
        select_bgl_normal_membership(
            assignments=[_bgl_assignment(0, partition="TEST")],
            **{**common, "raw_lines": iter(lines)},
        )
    malformed = _bgl_assignment(0)
    malformed["raw_rank_end_exclusive"] = 99
    with pytest.raises(NormalPoolError):
        select_bgl_normal_membership(
            assignments=[malformed],
            **{**common, "raw_lines": iter(lines)},
        )
