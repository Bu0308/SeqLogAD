"""CS-SPLIT-001 — leave-one-architecture-out chronological folds (Excel P1.5).

A fold holds out exactly one target architecture; every other ACTIVE architecture is
a source.  Within an architecture the chronological segmentation from
:mod:`seqlogad.protocol.chronology` is reused unchanged, so the same records occupy
the same segment no matter which role the architecture plays in a fold.  That
removes a whole class of role-dependent leakage by construction.

No ground-truth label, and no module from :mod:`seqlogad.protocol.labels`, is read
here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import yaml

from seqlogad.common.checksum import sha256_file
from seqlogad.protocol.architectures import ARCHITECTURES, TargetEligibility
from seqlogad.protocol.chronology import (
    SEGMENT_NAMES,
    ChronologyError,
    load_stream_frame,
    load_stream_index,
)


FOLD_SCHEMA_VERSION = "1.0"
FOLD_ROOT = "data/processed/protocol/folds"
SPLIT_CONTRACT = "configs/protocols/cross-system-split-v1.yaml"

SOURCE_PARTITIONS = ("SOURCE_TRAIN", "SOURCE_VALIDATION")
TARGET_PARTITIONS = ("TARGET_BURN_IN", "TARGET_EVALUATION")
ALL_PARTITIONS = SOURCE_PARTITIONS + TARGET_PARTITIONS

_SEGMENT_CODES = {name: code for code, name in SEGMENT_NAMES.items()}


class FoldError(RuntimeError):
    """Raised when a fold would violate a declared split invariant."""


@dataclass(frozen=True)
class SplitContract:
    path: str
    sha256: str
    version: str
    role_partitions: dict[str, dict[str, list[str]]]
    minimum_source_architectures: int
    invariants: tuple[str, ...]


def load_split_contract(project_root: str | Path) -> SplitContract:
    root = Path(project_root).resolve()
    path = root / SPLIT_CONTRACT
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))["cross_system_split"]
    if spec.get("target_labels_in_split_construction") is not False:
        raise FoldError("split contract must declare target_labels_in_split_construction: false")
    if spec.get("mixed_system_random_split_allowed") is not False:
        raise FoldError("split contract must forbid mixed-system random splits")
    return SplitContract(
        path=SPLIT_CONTRACT,
        sha256=sha256_file(path),
        version=str(spec["version"]),
        role_partitions=spec["role_partitions"],
        minimum_source_architectures=int(spec["minimum_source_architectures_per_fold"]),
        invariants=tuple(spec.get("invariants", ())),
    )


def _membership_digest(frame: pl.DataFrame) -> str:
    """SHA-256 over the packed, ascending chronological ranks of a membership."""

    digest = hashlib.sha256()
    ranks = frame["rank"].sort()
    step = 1 << 20
    for start in range(0, ranks.len(), step):
        chunk = ranks.slice(start, step).to_list()
        digest.update(b"".join(int(value).to_bytes(8, "big") for value in chunk))
    return digest.hexdigest()


def _iso(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1_000_000, tz=timezone.utc).isoformat()


def _member_block(
    architecture_id: str, frame: pl.DataFrame, segments: list[str]
) -> dict:
    codes = [_SEGMENT_CODES[name] for name in segments]
    part = frame.filter(pl.col("segment").is_in(codes))
    if part.height == 0:
        raise FoldError(f"{architecture_id}: segments {segments} contain no records")
    return {
        "architecture_id": architecture_id,
        "segments": segments,
        "records": int(part.height),
        "first_rank": int(part["rank"].min()),
        "last_rank": int(part["rank"].max()),
        "first_timestamp_utc": _iso(int(part["effective_ts"].min())),
        "last_timestamp_utc": _iso(int(part["effective_ts"].max())),
        "membership_sha256": _membership_digest(part),
        "distinct_normalized_messages": int(part["norm_h"].n_unique()),
    }


def build_fold(
    project_root: str | Path,
    target_architecture: str,
    *,
    active_architectures: list[str],
    contract: SplitContract,
    frames: dict[str, pl.DataFrame],
) -> dict:
    """Assemble one leave-one-architecture-out fold manifest."""

    root = Path(project_root).resolve()
    spec = ARCHITECTURES[target_architecture]
    if spec.target_eligibility is not TargetEligibility.ELIGIBLE:
        raise FoldError(
            f"{target_architecture} is {spec.target_eligibility}: "
            f"{spec.target_eligibility_rationale}"
        )
    sources = [a for a in active_architectures if a != target_architecture]
    if len(sources) < contract.minimum_source_architectures:
        raise FoldError(
            f"fold on {target_architecture} has {len(sources)} source architectures; "
            f"the contract requires at least {contract.minimum_source_architectures}"
        )

    source_map = contract.role_partitions["SOURCE"]
    target_map = contract.role_partitions["TARGET"]
    partitions: dict[str, dict] = {}

    for partition, segments in source_map.items():
        members = [_member_block(a, frames[a], list(segments)) for a in sources]
        partitions[partition] = {
            "role": "SOURCE",
            "members": members,
            "records": sum(m["records"] for m in members),
            "architectures": sources,
        }
    for partition, segments in target_map.items():
        member = _member_block(target_architecture, frames[target_architecture], list(segments))
        partitions[partition] = {
            "role": "TARGET",
            "members": [member],
            "records": member["records"],
            "architectures": [target_architecture],
        }

    # --- declared invariants, verified on the materialised membership -------------
    invariants: dict[str, object] = {}

    train_architectures = set(partitions["SOURCE_TRAIN"]["architectures"])
    invariants["TARGET_ARCHITECTURE_ABSENT_FROM_SOURCE_TRAIN"] = (
        target_architecture not in train_architectures
    )

    burn_in = partitions["TARGET_BURN_IN"]["members"][0]
    evaluation = partitions["TARGET_EVALUATION"]["members"][0]
    invariants["TARGET_BURN_IN_STRICTLY_PRECEDES_TARGET_EVALUATION"] = (
        burn_in["last_timestamp_utc"] < evaluation["first_timestamp_utc"]
        and burn_in["last_rank"] < evaluation["first_rank"]
    )

    source_order_ok = True
    for architecture in sources:
        train = next(
            m for m in partitions["SOURCE_TRAIN"]["members"] if m["architecture_id"] == architecture
        )
        validation = next(
            m
            for m in partitions["SOURCE_VALIDATION"]["members"]
            if m["architecture_id"] == architecture
        )
        source_order_ok &= (
            train["last_timestamp_utc"] < validation["first_timestamp_utc"]
            and train["last_rank"] < validation["first_rank"]
        )
    invariants["SOURCE_TRAIN_STRICTLY_PRECEDES_SOURCE_VALIDATION"] = bool(source_order_ok)

    disjoint = True
    for architecture in active_architectures:
        seen: dict[int, str] = {}
        for partition, block in partitions.items():
            for member in block["members"]:
                if member["architecture_id"] != architecture:
                    continue
                for segment in member["segments"]:
                    if segment in seen:
                        disjoint = False
                    seen[segment] = partition
    invariants["NO_RECORD_IN_TWO_PARTITIONS_OF_A_FOLD"] = disjoint

    used_segments = {
        segment
        for block in partitions.values()
        for member in block["members"]
        for segment in member["segments"]
    }
    invariants["GUARD_SEGMENT_UNUSED_BY_EVERY_PARTITION"] = "GUARD" not in used_segments

    fold = {
        "schema_version": FOLD_SCHEMA_VERSION,
        "fold_id": f"FOLD-TARGET-{target_architecture}",
        "artifact_id": "CS-SPLIT-001",
        "plan": "Bang_ke_hoach_SeqLogAD.xlsx",
        "protocol_id": "DOMAIN-ADAPTIVE-FUSION-001",
        "split_contract": {"path": contract.path, "sha256": contract.sha256, "version": contract.version},
        "target_architecture": target_architecture,
        "source_architectures": sources,
        "source_architecture_count": len(sources),
        "partitions": partitions,
        "invariants": invariants,
        "invariants_all_hold": all(bool(v) for v in invariants.values()),
        "target_labels_read": False,
        "seed": None,
        "determinism": "FLOOR_BOUNDARIES_ON_CHRONOLOGICAL_RANK",
        "stream_indices": {
            architecture: {
                "stream_index_sha256": load_stream_index(root, architecture)["stream_index_sha256"],
                "stream_parquet_sha256": load_stream_index(root, architecture)["stream_parquet_sha256"],
            }
            for architecture in active_architectures
        },
        "reproduction_command": (
            "python scripts/build_streams.py && python scripts/build_folds.py"
        ),
    }
    if not fold["invariants_all_hold"]:
        failed = [k for k, v in invariants.items() if not v]
        raise FoldError(f"{fold['fold_id']} violates split invariants: {failed}")
    return fold


def build_all_folds(project_root: str | Path, active_architectures: list[str]) -> list[dict]:
    root = Path(project_root).resolve()
    contract = load_split_contract(root)
    frames = {a: load_stream_frame(root, a) for a in active_architectures}
    eligible = [
        a
        for a in active_architectures
        if ARCHITECTURES[a].target_eligibility is TargetEligibility.ELIGIBLE
    ]
    if not eligible:
        raise FoldError("no target-eligible architecture is active")
    return [
        build_fold(
            root, target, active_architectures=active_architectures, contract=contract, frames=frames
        )
        for target in eligible
    ]


def write_fold(project_root: str | Path, fold: dict) -> str:
    root = Path(project_root).resolve()
    directory = root / FOLD_ROOT
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{fold['fold_id']}.json"
    path.write_text(json.dumps(fold, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha256_file(path)


def load_fold(project_root: str | Path, fold_id: str) -> dict:
    path = Path(project_root).resolve() / FOLD_ROOT / f"{fold_id}.json"
    if not path.is_file():
        raise FoldError(f"missing fold manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def list_folds(project_root: str | Path) -> list[str]:
    directory = Path(project_root).resolve() / FOLD_ROOT
    if not directory.is_dir():
        return []
    return sorted(p.stem for p in directory.glob("FOLD-TARGET-*.json"))


__all__ = [
    "ALL_PARTITIONS",
    "FOLD_ROOT",
    "FoldError",
    "SplitContract",
    "build_all_folds",
    "build_fold",
    "list_folds",
    "load_fold",
    "load_split_contract",
    "write_fold",
]
