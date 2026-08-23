"""Deterministic raw partition manifests and TEST sealing for SPLIT-001.

This module consumes only verified raw identity plus META-001 structural
metadata.  It never reads anomaly labels, fits a parser, creates templates,
builds model features, or computes a scientific metric.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
from array import array
from bisect import bisect_right
from collections.abc import Iterable, Iterator
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Final

import yaml

from seqlogad.common.schemas import ScientificPartition
from seqlogad.evaluation.test_seal import (
    SealBinding,
    TestAccessDeniedError,
    TestAccessGrant,
    assert_test_access_denied,
    canonical_json,
    consume_human_test_grant,
    create_sealed_test_state,
    deny_ordinary_test_access,
    load_test_seal,
    sha256_canonical,
    validate_unconsumed_grant,
)
from seqlogad.ingestion.dataset_config import load_dataset_config
from seqlogad.ingestion.raw_metadata import (
    HdfsAssignmentStatus,
    HdfsComponentIndex,
    MetadataSource,
    iter_hdfs_structural_references,
    resolve_metadata_source,
    scan_hdfs_components,
)


SPLIT_SCHEMA_VERSION: Final = "1.0"
PROTOCOL_ID: Final = "PROTOCOL-001"
PROTOCOL_VERSION: Final = "1.1"
SPLIT_CONTRACT_ID: Final = "PROTOCOL-SPLIT-CLARIFY-001"
SPLIT_CONTRACT_VERSION: Final = "1.0"
PARTITION_ORDER: Final = tuple(ScientificPartition)
TARGET_RATIOS: Final = {
    ScientificPartition.BASE_TRAIN: 0.60,
    ScientificPartition.FUSION_TRAIN: 0.10,
    ScientificPartition.VAL_EXPERT: 0.10,
    ScientificPartition.VAL_FUSION: 0.10,
    ScientificPartition.TEST: 0.10,
}
BOUNDARY_NUMERATORS: Final = (0, 60, 70, 80, 90, 100)
BOUNDARY_DENOMINATOR: Final = 100

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ASSIGNMENT_ID = re.compile(r"^PART-[0-9a-f]{64}$")


class SplitError(RuntimeError):
    """Raised for a contract, generation, reconciliation, or integrity failure."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _safe_relative_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or "\x00" in value
        or candidate.is_absolute()
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or candidate.as_posix() != value
    ):
        raise SplitError("artifact path must be normalized repository-relative POSIX")
    return value


def _canonical_bytes(value: object) -> bytes:
    return canonical_json(value).encode("utf-8")


def _sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: object) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    if path.exists() or temporary.exists():
        raise SplitError(f"refusing to overwrite split artifact: {path}")
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    with temporary.open("xb") as handle:
        handle.write(serialized.encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def cumulative_floor_boundaries(total: int) -> tuple[int, ...]:
    """Return the frozen integer-only 60/10/10/10/10 boundaries."""

    if total < 0:
        raise ValueError("allocation universe cannot be negative")
    return tuple((numerator * total) // BOUNDARY_DENOMINATOR for numerator in BOUNDARY_NUMERATORS)


def nominal_partition_index(rank: int, boundaries: tuple[int, ...]) -> int:
    if len(boundaries) != 6 or rank < 0 or rank >= boundaries[-1]:
        raise ValueError("rank is outside the frozen allocation universe")
    index = bisect_right(boundaries, rank) - 1
    if not 0 <= index < len(PARTITION_ORDER):
        raise ValueError("rank did not resolve to a scientific partition")
    return index


def _load_yaml(path: Path) -> dict:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SplitError(f"cannot load frozen contract {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SplitError(f"contract is not a mapping: {path}")
    return payload


def validate_frozen_split_prerequisites(
    project_root: str | Path,
    *,
    require_authorized: bool = True,
) -> dict[str, object]:
    """Validate the human-approved protocol without reading raw datasets."""

    root = Path(project_root).resolve()
    protocol = _load_yaml(root / "configs/protocols/protocol-v1.1.yaml")
    effect = _load_yaml(root / "configs/protocols/effect-001.yaml")
    clarification = _load_yaml(
        root / "configs/protocols/split-clarification-v1.yaml"
    )
    protocol_meta = protocol.get("protocol", {})
    effect_meta = effect.get("effect_contract", {})
    split_meta = clarification.get("split_clarification", {})
    if protocol_meta.get("id") != PROTOCOL_ID or protocol_meta.get("version") != PROTOCOL_VERSION:
        raise SplitError("active scientific protocol is not PROTOCOL-001 v1.1")
    if protocol_meta.get("status") != "FROZEN_HUMAN_APPROVED":
        raise SplitError("PROTOCOL-001 v1.1 is not frozen")
    if effect_meta.get("status") != "FROZEN_HUMAN_APPROVED":
        raise SplitError("EFFECT-001 is not frozen and human-approved")
    practical = effect.get("practical_effect", {})
    if practical.get("hdfs", {}).get("delta_ap") != 0.01 or practical.get("bgl", {}).get("delta_ap") != 0.01:
        raise SplitError("EFFECT-001 practical margins differ from 0.01 AP")
    if split_meta.get("id") != SPLIT_CONTRACT_ID or split_meta.get("version") != SPLIT_CONTRACT_VERSION:
        raise SplitError("active split addendum identity is unsupported")
    if split_meta.get("status") != "FROZEN_HUMAN_APPROVED" or not split_meta.get("execution_ready"):
        raise SplitError("split clarification is not frozen and execution-ready")
    if require_authorized and not split_meta.get("split_execution_authorized"):
        raise SplitError("real SPLIT-001 execution has not been human-authorized")

    shared = clarification.get("shared", {})
    expected_names = [item.value for item in PARTITION_ORDER]
    expected_ratios = {item.value: TARGET_RATIOS[item] for item in PARTITION_ORDER}
    if (
        shared.get("partition_order") != expected_names
        or shared.get("target_ratios") != expected_ratios
        or shared.get("boundary_algorithm") != "cumulative_floor"
        or shared.get("boundary_integer_numerators") != list(BOUNDARY_NUMERATORS)
        or shared.get("boundary_integer_denominator") != BOUNDARY_DENOMINATOR
        or shared.get("label_independent") is not True
        or shared.get("anomaly_labels_read_for_assignment") is not False
        or shared.get("parser_or_template_state_used_for_assignment") is not False
    ):
        raise SplitError("shared split semantics differ from the frozen contract")
    hdfs = clarification.get("hdfs", {})
    if (
        hdfs.get("allocation_unit") != "eligible_raw_line_rank"
        or hdfs.get("component_identity") != "META-001_connected_component"
        or hdfs.get("assignment_rule", {}).get("two_or_more_nominal_partitions") != "PURGED_BOUNDARY"
    ):
        raise SplitError("HDFS split semantics differ from the frozen contract")
    bgl = clarification.get("bgl", {})
    if (
        bgl.get("allocation_unit") != "raw_source_line_rank"
        or bgl.get("split_before_parent_window") is not True
        or bgl.get("parent_window_size") != 100
        or bgl.get("parent_window_stride") != 100
        or bgl.get("trailing_residual_disposition") != "DROPPED_RESIDUAL_WINDOW"
    ):
        raise SplitError("BGL split semantics differ from the frozen contract")
    return {
        "protocol": protocol_meta,
        "effect": effect_meta,
        "split": split_meta,
        "shared": shared,
        "hdfs": hdfs,
        "bgl": bgl,
    }


def _write_jsonl_record(handle: BinaryIO, record: dict) -> None:
    handle.write(_canonical_bytes(record) + b"\n")


def _read_jsonl(path: Path) -> Iterator[dict]:
    with path.open("rb") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise SplitError(f"blank JSONL record at {path}:{line_number}")
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SplitError(f"invalid JSONL at {path}:{line_number}") from exc
            if not isinstance(value, dict):
                raise SplitError(f"JSONL record must be an object at {path}:{line_number}")
            yield value


def _decision_spool_paths(staging: Path) -> tuple[dict[ScientificPartition, Path], Path]:
    spool = staging / ".decision-spool"
    spool.mkdir()
    partition_paths = {item: spool / f"{item.value}.jsonl" for item in PARTITION_ORDER}
    exclusions = spool / "exclusions.jsonl"
    for path in (*partition_paths.values(), exclusions):
        path.touch(exist_ok=False)
    return partition_paths, exclusions


def _common_decision(
    *,
    unit_kind: str,
    structural_unit_id: str,
    chronological_start: int,
    chronological_end_exclusive: int,
    disposition: str,
    partition: ScientificPartition | None,
    exclusion_reason: str | None,
) -> dict:
    if chronological_start < 0 or chronological_end_exclusive <= chronological_start:
        raise SplitError("structural decision has an invalid chronology range")
    return {
        "unit_kind": unit_kind,
        "structural_unit_id": structural_unit_id,
        "chronological_start": chronological_start,
        "chronological_end_exclusive": chronological_end_exclusive,
        "disposition": disposition,
        "partition_or_null": None if partition is None else partition.value,
        "exclusion_reason_or_null": exclusion_reason,
    }


def _hdfs_decisions(
    *,
    log_path: Path,
    source: MetadataSource,
    component_index: HdfsComponentIndex,
    partition_spools: dict[ScientificPartition, Path],
    exclusion_spool: Path,
) -> dict:
    components = component_index.components
    component_positions = {item.component_id: index for index, item in enumerate(components)}
    if len(component_positions) != len(components):
        raise SplitError("duplicate HDFS META-001 component identity")

    counts = array("Q", [0]) * len(components)
    ineligible: list[dict] = []
    eligible_total = 0
    total_raw = 0
    for reference in iter_hdfs_structural_references(log_path, source, component_index):
        if reference.chronological_index != total_raw:
            raise SplitError("HDFS META-001 chronology is not contiguous")
        total_raw += 1
        if reference.assignment_status is HdfsAssignmentStatus.ASSIGNED:
            assert reference.component_id is not None
            try:
                component_position = component_positions[reference.component_id]
            except KeyError as exc:
                raise SplitError("HDFS line references an unknown component") from exc
            counts[component_position] += 1
            eligible_total += 1
        else:
            if reference.record_id is None or reference.unassigned_reason is None:
                raise SplitError("structural HDFS exclusion lacks META-001 provenance")
            record = _common_decision(
                unit_kind="HDFS_RAW_LINE",
                structural_unit_id=reference.record_id,
                chronological_start=reference.chronological_index,
                chronological_end_exclusive=reference.chronological_index + 1,
                disposition="STRUCTURAL_EXCLUSION",
                partition=None,
                exclusion_reason=reference.unassigned_reason.value,
            )
            record.update(
                {
                    "raw_record_id": reference.record_id,
                    "raw_chronological_index": reference.chronological_index,
                    "meta_001_unassigned_reason": reference.unassigned_reason.value,
                }
            )
            ineligible.append(record)

    if total_raw != component_index.lines_scanned or not component_index.complete:
        raise SplitError("HDFS component scan and structural line scan disagree")
    if sum(counts) != eligible_total:
        raise SplitError("HDFS component counts do not reconcile")

    boundaries = cumulative_floor_boundaries(eligible_total)
    offsets = array("Q", [0]) * (len(components) + 1)
    running = 0
    for index, count in enumerate(counts):
        offsets[index] = running
        running += count
    offsets[len(components)] = running
    eligible_ranks = array("Q", [0]) * eligible_total
    raw_indices = array("Q", [0]) * eligible_total
    cursors = array("Q", offsets[:-1])
    partition_masks = bytearray(len(components))
    eligible_rank = 0
    for reference in iter_hdfs_structural_references(log_path, source, component_index):
        if reference.assignment_status is not HdfsAssignmentStatus.ASSIGNED:
            continue
        assert reference.component_id is not None
        position = component_positions[reference.component_id]
        destination = cursors[position]
        eligible_ranks[destination] = eligible_rank
        raw_indices[destination] = reference.chronological_index
        cursors[position] += 1
        partition_masks[position] |= 1 << nominal_partition_index(eligible_rank, boundaries)
        eligible_rank += 1
    if eligible_rank != eligible_total or any(cursors[i] != offsets[i + 1] for i in range(len(components))):
        raise SplitError("HDFS membership arrays did not fill deterministically")

    partition_units = {item.value: 0 for item in PARTITION_ORDER}
    partition_lines = {item.value: 0 for item in PARTITION_ORDER}
    purged_records: list[dict] = []
    purged_lines = 0
    with ExitStack() as stack:
        handles = {
            partition: stack.enter_context(path.open("ab"))
            for partition, path in partition_spools.items()
        }
        for position, component in enumerate(components):
            start_offset, end_offset = offsets[position], offsets[position + 1]
            if end_offset <= start_offset:
                raise SplitError("META-001 component has no eligible raw line")
            ranks = list(eligible_ranks[start_offset:end_offset])
            chronology = list(raw_indices[start_offset:end_offset])
            if ranks != sorted(set(ranks)) or chronology != sorted(set(chronology)):
                raise SplitError("HDFS component chronology/rank membership is not unique")
            mask = partition_masks[position]
            touched = [index for index in range(5) if mask & (1 << index)]
            if len(touched) == 1:
                partition = PARTITION_ORDER[touched[0]]
                disposition = "ASSIGNED"
                reason = None
            elif len(touched) >= 2:
                partition = None
                disposition = "PURGED_BOUNDARY"
                reason = "PURGED_BOUNDARY"
            else:
                raise SplitError("HDFS component did not touch a nominal partition")
            record = _common_decision(
                unit_kind="HDFS_COMPONENT",
                structural_unit_id=component.component_id,
                chronological_start=chronology[0],
                chronological_end_exclusive=chronology[-1] + 1,
                disposition=disposition,
                partition=partition,
                exclusion_reason=reason,
            )
            record.update(
                {
                    "component_id": component.component_id,
                    "block_ids_canonical_order": list(component.block_ids),
                    "eligible_ranks_increasing": ranks,
                    "raw_chronological_indices_increasing": chronology,
                }
            )
            if partition is None:
                purged_records.append(record)
                purged_lines += len(ranks)
            else:
                _write_jsonl_record(handles[partition], record)
                partition_units[partition.value] += 1
                partition_lines[partition.value] += len(ranks)

    exclusions = sorted(
        [*ineligible, *purged_records],
        key=lambda item: (
            item["chronological_start"],
            item["unit_kind"],
            item["structural_unit_id"],
        ),
    )
    with exclusion_spool.open("ab") as handle:
        for record in exclusions:
            _write_jsonl_record(handle, record)

    assigned_lines = sum(partition_lines.values())
    ineligible_lines = len(ineligible)
    if total_raw != ineligible_lines + assigned_lines + purged_lines:
        raise SplitError("HDFS total-raw reconciliation failed")
    if assigned_lines != sum(partition_lines.values()) or assigned_lines + purged_lines != eligible_total:
        raise SplitError("HDFS eligible-line reconciliation failed")
    target_counts = {
        PARTITION_ORDER[index].value: boundaries[index + 1] - boundaries[index]
        for index in range(5)
    }
    target_ratios = {
        key: (None if eligible_total == 0 else value / eligible_total)
        for key, value in target_counts.items()
    }
    realized_ratios = {
        key: (None if assigned_lines == 0 else value / assigned_lines)
        for key, value in partition_lines.items()
    }
    return {
        "dataset_key": "hdfs",
        "source_metadata_contract": "META-001",
        "source_id": source.source_id,
        "allocation_unit": "eligible_raw_line_rank",
        "boundaries": list(boundaries),
        "total_raw_lines": total_raw,
        "eligible_lines_pre_purge": eligible_total,
        "structurally_ineligible_lines": ineligible_lines,
        "component_count": len(components),
        "purged_component_count": len(purged_records),
        "purged_boundary_eligible_lines": purged_lines,
        "assigned_eligible_lines": assigned_lines,
        "partition_structural_unit_counts": partition_units,
        "partition_assigned_line_counts": partition_lines,
        "target_nominal_line_counts": target_counts,
        "target_nominal_ratios": target_ratios,
        "realized_assigned_line_ratios": realized_ratios,
        "purge_ratio": None if eligible_total == 0 else purged_lines / eligible_total,
        "execution_ready": assigned_lines > 0,
        "reconciliation": {
            "raw": [total_raw, ineligible_lines, assigned_lines, purged_lines],
            "assigned": [assigned_lines, *partition_lines.values()],
        },
    }


def _count_raw_lines(path: Path) -> int:
    count = 0
    with path.open("rb") as handle:
        for count, _ in enumerate(handle, start=1):
            pass
    return count


def _bgl_structural_id(prefix: str, source: MetadataSource, partition: ScientificPartition, start: int, end: int) -> str:
    payload = {
        "source_id": source.source_id,
        "partition": partition.value,
        "raw_rank_start_inclusive": start,
        "raw_rank_end_exclusive": end,
    }
    return f"{prefix}-{sha256_canonical(payload)}"


def _bgl_decisions(
    *,
    log_path: Path,
    source: MetadataSource,
    partition_spools: dict[ScientificPartition, Path],
    exclusion_spool: Path,
) -> dict:
    """Build ranges from line count only; inline label bytes are never parsed."""

    total_raw = _count_raw_lines(log_path)
    boundaries = cumulative_floor_boundaries(total_raw)
    raw_counts: dict[str, int] = {}
    window_counts: dict[str, int] = {}
    residual_counts: dict[str, int] = {}
    retained_counts: dict[str, int] = {}
    exclusions: list[dict] = []
    for index, partition in enumerate(PARTITION_ORDER):
        raw_start, raw_end = boundaries[index], boundaries[index + 1]
        raw_count = raw_end - raw_start
        complete_windows, residual = divmod(raw_count, 100)
        raw_counts[partition.value] = raw_count
        window_counts[partition.value] = complete_windows
        residual_counts[partition.value] = residual
        retained_counts[partition.value] = complete_windows * 100
        with partition_spools[partition].open("ab") as handle:
            for ordinal in range(complete_windows):
                start = raw_start + ordinal * 100
                end = start + 100
                unit_id = _bgl_structural_id("BGL-PARENT", source, partition, start, end)
                record = _common_decision(
                    unit_kind="BGL_PARENT_WINDOW",
                    structural_unit_id=unit_id,
                    chronological_start=start,
                    chronological_end_exclusive=end,
                    disposition="ASSIGNED",
                    partition=partition,
                    exclusion_reason=None,
                )
                record.update(
                    {
                        "raw_rank_start_inclusive": start,
                        "raw_rank_end_exclusive": end,
                        "raw_line_count": 100,
                        "parent_ordinal_within_partition_or_null": ordinal,
                    }
                )
                _write_jsonl_record(handle, record)
        if residual:
            start = raw_start + complete_windows * 100
            unit_id = _bgl_structural_id("BGL-RESIDUAL", source, partition, start, raw_end)
            record = _common_decision(
                unit_kind="BGL_RESIDUAL_RANGE",
                structural_unit_id=unit_id,
                chronological_start=start,
                chronological_end_exclusive=raw_end,
                disposition="DROPPED_RESIDUAL_WINDOW",
                partition=None,
                exclusion_reason="DROPPED_RESIDUAL_WINDOW",
            )
            record.update(
                {
                    "raw_rank_start_inclusive": start,
                    "raw_rank_end_exclusive": raw_end,
                    "raw_line_count": residual,
                    "parent_ordinal_within_partition_or_null": None,
                    "nominal_partition": partition.value,
                }
            )
            exclusions.append(record)
    exclusions.sort(
        key=lambda item: (
            item["chronological_start"],
            item["unit_kind"],
            item["structural_unit_id"],
        )
    )
    with exclusion_spool.open("ab") as handle:
        for record in exclusions:
            _write_jsonl_record(handle, record)
    retained_total = sum(retained_counts.values())
    residual_total = sum(residual_counts.values())
    if total_raw != retained_total + residual_total:
        raise SplitError("BGL raw-line reconciliation failed")
    return {
        "dataset_key": "bgl",
        "source_metadata_contract": "META-001",
        "source_id": source.source_id,
        "allocation_unit": "raw_source_line_rank",
        "split_before_parent_window": True,
        "parent_window_size": 100,
        "parent_window_stride": 100,
        "boundaries": list(boundaries),
        "total_raw_lines": total_raw,
        "partition_raw_line_counts": raw_counts,
        "partition_complete_parent_window_counts": window_counts,
        "partition_retained_line_counts": retained_counts,
        "partition_residual_line_counts": residual_counts,
        "target_raw_line_ratios": {
            key: (None if total_raw == 0 else value / total_raw)
            for key, value in raw_counts.items()
        },
        "realized_retained_line_ratios": {
            key: (None if retained_total == 0 else value / retained_total)
            for key, value in retained_counts.items()
        },
        "complete_parent_windows": sum(window_counts.values()),
        "complete_window_lines": retained_total,
        "residual_excluded_lines": residual_total,
        "execution_ready": retained_total > 0,
        "reconciliation": {"raw": [total_raw, retained_total, residual_total]},
    }


def _canonical_payload_header(source: MetadataSource, dataset_semantics: dict) -> dict:
    return {
        "schema_version": SPLIT_SCHEMA_VERSION,
        "dataset_fingerprint": source.dataset_fingerprint,
        "protocol": {"id": PROTOCOL_ID, "version": PROTOCOL_VERSION},
        "split_contract": {"id": SPLIT_CONTRACT_ID, "version": SPLIT_CONTRACT_VERSION},
        "partition_order": [item.value for item in PARTITION_ORDER],
        "target_ratios": {item.value: TARGET_RATIOS[item] for item in PARTITION_ORDER},
        "boundary_contract": {
            "algorithm": "cumulative_floor",
            "integer_denominator": BOUNDARY_DENOMINATOR,
            "integer_numerators": list(BOUNDARY_NUMERATORS),
        },
        "dataset_semantics": dataset_semantics,
    }


def _iter_record_bytes(paths: Iterable[Path], *, strip_assignment_id: bool = False) -> Iterator[bytes]:
    for path in paths:
        for record in _read_jsonl(path):
            if strip_assignment_id:
                record.pop("assignment_id", None)
            yield _canonical_bytes(record)


def _iter_canonical_object_chunks(
    fixed: dict,
    streamed: dict[str, Iterable[bytes]],
) -> Iterator[bytes]:
    keys = sorted([*fixed, *streamed])
    yield b"{"
    for key_index, key in enumerate(keys):
        if key_index:
            yield b","
        yield _canonical_bytes(key)
        yield b":"
        if key in fixed:
            yield _canonical_bytes(fixed[key])
            continue
        yield b"["
        first = True
        for record in streamed[key]:
            if not first:
                yield b","
            yield record
            first = False
        yield b"]"
    yield b"}"


def _write_canonical_payload(
    staging: Path,
    header: dict,
    partition_spools: dict[ScientificPartition, Path],
    exclusion_spool: Path,
) -> tuple[str, dict]:
    path = staging / "split-payload.json.gz"
    digest = hashlib.sha256()
    with path.open("xb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as compressed:
            chunks = _iter_canonical_object_chunks(
                header,
                {
                    "assignments": _iter_record_bytes(
                        [partition_spools[item] for item in PARTITION_ORDER]
                    ),
                    "exclusions": _iter_record_bytes([exclusion_spool]),
                },
            )
            for chunk in chunks:
                digest.update(chunk)
                compressed.write(chunk)
    artifact = _artifact_file(staging, path, record_count=None)
    return digest.hexdigest(), artifact


def _assignment_id(dataset_fingerprint: str, split_payload_hash: str, record: dict) -> str:
    identity = {
        "dataset_fingerprint": dataset_fingerprint,
        "protocol": {"id": PROTOCOL_ID, "version": PROTOCOL_VERSION},
        "split_contract": {"id": SPLIT_CONTRACT_ID, "version": SPLIT_CONTRACT_VERSION},
        "split_payload_hash": split_payload_hash,
        "structural_unit_identity": {
            "unit_kind": record["unit_kind"],
            "structural_unit_id": record["structural_unit_id"],
            "chronological_start": record["chronological_start"],
            "chronological_end_exclusive": record["chronological_end_exclusive"],
        },
        "disposition": record["disposition"],
        "assigned_partition_or_null": record["partition_or_null"],
        "exclusion_reason_or_null": record["exclusion_reason_or_null"],
    }
    return f"PART-{sha256_canonical(identity)}"


def _partition_hash(
    *,
    dataset_fingerprint: str,
    split_payload_hash: str,
    partition: ScientificPartition,
    records: Iterable[dict],
) -> str:
    membership = (
        _canonical_bytes(
            {
                "structural_unit_id": record["structural_unit_id"],
                "chronological_start": record["chronological_start"],
                "chronological_end_exclusive": record["chronological_end_exclusive"],
            }
        )
        for record in records
    )
    fixed = {
        "dataset_fingerprint": dataset_fingerprint,
        "protocol": {"id": PROTOCOL_ID, "version": PROTOCOL_VERSION},
        "split_contract": {"id": SPLIT_CONTRACT_ID, "version": SPLIT_CONTRACT_VERSION},
        "split_payload_hash": split_payload_hash,
        "partition_name": partition.value,
    }
    digest = hashlib.sha256()
    for chunk in _iter_canonical_object_chunks(
        fixed, {"ordered_structural_membership": membership}
    ):
        digest.update(chunk)
    return digest.hexdigest()


def _artifact_file(staging: Path, path: Path, *, record_count: int | None) -> dict:
    return {
        "path": path.relative_to(staging).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
        "record_count": record_count,
    }


def _persist_decisions(
    *,
    staging: Path,
    source: MetadataSource,
    split_payload_hash: str,
    partition_spools: dict[ScientificPartition, Path],
    exclusion_spool: Path,
) -> tuple[dict[str, str], dict[str, str], dict, list[dict]]:
    partition_hashes: dict[str, str] = {}
    public_files: dict[str, str] = {}
    artifacts: list[dict] = []
    (staging / "partitions").mkdir()
    (staging / "sealed").mkdir()
    for partition in PARTITION_ORDER:
        source_path = partition_spools[partition]
        destination = (
            staging / "sealed/TEST.jsonl"
            if partition is ScientificPartition.TEST
            else staging / f"partitions/{partition.value}.jsonl"
        )
        count = 0
        digest = hashlib.sha256()
        partition_hashes[partition.value] = _partition_hash(
            dataset_fingerprint=source.dataset_fingerprint,
            split_payload_hash=split_payload_hash,
            partition=partition,
            records=_read_jsonl(source_path),
        )
        with destination.open("xb") as output:
            for record in _read_jsonl(source_path):
                persisted = {
                    "assignment_id": _assignment_id(
                        source.dataset_fingerprint, split_payload_hash, record
                    ),
                    **record,
                }
                payload = _canonical_bytes(persisted) + b"\n"
                output.write(payload)
                digest.update(payload)
                count += 1
        artifact = {
            "path": destination.relative_to(staging).as_posix(),
            "size_bytes": destination.stat().st_size,
            "sha256": digest.hexdigest(),
            "record_count": count,
        }
        artifacts.append(artifact)
        if partition is not ScientificPartition.TEST:
            public_files[partition.value] = artifact["path"]
        source_path.unlink()

    exclusion_destination = staging / "exclusions.jsonl"
    count = 0
    digest = hashlib.sha256()
    with exclusion_destination.open("xb") as output:
        for record in _read_jsonl(exclusion_spool):
            persisted = {
                "assignment_id": _assignment_id(
                    source.dataset_fingerprint, split_payload_hash, record
                ),
                **record,
            }
            payload = _canonical_bytes(persisted) + b"\n"
            output.write(payload)
            digest.update(payload)
            count += 1
    exclusion_artifact = {
        "path": "exclusions.jsonl",
        "size_bytes": exclusion_destination.stat().st_size,
        "sha256": digest.hexdigest(),
        "record_count": count,
    }
    artifacts.append(exclusion_artifact)
    exclusion_spool.unlink()
    return partition_hashes, public_files, exclusion_artifact, artifacts


def _git_provenance(root: Path) -> dict:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return {"revision": revision, "dirty": bool(status)}
    except (OSError, subprocess.CalledProcessError):
        return {"revision": None, "dirty": None}


def generate_split_artifact(
    *,
    project_root: str | Path,
    dataset_key: str,
    output_directory: str | Path | None = None,
    generated_at_utc: str | None = None,
) -> dict:
    """Generate and atomically publish one sealed real/synthetic split tree."""

    if dataset_key not in {"hdfs", "bgl"}:
        raise SplitError("SPLIT-001 supports only hdfs and bgl")
    root = Path(project_root).resolve()
    validate_frozen_split_prerequisites(root, require_authorized=True)
    config = load_dataset_config(dataset_key, config_dir=root / "configs/datasets")
    source, log_path = resolve_metadata_source(config, project_root=root)
    destination = (
        Path(output_directory)
        if output_directory is not None
        else root / f"data/processed/splits/{dataset_key}"
    )
    if not destination.is_absolute():
        destination = (root / destination).resolve()
    else:
        destination = destination.resolve()
    if destination.exists():
        raise SplitError(f"split output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.tmp"
    if staging.exists():
        raise SplitError(f"stale split staging directory exists: {staging}")
    staging.mkdir()
    timestamp = generated_at_utc or _utc_now()
    try:
        partition_spools, exclusion_spool = _decision_spool_paths(staging)
        if dataset_key == "hdfs":
            component_index = scan_hdfs_components(log_path, source)
            semantics = _hdfs_decisions(
                log_path=log_path,
                source=source,
                component_index=component_index,
                partition_spools=partition_spools,
                exclusion_spool=exclusion_spool,
            )
        else:
            semantics = _bgl_decisions(
                log_path=log_path,
                source=source,
                partition_spools=partition_spools,
                exclusion_spool=exclusion_spool,
            )
        header = _canonical_payload_header(source, semantics)
        split_payload_hash, payload_artifact = _write_canonical_payload(
            staging, header, partition_spools, exclusion_spool
        )
        partition_hashes, public_files, exclusion_artifact, artifacts = _persist_decisions(
            staging=staging,
            source=source,
            split_payload_hash=split_payload_hash,
            partition_spools=partition_spools,
            exclusion_spool=exclusion_spool,
        )
        shutil.rmtree(staging / ".decision-spool")
        seal = create_sealed_test_state(
            staging,
            binding=SealBinding(
                dataset_key=dataset_key,
                dataset_fingerprint=source.dataset_fingerprint,
                protocol_version=PROTOCOL_VERSION,
                split_payload_hash=split_payload_hash,
                test_partition_hash=partition_hashes[ScientificPartition.TEST.value],
            ),
            created_at_utc=timestamp,
        )
        seal_artifact = _artifact_file(staging, staging / "test-seal.json", record_count=None)
        audit_artifact = _artifact_file(
            staging, staging / "test-access-audit.jsonl", record_count=0
        )
        artifacts.extend([payload_artifact, seal_artifact, audit_artifact])
        manifest = {
            "schema_version": SPLIT_SCHEMA_VERSION,
            "artifact_type": "DERIVED_SCIENTIFIC_STRUCTURAL_ARTIFACT",
            "dataset": {
                "key": dataset_key,
                "dataset_id": source.dataset_id,
                "dataset_version": source.dataset_version,
                "dataset_fingerprint": source.dataset_fingerprint,
                "source_id": source.source_id,
                "source_file": source.source_file,
                "source_file_sha256": source.source_file_sha256,
            },
            "protocol": {"id": PROTOCOL_ID, "version": PROTOCOL_VERSION},
            "split_contract": {"id": SPLIT_CONTRACT_ID, "version": SPLIT_CONTRACT_VERSION},
            "identity": {
                "split_payload_hash": split_payload_hash,
                "split_manifest_id": f"SPLIT-{split_payload_hash}",
                "partition_hashes": partition_hashes,
            },
            "partition_order": [item.value for item in PARTITION_ORDER],
            "target_ratios": {item.value: TARGET_RATIOS[item] for item in PARTITION_ORDER},
            "boundary_contract": header["boundary_contract"],
            "dataset_semantics": semantics,
            "partition_files": public_files,
            "sealed_test": {
                "seal_path": "test-seal.json",
                "membership_path": seal.test_membership_path,
                "status": "SEALED",
                "never_opened": True,
                "open_count": 0,
                "unlock_records": 0,
            },
            "exclusions_file": exclusion_artifact["path"],
            "canonical_payload_file": payload_artifact["path"],
            "artifact_files": sorted(artifacts, key=lambda item: item["path"]),
            "generation": {
                "generated_at_utc": timestamp,
                "git": _git_provenance(root),
                "labels_used": False,
                "parser_used": False,
                "templates_used": False,
                "scientific_metrics_computed": False,
            },
        }
        manifest_path = staging / "split-manifest.json"
        _atomic_json(manifest_path, manifest)
        manifest_hash = _sha256_file(manifest_path)
        sidecar = staging / "split-manifest.json.sha256"
        sidecar.write_text(f"{manifest_hash}  split-manifest.json\n", encoding="ascii")
        staging.replace(destination)
        return {
            "dataset": dataset_key,
            "output_directory": destination.as_posix(),
            "split_payload_hash": split_payload_hash,
            "partition_hashes": partition_hashes,
            "manifest_file_hash": manifest_hash,
            "test_status": "SEALED",
            "never_opened": True,
            "open_count": 0,
            "unlock_records": 0,
            "dataset_semantics": semantics,
        }
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def _load_manifest(split_directory: Path) -> dict:
    path = split_directory / "split-manifest.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SplitError(f"invalid split manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise SplitError("split manifest must be an object")
    return value


def _validate_assignment_id(record: dict, dataset_fingerprint: str, split_hash: str) -> None:
    assignment_id = record.get("assignment_id")
    raw = dict(record)
    raw.pop("assignment_id", None)
    expected = _assignment_id(dataset_fingerprint, split_hash, raw)
    if not isinstance(assignment_id, str) or not _ASSIGNMENT_ID.fullmatch(assignment_id) or assignment_id != expected:
        raise SplitError("partition assignment ID is stale or invalid")


def _bit_mark(bits: bytearray, index: int, *, universe: int) -> None:
    if not 0 <= index < universe:
        raise SplitError("structural member is outside the declared universe")
    byte_index, mask = divmod(index, 8)
    flag = 1 << mask
    if bits[byte_index] & flag:
        raise SplitError("structural universe member appears more than once")
    bits[byte_index] |= flag


def _bit_count(bits: bytearray) -> int:
    return sum(item.bit_count() for item in bits)


def _validate_hdfs_records(split_directory: Path, manifest: dict) -> dict:
    semantics = manifest["dataset_semantics"]
    total_raw = semantics["total_raw_lines"]
    eligible_total = semantics["eligible_lines_pre_purge"]
    eligible_bits = bytearray((eligible_total + 7) // 8)
    raw_bits = bytearray((total_raw + 7) // 8)
    component_ids: set[str] = set()
    partition_lines = {item.value: 0 for item in PARTITION_ORDER}
    partition_units = {item.value: 0 for item in PARTITION_ORDER}
    dataset_fingerprint = manifest["dataset"]["dataset_fingerprint"]
    split_hash = manifest["identity"]["split_payload_hash"]
    for partition in PARTITION_ORDER:
        path = (
            split_directory / manifest["sealed_test"]["membership_path"]
            if partition is ScientificPartition.TEST
            else split_directory / manifest["partition_files"][partition.value]
        )
        for record in _read_jsonl(path):
            _validate_assignment_id(record, dataset_fingerprint, split_hash)
            if record.get("unit_kind") != "HDFS_COMPONENT" or record.get("partition_or_null") != partition.value or record.get("disposition") != "ASSIGNED":
                raise SplitError("invalid assigned HDFS component record")
            component_id = record["component_id"]
            if component_id in component_ids or component_id != record["structural_unit_id"]:
                raise SplitError("duplicate or inconsistent HDFS component identity")
            component_ids.add(component_id)
            ranks = record["eligible_ranks_increasing"]
            chronology = record["raw_chronological_indices_increasing"]
            if not ranks or len(ranks) != len(chronology) or ranks != sorted(set(ranks)) or chronology != sorted(set(chronology)):
                raise SplitError("invalid HDFS component membership arrays")
            for rank in ranks:
                _bit_mark(eligible_bits, rank, universe=eligible_total)
            for raw_index in chronology:
                _bit_mark(raw_bits, raw_index, universe=total_raw)
            partition_lines[partition.value] += len(ranks)
            partition_units[partition.value] += 1
    purged_components = ineligible = purged_lines = 0
    for record in _read_jsonl(split_directory / manifest["exclusions_file"]):
        _validate_assignment_id(record, dataset_fingerprint, split_hash)
        if record.get("disposition") == "PURGED_BOUNDARY":
            if record.get("unit_kind") != "HDFS_COMPONENT":
                raise SplitError("HDFS purge must apply to a whole component")
            component_id = record["component_id"]
            if component_id in component_ids:
                raise SplitError("HDFS component appears assigned and purged")
            component_ids.add(component_id)
            ranks = record["eligible_ranks_increasing"]
            chronology = record["raw_chronological_indices_increasing"]
            if len(ranks) != len(chronology) or not ranks:
                raise SplitError("purged HDFS component membership is invalid")
            for rank in ranks:
                _bit_mark(eligible_bits, rank, universe=eligible_total)
            for raw_index in chronology:
                _bit_mark(raw_bits, raw_index, universe=total_raw)
            purged_components += 1
            purged_lines += len(ranks)
        elif record.get("disposition") == "STRUCTURAL_EXCLUSION":
            if record.get("unit_kind") != "HDFS_RAW_LINE":
                raise SplitError("HDFS structural exclusion must identify one raw line")
            _bit_mark(raw_bits, record["raw_chronological_index"], universe=total_raw)
            ineligible += 1
        else:
            raise SplitError("unsupported HDFS exclusion disposition")
    if _bit_count(eligible_bits) != eligible_total or _bit_count(raw_bits) != total_raw:
        raise SplitError("HDFS assignment/exclusion universe does not reconcile")
    assigned = sum(partition_lines.values())
    if total_raw != ineligible + assigned + purged_lines or eligible_total != assigned + purged_lines:
        raise SplitError("HDFS numerical reconciliation failed")
    if (
        partition_lines != semantics["partition_assigned_line_counts"]
        or partition_units != semantics["partition_structural_unit_counts"]
        or len(component_ids) != semantics["component_count"]
        or purged_components != semantics["purged_component_count"]
    ):
        raise SplitError("HDFS manifest summary differs from records")
    return {"assigned_lines": assigned, "purged_lines": purged_lines, "ineligible_lines": ineligible}


def _validate_bgl_records(split_directory: Path, manifest: dict) -> dict:
    semantics = manifest["dataset_semantics"]
    total_raw = semantics["total_raw_lines"]
    intervals: list[tuple[int, int]] = []
    dataset_fingerprint = manifest["dataset"]["dataset_fingerprint"]
    split_hash = manifest["identity"]["split_payload_hash"]
    windows = {item.value: 0 for item in PARTITION_ORDER}
    retained = {item.value: 0 for item in PARTITION_ORDER}
    for partition in PARTITION_ORDER:
        path = (
            split_directory / manifest["sealed_test"]["membership_path"]
            if partition is ScientificPartition.TEST
            else split_directory / manifest["partition_files"][partition.value]
        )
        previous_end: int | None = None
        for record in _read_jsonl(path):
            _validate_assignment_id(record, dataset_fingerprint, split_hash)
            start, end = record["raw_rank_start_inclusive"], record["raw_rank_end_exclusive"]
            if (
                record.get("unit_kind") != "BGL_PARENT_WINDOW"
                or record.get("partition_or_null") != partition.value
                or record.get("disposition") != "ASSIGNED"
                or end - start != 100
                or record.get("raw_line_count") != 100
                or (previous_end is not None and start != previous_end)
            ):
                raise SplitError("invalid BGL parent window")
            previous_end = end
            intervals.append((start, end))
            windows[partition.value] += 1
            retained[partition.value] += 100
    residuals = {item.value: 0 for item in PARTITION_ORDER}
    for record in _read_jsonl(split_directory / manifest["exclusions_file"]):
        _validate_assignment_id(record, dataset_fingerprint, split_hash)
        start, end = record["raw_rank_start_inclusive"], record["raw_rank_end_exclusive"]
        count = end - start
        nominal = record.get("nominal_partition")
        if (
            record.get("unit_kind") != "BGL_RESIDUAL_RANGE"
            or record.get("disposition") != "DROPPED_RESIDUAL_WINDOW"
            or record.get("partition_or_null") is not None
            or not 1 <= count <= 99
            or record.get("raw_line_count") != count
            or nominal not in residuals
        ):
            raise SplitError("invalid BGL residual exclusion")
        intervals.append((start, end))
        residuals[nominal] += count
    intervals.sort()
    cursor = 0
    for start, end in intervals:
        if start != cursor or end <= start:
            raise SplitError("BGL raw-line universe has overlap or a gap")
        cursor = end
    if cursor != total_raw:
        raise SplitError("BGL raw-line universe does not reconcile")
    if (
        windows != semantics["partition_complete_parent_window_counts"]
        or retained != semantics["partition_retained_line_counts"]
        or residuals != semantics["partition_residual_line_counts"]
    ):
        raise SplitError("BGL manifest summary differs from records")
    return {"complete_windows": sum(windows.values()), "retained_lines": sum(retained.values()), "residual_lines": sum(residuals.values())}


def _recompute_split_payload_hash(split_directory: Path, manifest: dict) -> str:
    fixed = {
        "schema_version": SPLIT_SCHEMA_VERSION,
        "dataset_fingerprint": manifest["dataset"]["dataset_fingerprint"],
        "protocol": manifest["protocol"],
        "split_contract": manifest["split_contract"],
        "partition_order": manifest["partition_order"],
        "target_ratios": manifest["target_ratios"],
        "boundary_contract": manifest["boundary_contract"],
        "dataset_semantics": manifest["dataset_semantics"],
    }
    paths = [
        (
            split_directory / manifest["sealed_test"]["membership_path"]
            if partition is ScientificPartition.TEST
            else split_directory / manifest["partition_files"][partition.value]
        )
        for partition in PARTITION_ORDER
    ]
    digest = hashlib.sha256()
    chunks = _iter_canonical_object_chunks(
        fixed,
        {
            "assignments": _iter_record_bytes(paths, strip_assignment_id=True),
            "exclusions": _iter_record_bytes(
                [split_directory / manifest["exclusions_file"]],
                strip_assignment_id=True,
            ),
        },
    )
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()


def validate_split_artifact(split_directory: str | Path) -> dict:
    """Independently verify hashes, records, reconciliation, and sealed state."""

    root = Path(split_directory).resolve()
    manifest = _load_manifest(root)
    if manifest.get("schema_version") != SPLIT_SCHEMA_VERSION:
        raise SplitError("unsupported split-manifest schema")
    if manifest.get("protocol") != {"id": PROTOCOL_ID, "version": PROTOCOL_VERSION}:
        raise SplitError("unsupported scientific protocol identity")
    if manifest.get("split_contract") != {"id": SPLIT_CONTRACT_ID, "version": SPLIT_CONTRACT_VERSION}:
        raise SplitError("unsupported split-contract identity")
    split_hash = manifest.get("identity", {}).get("split_payload_hash")
    if not isinstance(split_hash, str) or not _SHA256.fullmatch(split_hash):
        raise SplitError("split payload hash is missing or invalid")
    if manifest["identity"].get("split_manifest_id") != f"SPLIT-{split_hash}":
        raise SplitError("split manifest ID does not match payload hash")
    sidecar_parts = (root / "split-manifest.json.sha256").read_text(encoding="ascii").split()
    manifest_hash = _sha256_file(root / "split-manifest.json")
    if sidecar_parts != [manifest_hash, "split-manifest.json"]:
        raise SplitError("manifest file-hash sidecar is stale")

    for artifact in manifest.get("artifact_files", []):
        path = root / _safe_relative_path(artifact["path"])
        if not path.is_file() or path.stat().st_size != artifact["size_bytes"] or _sha256_file(path) != artifact["sha256"]:
            raise SplitError(f"split artifact integrity mismatch: {artifact['path']}")
        if artifact["record_count"] is not None:
            count = sum(1 for line in path.open("rb") if line.strip())
            if count != artifact["record_count"]:
                raise SplitError(f"split artifact record count mismatch: {artifact['path']}")

    payload_path = root / manifest["canonical_payload_file"]
    payload_digest = hashlib.sha256()
    with gzip.open(payload_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            payload_digest.update(chunk)
    if payload_digest.hexdigest() != split_hash:
        raise SplitError("persisted canonical split payload hash mismatch")
    recomputed = _recompute_split_payload_hash(root, manifest)
    if recomputed != split_hash:
        raise SplitError("manifest records do not reproduce the scientific split identity")

    dataset_key = manifest.get("dataset", {}).get("key")
    structural = (
        _validate_hdfs_records(root, manifest)
        if dataset_key == "hdfs"
        else _validate_bgl_records(root, manifest)
        if dataset_key == "bgl"
        else None
    )
    if structural is None:
        raise SplitError("unsupported dataset in split manifest")
    partition_hashes: dict[str, str] = {}
    for partition in PARTITION_ORDER:
        path = (
            root / manifest["sealed_test"]["membership_path"]
            if partition is ScientificPartition.TEST
            else root / manifest["partition_files"][partition.value]
        )
        partition_hashes[partition.value] = _partition_hash(
            dataset_fingerprint=manifest["dataset"]["dataset_fingerprint"],
            split_payload_hash=split_hash,
            partition=partition,
            records=(
                {key: value for key, value in record.items() if key != "assignment_id"}
                for record in _read_jsonl(path)
            ),
        )
    if partition_hashes != manifest["identity"]["partition_hashes"]:
        raise SplitError("partition hash mismatch")
    seal = assert_test_access_denied(root)
    expected_binding = SealBinding(
        dataset_key=dataset_key,
        dataset_fingerprint=manifest["dataset"]["dataset_fingerprint"],
        protocol_version=PROTOCOL_VERSION,
        split_payload_hash=split_hash,
        test_partition_hash=partition_hashes[ScientificPartition.TEST.value],
    )
    if seal.binding != expected_binding:
        raise SplitError("TEST seal is bound to another split identity")
    return {
        "dataset": dataset_key,
        "status": "VERIFIED",
        "split_payload_hash": split_hash,
        "partition_hashes": partition_hashes,
        "manifest_file_hash": manifest_hash,
        "structural_reconciliation": structural,
        "test_status": seal.status,
        "never_opened": seal.never_opened,
        "open_count": seal.open_count,
        "unlock_records": seal.unlock_records,
    }


def compare_split_artifacts(first: str | Path, second: str | Path) -> dict:
    """Compare deterministic scientific fields while ignoring audit timestamp."""

    first_root, second_root = Path(first), Path(second)
    left, right = _load_manifest(first_root), _load_manifest(second_root)
    fields = {
        "split_payload_hash": (
            left["identity"]["split_payload_hash"],
            right["identity"]["split_payload_hash"],
        ),
        "partition_hashes": (
            left["identity"]["partition_hashes"],
            right["identity"]["partition_hashes"],
        ),
        "dataset_semantics": (left["dataset_semantics"], right["dataset_semantics"]),
        "artifact_content": (
            {
                item["path"]: item["sha256"]
                for item in left["artifact_files"]
                if item["path"] not in {"test-seal.json"}
            },
            {
                item["path"]: item["sha256"]
                for item in right["artifact_files"]
                if item["path"] not in {"test-seal.json"}
            },
        ),
    }
    mismatches = [name for name, (a, b) in fields.items() if a != b]
    return {"deterministic": not mismatches, "mismatches": mismatches}


def iter_partition_assignments(
    split_directory: str | Path,
    partition: ScientificPartition,
) -> Iterator[dict]:
    """Ordinary loader; TEST is rejected before resolving its record path."""

    if partition is ScientificPartition.TEST:
        deny_ordinary_test_access()
    root = Path(split_directory).resolve()
    manifest = _load_manifest(root)
    try:
        relative = manifest["partition_files"][partition.value]
    except KeyError as exc:
        raise SplitError(f"partition membership is unavailable: {partition.value}") from exc
    yield from _read_jsonl(root / _safe_relative_path(relative))


def iter_final_test_assignments(
    split_directory: str | Path,
    grant: TestAccessGrant,
) -> Iterator[dict]:
    """Dedicated future path; consuming the grant precedes record access."""

    _, _ = validate_unconsumed_grant(split_directory, grant)
    membership_path = consume_human_test_grant(split_directory, grant)
    yield from _read_jsonl(membership_path)


def split_status(split_directory: str | Path) -> dict:
    root = Path(split_directory).resolve()
    manifest = _load_manifest(root)
    seal = load_test_seal(root)
    return {
        "dataset": manifest["dataset"]["key"],
        "split_payload_hash": manifest["identity"]["split_payload_hash"],
        "test_partition_hash": manifest["identity"]["partition_hashes"]["TEST"],
        "test_status": seal.status,
        "never_opened": seal.never_opened,
        "open_count": seal.open_count,
        "unlock_records": seal.unlock_records,
    }


__all__ = [
    "BOUNDARY_DENOMINATOR",
    "BOUNDARY_NUMERATORS",
    "PARTITION_ORDER",
    "PROTOCOL_ID",
    "PROTOCOL_VERSION",
    "SPLIT_CONTRACT_ID",
    "SPLIT_CONTRACT_VERSION",
    "SPLIT_SCHEMA_VERSION",
    "SplitError",
    "TARGET_RATIOS",
    "compare_split_artifacts",
    "cumulative_floor_boundaries",
    "generate_split_artifact",
    "iter_final_test_assignments",
    "iter_partition_assignments",
    "nominal_partition_index",
    "split_status",
    "validate_frozen_split_prerequisites",
    "validate_split_artifact",
]
