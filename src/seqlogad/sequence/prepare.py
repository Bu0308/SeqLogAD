"""Build bounded ordered P2.2 windows from verified P2.1/Phase-1 lineage."""
from __future__ import annotations

import hashlib
import heapq
import json
import shutil
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import yaml

from seqlogad.common.checksum import sha256_file
from seqlogad.semantic.contracts import dump, membership, read
from seqlogad.semantic.prepare import git_state

from .contracts import BUNDLE_SCHEMA, PARTITIONS, VIEW_SCHEMA, validate_bundle


SEGMENTS = {"SOURCE_TRAIN": 0, "SOURCE_VALIDATION": 2}


def _sequence_id(architecture: str, partition: str, group: str) -> str:
    payload = f"{architecture}|{partition}|{group}".encode()
    return "seq-" + hashlib.sha256(payload).hexdigest()[:24]


def _window_id(architecture: str, partition: str, target_rank: int) -> str:
    payload = f"{architecture}|{partition}|{target_rank}".encode()
    return "win-" + hashlib.sha256(payload).hexdigest()


def _candidate_score(architecture: str, partition: str, target_rank: int) -> int:
    return int.from_bytes(
        hashlib.sha256(f"P2.2-v1|{architecture}|{partition}|{target_rank}".encode()).digest(),
        "big",
    )


def _member(fold: dict, partition: str, architecture: str) -> dict:
    matches = [item for item in fold["partitions"][partition]["members"]
               if item["architecture_id"] == architecture]
    if len(matches) != 1:
        raise ValueError("missing/duplicate fold member")
    return matches[0]


def _bounded_windows(stream: pl.DataFrame, architecture: str, partition: str,
                     limit: int, max_context: int) -> tuple[pl.DataFrame, int]:
    histories: dict[str, deque] = {}
    heap: list[tuple[int, int, dict]] = []
    eligible = 0
    for rank, effective_ts, gid in stream.select("rank", "effective_ts", "gid").iter_rows():
        group = f"G{gid}" if gid >= 0 else "GLOBAL"
        history = histories.setdefault(group, deque(maxlen=max_context))
        if history:
            eligible += 1
            context = list(history)
            row = {
                "window_id": _window_id(architecture, partition, rank),
                "architecture_id": architecture,
                "partition": partition,
                "sequence_id": _sequence_id(architecture, partition, group),
                "target_rank": rank,
                "context_ranks": [item[0] for item in context],
                "context_record_count": len(context),
                "target_effective_ts": effective_ts,
                "context_last_effective_ts": context[-1][1],
            }
            score = _candidate_score(architecture, partition, rank)
            item = (-score, -rank, row)
            if len(heap) < limit:
                heapq.heappush(heap, item)
            elif score < -heap[0][0]:
                heapq.heapreplace(heap, item)
        history.append((rank, effective_ts))
    selected = [item[2] for item in heap]
    selected.sort(key=lambda row: row["target_rank"])
    if not selected:
        raise ValueError(f"no eligible sequence windows for {architecture}/{partition}")
    return pl.DataFrame(selected), eligible


def _source_fold(semantic_root: Path, architecture: str) -> tuple[dict, Path]:
    for manifest in sorted(semantic_root.glob("folds/*/manifests/fold.json")):
        fold = read(manifest)
        if architecture in fold["source_architectures"]:
            return fold, manifest.parents[1]
    raise ValueError(f"no semantic source fold for {architecture}")


def _build_architecture_cache(project_root: Path, semantic_root: Path, cache: Path,
                              architecture: str, config: dict) -> dict:
    fold, fold_root = _source_fold(semantic_root, architecture)
    stream_dir = project_root / "data/processed/protocol/streams" / architecture.lower()
    stream_index = read(stream_dir / "stream-index.json")
    stream_path = stream_dir / "stream.parquet"
    if sha256_file(stream_path) != stream_index["stream_parquet_sha256"]:
        raise ValueError("Phase-1 stream checksum mismatch")
    context = config["context_policy"]["max_predecessor_records"]
    results = {}
    event_frames = []
    for directory, partition in PARTITIONS.items():
        member = _member(fold, partition, architecture)
        semantic_path = fold_root / f"semantic/{directory}/records.parquet"
        semantic = pl.scan_parquet(semantic_path).filter(
            pl.col("architecture_id") == architecture
        ).collect()
        if set(semantic.columns) != {"architecture_id", "rank", "normalized_message"}:
            raise ValueError("semantic input allowlist violation")
        if semantic.height != member["records"] or membership(semantic["rank"]) != member["membership_sha256"]:
            raise ValueError("P2.1/Phase-1 membership mismatch")
        stream = pl.scan_parquet(stream_path).filter(
            pl.col("segment") == SEGMENTS[partition]
        ).select("rank", "effective_ts", "gid").sort("rank").collect()
        if stream.height != semantic.height or membership(stream["rank"]) != member["membership_sha256"]:
            raise ValueError("stream/fold membership mismatch")
        limit_key = "train_candidate_windows_per_source" if directory == "train" else "validation_candidate_windows_per_source"
        windows, eligible = _bounded_windows(
            stream, architecture, partition, config["materialization"][limit_key], context
        )
        required = set(windows["target_rank"].to_list())
        for values in windows["context_ranks"].to_list():
            required.update(values)
        selected = semantic.filter(pl.col("rank").is_in(required)).join(
            stream, on="rank", how="inner", validate="1:1"
        ).with_columns(
            pl.lit(partition).alias("partition"),
            pl.concat_str([pl.col("architecture_id"), pl.lit(":"), pl.col("rank")]).alias("record_id"),
            pl.when(pl.col("gid") >= 0)
            .then(pl.concat_str([pl.lit("G"), pl.col("gid")]))
            .otherwise(pl.lit("GLOBAL"))
            .alias("group_key"),
        ).with_columns(
            pl.struct("architecture_id", "partition", "group_key").map_elements(
                lambda value: _sequence_id(value["architecture_id"], value["partition"], value["group_key"]),
                return_dtype=pl.String,
            ).alias("sequence_id")
        ).select(
            "architecture_id", "partition", "rank", "record_id", "effective_ts",
            "sequence_id", "normalized_message",
        ).sort("rank")
        if selected.height != len(required):
            raise ValueError("sequence candidate references missing semantic events")
        windows.write_parquet(cache / f"{architecture}-{directory}-windows.parquet", compression="zstd")
        event_frames.append(selected)
        results[partition] = {
            "input_record_count": semantic.height,
            "eligible_window_count": eligible,
            "sample_count": windows.height,
            "referenced_event_count": selected.height,
            "membership_sha256": member["membership_sha256"],
            "stream_index_sha256": sha256_file(stream_dir / "stream-index.json"),
        }
    events = pl.concat(event_frames).sort("partition", "rank")
    events.write_parquet(cache / f"{architecture}-events.parquet", compression="zstd")
    return results


def _copy_fold_inputs(semantic_root: Path, staging: Path, fold_id: str) -> None:
    source = semantic_root / "folds" / fold_id
    target = staging / "folds" / fold_id
    for name in ("manifests/fold.json", "manifests/lineage.json", "metadata/normalizer-cs-v1.yaml"):
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, destination)


def _materialize_fold(semantic_root: Path, staging: Path, cache: Path, fold: dict,
                      source_results: dict, config: dict, provenance: dict) -> None:
    fold_id = fold["fold_id"]
    _copy_fold_inputs(semantic_root, staging, fold_id)
    base = staging / "folds" / fold_id / "sequence"
    (base / "train").mkdir(parents=True)
    (base / "val").mkdir(parents=True)
    (base / "metadata").mkdir(parents=True)
    sources = sorted(fold["source_architectures"])
    events = pl.concat([pl.read_parquet(cache / f"{source}-events.parquet") for source in sources])
    events.write_parquet(base / "metadata/events.parquet", compression="zstd")
    entries = []
    for directory, partition in PARTITIONS.items():
        windows = pl.concat([
            pl.read_parquet(cache / f"{source}-{directory}-windows.parquet") for source in sources
        ]).sort("architecture_id", "target_rank")
        window_path = base / f"{directory}/windows.parquet"
        windows.write_parquet(window_path, compression="zstd")
        for source in sources:
            details = source_results[source][partition]
            entries.append(dict(
                architecture_id=source,
                partition=partition,
                file_path=window_path.relative_to(staging).as_posix(),
                sha256=sha256_file(window_path),
                **details,
            ))
    semantic_lineage = semantic_root / "folds" / fold_id / "manifests/lineage.json"
    view = {
        "schema_version": VIEW_SCHEMA,
        "view_id": "P2.2-SEQUENCE-REFERENCE-001",
        "fold_id": fold_id,
        "objective": config["objective"],
        "target_scoring_unit": config["target_scoring_unit"],
        "context_policy": config["context_policy"],
        "materialization": config["materialization"],
        "source_architectures": sources,
        "events_file": "metadata/events.parquet",
        "events_sha256": sha256_file(base / "metadata/events.parquet"),
        "partitions": entries,
        "semantic_lineage_sha256": sha256_file(semantic_lineage),
        "target_labels_read": False,
        "label_columns": [],
        "provenance": provenance,
    }
    dump(base / "metadata/view.json", view)


def build_bundle(project_root, semantic_root, output_root):
    root = Path(project_root).resolve()
    semantic_root = Path(semantic_root).resolve()
    output = Path(output_root).resolve()
    if output.exists():
        raise ValueError("output exists; do not overwrite a prepared sequence bundle")
    semantic_bundle = read(semantic_root / "manifests/bundle.json")
    config_path = root / "configs/models/sequence-reference-v1.yaml"
    config = yaml.safe_load(config_path.read_text())["sequence_reference"]
    staging = output.with_name(output.name + ".building")
    if staging.exists():
        raise ValueError("stale sequence staging directory exists")
    staging.mkdir(parents=True)
    cache = staging / "_cache"
    cache.mkdir()
    folds = [read(semantic_root / "folds" / fold / "manifests/fold.json")
             for fold in semantic_bundle["folds"]]
    architectures = sorted({source for fold in folds for source in fold["source_architectures"]})
    source_results = {
        source: _build_architecture_cache(root, semantic_root, cache, source, config)
        for source in architectures
    }
    provenance = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git": git_state(root),
        "builder_revision": VIEW_SCHEMA,
        "builder_config_sha256": sha256_file(config_path),
        "semantic_bundle_sha256": sha256_file(semantic_root / "manifests/bundle.json"),
        "target_labels_read": False,
    }
    for fold in folds:
        _materialize_fold(semantic_root, staging, cache, fold, source_results, config, provenance)
    shutil.rmtree(cache)
    (staging / "README.md").write_text(
        "P2.2 source-only ordered next-log bundle. No labels, target records, raw corpora or model weights.\n"
    )
    files = {p.relative_to(staging).as_posix(): sha256_file(p)
             for p in sorted(staging.rglob("*")) if p.is_file()}
    bundle = {
        **provenance,
        "schema_version": BUNDLE_SCHEMA,
        "bundle_id": "P2.2-SEQUENCE-REFERENCE-S42-001",
        "folds": [fold["fold_id"] for fold in folds],
        "files": files,
        "label_columns": [],
    }
    dump(staging / "manifests/bundle.json", bundle)
    checks = dict(files, **{"manifests/bundle.json": sha256_file(staging / "manifests/bundle.json")})
    (staging / "manifests/checksums.sha256").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(checks.items()))
    )
    reports = [validate_bundle(staging, fold["fold_id"]) for fold in folds]
    staging.rename(output)
    return {"bundle": bundle, "reports": reports, "source_results": source_results}
