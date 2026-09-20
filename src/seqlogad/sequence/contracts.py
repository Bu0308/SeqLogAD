"""Portable P2.2 sequence-view identities and fail-closed validation."""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from seqlogad.common.checksum import sha256_file
from seqlogad.semantic.contracts import dump, read, safe_path


BUNDLE_SCHEMA = "SEQUENCE-VIEW-BUNDLE-1"
VIEW_SCHEMA = "SEQUENCE-VIEW-1"
PARTITIONS = {"train": "SOURCE_TRAIN", "val": "SOURCE_VALIDATION"}
EVENT_COLUMNS = {
    "architecture_id", "partition", "rank", "record_id", "effective_ts",
    "sequence_id", "normalized_message",
}
WINDOW_COLUMNS = {
    "window_id", "architecture_id", "partition", "sequence_id", "target_rank",
    "context_ranks", "context_record_count", "target_effective_ts",
    "context_last_effective_ts",
}


def _validate_ledger(root: Path, bundle: dict) -> None:
    bundle_path = root / "manifests/bundle.json"
    expected = dict(bundle["files"], **{"manifests/bundle.json": sha256_file(bundle_path)})
    lines = (root / "manifests/checksums.sha256").read_text().splitlines()
    if lines != [f"{digest}  {name}" for name, digest in sorted(expected.items())]:
        raise ValueError("sequence bundle checksum ledger mismatch")


def _expected_shape(folds: list[str]) -> set[str]:
    shape = {"README.md"}
    for fold in folds:
        prefix = f"folds/{fold}"
        shape.update({
            f"{prefix}/manifests/fold.json",
            f"{prefix}/manifests/lineage.json",
            f"{prefix}/metadata/normalizer-cs-v1.yaml",
            f"{prefix}/sequence/train/windows.parquet",
            f"{prefix}/sequence/val/windows.parquet",
            f"{prefix}/sequence/metadata/events.parquet",
            f"{prefix}/sequence/metadata/view.json",
        })
    return shape


def _forbidden_columns(columns: set[str]) -> set[str]:
    markers = ("label", "anomaly", "target_role", "outcome")
    return {name for name in columns if any(marker in name.lower() for marker in markers)}


def _validate_events(events: pl.DataFrame, sources: set[str]) -> None:
    if set(events.columns) != EVENT_COLUMNS or _forbidden_columns(set(events.columns)):
        raise ValueError("sequence event column allowlist violation")
    if events.is_empty() or events.null_count().row(0) != (0,) * len(events.columns):
        raise ValueError("empty or null sequence event table")
    if set(events["architecture_id"].unique()) != sources:
        raise ValueError("sequence event source-role violation")
    if set(events["partition"].unique()) != set(PARTITIONS.values()):
        raise ValueError("sequence event partition violation")
    identity = ["architecture_id", "partition", "rank"]
    if events.select(identity).unique().height != events.height:
        raise ValueError("duplicate sequence event identity")
    expected_ids = events.select(
        pl.concat_str([pl.col("architecture_id"), pl.lit(":"), pl.col("rank")]).alias("record_id")
    )["record_id"]
    if expected_ids.to_list() != events["record_id"].to_list():
        raise ValueError("sequence record identity mismatch")


def _validate_windows(windows: pl.DataFrame, events: pl.DataFrame, partition: str,
                      sources: set[str], max_context: int) -> dict[str, int]:
    if set(windows.columns) != WINDOW_COLUMNS or _forbidden_columns(set(windows.columns)):
        raise ValueError("sequence window column allowlist violation")
    if windows.is_empty() or windows.null_count().row(0) != (0,) * len(windows.columns):
        raise ValueError("empty or null sequence window table")
    if set(windows["partition"].unique()) != {partition}:
        raise ValueError("sequence window partition violation")
    if set(windows["architecture_id"].unique()) != sources:
        raise ValueError("sequence window source-role violation")
    if windows["window_id"].n_unique() != windows.height:
        raise ValueError("duplicate sequence window identity")
    lengths = windows["context_ranks"].list.len()
    if not lengths.equals(windows["context_record_count"]):
        raise ValueError("context count/list mismatch")
    if lengths.min() < 1 or lengths.max() > max_context:
        raise ValueError("context record horizon violation")
    bad_order = windows.filter(
        (pl.col("context_ranks").list.max() >= pl.col("target_rank"))
        | (pl.col("context_last_effective_ts") > pl.col("target_effective_ts"))
    )
    if bad_order.height:
        raise ValueError("causal sequence ordering violation")

    keys = ["architecture_id", "partition", "rank"]
    available = events.select(keys + ["sequence_id"]).unique()
    targets = windows.select(
        "window_id", "architecture_id", "partition", "sequence_id",
        pl.col("target_rank").alias("rank"),
    )
    target_join = targets.join(available, on=keys, how="left", suffix="_event")
    if target_join["sequence_id_event"].null_count() or target_join.filter(
        pl.col("sequence_id") != pl.col("sequence_id_event")
    ).height:
        raise ValueError("target event reference/sequence mismatch")

    contexts = windows.select(
        "window_id", "architecture_id", "partition", "sequence_id", "context_ranks",
    ).explode("context_ranks", empty_as_null=True).rename({"context_ranks": "rank"})
    context_join = contexts.join(available, on=keys, how="left", suffix="_event")
    if context_join["sequence_id_event"].null_count() or context_join.filter(
        pl.col("sequence_id") != pl.col("sequence_id_event")
    ).height:
        raise ValueError("context event reference/sequence mismatch")
    return {
        source: windows.filter(pl.col("architecture_id") == source).height
        for source in sorted(sources)
    }


def validate_bundle(data_root, fold_id, expected_bundle_sha256=None):
    root = Path(data_root)
    bundle_path = root / "manifests/bundle.json"
    if expected_bundle_sha256 and sha256_file(bundle_path) != expected_bundle_sha256:
        raise ValueError("trusted sequence bundle digest mismatch")
    bundle = read(bundle_path)
    if bundle.get("schema_version") != BUNDLE_SCHEMA:
        raise ValueError("sequence bundle schema mismatch")
    if bundle.get("target_labels_read") or bundle.get("label_columns"):
        raise ValueError("sequence bundle label policy violation")
    folds = bundle.get("folds", [])
    if fold_id not in folds or len(folds) != len(set(folds)):
        raise ValueError("unknown/duplicate sequence fold")
    shape = _expected_shape(folds)
    if set(bundle.get("files", {})) != shape:
        raise ValueError("sequence bundle file allowlist violation")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    allowed = shape | {"manifests/bundle.json", "manifests/checksums.sha256"}
    if actual != allowed:
        raise ValueError("unexpected/missing sequence bundle files")
    for name, digest in bundle["files"].items():
        if sha256_file(safe_path(root, name)) != digest:
            raise ValueError(f"sequence bundle checksum mismatch: {name}")
    _validate_ledger(root, bundle)

    prefix = f"folds/{fold_id}"
    fold = read(root / prefix / "manifests/fold.json")
    sources = set(fold["source_architectures"])
    if fold["fold_id"] != fold_id or fold["target_architecture"] in sources:
        raise ValueError("sequence fold/source identity violation")
    if set(fold["partitions"]) != set(PARTITIONS.values()):
        raise ValueError("target partition in sequence training bundle")
    view = read(root / prefix / "sequence/metadata/view.json")
    if view.get("schema_version") != VIEW_SCHEMA or view.get("fold_id") != fold_id:
        raise ValueError("sequence view identity mismatch")
    if view.get("target_labels_read") or view.get("label_columns"):
        raise ValueError("sequence view label policy violation")
    if view.get("objective") != "CAUSAL_NEXT_LOG_TARGET_TOKEN_NLL":
        raise ValueError("sequence objective mismatch")
    max_context = int(view["context_policy"]["max_predecessor_records"])
    events = pl.read_parquet(root / prefix / "sequence/metadata/events.parquet")
    _validate_events(events, sources)
    counts = {}
    for directory, partition in PARTITIONS.items():
        windows = pl.read_parquet(root / prefix / f"sequence/{directory}/windows.parquet")
        counts[partition] = _validate_windows(windows, events, partition, sources, max_context)
        for source, count in counts[partition].items():
            entries = [entry for entry in view["partitions"]
                       if entry["partition"] == partition and entry["architecture_id"] == source]
            if len(entries) != 1 or entries[0]["sample_count"] != count:
                raise ValueError("sequence view manifest count mismatch")
    return {
        "status": "PASS",
        "fold_id": fold_id,
        "counts": counts,
        "bundle_sha256": sha256_file(bundle_path),
        "view": view,
    }


def bundle_report(path: Path) -> dict:
    bundle = json.loads((Path(path) / "manifests/bundle.json").read_text())
    return {
        "schema": bundle["schema_version"],
        "folds": bundle["folds"],
        "sha256": sha256_file(Path(path) / "manifests/bundle.json"),
    }
