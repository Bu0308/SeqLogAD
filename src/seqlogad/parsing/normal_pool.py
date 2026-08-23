"""Leakage-scoped normal-only BASE_TRAIN selection for PARSE-001.

The public real-data entry point validates the existing split and TEST seal,
loads only ordinary BASE_TRAIN membership, and returns an in-memory bitset plus
a deterministic identity.  Raw messages and labels are never persisted in the
normal-pool summary.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator, Mapping, Sequence

import yaml

from seqlogad.common.schemas.events import ScientificPartition
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
from seqlogad.parsing.normalization import (
    MessageExtractionError,
    extract_bgl_record,
    extract_hdfs_message,
)


NORMAL_POOL_SCHEMA_VERSION = "1.0"
NORMAL_POOL_IDENTITY_ALGORITHM = (
    "SHA256(CANONICAL_HEADER_JSON_UTF8+LF+ORDERED_ZERO_BASED_SOURCE_INDEX_ASCII_LF)"
)


class NormalPoolError(RuntimeError):
    """Raised when label scope, split identity, or source structure is unsafe."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NormalPoolError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise NormalPoolError(f"JSON artifact must be an object: {path}")
    return payload


def _load_yaml(path: Path) -> dict:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise NormalPoolError(f"invalid YAML contract: {path}") from exc
    if not isinstance(payload, dict):
        raise NormalPoolError(f"YAML contract must be an object: {path}")
    return payload


def _safe_source_path(root: Path, relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise NormalPoolError("source path must be normalized repository-relative POSIX")
    resolved = (root / candidate.as_posix()).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise NormalPoolError("source path escapes the project root") from exc
    return resolved


def _new_bits(size: int) -> bytearray:
    if size < 0:
        raise NormalPoolError("membership universe must be non-negative")
    return bytearray((size + 7) // 8)


def _bit_is_set(bits: bytearray, index: int) -> bool:
    byte_index, bit_index = divmod(index, 8)
    return bool(bits[byte_index] & (1 << bit_index))


def _set_bit(bits: bytearray, index: int, *, universe: int, reject_duplicate: bool) -> None:
    if not 0 <= index < universe:
        raise NormalPoolError("source index is outside the declared raw universe")
    byte_index, bit_index = divmod(index, 8)
    mask = 1 << bit_index
    if reject_duplicate and bits[byte_index] & mask:
        raise NormalPoolError("source index appears in more than one eligible unit")
    bits[byte_index] |= mask


def _iter_set_indices(bits: bytearray, universe: int) -> Iterator[int]:
    for index in range(universe):
        if _bit_is_set(bits, index):
            yield index


def _normal_pool_hash(header: Mapping[str, object], bits: bytearray, universe: int) -> str:
    digest = hashlib.sha256()
    digest.update(_canonical_bytes(dict(header)))
    digest.update(b"\n")
    for index in _iter_set_indices(bits, universe):
        digest.update(str(index).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


@dataclass(slots=True)
class NormalPool:
    """Exact selected source membership without copied raw messages or labels."""

    dataset_key: str
    fit_partition: ScientificPartition
    source_path: Path
    source_file: str
    source_file_sha256: str
    dataset_fingerprint: str
    split_payload_hash: str
    base_train_partition_hash: str
    selection_contract: str
    selected_bits: bytearray
    source_universe_size: int
    source_read_stop_exclusive: int
    selected_record_count: int
    candidate_record_count: int
    selection_unit: str
    candidate_unit_count: int
    selected_unit_count: int
    excluded_unit_count: int
    membership_container_count: int
    mixed_unit_count: int
    normal_pool_hash: str

    def contains(self, source_index: int) -> bool:
        if not 0 <= source_index < self.source_universe_size:
            return False
        return _bit_is_set(self.selected_bits, source_index)

    def iter_source_indices(self) -> Iterator[int]:
        yield from _iter_set_indices(self.selected_bits, self.source_universe_size)

    def iter_messages(self) -> Iterator[tuple[int, str]]:
        """Yield selected, label-free parser messages in raw chronology."""

        seen = 0
        with self.source_path.open("rb") as handle:
            bounded = itertools.islice(handle, self.source_read_stop_exclusive)
            for source_index, raw_line in enumerate(bounded):
                if not self.contains(source_index):
                    continue
                try:
                    if self.dataset_key == "hdfs":
                        message = extract_hdfs_message(raw_line)
                    elif self.dataset_key == "bgl":
                        source = extract_bgl_record(raw_line)
                        if source.label_marker != "-":
                            raise NormalPoolError(
                                "selected BGL parser input is not a normal source event"
                            )
                        message = source.message
                    else:
                        raise NormalPoolError("unsupported normal-pool dataset")
                except MessageExtractionError as exc:
                    raise NormalPoolError(
                        f"message extraction failed at zero-based source index {source_index}"
                    ) from exc
                seen += 1
                yield source_index, message
        if seen != self.selected_record_count:
            raise NormalPoolError(
                f"selected source reconciliation failed: expected {self.selected_record_count}, got {seen}"
            )

    def summary(self) -> dict:
        return {
            "schema_version": NORMAL_POOL_SCHEMA_VERSION,
            "artifact_type": "DERIVED_NORMAL_POOL_IDENTITY",
            "dataset_key": self.dataset_key,
            "dataset_fingerprint": self.dataset_fingerprint,
            "source_file": self.source_file,
            "source_file_sha256": self.source_file_sha256,
            "protocol": {"id": "PROTOCOL-001", "version": "1.1"},
            "fit_partition": self.fit_partition.value,
            "split_payload_hash": self.split_payload_hash,
            "base_train_partition_hash": self.base_train_partition_hash,
            "selection_contract": self.selection_contract,
            "identity_algorithm": NORMAL_POOL_IDENTITY_ALGORITHM,
            "normal_pool_hash": self.normal_pool_hash,
            "candidate_record_count": self.candidate_record_count,
            "selected_normal_record_count": self.selected_record_count,
            "source_read_stop_exclusive": self.source_read_stop_exclusive,
            "selection_unit": self.selection_unit,
            "candidate_selection_unit_count": self.candidate_unit_count,
            "selected_normal_selection_unit_count": self.selected_unit_count,
            "excluded_non_normal_selection_unit_count": self.excluded_unit_count,
            "membership_container_count": self.membership_container_count,
            "mixed_label_unit_count": self.mixed_unit_count,
            "labels_persisted": False,
            "raw_messages_persisted": False,
            "test_accessed": False,
        }


def _identity_header(
    *,
    dataset_key: str,
    manifest: Mapping[str, object],
    selection_contract: str,
    selected_record_count: int,
    source_read_stop_exclusive: int,
) -> dict:
    dataset = manifest["dataset"]
    identity = manifest["identity"]
    if not isinstance(dataset, dict) or not isinstance(identity, dict):
        raise NormalPoolError("split manifest identity is malformed")
    return {
        "schema_version": NORMAL_POOL_SCHEMA_VERSION,
        "dataset_key": dataset_key,
        "dataset_fingerprint": dataset["dataset_fingerprint"],
        "source_file": dataset["source_file"],
        "source_file_sha256": dataset["source_file_sha256"],
        "protocol": {"id": "PROTOCOL-001", "version": "1.1"},
        "fit_partition": "BASE_TRAIN",
        "split_payload_hash": identity["split_payload_hash"],
        "base_train_partition_hash": identity["partition_hashes"]["BASE_TRAIN"],
        "selection_contract": selection_contract,
        "selected_record_count": selected_record_count,
        "source_read_stop_exclusive": source_read_stop_exclusive,
        "identity_algorithm": NORMAL_POOL_IDENTITY_ALGORITHM,
    }


def select_hdfs_normal_membership(
    *,
    assignments: Iterable[dict],
    scoped_labels: Mapping[str, str],
    total_raw_lines: int,
    manifest: Mapping[str, object],
    source_path: Path,
) -> NormalPool:
    """Select whole BASE_TRAIN components whose every block session is normal."""

    selected = _new_bits(total_raw_lines)
    candidate_lines = candidate_components = selected_components = 0
    excluded_components = mixed_components = 0
    for record in assignments:
        if (
            record.get("unit_kind") != "HDFS_COMPONENT"
            or record.get("partition_or_null") != "BASE_TRAIN"
            or record.get("disposition") != "ASSIGNED"
        ):
            raise NormalPoolError("HDFS normal selection received non-BASE_TRAIN membership")
        block_ids = record.get("block_ids_canonical_order")
        chronology = record.get("raw_chronological_indices_increasing")
        if not isinstance(block_ids, list) or not block_ids or not isinstance(chronology, list) or not chronology:
            raise NormalPoolError("HDFS component membership is malformed")
        try:
            labels = [scoped_labels[block_id] for block_id in block_ids]
        except KeyError as exc:
            raise NormalPoolError("a BASE_TRAIN block session has no scoped source label") from exc
        if any(label not in {"Normal", "Anomaly"} for label in labels):
            raise NormalPoolError("HDFS label must be exactly Normal or Anomaly")
        candidate_components += 1
        candidate_lines += len(chronology)
        if all(label == "Normal" for label in labels):
            selected_components += 1
            for source_index in chronology:
                _set_bit(
                    selected,
                    source_index,
                    universe=total_raw_lines,
                    reject_duplicate=True,
                )
        else:
            excluded_components += 1
            if len(set(labels)) > 1:
                mixed_components += 1

    selected_count = sum(1 for _ in _iter_set_indices(selected, total_raw_lines))
    selected_indices = _iter_set_indices(selected, total_raw_lines)
    source_read_stop_exclusive = max(selected_indices, default=-1) + 1
    selection_contract = "HDFS_ALL_MEMBER_BLOCK_SESSIONS_NORMAL_V1"
    header = _identity_header(
        dataset_key="hdfs",
        manifest=manifest,
        selection_contract=selection_contract,
        selected_record_count=selected_count,
        source_read_stop_exclusive=source_read_stop_exclusive,
    )
    dataset = manifest["dataset"]
    identity = manifest["identity"]
    assert isinstance(dataset, dict) and isinstance(identity, dict)
    return NormalPool(
        dataset_key="hdfs",
        fit_partition=ScientificPartition.BASE_TRAIN,
        source_path=source_path,
        source_file=str(dataset["source_file"]),
        source_file_sha256=str(dataset["source_file_sha256"]),
        dataset_fingerprint=str(dataset["dataset_fingerprint"]),
        split_payload_hash=str(identity["split_payload_hash"]),
        base_train_partition_hash=str(identity["partition_hashes"]["BASE_TRAIN"]),
        selection_contract=selection_contract,
        selected_bits=selected,
        source_universe_size=total_raw_lines,
        source_read_stop_exclusive=source_read_stop_exclusive,
        selected_record_count=selected_count,
        candidate_record_count=candidate_lines,
        selection_unit="connected_component",
        candidate_unit_count=candidate_components,
        selected_unit_count=selected_components,
        excluded_unit_count=excluded_components,
        membership_container_count=candidate_components,
        mixed_unit_count=mixed_components,
        normal_pool_hash=_normal_pool_hash(header, selected, total_raw_lines),
    )


def _collect_hdfs_base_block_ids(assignments_path: Path) -> set[str]:
    block_ids: set[str] = set()
    with assignments_path.open("rb") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise NormalPoolError(
                    f"invalid HDFS BASE_TRAIN assignment at line {line_number}"
                ) from exc
            if record.get("partition_or_null") != "BASE_TRAIN":
                raise NormalPoolError("ordinary HDFS assignment file contains another partition")
            values = record.get("block_ids_canonical_order")
            if not isinstance(values, list) or not values:
                raise NormalPoolError("HDFS BASE_TRAIN component has no block identities")
            block_ids.update(values)
    return block_ids


def _read_scoped_hdfs_labels(label_path: Path, allowed_block_ids: set[str]) -> dict[str, str]:
    """Scan the source CSV but retain/expose only requested BASE_TRAIN block labels."""

    scoped: dict[str, str] = {}
    try:
        with label_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["BlockId", "Label"]:
                raise NormalPoolError("HDFS label header must be BlockId,Label")
            for row in reader:
                block_id = row.get("BlockId")
                if block_id not in allowed_block_ids:
                    continue
                label = row.get("Label")
                if label not in {"Normal", "Anomaly"}:
                    raise NormalPoolError("HDFS scoped label is unsupported")
                previous = scoped.setdefault(block_id, label)
                if previous != label:
                    raise NormalPoolError("HDFS scoped block has conflicting labels")
    except (OSError, UnicodeError, csv.Error) as exc:
        raise NormalPoolError("unable to scan the HDFS controlled label file") from exc
    missing = allowed_block_ids.difference(scoped)
    if missing:
        raise NormalPoolError(
            f"HDFS scoped label lookup is incomplete ({len(missing)} BASE_TRAIN blocks missing)"
        )
    return scoped


def select_bgl_normal_membership(
    *,
    assignments: Iterable[dict],
    raw_lines: Iterable[bytes],
    total_raw_lines: int,
    manifest: Mapping[str, object],
    source_path: Path,
) -> NormalPool:
    """Select normal BGL events only inside complete BASE_TRAIN parent windows."""

    candidates = _new_bits(total_raw_lines)
    candidate_windows = candidate_lines = 0
    max_candidate_index = -1
    for record in assignments:
        if (
            record.get("unit_kind") != "BGL_PARENT_WINDOW"
            or record.get("partition_or_null") != "BASE_TRAIN"
            or record.get("disposition") != "ASSIGNED"
        ):
            raise NormalPoolError("BGL normal selection received non-BASE_TRAIN membership")
        start = record.get("raw_rank_start_inclusive")
        end = record.get("raw_rank_end_exclusive")
        if not isinstance(start, int) or not isinstance(end, int) or end - start != 100:
            raise NormalPoolError("BGL BASE_TRAIN parent window is malformed")
        for source_index in range(start, end):
            _set_bit(
                candidates,
                source_index,
                universe=total_raw_lines,
                reject_duplicate=True,
            )
        candidate_windows += 1
        candidate_lines += end - start
        max_candidate_index = max(max_candidate_index, end - 1)

    selected = _new_bits(total_raw_lines)
    normal_events = excluded_events = 0
    bounded_raw_lines = itertools.islice(raw_lines, max_candidate_index + 1)
    for source_index, raw_line in enumerate(bounded_raw_lines):
        if not _bit_is_set(candidates, source_index):
            continue
        try:
            record = extract_bgl_record(raw_line)
        except MessageExtractionError as exc:
            raise NormalPoolError(
                f"BGL source format failed at BASE_TRAIN index {source_index}"
            ) from exc
        if record.label_marker == "-":
            _set_bit(
                selected,
                source_index,
                universe=total_raw_lines,
                reject_duplicate=True,
            )
            normal_events += 1
        else:
            excluded_events += 1
    if normal_events + excluded_events != candidate_lines:
        raise NormalPoolError("BGL BASE_TRAIN source coverage does not reconcile")

    selection_contract = "BGL_NORMAL_EVENT_IN_COMPLETE_BASE_TRAIN_WINDOW_V1"
    header = _identity_header(
        dataset_key="bgl",
        manifest=manifest,
        selection_contract=selection_contract,
        selected_record_count=normal_events,
        source_read_stop_exclusive=max_candidate_index + 1,
    )
    dataset = manifest["dataset"]
    identity = manifest["identity"]
    assert isinstance(dataset, dict) and isinstance(identity, dict)
    return NormalPool(
        dataset_key="bgl",
        fit_partition=ScientificPartition.BASE_TRAIN,
        source_path=source_path,
        source_file=str(dataset["source_file"]),
        source_file_sha256=str(dataset["source_file_sha256"]),
        dataset_fingerprint=str(dataset["dataset_fingerprint"]),
        split_payload_hash=str(identity["split_payload_hash"]),
        base_train_partition_hash=str(identity["partition_hashes"]["BASE_TRAIN"]),
        selection_contract=selection_contract,
        selected_bits=selected,
        source_universe_size=total_raw_lines,
        source_read_stop_exclusive=max_candidate_index + 1,
        selected_record_count=normal_events,
        candidate_record_count=candidate_lines,
        selection_unit="event",
        candidate_unit_count=candidate_lines,
        selected_unit_count=normal_events,
        excluded_unit_count=excluded_events,
        membership_container_count=candidate_windows,
        mixed_unit_count=0,
        normal_pool_hash=_normal_pool_hash(header, selected, total_raw_lines),
    )


def _assert_parser_contract(root: Path) -> dict:
    contract = _load_yaml(root / "configs/parsing/drain3-v1.yaml")
    metadata = contract.get("parser_contract", {})
    if (
        metadata.get("id") != "PARSE-001"
        or metadata.get("version") != "1.0"
        or metadata.get("status") != "FROZEN_BEFORE_REAL_FIT"
        or metadata.get("protocol_version") != "1.1"
        or metadata.get("fit_partition") != "BASE_TRAIN"
        or metadata.get("fit_normal_only") is not True
        or metadata.get("scientific_metrics_allowed") is not False
    ):
        raise NormalPoolError("PARSE-001 configuration is not frozen and safe")
    hdfs = contract.get("normal_selection", {}).get("hdfs", {})
    bgl = contract.get("normal_selection", {}).get("bgl", {})
    if hdfs.get("component_policy") != "ALL_MEMBER_BLOCK_SESSIONS_MUST_BE_NORMAL":
        raise NormalPoolError("HDFS normal-selection granularity is not frozen")
    if bgl.get("label_granularity") != "event" or bgl.get("normal_label_marker") != "-":
        raise NormalPoolError("BGL normal-selection granularity is not frozen")
    return contract


def validate_parser_prefit_gate(project_root: str | Path, dataset_key: str) -> dict:
    """Verify every identity/access prerequisite before the first label lookup."""

    if dataset_key not in {"hdfs", "bgl"}:
        raise NormalPoolError("PARSE-001 supports only hdfs and bgl")
    root = Path(project_root).resolve()
    contract = _assert_parser_contract(root)
    effect = _load_yaml(root / "configs/protocols/effect-001.yaml")
    if effect.get("effect_contract", {}).get("status") != "FROZEN_HUMAN_APPROVED":
        raise NormalPoolError("EFFECT-001 is not frozen and human-approved")

    split_directory = root / f"data/processed/splits/{dataset_key}"
    split_validation = validate_split_artifact(split_directory)
    status = split_status(split_directory)
    if (
        split_validation.get("status") != "VERIFIED"
        or status.get("test_status") != "SEALED"
        or status.get("never_opened") is not True
        or status.get("open_count") != 0
        or status.get("unlock_records") != 0
    ):
        raise NormalPoolError("scientific TEST is not SEALED / NEVER_OPENED")

    clarification = _load_yaml(root / "configs/protocols/split-clarification-v1.yaml")
    split_meta = clarification.get("split_clarification", {})
    approved = split_meta.get("real_artifacts", {}).get(dataset_key, {})
    if (
        split_meta.get("status") != "FROZEN_HUMAN_APPROVED"
        or split_meta.get("implementation_status") != "COMPLETE"
        or split_meta.get("parser_fitted") is not False
        or split_meta.get("scientific_test_accessed") is not False
        or approved.get("split_payload_hash") != split_validation["split_payload_hash"]
    ):
        raise NormalPoolError("approved split identity/status is stale")

    config = load_dataset_config(dataset_key, config_dir=root / "configs/datasets")
    verification = verify_dataset_manifest(
        config,
        project_root=root,
        manifest_path=resolve_repository_path(root, config.manifest_path),
    )
    if not verification.valid:
        raise NormalPoolError("raw dataset manifest verification failed")
    manifest = _load_json(split_directory / "split-manifest.json")
    if verification.expected_fingerprint != manifest["dataset"]["dataset_fingerprint"]:
        raise NormalPoolError("raw dataset fingerprint differs from the split binding")
    if manifest["identity"]["partition_hashes"]["BASE_TRAIN"] != split_validation["partition_hashes"]["BASE_TRAIN"]:
        raise NormalPoolError("BASE_TRAIN partition hash is stale")
    return {
        "dataset": dataset_key,
        "dataset_fingerprint": verification.expected_fingerprint,
        "split_payload_hash": split_validation["split_payload_hash"],
        "base_train_partition_hash": split_validation["partition_hashes"]["BASE_TRAIN"],
        "test_status": status["test_status"],
        "never_opened": status["never_opened"],
        "open_count": status["open_count"],
        "unlock_records": status["unlock_records"],
        "protocol_version": "1.1",
        "effect_status": "FROZEN_HUMAN_APPROVED",
        "parser_config_status": contract["parser_contract"]["status"],
    }


def build_real_normal_pool(project_root: str | Path, dataset_key: str) -> NormalPool:
    """Build the real deterministic pool only after the complete pre-fit gate."""

    root = Path(project_root).resolve()
    validate_parser_prefit_gate(root, dataset_key)
    split_directory = root / f"data/processed/splits/{dataset_key}"
    manifest = _load_json(split_directory / "split-manifest.json")
    source_path = _safe_source_path(root, manifest["dataset"]["source_file"])
    total_raw_lines = int(manifest["dataset_semantics"]["total_raw_lines"])

    if dataset_key == "hdfs":
        assignments_path = split_directory / manifest["partition_files"]["BASE_TRAIN"]
        allowed = _collect_hdfs_base_block_ids(assignments_path)
        config = load_dataset_config("hdfs", config_dir=root / "configs/datasets")
        if config.labels.file is None:
            raise NormalPoolError("HDFS controlled label path is missing")
        label_path = resolve_repository_path(root, config.raw_dir) / config.labels.file
        scoped_labels = _read_scoped_hdfs_labels(label_path, allowed)
        return select_hdfs_normal_membership(
            assignments=iter_partition_assignments(
                split_directory, ScientificPartition.BASE_TRAIN
            ),
            scoped_labels=scoped_labels,
            total_raw_lines=total_raw_lines,
            manifest=manifest,
            source_path=source_path,
        )

    with source_path.open("rb") as raw_handle:
        return select_bgl_normal_membership(
            assignments=iter_partition_assignments(
                split_directory, ScientificPartition.BASE_TRAIN
            ),
            raw_lines=raw_handle,
            total_raw_lines=total_raw_lines,
            manifest=manifest,
            source_path=source_path,
        )


__all__ = [
    "NORMAL_POOL_IDENTITY_ALGORITHM",
    "NORMAL_POOL_SCHEMA_VERSION",
    "NormalPool",
    "NormalPoolError",
    "build_real_normal_pool",
    "select_bgl_normal_membership",
    "select_hdfs_normal_membership",
    "validate_parser_prefit_gate",
]
