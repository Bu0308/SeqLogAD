"""Build an independent labelled source-development cohort for FUSION-E2-CONFIRM.

Same SOURCE_VALIDATION (MID) segments, same window construction as P2.2
(<= 8 same-group predecessors), but a different deterministic selection hash
and every window already materialised in the original bundle excluded, so no
unit overlaps E1 / E1.1.  Only SOURCE labels of BGL/HDFS are read (same scope
as the V13R1 source-development sidecar).  No target record is touched.

    PYTHONPATH=src python scripts/build_confirm_cohort.py --project . \
        --sequence-bundle data/phase2-sequence --semantic-bundle data/phase2 \
        --out <dir outside git> --per-source 2048

FUSION-E4 reuses it with a new selection tag, BGL only, and every earlier
confirmation cohort excluded:

    ... --tag FUSION-E4-GATED-BGL-seed3 --architectures ARCH-BGL --per-source 6144 \
        --exclude-sidecar <E2C>/source_dev_confirm
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import shutil
from collections import Counter, deque
from pathlib import Path

import polars as pl

from seqlogad.common.checksum import sha256_file
from seqlogad.sequence.prepare import SEGMENTS, _sequence_id, _source_fold, _window_id
from seqlogad.sequence.source_development import SCHEMA, _labels_for_ranks

TAG = "FUSION-E2-CONFIRM-seed2"
LABELLED = ("ARCH-BGL", "ARCH-HDFS")
PARTITION = "SOURCE_VALIDATION"


def _score(architecture: str, rank: int, tag: str = TAG) -> int:
    return int.from_bytes(hashlib.sha256(f"{tag}|{architecture}|{PARTITION}|{rank}".encode()).digest(), "big")


def select_windows(stream: pl.DataFrame, architecture: str, exclude: set[str], limit: int, context: int,
                   tag: str = TAG):
    histories: dict[str, deque] = {}
    heap: list = []
    for rank, effective_ts, gid in stream.select("rank", "effective_ts", "gid").iter_rows():
        group = f"G{gid}" if gid >= 0 else "GLOBAL"
        history = histories.setdefault(group, deque(maxlen=context))
        if history:
            window_id = _window_id(architecture, PARTITION, rank)
            if window_id not in exclude:
                row = {"window_id": window_id, "architecture_id": architecture, "partition": PARTITION,
                       "sequence_id": _sequence_id(architecture, PARTITION, group), "target_rank": rank,
                       "context_ranks": [item[0] for item in history],
                       "context_record_count": len(history), "target_effective_ts": effective_ts,
                       "context_last_effective_ts": history[-1][1]}
                score = _score(architecture, rank, tag)
                item = (-score, -rank, row)
                if len(heap) < limit:
                    heapq.heappush(heap, item)
                elif score < -heap[0][0]:
                    heapq.heapreplace(heap, item)
        history.append((rank, effective_ts))
    rows = sorted((item[2] for item in heap), key=lambda r: r["target_rank"])
    if len(rows) != limit:
        raise ValueError(f"only {len(rows)} eligible new windows for {architecture}")
    return rows


def excluded_windows(sidecars: list[Path]) -> set[str]:
    out = set()
    for sidecar in sidecars:
        for path in sidecar.glob("FOLD-*.json"):
            out |= {e["window_id"] for e in json.loads(path.read_text())["entries"]}
    return out


def build(project: Path, seq_bundle: Path, sem_bundle: Path, out: Path, per_source: int, tag: str = TAG,
          architectures: tuple[str, ...] = LABELLED, exclude_sidecars: tuple[Path, ...] = ()) -> dict:
    if out.exists():
        raise SystemExit(f"output exists, preserve evidence: {out}")
    all_folds = sorted(p.name for p in (seq_bundle / "folds").iterdir() if p.is_dir())
    original = set()
    for fold in all_folds:
        original |= set(pl.read_parquet(seq_bundle / "folds" / fold / "sequence/val/windows.parquet")["window_id"])
    prior = excluded_windows(list(exclude_sidecars))
    folds = [f for f in all_folds if any(
        a in json.loads((seq_bundle / "folds" / f / "manifests/fold.json").read_text())["source_architectures"]
        for a in architectures)]
    windows, events, labels = {}, {}, {}
    for arch in architectures:
        _, fold_root = _source_fold(sem_bundle, arch)
        stream_dir = project / "data/processed/protocol/streams" / arch.lower()
        stream = pl.scan_parquet(stream_dir / "stream.parquet").filter(
            pl.col("segment") == SEGMENTS[PARTITION]).select("rank", "effective_ts", "gid").sort("rank").collect()
        rows = select_windows(stream, arch, original | prior, per_source, 8, tag)
        needed = {r["target_rank"] for r in rows} | {c for r in rows for c in r["context_ranks"]}
        semantic = pl.scan_parquet(fold_root / "semantic/val/records.parquet").filter(
            (pl.col("architecture_id") == arch) & pl.col("rank").is_in(needed)).collect()
        joined = semantic.join(stream, on="rank", how="inner", validate="1:1")
        if joined.height != len(needed):
            raise ValueError(f"unresolved events for {arch}")
        events[arch] = joined.with_columns(
            pl.lit(PARTITION).alias("partition"),
            pl.concat_str([pl.col("architecture_id"), pl.lit(":"), pl.col("rank")]).alias("record_id"),
            pl.when(pl.col("gid") >= 0).then(pl.concat_str([pl.lit("G"), pl.col("gid")]))
            .otherwise(pl.lit("GLOBAL")).alias("group_key"),
        ).with_columns(pl.col("group_key").map_elements(
            lambda g, a=arch: _sequence_id(a, PARTITION, g), return_dtype=pl.String).alias("sequence_id")
        ).select("architecture_id", "partition", "rank", "record_id", "effective_ts", "sequence_id",
                 "normalized_message")
        windows[arch] = rows
        labels[arch] = _labels_for_ranks(project, arch, {r["target_rank"] for r in rows})
    out.mkdir(parents=True)
    bundle, sidecar = out / "phase2_sequence_confirm", out / "source_dev_confirm"
    sidecar.mkdir()
    files, counts = {}, {}
    for fold in folds:
        src = seq_bundle / "folds" / fold
        fold_json = json.loads((src / "manifests/fold.json").read_text())
        archs = [a for a in architectures if a in fold_json["source_architectures"]]
        dst = bundle / "folds" / fold
        (dst / "manifests").mkdir(parents=True)
        (dst / "sequence/val").mkdir(parents=True)
        (dst / "sequence/metadata").mkdir(parents=True)
        shutil.copy2(src / "manifests/fold.json", dst / "manifests/fold.json")
        pl.DataFrame([r for a in archs for r in windows[a]]).write_parquet(dst / "sequence/val/windows.parquet")
        old = pl.read_parquet(src / "sequence/metadata/events.parquet")
        new = pl.concat([events[a] for a in archs]).select(old.columns)
        pl.concat([old, new]).unique(subset=["architecture_id", "partition", "rank"], keep="first").sort(
            "architecture_id", "partition", "rank").write_parquet(dst / "sequence/metadata/events.parquet")
        entries, unit_labels = [], {}
        for a in archs:
            for r in windows[a]:
                unit = r["window_id"] if a == "ARCH-BGL" else r["sequence_id"]
                value = bool(labels[a][r["target_rank"]])
                if unit_labels.setdefault((a, unit), value) != value:
                    raise ValueError("conflicting labels inside one unit")
                entries.append({"architecture_id": a, "window_id": r["window_id"], "target_rank": r["target_rank"],
                                "unit_id": unit, "anomaly": value})
        (sidecar / f"{fold}.json").write_text(json.dumps({"schema": SCHEMA, "fold_id": fold, "entries": entries},
                                                         sort_keys=True) + "\n")
        files[f"{fold}.json"] = sha256_file(sidecar / f"{fold}.json")
        counts[fold] = {a: dict(Counter(str(e["anomaly"]).lower() for e in entries if e["architecture_id"] == a))
                        for a in archs}
    bundle_manifest = {"schema_version": "PHASE2-SEQUENCE-CONFIRM-1", "selection_tag": tag,
                       "per_source": per_source, "derived_from_bundle_sha256": sha256_file(
                           seq_bundle / "manifests/bundle.json"),
                       "excluded_original_windows": len(original), "excluded_prior_cohort_windows": len(prior),
                       "folds": folds,
                       "files": {p.relative_to(bundle).as_posix(): sha256_file(p)
                                 for p in sorted(bundle.rglob("*")) if p.is_file()},
                       "target_labels_read": False}
    (bundle / "manifests").mkdir()
    (bundle / "manifests/bundle.json").write_text(json.dumps(bundle_manifest, indent=2, sort_keys=True) + "\n")
    manifest = {"schema": SCHEMA, "sequence_bundle_sha256": sha256_file(bundle / "manifests/bundle.json"),
                "folds": folds, "files": files, "target_labels_used_for_selection": False,
                "access_scope": "SOURCE_VALIDATION_CONFIRMATION", "selection_tag": tag,
                "class_counts_by_window": counts}
    (sidecar / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    for flag in ("--project", "--sequence-bundle", "--semantic-bundle", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--per-source", type=int, default=2048)
    parser.add_argument("--tag", default=TAG)
    parser.add_argument("--architectures", default=",".join(LABELLED))
    parser.add_argument("--exclude-sidecar", type=Path, action="append", default=[])
    args = parser.parse_args()
    manifest = build(args.project.resolve(), args.sequence_bundle, args.semantic_bundle, args.out, args.per_source,
                     args.tag, tuple(args.architectures.split(",")), tuple(args.exclude_sidecar))
    print(json.dumps(manifest["class_counts_by_window"], indent=1))
    print("CONFIRM_COHORT_BUILT=" + str(args.out))


if __name__ == "__main__":
    main()
