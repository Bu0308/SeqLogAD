"""Deterministic non-TEST canonical-event generation.

CANONICAL-EVENT-001 consumes only frozen SPLIT-001 membership and frozen
PARSE-001 inference artifacts.  It deliberately keeps scientific TEST sealed,
never updates Drain3, and separates label-free canonical event identity from
controlled supervision metadata stored in the exact artifact bytes.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import itertools
import json
import os
import shutil
from array import array
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Callable, Final, Iterable, Iterator, Mapping

import yaml

from seqlogad.common.checksum import sha256_file
from seqlogad.common.schemas.events import (
    AnomalyLabel,
    EventObservation,
    EventProvenance,
    EventSupervision,
    GroupKind,
    LabelAccess,
    LabelGranularity,
    LabelSourceKind,
    LogEvent,
    ScientificPartition,
    UNSEEN_EVENT_ID,
    build_record_id,
)
from seqlogad.evaluation.split import (
    iter_partition_assignments,
    split_status,
    validate_split_artifact,
)
from seqlogad.ingestion.dataset_config import (
    load_dataset_config,
    resolve_repository_path,
)
from seqlogad.ingestion.dataset_manifest import verify_dataset_manifest
from seqlogad.parsing.drain_parser import (
    PARSER_IMPLEMENTATION_VERSION,
    FrozenDrainParser,
    FrozenTransformResult,
    load_frozen_parser,
    validate_parser_artifact,
)
from seqlogad.parsing.normalization import (
    MessageExtractionError,
    extract_bgl_record,
    extract_hdfs_message,
)


CANONICAL_ARTIFACT_SCHEMA_VERSION: Final = "1.0"
CANONICAL_IMPLEMENTATION_VERSION: Final = "seqlogad-canonical-event-001-v1"
PROTOCOL_VERSION: Final = "1.1"
AUTHORIZED_PARTITIONS: Final = (
    ScientificPartition.BASE_TRAIN,
    ScientificPartition.FUSION_TRAIN,
    ScientificPartition.VAL_EXPERT,
    ScientificPartition.VAL_FUSION,
)
TRAINING_PARTITIONS: Final = frozenset(
    {ScientificPartition.BASE_TRAIN, ScientificPartition.FUSION_TRAIN}
)
VALIDATION_PARTITIONS: Final = frozenset(
    {ScientificPartition.VAL_EXPERT, ScientificPartition.VAL_FUSION}
)
DEFAULT_BATCH_SIZE: Final = 4096


class CanonicalEventError(RuntimeError):
    """Raised when a frozen identity, boundary, or reconciliation fails."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanonicalEventError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise CanonicalEventError(f"JSON artifact must be an object: {path}")
    return value


def _load_yaml(path: Path) -> dict:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CanonicalEventError(f"invalid YAML artifact: {path}") from exc
    if not isinstance(value, dict):
        raise CanonicalEventError(f"YAML artifact must be an object: {path}")
    return value


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
        raise CanonicalEventError("artifact path must be repository-relative POSIX")
    return value


def _sha256_raw_line(raw_line: bytes) -> str:
    return hashlib.sha256(raw_line).hexdigest()


def _partition_path(partition: ScientificPartition) -> str:
    if partition is ScientificPartition.TEST:
        raise CanonicalEventError("scientific TEST canonical path is forbidden")
    return f"partitions/{partition.value}.jsonl.gz"


def _label_free_record_payload(record: Mapping[str, object]) -> dict:
    """Return the label-independent scientific identity projection."""

    payload = dict(record)
    payload.pop("canonical_event_sha256", None)
    event = payload.get("event")
    if not isinstance(event, dict):
        raise CanonicalEventError("canonical record event payload is malformed")
    event_without_supervision = dict(event)
    event_without_supervision.pop("supervision", None)
    # BGL's exact source-line hash and derived LOG-* occurrence ID necessarily
    # bind the inline first-column label byte. They remain in the persisted
    # provenance and exact file hash, but cannot define the label-independent
    # canonical transform identity. Source path + one-based line number + raw
    # chronology + assignment identity still bind this projection uniquely.
    event_without_supervision.pop("record_id", None)
    provenance = event_without_supervision.get("provenance")
    if isinstance(provenance, dict):
        provenance_without_exact_line = dict(provenance)
        provenance_without_exact_line.pop("source_line_sha256", None)
        event_without_supervision["provenance"] = provenance_without_exact_line
    payload["event"] = event_without_supervision
    return payload


def canonical_event_sha256(record: Mapping[str, object]) -> str:
    """Hash one event and its structural binding without supervision labels."""

    return _canonical_sha256(_label_free_record_payload(record))


@dataclass(frozen=True, slots=True)
class _Unit:
    partition: ScientificPartition
    assignment_id: str
    structural_unit_id: str
    unit_kind: str
    expected_records: int
    block_ids: tuple[str, ...] = ()
    chronological_start: int = 0
    chronological_end_exclusive: int = 0


@dataclass(frozen=True, slots=True)
class _Pending:
    unit_ordinal: int
    position_within_unit: int
    source_index: int
    raw_line: bytes
    message: str
    supervision: EventSupervision


@dataclass(slots=True)
class _PartitionStats:
    authorized_input_records: int = 0
    authorized_units: int = 0
    emitted_records: int = 0
    emitted_units: int = 0
    matched_records: int = 0
    unseen_records: int = 0
    excluded_records: int = 0
    excluded_units: int = 0
    minimum_source_index: int | None = None
    maximum_source_index: int | None = None

    def as_dict(self) -> dict:
        return {
            "authorized_input_records": self.authorized_input_records,
            "authorized_structural_units": self.authorized_units,
            "emitted_records": self.emitted_records,
            "emitted_structural_units": self.emitted_units,
            "matched_records": self.matched_records,
            "evt_unseen_records": self.unseen_records,
            "explicit_allowed_exclusion_records": self.excluded_records,
            "explicit_allowed_exclusion_units": self.excluded_units,
            "minimum_source_index_or_null": self.minimum_source_index,
            "maximum_source_index_or_null": self.maximum_source_index,
        }


class _CorpusSink:
    """Write deterministic gzip artifacts or operate as a hash-only sink."""

    def __init__(
        self,
        *,
        staging: Path | None,
        identity_headers: Mapping[ScientificPartition, dict],
    ) -> None:
        self.staging = staging
        self.stats = {partition: _PartitionStats() for partition in AUTHORIZED_PARTITIONS}
        self._digests: dict[ScientificPartition, hashlib._Hash] = {}
        self._raw_handles: dict[ScientificPartition, BinaryIO] = {}
        self._gzip_handles: dict[ScientificPartition, gzip.GzipFile] = {}
        self._exclusion_digest = hashlib.sha256()
        self._exclusion_count = 0
        self._exclusion_handle: gzip.GzipFile | None = None
        for partition in AUTHORIZED_PARTITIONS:
            digest = hashlib.sha256()
            digest.update(_canonical_bytes(identity_headers[partition]) + b"\n")
            self._digests[partition] = digest
        if staging is not None:
            (staging / "partitions").mkdir(parents=True)
            for partition in AUTHORIZED_PARTITIONS:
                path = staging / _partition_path(partition)
                raw = path.open("xb")
                zipped = gzip.GzipFile(
                    filename="",
                    mode="wb",
                    fileobj=raw,
                    compresslevel=6,
                    mtime=0,
                )
                self._raw_handles[partition] = raw
                self._gzip_handles[partition] = zipped
            exclusion_raw = (staging / "exclusions.jsonl.gz").open("xb")
            self._raw_handles[ScientificPartition.TEST] = exclusion_raw
            self._exclusion_handle = gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=exclusion_raw,
                compresslevel=6,
                mtime=0,
            )

    def write_record(self, partition: ScientificPartition, record: dict) -> None:
        if partition not in AUTHORIZED_PARTITIONS:
            raise CanonicalEventError("canonical sink rejects non-authorized partition")
        identity_bytes = _canonical_bytes(_label_free_record_payload(record)) + b"\n"
        self._digests[partition].update(identity_bytes)
        payload = _canonical_bytes(record) + b"\n"
        if partition in self._gzip_handles:
            self._gzip_handles[partition].write(payload)

    def write_exclusion(self, record: dict) -> None:
        payload = _canonical_bytes(record) + b"\n"
        self._exclusion_digest.update(payload)
        self._exclusion_count += 1
        if self._exclusion_handle is not None:
            self._exclusion_handle.write(payload)

    def close(self) -> None:
        for handle in self._gzip_handles.values():
            handle.close()
        if self._exclusion_handle is not None:
            self._exclusion_handle.close()
        for handle in self._raw_handles.values():
            handle.flush()
            os.fsync(handle.fileno())
            handle.close()
        self._gzip_handles.clear()
        self._raw_handles.clear()
        self._exclusion_handle = None

    def identity(self) -> dict:
        return {
            "partition_canonical_event_hashes": {
                partition.value: self._digests[partition].hexdigest()
                for partition in AUTHORIZED_PARTITIONS
            },
            "exclusions_payload_sha256": self._exclusion_digest.hexdigest(),
            "exclusion_record_count": self._exclusion_count,
        }


def _active_gate(root: Path, dataset_key: str) -> dict:
    state = _load_yaml(root / "configs/active-state.yaml").get("active_state", {})
    if (
        state.get("next_scientific_task") != "CANONICAL-EVENT-001"
        or state.get("scientific_results_status") != "NOT_RUN"
        or state.get("pipeline", {}).get("CANONICAL-EVENT-001")
        != "AUTHORIZED_NEXT_TASK"
    ):
        raise CanonicalEventError("active state does not authorize CANONICAL-EVENT-001")
    dataset_state = _load_yaml(root / "configs/active-state.yaml").get("datasets", {}).get(
        dataset_key, {}
    )
    if not isinstance(dataset_state, dict):
        raise CanonicalEventError("active dataset identity is missing")
    return dataset_state


def validate_canonical_prerequisites(project_root: str | Path, dataset_key: str) -> dict:
    """Verify frozen identities and TEST seal before any label or raw-log access."""

    if dataset_key not in {"hdfs", "bgl"}:
        raise CanonicalEventError("CANONICAL-EVENT-001 supports only hdfs and bgl")
    root = Path(project_root).resolve()
    active_dataset = _active_gate(root, dataset_key)
    split_directory = root / f"data/processed/splits/{dataset_key}"
    parser_directory = root / f"data/processed/parsers/{dataset_key}"
    split = validate_split_artifact(split_directory)
    seal = split_status(split_directory)
    parser = validate_parser_artifact(parser_directory)
    config = load_dataset_config(dataset_key, config_dir=root / "configs/datasets")
    dataset = verify_dataset_manifest(
        config,
        project_root=root,
        manifest_path=resolve_repository_path(root, config.manifest_path),
    )
    if not dataset.valid:
        raise CanonicalEventError("raw dataset verification failed")
    if (
        seal.get("test_status") != "SEALED"
        or seal.get("never_opened") is not True
        or seal.get("open_count") != 0
        or seal.get("unlock_records") != 0
    ):
        raise CanonicalEventError("scientific TEST is not SEALED / NEVER_OPENED")
    split_hash = split["split_payload_hash"]
    parser_hash = parser["parser_state_sha256"]
    if (
        active_dataset.get("dataset_fingerprint") != dataset.expected_fingerprint
        or active_dataset.get("split", {}).get("split_payload_hash") != split_hash
        or active_dataset.get("parser", {}).get("parser_state_sha256") != parser_hash
    ):
        raise CanonicalEventError("active dataset/split/parser identity mismatch")
    manifest = _load_json(split_directory / "split-manifest.json")
    parser_manifest = _load_json(parser_directory / "parser-manifest.json")
    return {
        "project_root": root,
        "dataset_key": dataset_key,
        "dataset_fingerprint": dataset.expected_fingerprint,
        "split_directory": split_directory,
        "split_manifest": manifest,
        "split_payload_hash": split_hash,
        "partition_hashes": split["partition_hashes"],
        "parser_directory": parser_directory,
        "parser_manifest": parser_manifest,
        "parser_validation": parser,
        "test_status": seal,
    }


def _identity_headers(gate: Mapping[str, object]) -> dict[ScientificPartition, dict]:
    parser_manifest = gate["parser_manifest"]
    assert isinstance(parser_manifest, dict)
    partition_hashes = gate["partition_hashes"]
    assert isinstance(partition_hashes, dict)
    return {
        partition: {
            "schema_version": CANONICAL_ARTIFACT_SCHEMA_VERSION,
            "implementation_version": CANONICAL_IMPLEMENTATION_VERSION,
            "dataset_key": gate["dataset_key"],
            "dataset_fingerprint": gate["dataset_fingerprint"],
            "protocol": {"id": "PROTOCOL-001", "version": PROTOCOL_VERSION},
            "split_payload_hash": gate["split_payload_hash"],
            "partition": partition.value,
            "partition_hash": partition_hashes[partition.value],
            "parser_implementation_version": parser_manifest["software"][
                "implementation_version"
            ],
            "drain3_version": parser_manifest["software"]["drain3_version"],
            "parser_config_sha256": parser_manifest["configuration"][
                "parser_config_sha256"
            ],
            "parser_state_sha256": parser_manifest["identity"]["parser_state_sha256"],
            "template_registry_sha256": parser_manifest["identity"][
                "template_registry_sha256"
            ],
        }
        for partition in AUTHORIZED_PARTITIONS
    }


def _build_record(
    *,
    gate: Mapping[str, object],
    unit: _Unit,
    pending: _Pending,
    result: FrozenTransformResult,
) -> dict:
    split_manifest = gate["split_manifest"]
    parser_manifest = gate["parser_manifest"]
    assert isinstance(split_manifest, dict) and isinstance(parser_manifest, dict)
    dataset = split_manifest["dataset"]
    raw_hash = _sha256_raw_line(pending.raw_line)
    provenance = EventProvenance(
        dataset_key=str(dataset["key"]),
        dataset_id=str(dataset["dataset_id"]),
        dataset_version=str(dataset["dataset_version"]),
        dataset_fingerprint=str(dataset["dataset_fingerprint"]),
        source_file=str(dataset["source_file"]),
        source_line_number=pending.source_index + 1,
        chronological_index=pending.source_index,
        source_line_sha256=raw_hash,
        partition=unit.partition,
        group_kind=(
            GroupKind.HDFS_BLOCK if dataset["key"] == "hdfs" else GroupKind.NONE
        ),
        group_ids=unit.block_ids,
    )
    event = LogEvent(
        record_id=build_record_id(
            dataset_fingerprint=provenance.dataset_fingerprint,
            source_file=provenance.source_file,
            source_line_number=provenance.source_line_number,
            source_line_sha256=provenance.source_line_sha256,
        ),
        provenance=provenance,
        observation=EventObservation(message=pending.message),
        event_id=result.event_id,
        parameters=result.parameters,
        parser_state_sha256=parser_manifest["identity"]["parser_state_sha256"],
        template_registry_sha256=parser_manifest["identity"][
            "template_registry_sha256"
        ],
        supervision=pending.supervision,
    )
    record = {
        "schema_version": CANONICAL_ARTIFACT_SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "split_payload_hash": gate["split_payload_hash"],
        "partition_hash": gate["partition_hashes"][unit.partition.value],
        "assignment_id": unit.assignment_id,
        "structural_unit_id": unit.structural_unit_id,
        "unit_kind": unit.unit_kind,
        "position_within_unit": pending.position_within_unit,
        "parser_implementation_version": parser_manifest["software"][
            "implementation_version"
        ],
        "parser_config_sha256": parser_manifest["configuration"][
            "parser_config_sha256"
        ],
        "event": event.model_dump(mode="json"),
    }
    record["canonical_event_sha256"] = canonical_event_sha256(record)
    return record


def _flush_pending(
    *,
    pending: list[_Pending],
    partition: ScientificPartition,
    units: list[_Unit],
    parser: FrozenDrainParser,
    sink: _CorpusSink,
    gate: Mapping[str, object],
) -> None:
    if not pending:
        return
    results = parser.transform_batch(
        (item.message for item in pending), partition=partition
    )
    if len(results) != len(pending):
        raise CanonicalEventError("frozen parser batch output count mismatch")
    stats = sink.stats[partition]
    for item, result in zip(pending, results, strict=True):
        unit = units[item.unit_ordinal]
        record = _build_record(gate=gate, unit=unit, pending=item, result=result)
        sink.write_record(partition, record)
        stats.emitted_records += 1
        if result.matched:
            stats.matched_records += 1
        else:
            stats.unseen_records += 1
        stats.minimum_source_index = (
            item.source_index
            if stats.minimum_source_index is None
            else min(stats.minimum_source_index, item.source_index)
        )
        stats.maximum_source_index = (
            item.source_index
            if stats.maximum_source_index is None
            else max(stats.maximum_source_index, item.source_index)
        )
    pending.clear()


def _load_hdfs_units(
    gate: Mapping[str, object],
) -> tuple[list[_Unit], array, dict[str, int], int]:
    manifest = gate["split_manifest"]
    assert isinstance(manifest, dict)
    total = int(manifest["dataset_semantics"]["total_raw_lines"])
    membership = array("i", [-1]) * total
    units: list[_Unit] = []
    block_to_unit: dict[str, int] = {}
    max_index = -1
    split_directory = gate["split_directory"]
    assert isinstance(split_directory, Path)
    for partition in AUTHORIZED_PARTITIONS:
        for record in iter_partition_assignments(split_directory, partition):
            indices = record.get("raw_chronological_indices_increasing")
            block_ids = record.get("block_ids_canonical_order")
            if (
                record.get("unit_kind") != "HDFS_COMPONENT"
                or record.get("partition_or_null") != partition.value
                or record.get("disposition") != "ASSIGNED"
                or not isinstance(indices, list)
                or not indices
                or not isinstance(block_ids, list)
                or not block_ids
                or indices != sorted(indices)
                or block_ids != sorted(block_ids)
            ):
                raise CanonicalEventError("malformed frozen HDFS assignment")
            ordinal = len(units)
            unit = _Unit(
                partition=partition,
                assignment_id=str(record["assignment_id"]),
                structural_unit_id=str(record["structural_unit_id"]),
                unit_kind="HDFS_COMPONENT",
                expected_records=len(indices),
                block_ids=tuple(str(item) for item in block_ids),
                chronological_start=int(indices[0]),
                chronological_end_exclusive=int(indices[-1]) + 1,
            )
            units.append(unit)
            for block_id in unit.block_ids:
                if block_id in block_to_unit:
                    raise CanonicalEventError("HDFS block belongs to multiple components")
                block_to_unit[block_id] = ordinal
            for value in indices:
                if not isinstance(value, int) or not 0 <= value < total:
                    raise CanonicalEventError("HDFS assignment index is outside raw universe")
                if membership[value] != -1:
                    raise CanonicalEventError("HDFS raw line appears in multiple partitions")
                membership[value] = ordinal
                max_index = max(max_index, value)
    if not units or max_index < 0:
        raise CanonicalEventError("HDFS non-TEST assignment universe is empty")
    return units, membership, block_to_unit, max_index


def _hdfs_unit_labels(
    *,
    root: Path,
    block_to_unit: Mapping[str, int],
    unit_count: int,
) -> list[AnomalyLabel]:
    config = load_dataset_config("hdfs", config_dir=root / "configs/datasets")
    if config.labels.file is None:
        raise CanonicalEventError("HDFS controlled label path is missing")
    label_path = resolve_repository_path(root, config.raw_dir) / config.labels.file
    states = array("b", [-1]) * unit_count
    seen_blocks: set[str] = set()
    try:
        with label_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["BlockId", "Label"]:
                raise CanonicalEventError("HDFS label header must be BlockId,Label")
            for row in reader:
                block_id = row.get("BlockId")
                ordinal = block_to_unit.get(str(block_id))
                if ordinal is None:
                    continue
                if block_id in seen_blocks:
                    raise CanonicalEventError("duplicate scoped HDFS label row")
                seen_blocks.add(str(block_id))
                label_text = row.get("Label")
                if label_text not in {"Normal", "Anomaly"}:
                    raise CanonicalEventError("unsupported scoped HDFS label")
                code = 0 if label_text == "Normal" else 1
                if states[ordinal] == -1:
                    states[ordinal] = code
                elif states[ordinal] != code:
                    states[ordinal] = 2
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CanonicalEventError("unable to scan scoped HDFS labels") from exc
    if len(seen_blocks) != len(block_to_unit):
        raise CanonicalEventError("HDFS scoped label lookup is incomplete")
    if any(value == -1 for value in states):
        raise CanonicalEventError("HDFS component has no controlled source label")
    if any(value == 2 for value in states):
        raise CanonicalEventError(
            "SCHEMA_GAP: an HDFS connected component has conflicting block labels"
        )
    return [
        AnomalyLabel.NORMAL if value == 0 else AnomalyLabel.ANOMALY
        for value in states
    ]


def _hdfs_supervision(
    *, partition: ScientificPartition, label: AnomalyLabel
) -> EventSupervision:
    return EventSupervision(
        label=label,
        granularity=LabelGranularity.BLOCK_SESSION,
        access=(
            LabelAccess.NORMAL_POOL_FILTERING
            if partition in TRAINING_PARTITIONS
            else LabelAccess.VALIDATION_EVALUATION
        ),
        source_kind=LabelSourceKind.EXTERNAL_FILE,
        source_reference="data/raw/hdfs/HDFS_v1/preprocessed/anomaly_label.csv",
    )


def _generate_hdfs(
    *, gate: Mapping[str, object], parser: FrozenDrainParser, sink: _CorpusSink
) -> None:
    root = gate["project_root"]
    assert isinstance(root, Path)
    units, membership, block_to_unit, max_index = _load_hdfs_units(gate)
    labels = _hdfs_unit_labels(
        root=root, block_to_unit=block_to_unit, unit_count=len(units)
    )
    counters = array("I", [0]) * len(units)
    emitted_unit = bytearray(len(units))
    pending = {partition: [] for partition in AUTHORIZED_PARTITIONS}
    for ordinal, unit in enumerate(units):
        stats = sink.stats[unit.partition]
        stats.authorized_units += 1
        stats.authorized_input_records += unit.expected_records
        if unit.partition in TRAINING_PARTITIONS and labels[ordinal] is AnomalyLabel.ANOMALY:
            stats.excluded_units += 1
            stats.excluded_records += unit.expected_records
            sink.write_exclusion(
                {
                    "dataset_key": "hdfs",
                    "partition": unit.partition.value,
                    "assignment_id": unit.assignment_id,
                    "structural_unit_id": unit.structural_unit_id,
                    "unit_kind": unit.unit_kind,
                    "reason": "NON_NORMAL_TRAINING_UNIT",
                    "excluded_record_count": unit.expected_records,
                }
            )
        else:
            emitted_unit[ordinal] = 1
            stats.emitted_units += 1
    source_file = gate["split_manifest"]["dataset"]["source_file"]
    source_path = root / _safe_relative_path(str(source_file))
    with source_path.open("rb") as handle:
        for source_index, raw_line in enumerate(itertools.islice(handle, max_index + 1)):
            ordinal = membership[source_index]
            if ordinal < 0:
                continue
            position = int(counters[ordinal])
            counters[ordinal] += 1
            if not emitted_unit[ordinal]:
                continue
            unit = units[ordinal]
            try:
                message = extract_hdfs_message(raw_line)
            except MessageExtractionError as exc:
                raise CanonicalEventError(
                    f"HDFS normalization failed at source index {source_index}"
                ) from exc
            bucket = pending[unit.partition]
            bucket.append(
                _Pending(
                    unit_ordinal=ordinal,
                    position_within_unit=position,
                    source_index=source_index,
                    raw_line=raw_line,
                    message=message,
                    supervision=_hdfs_supervision(
                        partition=unit.partition, label=labels[ordinal]
                    ),
                )
            )
            if len(bucket) >= DEFAULT_BATCH_SIZE:
                _flush_pending(
                    pending=bucket,
                    partition=unit.partition,
                    units=units,
                    parser=parser,
                    sink=sink,
                    gate=gate,
                )
    for partition, bucket in pending.items():
        _flush_pending(
            pending=bucket,
            partition=partition,
            units=units,
            parser=parser,
            sink=sink,
            gate=gate,
        )
    for ordinal, unit in enumerate(units):
        if counters[ordinal] != unit.expected_records:
            raise CanonicalEventError("HDFS source/assignment reconciliation failed")


def _load_bgl_units(gate: Mapping[str, object]) -> list[_Unit]:
    split_directory = gate["split_directory"]
    assert isinstance(split_directory, Path)
    units: list[_Unit] = []
    for partition in AUTHORIZED_PARTITIONS:
        for record in iter_partition_assignments(split_directory, partition):
            start = record.get("raw_rank_start_inclusive")
            end = record.get("raw_rank_end_exclusive")
            if (
                record.get("unit_kind") != "BGL_PARENT_WINDOW"
                or record.get("partition_or_null") != partition.value
                or record.get("disposition") != "ASSIGNED"
                or not isinstance(start, int)
                or not isinstance(end, int)
                or end - start != 100
            ):
                raise CanonicalEventError("malformed frozen BGL parent assignment")
            units.append(
                _Unit(
                    partition=partition,
                    assignment_id=str(record["assignment_id"]),
                    structural_unit_id=str(record["structural_unit_id"]),
                    unit_kind="BGL_PARENT_WINDOW",
                    expected_records=100,
                    chronological_start=start,
                    chronological_end_exclusive=end,
                )
            )
    units.sort(key=lambda item: item.chronological_start)
    previous_end = -1
    for unit in units:
        if unit.chronological_start < previous_end:
            raise CanonicalEventError("BGL parent windows overlap")
        previous_end = unit.chronological_end_exclusive
    if not units:
        raise CanonicalEventError("BGL non-TEST parent universe is empty")
    return units


def _bgl_supervision(
    *, partition: ScientificPartition, marker: str, source_index: int
) -> EventSupervision:
    return EventSupervision(
        label=(AnomalyLabel.NORMAL if marker == "-" else AnomalyLabel.ANOMALY),
        granularity=LabelGranularity.EVENT,
        access=(
            LabelAccess.NORMAL_POOL_FILTERING
            if partition in TRAINING_PARTITIONS
            else LabelAccess.VALIDATION_EVALUATION
        ),
        source_kind=LabelSourceKind.INLINE_FIELD,
        source_reference=f"data/raw/bgl/BGL/BGL.log:{source_index + 1}:first-field",
        category=None if marker == "-" else marker,
    )


def _generate_bgl(
    *, gate: Mapping[str, object], parser: FrozenDrainParser, sink: _CorpusSink
) -> None:
    root = gate["project_root"]
    assert isinstance(root, Path)
    units = _load_bgl_units(gate)
    source_file = gate["split_manifest"]["dataset"]["source_file"]
    source_path = root / _safe_relative_path(str(source_file))
    cursor = 0
    with source_path.open("rb") as handle:
        for ordinal, unit in enumerate(units):
            stats = sink.stats[unit.partition]
            stats.authorized_units += 1
            stats.authorized_input_records += 100
            skip = unit.chronological_start - cursor
            for _ in range(skip):
                if next(handle, None) is None:
                    raise CanonicalEventError("BGL source ended before an authorized parent")
            cursor += skip
            raw_lines = list(itertools.islice(handle, 100))
            if len(raw_lines) != 100:
                raise CanonicalEventError("BGL source ended inside an authorized parent")
            records = []
            for offset, raw_line in enumerate(raw_lines):
                try:
                    records.append(extract_bgl_record(raw_line))
                except MessageExtractionError as exc:
                    raise CanonicalEventError(
                        f"BGL normalization failed at source index {cursor + offset}"
                    ) from exc
            emit = unit.partition in VALIDATION_PARTITIONS or all(
                item.label_marker == "-" for item in records
            )
            if not emit:
                stats.excluded_units += 1
                stats.excluded_records += 100
                sink.write_exclusion(
                    {
                        "dataset_key": "bgl",
                        "partition": unit.partition.value,
                        "assignment_id": unit.assignment_id,
                        "structural_unit_id": unit.structural_unit_id,
                        "unit_kind": unit.unit_kind,
                        "reason": "NON_NORMAL_TRAINING_UNIT",
                        "excluded_record_count": 100,
                    }
                )
            else:
                stats.emitted_units += 1
                pending = [
                    _Pending(
                        unit_ordinal=ordinal,
                        position_within_unit=offset,
                        source_index=cursor + offset,
                        raw_line=raw_line,
                        message=source.message,
                        supervision=_bgl_supervision(
                            partition=unit.partition,
                            marker=source.label_marker,
                            source_index=cursor + offset,
                        ),
                    )
                    for offset, (raw_line, source) in enumerate(
                        zip(raw_lines, records, strict=True)
                    )
                ]
                _flush_pending(
                    pending=pending,
                    partition=unit.partition,
                    units=units,
                    parser=parser,
                    sink=sink,
                    gate=gate,
                )
            cursor += 100


def _reconcile(sink: _CorpusSink) -> None:
    for partition in AUTHORIZED_PARTITIONS:
        stats = sink.stats[partition]
        if (
            stats.authorized_input_records
            != stats.emitted_records + stats.excluded_records
            or stats.emitted_records != stats.matched_records + stats.unseen_records
            or stats.authorized_units != stats.emitted_units + stats.excluded_units
        ):
            raise CanonicalEventError(
                f"canonical input/output reconciliation failed for {partition.value}"
            )


def _scientific_identity_payload(
    *, gate: Mapping[str, object], sink: _CorpusSink
) -> dict:
    parser_manifest = gate["parser_manifest"]
    assert isinstance(parser_manifest, dict)
    sink_identity = sink.identity()
    return {
        "schema_version": CANONICAL_ARTIFACT_SCHEMA_VERSION,
        "implementation_version": CANONICAL_IMPLEMENTATION_VERSION,
        "dataset_key": gate["dataset_key"],
        "dataset_fingerprint": gate["dataset_fingerprint"],
        "protocol": {"id": "PROTOCOL-001", "version": PROTOCOL_VERSION},
        "split_payload_hash": gate["split_payload_hash"],
        "partition_hashes": {
            partition.value: gate["partition_hashes"][partition.value]
            for partition in AUTHORIZED_PARTITIONS
        },
        "parser": {
            "implementation_version": parser_manifest["software"][
                "implementation_version"
            ],
            "drain3_version": parser_manifest["software"]["drain3_version"],
            "parser_config_sha256": parser_manifest["configuration"][
                "parser_config_sha256"
            ],
            "parser_state_sha256": parser_manifest["identity"]["parser_state_sha256"],
            "template_registry_sha256": parser_manifest["identity"][
                "template_registry_sha256"
            ],
        },
        "partition_canonical_event_hashes": sink_identity[
            "partition_canonical_event_hashes"
        ],
        "partition_structural_summaries": {
            partition.value: sink.stats[partition].as_dict()
            for partition in AUTHORIZED_PARTITIONS
        },
        "exclusions_payload_sha256": sink_identity["exclusions_payload_sha256"],
        "exclusion_record_count": sink_identity["exclusion_record_count"],
    }


def _run_generation(
    *, gate: Mapping[str, object], staging: Path | None
) -> tuple[dict, _CorpusSink]:
    parser = load_frozen_parser(gate["parser_directory"])
    sink = _CorpusSink(staging=staging, identity_headers=_identity_headers(gate))
    try:
        if gate["dataset_key"] == "hdfs":
            _generate_hdfs(gate=gate, parser=parser, sink=sink)
        else:
            _generate_bgl(gate=gate, parser=parser, sink=sink)
        _reconcile(sink)
    finally:
        sink.close()
    payload = _scientific_identity_payload(gate=gate, sink=sink)
    return payload, sink


def generate_canonical_corpus(
    *,
    project_root: str | Path,
    dataset_key: str,
    output_directory: str | Path | None = None,
    generated_at_utc: str | None = None,
) -> dict:
    """Generate one real non-TEST corpus atomically under non-overwrite policy."""

    gate = validate_canonical_prerequisites(project_root, dataset_key)
    root = gate["project_root"]
    assert isinstance(root, Path)
    destination = (
        Path(output_directory).resolve()
        if output_directory is not None
        else root / f"data/processed/canonical-events/{dataset_key}"
    )
    if destination.exists():
        raise CanonicalEventError(f"refusing to overwrite canonical corpus: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.tmp"
    if staging.exists():
        raise CanonicalEventError(f"stale canonical staging directory exists: {staging}")
    staging.mkdir()
    try:
        identity_payload, sink = _run_generation(gate=gate, staging=staging)
        corpus_hash = _canonical_sha256(identity_payload)
        artifact_files = []
        for partition in AUTHORIZED_PARTITIONS:
            relative = _partition_path(partition)
            path = staging / relative
            artifact_files.append(
                {
                    "path": relative,
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "record_count": sink.stats[partition].emitted_records,
                }
            )
        exclusion_path = staging / "exclusions.jsonl.gz"
        artifact_files.append(
            {
                "path": "exclusions.jsonl.gz",
                "size_bytes": exclusion_path.stat().st_size,
                "sha256": sha256_file(exclusion_path),
                "record_count": sink.identity()["exclusion_record_count"],
            }
        )
        manifest = {
            "schema_version": CANONICAL_ARTIFACT_SCHEMA_VERSION,
            "artifact_type": "DERIVED_CANONICAL_EVENT_CORPUS_NON_TEST",
            "status": "COMPLETE_FROZEN",
            "identity": {
                "canonical_corpus_sha256": corpus_hash,
                "identity_algorithm": "SHA256(CANONICAL_IDENTITY_PAYLOAD_JSON_UTF8)",
                "identity_payload": identity_payload,
                "labels_participate_in_event_identity": False,
                "exact_file_hashes_include_supervision_metadata": True,
            },
            "artifact_files": artifact_files,
            "reconciliation": {
                partition.value: sink.stats[partition].as_dict()
                for partition in AUTHORIZED_PARTITIONS
            },
            "access_audit": {
                "authorized_partitions": [item.value for item in AUTHORIZED_PARTITIONS],
                "test_accessed": False,
                "test_artifact_created": False,
                "scientific_metrics_computed": False,
                "parser_updated": False,
                "labels_used_for_identity_or_matching": False,
                "training_labels_used_only_for_normal_unit_filtering": True,
                "validation_labels_isolated_as_supervision": True,
            },
            "generation": {
                "generated_at_utc": generated_at_utc or _utc_now(),
                "timestamp_participates_in_identity": False,
            },
        }
        manifest_path = staging / "canonical-manifest.json"
        manifest_path.write_bytes(
            json.dumps(
                manifest, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True
            ).encode("utf-8")
            + b"\n"
        )
        manifest_hash = sha256_file(manifest_path)
        (staging / "canonical-manifest.json.sha256").write_text(
            f"{manifest_hash}  canonical-manifest.json\n", encoding="ascii"
        )
        staged_validation = validate_canonical_corpus(staging)
        after_parser = validate_parser_artifact(gate["parser_directory"])
        if after_parser["parser_state_sha256"] != gate["parser_validation"][
            "parser_state_sha256"
        ]:
            raise CanonicalEventError("frozen parser identity changed during generation")
        staging.replace(destination)
        return staged_validation
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def validate_canonical_corpus(output_directory: str | Path) -> dict:
    """Independently reload and verify persisted canonical artifacts."""

    root = Path(output_directory).resolve()
    manifest_path = root / "canonical-manifest.json"
    manifest = _load_json(manifest_path)
    sidecar = (root / "canonical-manifest.json.sha256").read_text(
        encoding="ascii"
    ).split()
    manifest_hash = sha256_file(manifest_path)
    if sidecar != [manifest_hash, "canonical-manifest.json"]:
        raise CanonicalEventError("canonical manifest sidecar is stale")
    if (
        manifest.get("schema_version") != CANONICAL_ARTIFACT_SCHEMA_VERSION
        or manifest.get("status") != "COMPLETE_FROZEN"
        or manifest.get("access_audit", {}).get("test_accessed") is not False
        or manifest.get("access_audit", {}).get("test_artifact_created") is not False
    ):
        raise CanonicalEventError("canonical manifest status/access contract failed")
    identity_payload = manifest.get("identity", {}).get("identity_payload")
    if not isinstance(identity_payload, dict):
        raise CanonicalEventError("canonical scientific identity payload is missing")
    if _canonical_sha256(identity_payload) != manifest["identity"][
        "canonical_corpus_sha256"
    ]:
        raise CanonicalEventError("canonical corpus scientific identity mismatch")
    expected_artifacts = {
        _partition_path(partition) for partition in AUTHORIZED_PARTITIONS
    } | {"exclusions.jsonl.gz"}
    declared_artifacts = {item.get("path") for item in manifest.get("artifact_files", [])}
    if declared_artifacts != expected_artifacts:
        raise CanonicalEventError("canonical artifact inventory is incomplete or unsafe")
    for artifact in manifest["artifact_files"]:
        relative = _safe_relative_path(str(artifact["path"]))
        path = root / relative
        if (
            not path.is_file()
            or path.stat().st_size != artifact["size_bytes"]
            or sha256_file(path) != artifact["sha256"]
        ):
            raise CanonicalEventError(f"canonical exact-file integrity failed: {relative}")
    headers = {
        partition: {
            "schema_version": CANONICAL_ARTIFACT_SCHEMA_VERSION,
            "implementation_version": identity_payload["implementation_version"],
            "dataset_key": identity_payload["dataset_key"],
            "dataset_fingerprint": identity_payload["dataset_fingerprint"],
            "protocol": identity_payload["protocol"],
            "split_payload_hash": identity_payload["split_payload_hash"],
            "partition": partition.value,
            "partition_hash": identity_payload["partition_hashes"][partition.value],
            "parser_implementation_version": identity_payload["parser"][
                "implementation_version"
            ],
            "drain3_version": identity_payload["parser"]["drain3_version"],
            "parser_config_sha256": identity_payload["parser"][
                "parser_config_sha256"
            ],
            "parser_state_sha256": identity_payload["parser"]["parser_state_sha256"],
            "template_registry_sha256": identity_payload["parser"][
                "template_registry_sha256"
            ],
        }
        for partition in AUTHORIZED_PARTITIONS
    }
    for partition in AUTHORIZED_PARTITIONS:
        digest = hashlib.sha256()
        digest.update(_canonical_bytes(headers[partition]) + b"\n")
        count = matched = unseen = 0
        previous_source_index = -1
        with gzip.open(root / _partition_path(partition), "rb") as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise CanonicalEventError(
                        f"invalid canonical JSONL at {partition.value}:{line_number}"
                    ) from exc
                if not isinstance(record, dict):
                    raise CanonicalEventError("canonical event record must be an object")
                event = LogEvent.model_validate(record.get("event"))
                if event.provenance.partition is not partition:
                    raise CanonicalEventError("canonical partition provenance mismatch")
                if event.provenance.chronological_index <= previous_source_index:
                    raise CanonicalEventError("canonical partition chronology is not strict")
                previous_source_index = event.provenance.chronological_index
                expected = canonical_event_sha256(record)
                if record.get("canonical_event_sha256") != expected:
                    raise CanonicalEventError("canonical event identity mismatch")
                digest.update(_canonical_bytes(_label_free_record_payload(record)) + b"\n")
                count += 1
                if event.event_id == UNSEEN_EVENT_ID:
                    unseen += 1
                else:
                    matched += 1
        expected_summary = identity_payload["partition_structural_summaries"][
            partition.value
        ]
        if (
            digest.hexdigest()
            != identity_payload["partition_canonical_event_hashes"][partition.value]
            or count != expected_summary["emitted_records"]
            or matched != expected_summary["matched_records"]
            or unseen != expected_summary["evt_unseen_records"]
        ):
            raise CanonicalEventError("canonical partition reload reconciliation failed")
    exclusion_digest = hashlib.sha256()
    exclusion_count = 0
    with gzip.open(root / "exclusions.jsonl.gz", "rb") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                exclusion = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CanonicalEventError(
                    f"invalid exclusion JSONL at line {line_number}"
                ) from exc
            if (
                not isinstance(exclusion, dict)
                or exclusion.get("partition")
                not in {item.value for item in TRAINING_PARTITIONS}
                or exclusion.get("reason") != "NON_NORMAL_TRAINING_UNIT"
                or not isinstance(exclusion.get("excluded_record_count"), int)
                or exclusion["excluded_record_count"] <= 0
            ):
                raise CanonicalEventError("canonical training exclusion is malformed")
            exclusion_digest.update(_canonical_bytes(exclusion) + b"\n")
            exclusion_count += 1
    if (
        exclusion_digest.hexdigest()
        != identity_payload["exclusions_payload_sha256"]
        or exclusion_count != identity_payload["exclusion_record_count"]
    ):
        raise CanonicalEventError("canonical exclusion reload reconciliation failed")
    if (root / "partitions/TEST.jsonl.gz").exists() or (root / "TEST.jsonl.gz").exists():
        raise CanonicalEventError("forbidden scientific TEST canonical artifact exists")
    return {
        "dataset": identity_payload["dataset_key"],
        "status": "VERIFIED",
        "canonical_corpus_sha256": manifest["identity"]["canonical_corpus_sha256"],
        "manifest_file_sha256": manifest_hash,
        "partition_canonical_event_hashes": identity_payload[
            "partition_canonical_event_hashes"
        ],
        "partition_summaries": identity_payload["partition_structural_summaries"],
        "test_accessed": False,
        "test_artifact_created": False,
        "parser_updated": False,
    }


def compare_canonical_regeneration(
    *, project_root: str | Path, dataset_key: str, output_directory: str | Path | None = None
) -> dict:
    """Re-run the real transform into a hash sink and compare scientific identity."""

    gate = validate_canonical_prerequisites(project_root, dataset_key)
    root = gate["project_root"]
    assert isinstance(root, Path)
    destination = (
        Path(output_directory).resolve()
        if output_directory is not None
        else root / f"data/processed/canonical-events/{dataset_key}"
    )
    manifest = _load_json(destination / "canonical-manifest.json")
    regenerated, _ = _run_generation(gate=gate, staging=None)
    regenerated_hash = _canonical_sha256(regenerated)
    expected_hash = manifest["identity"]["canonical_corpus_sha256"]
    return {
        "dataset": dataset_key,
        "deterministic": regenerated_hash == expected_hash,
        "expected_canonical_corpus_sha256": expected_hash,
        "regenerated_canonical_corpus_sha256": regenerated_hash,
        "test_accessed": False,
    }


__all__ = [
    "AUTHORIZED_PARTITIONS",
    "CANONICAL_ARTIFACT_SCHEMA_VERSION",
    "CANONICAL_IMPLEMENTATION_VERSION",
    "CanonicalEventError",
    "canonical_event_sha256",
    "compare_canonical_regeneration",
    "generate_canonical_corpus",
    "validate_canonical_corpus",
    "validate_canonical_prerequisites",
]
