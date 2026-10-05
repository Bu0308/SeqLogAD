"""Restrict per-fold development selection to authorized source labels."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl

from seqlogad.common.checksum import sha256_file
from seqlogad.protocol.architectures import ARCHITECTURES, resolve_files, parse_hdfs
from seqlogad.semantic.prepare import locate_source_rows
from .contracts import validate_bundle


SCHEMA = "SEQUENCE-SOURCE-DEVELOPMENT-1"
LABELED_ARCHITECTURES = {"ARCH-BGL", "ARCH-HDFS"}


def _hdfs_labels(path: Path, allowed_blocks: set[str]) -> dict[str, bool]:
    labels = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            block = row["BlockId"].strip()
            if block not in allowed_blocks:
                continue
            value = row["Label"].strip().lower()
            if not block or value not in {"normal", "anomaly"} or block in labels:
                raise ValueError("invalid or duplicate public HDFS block label")
            labels[block] = value == "anomaly"
    if not labels:
        raise ValueError("empty public HDFS label file")
    return labels


def _labels_for_ranks(root: Path, architecture: str, ranks: set[int]) -> dict[int, bool]:
    """Match frozen chronological ranks to raw source lines before reading labels."""
    stream_dir = root / "data/processed/protocol/streams" / architecture.lower()
    index = json.loads((stream_dir / "stream-index.json").read_text())
    stream_path = stream_dir / "stream.parquet"
    if sha256_file(stream_path) != index["stream_parquet_sha256"]:
        raise ValueError("frozen stream checksum mismatch")
    stream = pl.read_parquet(stream_path)
    mapped = locate_source_rows(root, architecture, stream, index).filter(
        pl.col("rank").is_in(ranks) & (pl.col("segment") == 2)
    ).select("rank", "file_position")
    if mapped.height != len(ranks) or mapped["rank"].n_unique() != len(ranks):
        raise ValueError("source validation rank-to-raw join is incomplete")
    by_position = dict(mapped.select("file_position", "rank").iter_rows())
    result = {}
    position = 0
    spec = ARCHITECTURES[architecture]
    for path in resolve_files(root, spec):
        with path.open("rb") as handle:
            for line_number, line in enumerate(handle, 1):
                rank = by_position.get(position)
                if rank is not None:
                    if architecture == "ARCH-BGL":
                        marker = line.split(maxsplit=1)[0]
                        result[rank] = marker != b"-"
                    else:
                        record = parse_hdfs(line, path.relative_to(root).as_posix(), line_number)
                        if record.session_id is None:
                            raise ValueError("HDFS source validation target has no block label")
                        result[rank] = record.session_id
                position += 1
    if set(result) != ranks:
        raise ValueError("source validation raw label coverage is incomplete")
    if architecture == "ARCH-HDFS":
        block_labels = _hdfs_labels(
            root / "data/raw/hdfs/HDFS_v1/preprocessed/anomaly_label.csv", set(result.values())
        )
        if set(block_labels) != set(result.values()):
            raise ValueError("missing authorized HDFS block labels")
        result = {rank: block_labels[block] for rank, block in result.items()}
    return result


def _fold_entries(data_root: Path, fold_id: str, labels: dict[str, dict[int, bool]]) -> list[dict]:
    root = data_root / "folds" / fold_id
    fold = json.loads((root / "manifests/fold.json").read_text())
    expected = LABELED_ARCHITECTURES & set(fold["source_architectures"])
    if fold["target_architecture"] in expected or not expected:
        raise ValueError("source development target isolation failed")
    windows = pl.read_parquet(root / "sequence/val/windows.parquet")
    rows = windows.filter(pl.col("architecture_id").is_in(expected)).to_dicts()
    entries = []
    unit_labels = defaultdict(dict)
    for row in rows:
        arch, rank = row["architecture_id"], row["target_rank"]
        if rank not in labels[arch]:
            raise ValueError("source development label join incomplete")
        unit = row["window_id"] if arch == "ARCH-BGL" else row["sequence_id"]
        value = labels[arch][rank]
        prior = unit_labels[arch].setdefault(unit, value)
        if prior != value:
            raise ValueError("conflicting HDFS block labels inside one sequence unit")
        entries.append({
            "architecture_id": arch, "window_id": row["window_id"],
            "target_rank": rank, "unit_id": unit, "anomaly": value,
        })
    if {row["architecture_id"] for row in entries} != expected:
        raise ValueError("source development architecture coverage incomplete")
    for architecture, units in unit_labels.items():
        counts = Counter(units.values())
        if not counts[True] or not counts[False]:
            raise ValueError(f"source development lacks both classes: {architecture}")
    return sorted(entries, key=lambda row: (row["architecture_id"], row["target_rank"]))


def build_source_development(project_root: str | Path, data_root: str | Path,
                             output_root: str | Path) -> dict:
    root, data, output = map(lambda value: Path(value).resolve(),
                             (project_root, data_root, output_root))
    if output.exists():
        raise ValueError("source development output exists; preserve existing evidence")
    bundle_hash = sha256_file(data / "manifests/bundle.json")
    folds = sorted(path.name for path in (data / "folds").iterdir() if path.is_dir())
    ranks = {arch: set() for arch in LABELED_ARCHITECTURES}
    for fold_id in folds:
        validate_bundle(data, fold_id, bundle_hash)
        fold = json.loads((data / "folds" / fold_id / "manifests/fold.json").read_text())
        windows = pl.read_parquet(data / "folds" / fold_id / "sequence/val/windows.parquet")
        for arch in LABELED_ARCHITECTURES & set(fold["source_architectures"]):
            ranks[arch].update(windows.filter(pl.col("architecture_id") == arch)["target_rank"].to_list())
    labels = {arch: _labels_for_ranks(root, arch, needed)
              for arch, needed in sorted(ranks.items()) if needed}
    staging = output.with_name(output.name + ".building")
    if staging.exists():
        raise ValueError("source development staging exists; inspect before retry")
    staging.mkdir(parents=True)
    files, counts = {}, {}
    for fold_id in folds:
        entries = _fold_entries(data, fold_id, labels)
        path = staging / f"{fold_id}.json"
        path.write_text(json.dumps({"schema": SCHEMA, "fold_id": fold_id,
                                    "entries": entries}, sort_keys=True) + "\n")
        files[path.name] = sha256_file(path)
        counts[fold_id] = {arch: dict(Counter(row["anomaly"] for row in entries
                                                   if row["architecture_id"] == arch))
                           for arch in sorted({row["architecture_id"] for row in entries})}
    manifest = {"schema": SCHEMA, "sequence_bundle_sha256": bundle_hash,
                "folds": folds, "files": files,
                "target_labels_used_for_selection": False,
                "label_file_bytes_scanned": True,
                "label_values_converted_and_retained": "AUTHORIZED_SOURCE_VALIDATION_IDS_ONLY",
                "access_scope": "SOURCE_VALIDATION_MODEL_SELECTION",
                "source_label_file_sha256": {
                    "ARCH-BGL": sha256_file(root / "data/raw/bgl/BGL/BGL.log"),
                    "ARCH-HDFS": sha256_file(root / "data/raw/hdfs/HDFS_v1/preprocessed/anomaly_label.csv"),
                }, "class_counts_by_window": counts}
    (staging / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    staging.rename(output)
    return manifest


def load_source_development(sidecar_root: str | Path, data_root: str | Path,
                            fold_id: str, selected_windows: list[dict]) -> dict[str, dict]:
    root = Path(sidecar_root)
    manifest = json.loads((root / "manifest.json").read_text())
    source_only = (manifest.get("target_labels_used_for_selection") is False
                   or manifest.get("target_labels_read") is False)
    if manifest.get("schema") != SCHEMA or not source_only:
        raise ValueError("source development sidecar contract mismatch")
    if manifest["sequence_bundle_sha256"] != sha256_file(Path(data_root) / "manifests/bundle.json"):
        raise ValueError("source development sequence bundle mismatch")
    name = f"{fold_id}.json"
    if fold_id not in manifest["folds"] or sha256_file(root / name) != manifest["files"][name]:
        raise ValueError("source development fold checksum mismatch")
    fold = json.loads((Path(data_root) / "folds" / fold_id / "manifests/fold.json").read_text())
    entries = json.loads((root / name).read_text())["entries"]
    allowed = LABELED_ARCHITECTURES & set(fold["source_architectures"])
    if not allowed or {entry["architecture_id"] for entry in entries} != allowed:
        raise ValueError("source-development sidecar contains a target or missing source")
    by_window = {entry["window_id"]: entry for entry in entries}
    if len(by_window) != len(entries):
        raise ValueError("duplicate source development window identity")
    selected = {}
    for row in selected_windows:
        entry = by_window.get(row["window_id"])
        if entry is None:
            if row["architecture_id"] in allowed:
                raise ValueError("selected labeled source window is missing from sidecar")
            continue
        if (entry["architecture_id"] != row["architecture_id"]
                or entry["target_rank"] != row["target_rank"]
                or entry["architecture_id"] == fold["target_architecture"]):
            raise ValueError("source development selection identity mismatch")
        selected[row["window_id"]] = entry
    if not selected:
        raise ValueError("no selected labeled source validation windows")
    for arch in {entry["architecture_id"] for entry in selected.values()}:
        units = {entry["unit_id"]: entry["anomaly"] for entry in selected.values()
                 if entry["architecture_id"] == arch}
        if set(units.values()) != {False, True}:
            raise ValueError(f"selected source development lacks both classes: {arch}")
    return selected
