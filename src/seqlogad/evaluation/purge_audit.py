"""Read-only HDFS purge-representativeness audit for PURGE-AUDIT-001.

The audit fixes PURGED from the public SPLIT-001 exclusion artifact and derives
RETAINED as its complement in the META-001 component universe. It deliberately
does not open any scientific partition membership file, including sealed TEST.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from array import array
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Final, Literal

import yaml

from seqlogad.evaluation.split import (
    nominal_partition_index,
    split_status,
)
from seqlogad.ingestion.dataset_config import (
    load_dataset_config,
    resolve_repository_path,
)
from seqlogad.ingestion.raw_metadata import (
    HdfsAssignmentStatus,
    HdfsComponentIndex,
    iter_hdfs_structural_references,
    normalize_hdfs_block_id,
    resolve_metadata_source,
    scan_hdfs_components,
)


AUDIT_ID: Final = "PURGE-AUDIT-001"
AUDIT_VERSION: Final = "1.0"
EXPECTED_DATASET_FINGERPRINT: Final = (
    "0103c63b2847ba98b0b309a9e06eebb80ac8030e2f92d1f62320742537a34013"
)
EXPECTED_SPLIT_PAYLOAD_HASH: Final = (
    "21ec061a7717cd03e7648e3d89200d486bce81eb7dd1bf4114272dd90fc4295c"
)
EXPECTED_TEST_PARTITION_HASH: Final = (
    "fa0c743619f8e2f7ef82a3cb2057eb99891515d56b0aa87f168c60bec093175d"
)
EXPECTED_STRUCTURAL_FACTS: Final = {
    "total_raw_lines": 11_175_629,
    "eligible_lines_pre_purge": 11_175_629,
    "assigned_eligible_lines": 8_634_576,
    "purged_boundary_eligible_lines": 2_541_053,
    "component_count": 575_061,
    "purged_component_count": 133_184,
}
FINAL_CLASSIFICATIONS: Final = {
    "PURGE_REPRESENTATIVENESS_CONCERN",
    "PURGE_REPRESENTATIVENESS_INCONCLUSIVE",
}
EVIDENCE_CLASSES: Final = {
    "LITERATURE_SUPPORTED",
    "LITERATURE_INFORMED_SEQLOGAD_DECISION",
    "SEQLOGAD_PROTOCOL_DECISION",
    "ENGINEERING_DECISION",
}


class PurgeAuditError(RuntimeError):
    """Fail-closed audit error carrying a stable scientific blocker code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class LabelLoadResult:
    labels: Mapping[str, bool]
    rows: int
    duplicate_rows: int


@dataclass(frozen=True)
class LabelMappingResult:
    component_labels: tuple[bool, ...]
    label_rows: int
    unique_labeled_blocks: int
    duplicate_rows: int
    unknown_block_ids: int
    missing_block_ids: int
    multi_block_components: int
    conflicting_components: int


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def scientific_payload_sha256(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", f"cannot read {path.name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", f"{path.name} is not an object")
    return payload


def _load_yaml(path: Path) -> dict:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", f"cannot read {path.name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", f"{path.name} is not a mapping")
    return payload


def _safe_relative(value: str) -> str:
    candidate = PurePosixPath(value)
    if (
        not value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or "\\" in value
        or candidate.as_posix() != value
    ):
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "unsafe artifact path")
    return value


def verify_frozen_audit_gate(project_root: str | Path) -> dict:
    """Verify identities and TEST seal without reading partition membership."""

    root = Path(project_root).resolve()
    active = _load_yaml(root / "configs/active-state.yaml")
    active_hdfs = active.get("datasets", {}).get("hdfs", {})
    active_split = active_hdfs.get("split", {})
    split_dir = root / _safe_relative(active_split.get("directory", ""))
    manifest_path = root / _safe_relative(active_split.get("manifest", ""))
    manifest = _load_json(manifest_path)

    observed_fingerprints = {
        active_hdfs.get("dataset_fingerprint"),
        manifest.get("dataset", {}).get("dataset_fingerprint"),
    }
    if observed_fingerprints != {EXPECTED_DATASET_FINGERPRINT}:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "HDFS dataset fingerprint differs")
    observed_split_hashes = {
        active_split.get("split_payload_hash"),
        manifest.get("identity", {}).get("split_payload_hash"),
    }
    if observed_split_hashes != {EXPECTED_SPLIT_PAYLOAD_HASH}:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "HDFS split payload differs")
    if manifest.get("protocol") != {"id": "PROTOCOL-001", "version": "1.1"}:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "Protocol v1.1 is not bound")
    if manifest.get("split_contract") != {
        "id": "PROTOCOL-SPLIT-CLARIFY-001",
        "version": "1.0",
    }:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "split addendum differs")

    semantics = manifest.get("dataset_semantics", {})
    for key, expected in EXPECTED_STRUCTURAL_FACTS.items():
        if semantics.get(key) != expected:
            raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", f"structural fact changed: {key}")

    test_hash = manifest.get("identity", {}).get("partition_hashes", {}).get("TEST")
    if test_hash != EXPECTED_TEST_PARTITION_HASH or active_split.get("test_partition_hash") != test_hash:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "TEST partition identity differs")

    sidecar = manifest_path.with_name("split-manifest.json.sha256")
    sidecar_parts = sidecar.read_text(encoding="ascii").split()
    manifest_file_hash = _sha256_file(manifest_path)
    if sidecar_parts != [manifest_file_hash, "split-manifest.json"]:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "split manifest sidecar is stale")

    exclusions_name = _safe_relative(manifest.get("exclusions_file", ""))
    exclusions_path = split_dir / exclusions_name
    artifacts = {item.get("path"): item for item in manifest.get("artifact_files", [])}
    exclusion_contract = artifacts.get(exclusions_name)
    if not exclusion_contract or _sha256_file(exclusions_path) != exclusion_contract.get("sha256"):
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "public exclusions integrity differs")

    status = split_status(split_dir)
    expected_status = {
        "test_status": "SEALED",
        "never_opened": True,
        "open_count": 0,
        "unlock_records": 0,
    }
    if any(status.get(key) != value for key, value in expected_status.items()):
        raise PurgeAuditError("TEST_BOUNDARY_CONFLICT", "scientific TEST is not sealed/never-opened")
    audit_log = split_dir / "test-access-audit.jsonl"
    if audit_log.stat().st_size != 0 or (split_dir / "test-access-grant.json").exists():
        raise PurgeAuditError("TEST_BOUNDARY_CONFLICT", "TEST audit/grant state is not pristine")

    return {
        "dataset_fingerprint": EXPECTED_DATASET_FINGERPRINT,
        "split_payload_hash": EXPECTED_SPLIT_PAYLOAD_HASH,
        "split_manifest_file_sha256": manifest_file_hash,
        "partition_hashes": dict(sorted(manifest["identity"]["partition_hashes"].items())),
        "exclusions_file": exclusions_name,
        "exclusions_sha256": exclusion_contract["sha256"],
        "test_status": status["test_status"],
        "test_never_opened": status["never_opened"],
        "test_open_count": status["open_count"],
        "test_unlock_records": status["unlock_records"],
        "dataset_semantics": semantics,
        "split_directory": split_dir,
        "manifest": manifest,
    }


def load_hdfs_label_file(path: str | Path) -> LabelLoadResult:
    labels: dict[str, bool] = {}
    duplicate_rows = 0
    rows = 0
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["BlockId", "Label"]:
            raise PurgeAuditError("LABEL_MAPPING_INCOMPLETE", "unexpected HDFS label header")
        for row in reader:
            rows += 1
            try:
                block_id = normalize_hdfs_block_id(row["BlockId"])
            except (KeyError, ValueError) as exc:
                raise PurgeAuditError("LABEL_MAPPING_INCOMPLETE", f"invalid label block ID at row {rows + 1}") from exc
            label_text = row.get("Label", "").strip()
            if label_text not in {"Normal", "Anomaly"}:
                raise PurgeAuditError("LABEL_MAPPING_INCOMPLETE", f"invalid HDFS label at row {rows + 1}")
            label = label_text == "Anomaly"
            previous = labels.get(block_id)
            if previous is not None or block_id in labels:
                duplicate_rows += 1
                if previous != label:
                    raise PurgeAuditError("LABEL_MAPPING_INCOMPLETE", "duplicate block ID has conflicting labels")
                continue
            labels[block_id] = label
    if not labels:
        raise PurgeAuditError("LABEL_MAPPING_INCOMPLETE", "HDFS label file is empty")
    return LabelLoadResult(labels=labels, rows=rows, duplicate_rows=duplicate_rows)


def map_labels_to_components(
    component_index: HdfsComponentIndex,
    label_result: LabelLoadResult,
) -> LabelMappingResult:
    component_position = {
        component.component_id: index
        for index, component in enumerate(component_index.components)
    }
    unknown = sorted(set(label_result.labels) - set(component_index.block_to_component))
    missing = sorted(set(component_index.block_to_component) - set(label_result.labels))
    if unknown or missing:
        raise PurgeAuditError(
            "LABEL_MAPPING_INCOMPLETE",
            f"unknown_block_ids={len(unknown)} missing_block_ids={len(missing)}",
        )

    codes: list[bool | None] = [None] * len(component_index.components)
    conflicts: list[str] = []
    for block_id, label in label_result.labels.items():
        component_id = component_index.block_to_component[block_id]
        position = component_position[component_id]
        previous = codes[position]
        if previous is not None and previous != label:
            conflicts.append(component_id)
        else:
            codes[position] = label
    if conflicts:
        affected_blocks = sum(
            len(component_index.components[component_position[item]].block_ids)
            for item in set(conflicts)
        )
        examples = ",".join(sorted(set(conflicts))[:3])
        raise PurgeAuditError(
            "LABEL_COMPONENT_CONFLICT",
            f"components={len(set(conflicts))} blocks={affected_blocks} examples={examples}",
        )
    if any(item is None for item in codes):
        raise PurgeAuditError("LABEL_MAPPING_INCOMPLETE", "one or more components lack a label")
    return LabelMappingResult(
        component_labels=tuple(bool(item) for item in codes),
        label_rows=label_result.rows,
        unique_labeled_blocks=len(label_result.labels),
        duplicate_rows=label_result.duplicate_rows,
        unknown_block_ids=0,
        missing_block_ids=0,
        multi_block_components=sum(len(item.block_ids) > 1 for item in component_index.components),
        conflicting_components=0,
    )


def wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    if total <= 0 or not 0 <= successes <= total or confidence != 0.95:
        raise ValueError("Wilson interval requires 0 <= successes <= total and confidence=0.95")
    z = 1.959963984540054
    p = successes / total
    z2 = z * z
    denominator = 1.0 + z2 / total
    center = (p + z2 / (2.0 * total)) / denominator
    half = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def newcombe_wilson_difference_interval(
    successes_left: int,
    total_left: int,
    successes_right: int,
    total_right: int,
) -> tuple[float, float]:
    """Newcombe hybrid-score interval for p_left - p_right (method 10)."""

    left = successes_left / total_left
    right = successes_right / total_right
    left_low, left_high = wilson_score_interval(successes_left, total_left)
    right_low, right_high = wilson_score_interval(successes_right, total_right)
    difference = left - right
    lower = difference - math.sqrt((left - left_low) ** 2 + (right_high - right) ** 2)
    upper = difference + math.sqrt((left_high - left) ** 2 + (right - right_low) ** 2)
    return max(-1.0, lower), min(1.0, upper)


def prevalence_ratio(left: float, right: float) -> dict:
    if right == 0.0:
        return {"value": None, "status": "UNDEFINED_ZERO_RETAINED_PREVALENCE"}
    return {"value": left / right, "status": "DEFINED"}


def _quantile(sorted_values: Sequence[int], probability: float) -> float:
    if not sorted_values:
        raise ValueError("cannot summarize an empty population")
    index = (len(sorted_values) - 1) * probability
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(sorted_values[lower])
    fraction = index - lower
    return float(sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction)


def robust_summary(values: Iterable[int]) -> dict:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot summarize an empty population")
    q25 = _quantile(ordered, 0.25)
    q75 = _quantile(ordered, 0.75)
    return {
        "count": len(ordered),
        "min": ordered[0],
        "q05": _quantile(ordered, 0.05),
        "q25": q25,
        "median": _quantile(ordered, 0.50),
        "q75": q75,
        "q95": _quantile(ordered, 0.95),
        "q99": _quantile(ordered, 0.99),
        "max": ordered[-1],
        "iqr": q75 - q25,
    }


def load_purged_components(
    exclusions_path: Path,
    component_index: HdfsComponentIndex,
    boundaries: tuple[int, ...],
) -> tuple[set[str], dict[str, tuple[int, int, int, int]]]:
    components = {item.component_id: item for item in component_index.components}
    purged: set[str] = set()
    record_stats: dict[str, tuple[int, int, int, int]] = {}
    with exclusions_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("disposition") != "PURGED_BOUNDARY":
                continue
            component_id = record.get("component_id")
            if component_id not in components or component_id in purged:
                raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", f"invalid purged component at exclusion row {line_number}")
            if record.get("block_ids_canonical_order") != list(components[component_id].block_ids):
                raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "purged block membership differs from META-001")
            ranks = record.get("eligible_ranks_increasing")
            chronology = record.get("raw_chronological_indices_increasing")
            if (
                not isinstance(ranks, list)
                or not isinstance(chronology, list)
                or not ranks
                or len(ranks) != len(chronology)
                or ranks != sorted(set(ranks))
                or chronology != sorted(set(chronology))
            ):
                raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "invalid purged structural membership")
            mask = 0
            for rank in ranks:
                mask |= 1 << nominal_partition_index(rank, boundaries)
            if mask.bit_count() < 2:
                raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "purged component does not cross a boundary")
            purged.add(component_id)
            record_stats[component_id] = (len(ranks), chronology[0], chronology[-1], mask)
    return purged, record_stats


def _git_provenance(root: Path) -> dict:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False
    )
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, text=True, capture_output=True, check=False
    )
    return {
        "revision": revision.stdout.strip() if revision.returncode == 0 else None,
        "dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None,
    }


def _population_payload(
    *,
    positions: Sequence[int],
    components: Sequence,
    labels: Sequence[bool],
    raw_line_counts: Sequence[int],
    source_line_maxima: Sequence[int],
    nominal_masks: Sequence[int],
) -> dict:
    anomaly_count = sum(labels[position] for position in positions)
    total = len(positions)
    prevalence = anomaly_count / total
    return {
        "component_count": total,
        "unique_block_id_count": sum(len(components[position].block_ids) for position in positions),
        "raw_line_count": sum(raw_line_counts[position] for position in positions),
        "anomalous_component_count": anomaly_count,
        "normal_component_count": total - anomaly_count,
        "anomaly_prevalence": prevalence,
        "structural_diagnostics": {
            "block_ids_per_component": robust_summary(len(components[position].block_ids) for position in positions),
            "raw_lines_per_component": robust_summary(raw_line_counts[position] for position in positions),
            "source_line_start_1_based": robust_summary(components[position].source_line_start for position in positions),
            "source_line_end_1_based": robust_summary(source_line_maxima[position] + 1 for position in positions),
            "source_line_span_inclusive": robust_summary(
                source_line_maxima[position] - components[position].chronological_start + 1
                for position in positions
            ),
            "nominal_partitions_touched": robust_summary(nominal_masks[position].bit_count() for position in positions),
            "nominal_boundaries_crossed": robust_summary(max(0, nominal_masks[position].bit_count() - 1) for position in positions),
        },
    }


def build_real_audit_payload(
    project_root: str | Path,
    *,
    final_classification: Literal[
        "PURGE_REPRESENTATIVENESS_CONCERN",
        "PURGE_REPRESENTATIVENESS_INCONCLUSIVE",
    ],
    progress: Callable[[str], None] | None = None,
) -> dict:
    if final_classification not in FINAL_CLASSIFICATIONS:
        raise ValueError("unsupported PURGE-AUDIT-001 classification")
    notify = progress or (lambda _message: None)
    root = Path(project_root).resolve()
    notify("verify-frozen-gate")
    gate = verify_frozen_audit_gate(root)
    config = load_dataset_config("hdfs", config_dir=root / "configs/datasets")
    source, log_path = resolve_metadata_source(config, project_root=root)
    if source.dataset_fingerprint != EXPECTED_DATASET_FINGERPRINT:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "resolved raw HDFS identity differs")

    notify("scan-meta-components")
    component_index = scan_hdfs_components(log_path, source)
    if (
        not component_index.complete
        or component_index.lines_scanned != EXPECTED_STRUCTURAL_FACTS["total_raw_lines"]
        or len(component_index.components) != EXPECTED_STRUCTURAL_FACTS["component_count"]
    ):
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "reconstructed META-001 universe differs")

    boundaries = tuple(gate["dataset_semantics"]["boundaries"])
    exclusions_path = gate["split_directory"] / gate["exclusions_file"]
    purged, purged_records = load_purged_components(exclusions_path, component_index, boundaries)
    if len(purged) != EXPECTED_STRUCTURAL_FACTS["purged_component_count"]:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "purged component count differs")

    components = component_index.components
    positions = {component.component_id: index for index, component in enumerate(components)}
    line_counts = array("Q", [0]) * len(components)
    maxima = array("Q", [0]) * len(components)
    masks = bytearray(len(components))
    eligible_rank = 0
    notify("scan-structural-observations")
    for raw_count, reference in enumerate(
        iter_hdfs_structural_references(log_path, source, component_index), start=1
    ):
        if reference.assignment_status is not HdfsAssignmentStatus.ASSIGNED or reference.component_id is None:
            raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "unexpected structurally ineligible HDFS line")
        position = positions[reference.component_id]
        line_counts[position] += 1
        maxima[position] = reference.chronological_index
        masks[position] |= 1 << nominal_partition_index(eligible_rank, boundaries)
        eligible_rank += 1
        if raw_count % 1_000_000 == 0:
            notify(f"scan-structural-observations:{raw_count}")
    if eligible_rank != EXPECTED_STRUCTURAL_FACTS["eligible_lines_pre_purge"]:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "eligible raw-line count differs")

    purged_positions: list[int] = []
    retained_positions: list[int] = []
    for position, component in enumerate(components):
        if line_counts[position] == 0:
            raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "component has no raw observations")
        observed = (int(line_counts[position]), component.chronological_start, int(maxima[position]), masks[position])
        if component.component_id in purged:
            if purged_records[component.component_id] != observed or masks[position].bit_count() < 2:
                raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "purged reconstruction differs")
            purged_positions.append(position)
        else:
            if masks[position].bit_count() != 1:
                raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "retained complement crosses a boundary")
            retained_positions.append(position)
    if sum(line_counts[position] for position in purged_positions) != EXPECTED_STRUCTURAL_FACTS["purged_boundary_eligible_lines"]:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "purged raw-line count differs")
    if sum(line_counts[position] for position in retained_positions) != EXPECTED_STRUCTURAL_FACTS["assigned_eligible_lines"]:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "retained raw-line count differs")

    # Population identity is now frozen. Labels enter only below this point.
    notify("load-audit-labels-after-population-freeze")
    if not config.labels.available or not config.labels.file:
        raise PurgeAuditError("LABEL_MAPPING_INCOMPLETE", "HDFS label contract is absent")
    label_relative = (PurePosixPath(config.raw_dir) / config.labels.file).as_posix()
    label_path = resolve_repository_path(root, label_relative)
    # Split manifests intentionally omit raw manifest file inventory; resolve it independently.
    dataset_manifest = _load_json(root / config.manifest_path)
    label_contract = next((item for item in dataset_manifest["files"] if item["path"] == label_relative), None)
    if label_contract is None or _sha256_file(label_path) != label_contract["sha256"]:
        raise PurgeAuditError("LABEL_MAPPING_INCOMPLETE", "label-file identity differs from dataset manifest")
    label_mapping = map_labels_to_components(component_index, load_hdfs_label_file(label_path))

    purged_payload = _population_payload(
        positions=purged_positions,
        components=components,
        labels=label_mapping.component_labels,
        raw_line_counts=line_counts,
        source_line_maxima=maxima,
        nominal_masks=masks,
    )
    retained_payload = _population_payload(
        positions=retained_positions,
        components=components,
        labels=label_mapping.component_labels,
        raw_line_counts=line_counts,
        source_line_maxima=maxima,
        nominal_masks=masks,
    )
    difference = purged_payload["anomaly_prevalence"] - retained_payload["anomaly_prevalence"]
    ci_low, ci_high = newcombe_wilson_difference_interval(
        purged_payload["anomalous_component_count"],
        purged_payload["component_count"],
        retained_payload["anomalous_component_count"],
        retained_payload["component_count"],
    )

    return {
        "audit_id": AUDIT_ID,
        "audit_version": AUDIT_VERSION,
        "active_protocol_stack": [
            "PROTOCOL-001-v1.1",
            "EFFECT-001",
            "PROTOCOL-SPLIT-CLARIFY-001-v1.0",
        ],
        "frozen_identity": {
            key: value
            for key, value in gate.items()
            if key not in {"split_directory", "manifest", "dataset_semantics"}
        },
        "population_definitions": {
            "PURGED": "META-001 connected components recorded as PURGED_BOUNDARY by frozen SPLIT-001",
            "RETAINED": "META-001 connected-component universe minus the public PURGED_BOUNDARY set",
            "retained_derivation_reads_partition_membership": False,
        },
        "primary_unit_of_analysis": "HDFS_META_001_CONNECTED_COMPONENT_SESSION",
        "raw_lines_role": "STRUCTURAL_DESCRIPTIVE_QUANTITY_ONLY",
        "label_mapping": {
            "status": "COMPLETE_UNAMBIGUOUS",
            "label_file": label_relative,
            "label_file_sha256": label_contract["sha256"],
            "label_rows": label_mapping.label_rows,
            "unique_labeled_blocks": label_mapping.unique_labeled_blocks,
            "duplicate_label_rows": label_mapping.duplicate_rows,
            "unknown_block_ids": label_mapping.unknown_block_ids,
            "missing_block_ids": label_mapping.missing_block_ids,
            "multi_block_components": label_mapping.multi_block_components,
            "conflicting_components": label_mapping.conflicting_components,
        },
        "populations": {"PURGED": purged_payload, "RETAINED": retained_payload},
        "primary_contrast": {
            "estimand": "anomaly_prevalence_PURGED_minus_RETAINED",
            "difference": difference,
            "confidence_level": 0.95,
            "confidence_interval": [ci_low, ci_high],
            "interval_method": "NEWCOMBE_HYBRID_SCORE_WILSON_METHOD_10",
            "inferential_unit": "connected_component_session",
            "assumptions": [
                "binary component labels are mapped without conflict",
                "connected components are treated as independent inferential units",
                "interval is a superpopulation-style uncertainty summary; observed dataset contrast is exact",
            ],
            "prevalence_ratio_PURGED_over_RETAINED": prevalence_ratio(
                purged_payload["anomaly_prevalence"], retained_payload["anomaly_prevalence"]
            ),
            "p_value_reported": False,
            "practical_equivalence_threshold": None,
        },
        "leakage_boundary": {
            "status": "PASS",
            "audit_item": "purge_representativeness",
            "population_identity_frozen_before_label_read": True,
            "label_used_for_split_assignment": False,
            "partition_membership_read_by_audit": False,
            "sealed_test_membership_read_by_audit": False,
            "test_unlock_created": False,
            "parser_read_or_modified": False,
            "canonical_events_or_sequences_generated": False,
            "models_or_scientific_metrics_run": False,
        },
        "evidence_classification": [
            {
                "claim": "connected component/session is the primary inferential unit",
                "classification": "LITERATURE_INFORMED_SEQLOGAD_DECISION",
            },
            {
                "claim": "Newcombe hybrid Wilson interval is used instead of naive Wald",
                "classification": "LITERATURE_SUPPORTED",
            },
            {
                "claim": "PURGED and RETAINED follow the frozen structural split",
                "classification": "SEQLOGAD_PROTOCOL_DECISION",
            },
            {
                "claim": "RETAINED is reconstructed as a complement without membership files",
                "classification": "ENGINEERING_DECISION",
            },
        ],
        "final_classification": final_classification,
        "acceptance_threshold_available": False,
        "plan_conflict_status": (
            "PLAN_CONFLICT_DETECTED"
            if final_classification == "PURGE_REPRESENTATIVENESS_CONCERN"
            else "HUMAN_REVIEW_REQUIRED"
        ),
        "limitations": [
            "no human-approved prevalence-equivalence margin exists",
            "the interval assumes independence across connected components",
            "the audit assesses aggregate PURGED versus RETAINED only and cannot establish causality",
            "the audit does not answer whether sequence order improves anomaly detection",
        ],
        "source_provenance": {
            "raw_log": source.source_file,
            "raw_log_sha256": source.source_file_sha256,
            "label_file": label_relative,
            "label_file_sha256": label_contract["sha256"],
            "public_exclusions": gate["exclusions_file"],
            "public_exclusions_sha256": gate["exclusions_sha256"],
        },
        "implementation_provenance": {
            "audit_module": "src/seqlogad/evaluation/purge_audit.py",
            "audit_module_sha256": _sha256_file(
                root / "src/seqlogad/evaluation/purge_audit.py"
            ),
            "meta_normalization_module": "src/seqlogad/ingestion/raw_metadata.py",
            "meta_normalization_module_sha256": _sha256_file(
                root / "src/seqlogad/ingestion/raw_metadata.py"
            ),
            "protocol_v1_1_sha256": _sha256_file(
                root / "configs/protocols/protocol-v1.1.yaml"
            ),
            "effect_001_sha256": _sha256_file(
                root / "configs/protocols/effect-001.yaml"
            ),
            "split_clarification_sha256": _sha256_file(
                root / "configs/protocols/split-clarification-v1.yaml"
            ),
            "hdfs_dataset_config_sha256": _sha256_file(
                root / "configs/datasets/hdfs.yaml"
            ),
        },
    }


def wrap_audit_artifact(scientific_payload: Mapping[str, object], *, project_root: Path) -> dict:
    return {
        "artifact_schema_version": "1.0",
        "artifact_type": "PURGE_REPRESENTATIVENESS_AUDIT",
        "scientific_payload": scientific_payload,
        "audit_payload_sha256": scientific_payload_sha256(scientific_payload),
        "generation": {
            "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "git": _git_provenance(project_root),
            "volatile_fields_excluded_from_scientific_identity": ["generation"],
        },
    }


def validate_audit_artifact(path: str | Path) -> dict:
    artifact = _load_json(Path(path))
    payload = artifact.get("scientific_payload")
    if not isinstance(payload, dict):
        raise PurgeAuditError("AUDIT_ARTIFACT_INVALID", "scientific payload missing")
    expected = scientific_payload_sha256(payload)
    if artifact.get("audit_payload_sha256") != expected:
        raise PurgeAuditError("AUDIT_ARTIFACT_INVALID", "scientific payload SHA-256 differs")
    if payload.get("audit_id") != AUDIT_ID or payload.get("audit_version") != AUDIT_VERSION:
        raise PurgeAuditError("AUDIT_ARTIFACT_INVALID", "audit identity differs")
    if payload.get("frozen_identity", {}).get("dataset_fingerprint") != EXPECTED_DATASET_FINGERPRINT:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "artifact dataset identity differs")
    if payload.get("frozen_identity", {}).get("split_payload_hash") != EXPECTED_SPLIT_PAYLOAD_HASH:
        raise PurgeAuditError("FROZEN_IDENTITY_MISMATCH", "artifact split identity differs")
    if payload.get("final_classification") not in FINAL_CLASSIFICATIONS:
        raise PurgeAuditError("AUDIT_ARTIFACT_INVALID", "final classification is invalid")
    evidence = payload.get("evidence_classification")
    if not isinstance(evidence, list) or any(
        not isinstance(item, dict)
        or item.get("classification") not in EVIDENCE_CLASSES
        for item in evidence
    ):
        raise PurgeAuditError("AUDIT_ARTIFACT_INVALID", "evidence classification is invalid")
    forbidden_keys = {
        "test_anomalous_count",
        "test_normal_count",
        "test_anomaly_prevalence",
        "partition_outcome_statistics",
        "test_members",
    }
    if forbidden_keys.intersection(_all_keys(payload)):
        raise PurgeAuditError("TEST_BOUNDARY_CONFLICT", "TEST-specific outcome field emitted")
    return {
        "audit_id": AUDIT_ID,
        "audit_payload_sha256": expected,
        "final_classification": payload["final_classification"],
        "valid": True,
    }


def _all_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key).lower())
            keys.update(_all_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_all_keys(item))
    return keys


def compare_audit_artifacts(first: str | Path, second: str | Path) -> dict:
    first_result = validate_audit_artifact(first)
    second_result = validate_audit_artifact(second)
    deterministic = first_result["audit_payload_sha256"] == second_result["audit_payload_sha256"]
    return {
        "audit_id": AUDIT_ID,
        "first_payload_sha256": first_result["audit_payload_sha256"],
        "second_payload_sha256": second_result["audit_payload_sha256"],
        "deterministic": deterministic,
    }


def write_audit_artifact(path: str | Path, artifact: Mapping[str, object]) -> None:
    destination = Path(path)
    if destination.exists():
        raise PurgeAuditError("AUDIT_ARTIFACT_EXISTS", f"refusing to overwrite {destination.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(artifact, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "AUDIT_ID",
    "AUDIT_VERSION",
    "PurgeAuditError",
    "build_real_audit_payload",
    "canonical_json",
    "compare_audit_artifacts",
    "load_hdfs_label_file",
    "map_labels_to_components",
    "newcombe_wilson_difference_interval",
    "prevalence_ratio",
    "robust_summary",
    "scientific_payload_sha256",
    "validate_audit_artifact",
    "verify_frozen_audit_gate",
    "wilson_score_interval",
    "wrap_audit_artifact",
    "write_audit_artifact",
]
