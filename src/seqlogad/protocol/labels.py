"""Evaluation-only ground-truth boundary.

Target anomaly labels are forbidden in training, adaptation, calibration, routing,
fusion fitting, model selection, normaliser fitting and parser fitting (Excel P1.1,
P1.6, P1.7).  This module is the *only* place in the protocol package that can read
a label, and every read must name an explicit evaluation scope and be recorded.

The isolation is architectural, not documentary:

* no other ``seqlogad.protocol`` module imports this one -- ``tests`` assert it;
* the adaptation-facing record contract (:mod:`seqlogad.protocol.schema`) has no
  label field at all, so there is nothing to leak through it;
* :func:`open_labels` refuses any scope other than the evaluation boundary and
  appends an access record before returning data.
"""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path


LABEL_ACCESS_LOG = "data/processed/protocol/label-access-audit.jsonl"


class LabelAccessScope(StrEnum):
    """The only scopes under which ground truth may be opened."""

    FINAL_EVALUATION = "FINAL_EVALUATION"
    PROTOCOL_LABEL_INVENTORY = "PROTOCOL_LABEL_INVENTORY"


FORBIDDEN_SCOPES = (
    "TRAINING",
    "ADAPTATION",
    "CALIBRATION",
    "ROUTING",
    "FUSION_FITTING",
    "MODEL_SELECTION",
    "NORMALIZER_FITTING",
    "PARSER_FITTING",
    "BUFFER_SELECTION",
    "SPLIT_CONSTRUCTION",
)


class LabelAccessDeniedError(PermissionError):
    """Raised when a caller tries to read ground truth outside the boundary."""


@dataclass(frozen=True, slots=True)
class LabelInventory:
    """Counts only. Never the per-record label vector."""

    architecture_id: str
    granularity: str
    label_source: str
    positive_units: int
    negative_units: int
    total_units: int
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "architecture_id": self.architecture_id,
            "granularity": self.granularity,
            "label_source": self.label_source,
            "positive_units": self.positive_units,
            "negative_units": self.negative_units,
            "total_units": self.total_units,
            "notes": self.notes,
        }


def _record_access(project_root: Path, architecture_id: str, scope: str, reason: str) -> None:
    path = project_root / LABEL_ACCESS_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "recorded_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "architecture_id": architecture_id,
        "scope": scope,
        "reason": reason,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _authorize(project_root: Path, architecture_id: str, scope: object, reason: str) -> str:
    text = str(scope)
    if text in FORBIDDEN_SCOPES:
        raise LabelAccessDeniedError(
            f"scope {text} may never read target ground truth (Excel P1.1/P1.6/P1.7)"
        )
    try:
        approved = LabelAccessScope(text)
    except ValueError as exc:
        raise LabelAccessDeniedError(f"unknown label access scope: {text}") from exc
    if not reason.strip():
        raise LabelAccessDeniedError("label access requires a recorded reason")
    _record_access(project_root, architecture_id, str(approved), reason)
    return str(approved)


# ---------------------------------------------------------------- label inventories

def _hdfs_inventory(root: Path) -> LabelInventory:
    path = root / "data/raw/hdfs/HDFS_v1/preprocessed/anomaly_label.csv"
    positives = negatives = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["Label"].strip().lower() == "anomaly":
                positives += 1
            else:
                negatives += 1
    return LabelInventory(
        "ARCH-HDFS", "block_trace", "preprocessed/anomaly_label.csv",
        positives, negatives, positives + negatives,
        "Loghub ships block-trace level ground truth for HDFS_v1.",
    )


def _bgl_inventory(root: Path) -> LabelInventory:
    path = root / "data/raw/bgl/BGL/BGL.log"
    positives = negatives = 0
    with path.open("rb") as handle:
        for line in handle:
            marker = line.split(b" ", 1)[0]
            if marker == b"-":
                negatives += 1
            elif marker:
                positives += 1
    return LabelInventory(
        "ARCH-BGL", "log_line", "BGL.log:field_0_alert_marker",
        positives, negatives, positives + negatives,
        "'-' marks a non-alert line; any other first-column token is an alert category.",
    )


_HADOOP_SECTION = re.compile(r"^(Normal|Machine down|Network disconnection|Disk full):\s*$")


def _hadoop_inventory(root: Path) -> LabelInventory:
    path = root / "data/raw/hadoop/abnormal_label.txt"
    section: str | None = None
    positives = negatives = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        match = _HADOOP_SECTION.match(stripped)
        if match:
            section = match.group(1)
            continue
        if stripped.startswith("+ application_"):
            if section == "Normal":
                negatives += 1
            elif section is not None:
                positives += 1
    return LabelInventory(
        "ARCH-HADOOP", "application", "abnormal_label.txt",
        positives, negatives, positives + negatives,
        "Applications are labelled normal or by injected failure category.",
    )


def _openstack_inventory(root: Path) -> LabelInventory:
    path = root / "data/raw/openstack/anomaly_labels.txt"
    uuid = re.compile(r"^[0-9a-fA-F-]{36}$")
    positives = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if uuid.match(line.strip()))
    return LabelInventory(
        "ARCH-OPENSTACK", "instance_uuid", "anomaly_labels.txt",
        positives, 0, positives,
        "Only the anomalous VM instances are enumerated; the negative set is implicit.",
    )


_INVENTORIES = {
    "ARCH-HDFS": _hdfs_inventory,
    "ARCH-BGL": _bgl_inventory,
    "ARCH-HADOOP": _hadoop_inventory,
    "ARCH-OPENSTACK": _openstack_inventory,
}


def label_inventory(
    project_root: str | Path,
    architecture_id: str,
    *,
    scope: object = LabelAccessScope.PROTOCOL_LABEL_INVENTORY,
    reason: str = "",
) -> LabelInventory:
    """Return aggregate label availability for the dataset registry (Excel P1.2).

    This yields counts only.  It records that ground truth *exists* and at what
    granularity; it never returns which record carries which label, so it cannot be
    used to select a burn-in buffer or to tune anything.
    """

    root = Path(project_root).resolve()
    _authorize(root, architecture_id, scope, reason or "P1.2 dataset registry label availability")
    if architecture_id not in _INVENTORIES:
        raise LabelAccessDeniedError(f"no declared label source for {architecture_id}")
    return _INVENTORIES[architecture_id](root)


def open_labels(
    project_root: str | Path,
    architecture_id: str,
    *,
    scope: object,
    reason: str,
) -> Iterator[tuple[str, bool]]:
    """Yield ``(unit_id, is_anomalous)`` -- **final evaluation only**.

    Phase 1 never calls this.  It exists so that the evaluation boundary is a real,
    auditable code path rather than a convention, and so that P4 has exactly one
    place to open ground truth from.
    """

    root = Path(project_root).resolve()
    approved = _authorize(root, architecture_id, scope, reason)
    if approved != str(LabelAccessScope.FINAL_EVALUATION):
        raise LabelAccessDeniedError(
            "per-unit ground truth requires scope FINAL_EVALUATION"
        )
    raise NotImplementedError(
        "Per-unit label materialisation is a P4 deliverable (EVAL-CS-001). "
        "Phase 1 deliberately stops at aggregate inventories."
    )


__all__ = [
    "FORBIDDEN_SCOPES",
    "LABEL_ACCESS_LOG",
    "LabelAccessDeniedError",
    "LabelAccessScope",
    "LabelInventory",
    "label_inventory",
    "open_labels",
]
