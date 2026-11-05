"""FUSION-E3-HDFS: fresh HDFS blocks with EVERY line scored (block-level aggregation).

E1/E2C scored ~1 sampled window per HDFS block, so an anomaly on another line
was invisible.  This builder takes blocks never used in E1 or E2C, selected by a
new deterministic hash, and emits one window per line that has >= 1 predecessor
in its block (<= 8 predecessors, same construction as P2.2).  Only SOURCE HDFS
block labels are read.

    PYTHONPATH=src python scripts/build_block_cohort.py --project . \
        --sequence-bundle data/phase2-sequence --semantic-bundle data/phase2 \
        --exclude-sidecar data/phase2-source-dev-v13r1 \
        --exclude-sidecar <confirm>/source_dev_confirm --out <dir> --blocks 3000
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter, deque
from pathlib import Path

import polars as pl

from seqlogad.common.checksum import sha256_file
from seqlogad.sequence.prepare import SEGMENTS, _sequence_id, _source_fold, _window_id
from seqlogad.sequence.source_development import SCHEMA, _labels_for_ranks

TAG = "FUSION-E3-HDFS-BLOCKS"
ARCH, PARTITION, FOLD = "ARCH-HDFS", "SOURCE_VALIDATION", "FOLD-TARGET-ARCH-HADOOP"
MAX_LINES = 32


def _block_score(seq_id: str, tag: str = TAG) -> int:
    return int.from_bytes(hashlib.sha256(f"{tag}|{seq_id}".encode()).digest(), "big")


def main():
    parser = argparse.ArgumentParser()
    for flag in ("--project", "--sequence-bundle", "--semantic-bundle", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--exclude-sidecar", type=Path, action="append", default=[])
    parser.add_argument("--blocks", type=int, default=3000)
    parser.add_argument("--tag", default=TAG, help="selection hash tag (FUSION-E4 uses a new one)")
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit(f"output exists, preserve evidence: {args.out}")
    project = args.project.resolve()
    used = set()
    for sidecar in args.exclude_sidecar:
        for path in sidecar.glob("FOLD-*.json"):
            used |= {e["unit_id"] for e in json.loads(path.read_text())["entries"] if e["architecture_id"] == ARCH}
    stream = pl.scan_parquet(project / "data/processed/protocol/streams/arch-hdfs/stream.parquet").filter(
        pl.col("segment") == SEGMENTS[PARTITION]).select("rank", "effective_ts", "gid").sort("rank").collect()
    stream = stream.with_columns(pl.col("gid").map_elements(
        lambda g: _sequence_id(ARCH, PARTITION, f"G{g}"), return_dtype=pl.String).alias("sequence_id"))
    candidates = sorted((s for s in stream["sequence_id"].unique().to_list() if s not in used), key=lambda s: _block_score(s, args.tag))
    chosen = set(candidates[:args.blocks])
    histories, windows = {}, []
    for rank, ts, gid, seq_id in stream.iter_rows():
        if seq_id not in chosen:
            continue
        history = histories.setdefault(seq_id, deque(maxlen=8))
        if history:
            windows.append({"window_id": _window_id(ARCH, PARTITION, rank), "architecture_id": ARCH,
                            "partition": PARTITION, "sequence_id": seq_id, "target_rank": rank,
                            "context_ranks": [h[0] for h in history], "context_record_count": len(history),
                            "target_effective_ts": ts, "context_last_effective_ts": history[-1][1]})
        history.append((rank, ts))
    per_block = Counter(w["sequence_id"] for w in windows)
    capped, seen = [], Counter()
    for w in windows:
        seen[w["sequence_id"]] += 1
        if seen[w["sequence_id"]] <= MAX_LINES:
            capped.append(w)
    windows = capped
    needed = {w["target_rank"] for w in windows} | {c for w in windows for c in w["context_ranks"]}
    _, fold_root = _source_fold(args.semantic_bundle, ARCH)
    semantic = pl.scan_parquet(fold_root / "semantic/val/records.parquet").filter(
        (pl.col("architecture_id") == ARCH) & pl.col("rank").is_in(needed)).collect()
    joined = semantic.join(stream.select("rank", "effective_ts", "sequence_id"), on="rank", how="inner",
                           validate="1:1")
    if joined.height != len(needed):
        raise ValueError("unresolved events")
    events = joined.with_columns(pl.lit(PARTITION).alias("partition"),
                                 pl.concat_str([pl.col("architecture_id"), pl.lit(":"), pl.col("rank")]).alias(
                                     "record_id")).select(
        "architecture_id", "partition", "rank", "record_id", "effective_ts", "sequence_id", "normalized_message")
    labels = _labels_for_ranks(project, ARCH, {w["target_rank"] for w in windows})
    bundle, sidecar = args.out / "phase2_sequence_blocks", args.out / "source_dev_blocks"
    dst = bundle / "folds" / FOLD
    for sub in ("manifests", "sequence/val", "sequence/metadata"):
        (dst / sub).mkdir(parents=True)
    sidecar.mkdir(parents=True)
    src = args.sequence_bundle / "folds" / FOLD
    shutil.copy2(src / "manifests/fold.json", dst / "manifests/fold.json")
    pl.DataFrame(windows).write_parquet(dst / "sequence/val/windows.parquet")
    old = pl.read_parquet(src / "sequence/metadata/events.parquet")
    pl.concat([old, events.select(old.columns)]).unique(subset=["architecture_id", "partition", "rank"],
                                                        keep="first").sort("architecture_id", "partition", "rank"
                                                                            ).write_parquet(dst / "sequence/metadata/events.parquet")
    entries, block_label = [], {}
    for w in windows:
        value = bool(labels[w["target_rank"]])
        if block_label.setdefault(w["sequence_id"], value) != value:
            raise ValueError("conflicting labels inside one block")
        entries.append({"architecture_id": ARCH, "window_id": w["window_id"], "target_rank": w["target_rank"],
                        "unit_id": w["sequence_id"], "anomaly": value})
    (sidecar / f"{FOLD}.json").write_text(json.dumps({"schema": SCHEMA, "fold_id": FOLD, "entries": entries},
                                                     sort_keys=True) + "\n")
    (bundle / "manifests").mkdir()
    (bundle / "manifests/bundle.json").write_text(json.dumps({
        "schema_version": "PHASE2-SEQUENCE-BLOCKS-1", "selection_tag": args.tag, "blocks": len(block_label),
        "windows": len(windows), "max_lines_per_block": MAX_LINES, "excluded_blocks": len(used),
        "files": {p.relative_to(bundle).as_posix(): sha256_file(p) for p in sorted(bundle.rglob("*")) if p.is_file()},
        "target_labels_read": False}, indent=2, sort_keys=True) + "\n")
    counts = Counter(block_label.values())
    (sidecar / "manifest.json").write_text(json.dumps({
        "schema": SCHEMA, "sequence_bundle_sha256": sha256_file(bundle / "manifests/bundle.json"),
        "folds": [FOLD], "files": {f"{FOLD}.json": sha256_file(sidecar / f"{FOLD}.json")},
        "target_labels_used_for_selection": False, "access_scope": "SOURCE_VALIDATION_BLOCK_STUDY",
        "selection_tag": args.tag, "class_counts_by_block": {"true": counts[True], "false": counts[False]},
        "windows": len(windows), "lines_per_block_before_cap_max": max(per_block.values())},
        indent=2, sort_keys=True) + "\n")
    print(json.dumps({"blocks": len(block_label), "windows": len(windows), "anomalous_blocks": counts[True]}))


if __name__ == "__main__":
    main()
