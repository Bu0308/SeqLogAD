"""Synthetic tests for parser-independent META-001 contracts."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import seqlogad.ingestion.raw_metadata as raw_metadata_module
from seqlogad.ingestion.raw_metadata import (
    BglIssue,
    BglLineMetadata,
    BglTimestampStatus,
    DecodeStatus,
    HdfsAssignmentStatus,
    HdfsIssue,
    HdfsLineMetadata,
    HdfsUnassignedReason,
    LineEnding,
    MetadataSource,
    build_metadata_source_id,
    extract_bgl_line_metadata,
    iter_bgl_metadata,
    iter_hdfs_metadata,
    scan_hdfs_components,
    write_bgl_metadata_artifact,
    write_hdfs_metadata_artifact,
)


def _source(dataset: str) -> MetadataSource:
    source_file = f"tests/fixtures/{dataset.upper()}.log"
    dataset_id = dataset.upper()
    dataset_version = "synthetic-v1"
    fingerprint = "a" * 64
    source_hash = "b" * 64
    source_id = build_metadata_source_id(
        dataset_key=dataset,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_fingerprint=fingerprint,
        source_file=source_file,
        source_file_sha256=source_hash,
    )
    return MetadataSource(
        source_id=source_id,
        dataset_key=dataset,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_fingerprint=fingerprint,
        source_file=source_file,
        source_file_sha256=source_hash,
    )


def _hdfs_records(path: Path) -> tuple[object, list[HdfsLineMetadata]]:
    source = _source("hdfs")
    index = scan_hdfs_components(path, source)
    return index, list(iter_hdfs_metadata(path, source, index))


@pytest.mark.parametrize(
    ("token", "normalized"),
    [
        ("blk_00042", "blk_42"),
        ("blk_-00042", "blk_-42"),
        ("blk_-0", "blk_0"),
    ],
)
def test_hdfs_single_and_negative_block_normalization(
    tmp_path: Path, token: str, normalized: str
) -> None:
    path = tmp_path / "HDFS.log"
    path.write_bytes(f"raw message {token}\r\n".encode())

    index, records = _hdfs_records(path)

    assert len(index.components) == 1
    assert records[0].block_ids == (normalized,)
    assert records[0].assignment_status is HdfsAssignmentStatus.ASSIGNED
    assert records[0].line_ending is LineEnding.CRLF
    assert records[0].chronological_index == 0


def test_hdfs_duplicate_and_malformed_tokens_are_explicit(tmp_path: Path) -> None:
    path = tmp_path / "HDFS.log"
    path.write_bytes(b"blk_7 again blk_007 malformed blk_bad\n")

    _, records = _hdfs_records(path)
    record = records[0]

    assert record.raw_block_tokens == ("blk_7", "blk_007")
    assert record.block_ids == ("blk_7",)
    assert record.duplicate_block_ids == ("blk_7",)
    assert record.malformed_block_tokens == ("blk_bad",)
    assert HdfsIssue.DUPLICATE_BLOCK_ID in record.issues
    assert HdfsIssue.MALFORMED_BLOCK_TOKEN in record.issues


def test_hdfs_multiple_blocks_form_one_connected_component(tmp_path: Path) -> None:
    path = tmp_path / "HDFS.log"
    path.write_bytes(
        b"line blk_1 and blk_2\n"
        b"line blk_2 and blk_3\n"
        b"line blk_4\n"
    )

    index, records = _hdfs_records(path)

    assert len(index.components) == 2
    assert index.block_to_component["blk_1"] == index.block_to_component["blk_3"]
    assert index.block_to_component["blk_1"] != index.block_to_component["blk_4"]
    assert records[0].component_id == records[1].component_id
    assert HdfsIssue.MULTIPLE_BLOCK_IDS in records[0].issues
    assert records[0].block_ids == ("blk_1", "blk_2")


def test_hdfs_unassigned_lines_are_retained_with_reason(tmp_path: Path) -> None:
    path = tmp_path / "HDFS.log"
    path.write_bytes(b"line without a block\nmalformed blk_bad\n\xff")

    _, records = _hdfs_records(path)

    assert len(records) == 3
    assert [item.assignment_status for item in records] == [
        HdfsAssignmentStatus.UNASSIGNED,
        HdfsAssignmentStatus.UNASSIGNED,
        HdfsAssignmentStatus.UNASSIGNED,
    ]
    assert [item.unassigned_reason for item in records] == [
        HdfsUnassignedReason.NO_BLOCK_ID,
        HdfsUnassignedReason.MALFORMED_BLOCK_TOKEN,
        HdfsUnassignedReason.DECODE_ERROR,
    ]
    assert records[2].decode_status is DecodeStatus.DECODE_ERROR
    assert HdfsIssue.MISSING_LINE_TERMINATOR in records[2].issues


def test_hdfs_group_identity_is_label_independent_and_deterministic(
    tmp_path: Path,
) -> None:
    normal_path = tmp_path / "normal.log"
    anomaly_path = tmp_path / "anomaly.log"
    normal_path.write_bytes(b"blk_9 label=Normal\n")
    anomaly_path.write_bytes(b"blk_9 label=Anomaly\n")
    source = _source("hdfs")

    normal_index = scan_hdfs_components(normal_path, source)
    anomaly_index = scan_hdfs_components(anomaly_path, source)
    repeated_index = scan_hdfs_components(normal_path, source)

    assert normal_index.components == repeated_index.components
    assert normal_index.block_to_component == repeated_index.block_to_component
    assert (
        normal_index.block_to_component["blk_9"]
        == anomaly_index.block_to_component["blk_9"]
    )


def _bgl_line(label: str, timestamp: str, message: str = "message") -> bytes:
    return (
        f"{label} 1117838570 2005.06.03 NODE "
        f"{timestamp} NODE RAS KERNEL INFO {message}\n"
    ).encode()


def test_bgl_timestamp_parsing_and_source_order_rank() -> None:
    record = extract_bgl_line_metadata(
        _bgl_line("-", "2005-06-03-15.42.50.363779"),
        line_number=7,
        source=_source("bgl"),
    )

    assert record.timestamp_status is BglTimestampStatus.PARSED
    assert record.timestamp_iso == "2005-06-03T15:42:50.363779"
    assert record.source_epoch_seconds == 1117838570
    assert record.original_line_index == 6
    assert record.chronological_rank == 6


def test_bgl_timestamp_ties_use_original_line_index(tmp_path: Path) -> None:
    path = tmp_path / "BGL.log"
    timestamp = "2005-06-03-15.42.50.363779"
    path.write_bytes(_bgl_line("-", timestamp, "one") + _bgl_line("-", timestamp, "two"))

    records = list(iter_bgl_metadata(path, _source("bgl")))

    assert [item.chronological_rank for item in records] == [0, 1]
    assert records[0].timestamp_iso == records[1].timestamp_iso
    assert records[0].chronology_id != records[1].chronology_id


def test_bgl_malformed_timestamp_and_regression_are_retained(tmp_path: Path) -> None:
    path = tmp_path / "BGL.log"
    path.write_bytes(
        _bgl_line("-", "2005-06-03-15.42.51.000000")
        + _bgl_line("-", "not-a-timestamp")
        + _bgl_line("-", "2005-06-03-15.42.50.000000")
    )

    records = list(iter_bgl_metadata(path, _source("bgl")))

    assert len(records) == 3
    assert records[1].timestamp_status is BglTimestampStatus.MALFORMED_TIMESTAMP
    assert records[1].timestamp_iso is None
    assert BglIssue.TIMESTAMP_REGRESSION in records[2].issues
    assert [item.chronological_rank for item in records] == [0, 1, 2]


def test_bgl_chronology_is_label_independent_and_deterministic() -> None:
    source = _source("bgl")
    timestamp = "2005-06-03-15.42.50.363779"
    normal = extract_bgl_line_metadata(
        _bgl_line("-", timestamp), line_number=4, source=source
    )
    alert = extract_bgl_line_metadata(
        _bgl_line("KERNDTLB", timestamp), line_number=4, source=source
    )
    repeated = extract_bgl_line_metadata(
        _bgl_line("-", timestamp), line_number=4, source=source
    )

    assert normal.chronology_id == alert.chronology_id
    assert normal.chronological_rank == alert.chronological_rank
    assert normal.timestamp_iso == alert.timestamp_iso
    assert normal == repeated
    assert normal.record_id != alert.record_id


def test_bgl_metadata_is_ready_for_later_100_event_grouping_without_building_windows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "BGL.log"
    path.write_bytes(
        b"".join(
            _bgl_line("-", f"2005-06-03-15.42.50.{index:06d}")
            for index in range(101)
        )
    )

    records = list(iter_bgl_metadata(path, _source("bgl")))

    assert [item.chronological_rank for item in records] == list(range(101))
    assert "partition" not in BglLineMetadata.model_fields
    assert "parent_window_id" not in BglLineMetadata.model_fields


def test_metadata_contract_has_no_label_or_partition_fields() -> None:
    for model in (HdfsLineMetadata, BglLineMetadata):
        assert all("label" not in field for field in model.model_fields)
        assert all("partition" not in field for field in model.model_fields)


def test_metadata_module_has_no_parser_dependency() -> None:
    module_path = Path(raw_metadata_module.__file__)
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    assert "drain3" not in imported_modules
    assert all(not item.startswith("seqlogad.parsing") for item in imported_modules)


def test_hdfs_artifact_is_deterministic_and_non_overwriting(tmp_path: Path) -> None:
    path = tmp_path / "HDFS.log"
    path.write_bytes(b"blk_2 and blk_1\nblk_2\n")
    source = _source("hdfs")
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_summary = write_hdfs_metadata_artifact(path, source, first)
    second_summary = write_hdfs_metadata_artifact(path, source, second)

    assert first_summary == second_summary
    for name in ("components.jsonl", "lines.jsonl", "summary.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    with pytest.raises(FileExistsError):
        write_hdfs_metadata_artifact(path, source, first)


def test_bgl_artifact_retains_all_lines_and_is_metadata_only(tmp_path: Path) -> None:
    path = tmp_path / "BGL.log"
    path.write_bytes(
        _bgl_line("-", "2005-06-03-15.42.50.000001")
        + _bgl_line("-", "malformed")
    )
    output = tmp_path / "bgl-metadata"

    summary = write_bgl_metadata_artifact(path, _source("bgl"), output)

    assert summary.lines_observed == 2
    assert summary.counts["retained_malformed_timestamps"] == 1
    assert summary.labels_used is False
    assert summary.parser_used is False
    assert summary.scientific_split_created is False
    assert summary.test_partition_assigned is False
    assert len((output / "lines.jsonl").read_text().splitlines()) == 2
