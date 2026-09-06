"""ADAPT-INPUT-001 — target normal burn-in buffer contract (Excel P1.6).

The buffer is acquired by a *label-blind* rule: it is the EARLY chronological
segment of the target architecture, nothing else.  The forbidden operation

    select records where label == normal

is impossible here because no code path in this module can reach a label; the
buffer records carry no label field and :mod:`seqlogad.protocol.labels` is not
imported.

"Normal burn-in" is therefore an *operational assumption* with a declared
contamination bound, not a property established from ground truth.  Realised
contamination can only be measured at the P4 evaluation boundary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import polars as pl
import yaml

from seqlogad.common.checksum import sha256_file
from seqlogad.protocol.chronology import load_stream_frame, load_stream_index
from seqlogad.protocol.folds import FoldError, load_fold


BUFFER_SCHEMA_VERSION = "1.0"
BUFFER_ROOT = "data/processed/protocol/buffers"
BUFFER_CONTRACT = "configs/protocols/target-buffer-v1.yaml"

READY = "READY"
NOT_READY = "NOT_READY"
UNKNOWN = "UNKNOWN"


class BufferError(RuntimeError):
    """Raised when a buffer would violate the declared acquisition contract."""


@dataclass(frozen=True)
class BufferContract:
    path: str
    sha256: str
    version: str
    minima: dict
    contamination: dict
    acquisition: dict
    signature: dict
    rejection_rule: dict


def load_buffer_contract(project_root: str | Path) -> BufferContract:
    root = Path(project_root).resolve()
    path = root / BUFFER_CONTRACT
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))["target_buffer"]
    exposure = spec["label_exposure"]
    if any(exposure[key] is not False for key in exposure):
        raise BufferError("buffer contract must declare every label-exposure flag false")
    if spec["acquisition"]["rule"] != "LABEL_BLIND_CHRONOLOGICAL_PREFIX":
        raise BufferError("buffer acquisition rule must be label-blind")
    if "rejection_rule" not in spec:
        # Excel P1.6 requires a signed rejection rule alongside the assumptions,
        # hash and duration. A contract without one is incomplete.
        raise BufferError("buffer contract must declare a rejection_rule (Excel P1.6)")
    return BufferContract(
        path=BUFFER_CONTRACT,
        sha256=sha256_file(path),
        version=str(spec["version"]),
        minima=spec["readiness_minima"],
        contamination=spec["contamination"],
        acquisition=spec["acquisition"],
        signature=spec["researcher_signature"],
        rejection_rule=spec["rejection_rule"],
    )


def _check(name: str, value, threshold, comparison: str) -> dict:
    if value is None:
        state = UNKNOWN
    elif comparison == "min":
        state = READY if value >= threshold else NOT_READY
    else:
        state = READY if value <= threshold else NOT_READY
    return {
        "check": name,
        "observed": value,
        "threshold": threshold,
        "comparison": comparison,
        "state": state,
        "reads_labels": False,
    }


def build_buffer(project_root: str | Path, fold_id: str) -> dict:
    """Materialise the burn-in buffer manifest and its label-free readiness report."""

    root = Path(project_root).resolve()
    contract = load_buffer_contract(root)
    fold = load_fold(root, fold_id)
    target = fold["target_architecture"]

    block = fold["partitions"]["TARGET_BURN_IN"]
    member = block["members"][0]
    if member["segments"] != list(contract.acquisition.get("segments", ["EARLY"])):
        # The contract defines the buffer as the EARLY segment; a fold that says
        # anything else must fail loudly rather than silently redefine the buffer.
        if member["segments"] != ["EARLY"]:
            raise BufferError(
                f"{fold_id}: TARGET_BURN_IN is {member['segments']}, contract requires ['EARLY']"
            )

    index = load_stream_index(root, target)
    frame = load_stream_frame(root, target).filter(pl.col("segment") == 0)
    if frame.height != member["records"]:
        raise BufferError(
            f"{fold_id}: buffer size {frame.height} disagrees with fold manifest "
            f"{member['records']}"
        )

    timestamps = frame["effective_ts"]
    first_us, last_us = int(timestamps.min()), int(timestamps.max())
    span_seconds = (last_us - first_us) / 1_000_000
    gaps = timestamps.diff().drop_nulls()
    max_gap_seconds = float(gaps.max() or 0) / 1_000_000
    distinct_normalized = int(frame["norm_h"].n_unique())

    # Coverage is measured on the buffer segment itself. Measuring the whole
    # architecture would answer a different question and could pass a buffer whose
    # own metadata is unusable.
    coverage = index["segments"]["EARLY"]["field_coverage"]
    parse_ok_ratio = coverage["parse_ok"]["ratio"]

    checks = [
        _check("min_records", frame.height, contract.minima["min_records"], "min"),
        _check("min_time_span_seconds", span_seconds, contract.minima["min_time_span_seconds"], "min"),
        _check(
            "max_relative_time_gap",
            (max_gap_seconds / span_seconds) if span_seconds > 0 else None,
            contract.minima["max_relative_time_gap"],
            "max",
        ),
        _check("min_parse_ok_ratio", parse_ok_ratio, contract.minima["min_parse_ok_ratio"], "min"),
        _check(
            "min_level_coverage",
            coverage.get("level", {}).get("ratio"),
            contract.minima["min_level_coverage"],
            "min",
        ),
        _check(
            "min_component_coverage",
            coverage.get("component", {}).get("ratio"),
            contract.minima["min_component_coverage"],
            "min",
        ),
        _check(
            "min_distinct_normalized_messages",
            distinct_normalized,
            contract.minima["min_distinct_normalized_messages"],
            "min",
        ),
        _check(
            "max_duplicate_ratio",
            1.0 - (distinct_normalized / frame.height),
            contract.minima["max_duplicate_ratio"],
            "max",
        ),
    ]

    states = {check["state"] for check in checks}
    if NOT_READY in states:
        readiness = NOT_READY
    elif UNKNOWN in states:
        readiness = UNKNOWN
    else:
        readiness = READY

    # BUFFER-REJECT-001. Stated separately from `readiness` so the *consequence* of
    # a failing check is recorded in the artifact, not left to a reader's judgement.
    if readiness == NOT_READY:
        acceptance = "REJECTED"
    elif readiness == UNKNOWN:
        acceptance = "INDETERMINATE"
    else:
        acceptance = "ACCEPTED"
    failing = [check["check"] for check in checks if check["state"] != READY]

    return {
        "schema_version": BUFFER_SCHEMA_VERSION,
        "artifact_id": "ADAPT-INPUT-001",
        "buffer_id": f"BUFFER-{target}",
        "fold_id": fold_id,
        "target_architecture": target,
        "acquisition_rule": contract.acquisition["rule"],
        "acquisition_definition": contract.acquisition["definition"],
        "forbidden_operation": contract.acquisition["forbidden_operation"],
        "records": frame.height,
        "first_timestamp_utc": datetime.utcfromtimestamp(first_us / 1_000_000).isoformat() + "+00:00",
        "last_timestamp_utc": datetime.utcfromtimestamp(last_us / 1_000_000).isoformat() + "+00:00",
        "time_span_seconds": round(span_seconds, 3),
        "distinct_normalized_messages": distinct_normalized,
        "buffer_membership_sha256": member["membership_sha256"],
        "provenance": {
            "split_contract_sha256": fold["split_contract"]["sha256"],
            "buffer_contract_sha256": contract.sha256,
            "buffer_contract_version": contract.version,
            "stream_index_sha256": index["stream_index_sha256"],
            "stream_parquet_sha256": index["stream_parquet_sha256"],
            "normalizer_rule_file_sha256": index["normalizer"]["rule_file_sha256"],
            "normalizer_version": index["normalizer"]["normalizer_version"],
        },
        "contamination": {
            "assumption": contract.contamination["assumption"],
            "declared_bound_fraction": contract.contamination["declared_bound_fraction"],
            "measured": None,
            "measurement_boundary": contract.contamination["verification_boundary"],
            "note": contract.contamination["note"],
        },
        "readiness": readiness,
        "readiness_checks": checks,
        "rejection_rule": {
            "id": contract.rejection_rule["id"],
            "acceptance": acceptance,
            "failing_checks": failing,
            "adaptation_use_permitted": acceptance == "ACCEPTED",
            "g1_claimable_for_this_fold": acceptance == "ACCEPTED",
            "minima_relaxed_to_obtain_pass": False,
            "authority": contract.rejection_rule["authority"],
        },
        "target_labels_read": False,
        "label_columns_present": [],
        "researcher_signature": dict(contract.signature),
    }


def write_buffer(project_root: str | Path, manifest: dict) -> str:
    root = Path(project_root).resolve()
    directory = root / BUFFER_ROOT
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{manifest['buffer_id']}.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha256_file(path)


def load_buffer(project_root: str | Path, buffer_id: str) -> dict:
    path = Path(project_root).resolve() / BUFFER_ROOT / f"{buffer_id}.json"
    if not path.is_file():
        raise BufferError(f"missing buffer manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = [
    "BUFFER_ROOT",
    "BufferContract",
    "BufferError",
    "NOT_READY",
    "READY",
    "UNKNOWN",
    "build_buffer",
    "load_buffer",
    "load_buffer_contract",
    "write_buffer",
]
