"""Same-protocol comparison: published baselines vs. SeqLogAD experts and fusion.

For each evaluation cohort (E2C confirmation: BGL lines; E3: HDFS blocks with
every line) the baselines are fitted on the SOURCE_TRAIN windows of the same
architecture from the original bundle, then scored on exactly the cohort units
our experts scored.  Paired cluster bootstrap compares our pre-registered
method against each baseline (AP difference, 95 % CI).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from . import rules
from .baselines import B0, score_rows, train_messages
from .calibration import transductive_pvalues
from .evaluate import load_scores, single_metrics, unit_table
from .metrics import average_precision, cluster_bootstrap, summarize_interval
from .paper_baselines import all_baselines
from .units import build_cohort

TRAIN_LIMIT = 32768


def train_windows(bundle: Path, fold_id: str, arch: str) -> list[tuple[list[str], str]]:
    root = bundle / "folds" / fold_id / "sequence"
    windows = [w for w in pq.read_table(root / "train/windows.parquet").to_pylist() if w["architecture_id"] == arch]
    events = pq.read_table(root / "metadata/events.parquet",
                           columns=["architecture_id", "partition", "rank", "normalized_message"])
    text = {(a, r): m for a, p, r, m in zip(*(events[c].to_pylist() for c in
                                                ("architecture_id", "partition", "rank", "normalized_message")))
            if a == arch and p == "SOURCE_TRAIN"}
    out = [([text[(arch, r)] for r in w["context_ranks"]], text[(arch, w["target_rank"])]) for w in windows]
    return out[:TRAIN_LIMIT]


def compare(rows, ours: dict[str, dict[str, float]], baseline_windows, aggregate, boot, primary):
    scores = dict(ours)
    scores.update(baseline_windows)
    table, _ = unit_table(rows, scores, aggregate)
    y = table["anomaly"]
    seq = next(k for k in ours if k.startswith("sequence_"))
    sem = next((k for k in ours if k.endswith("mkmean")), None)
    p = {k: transductive_pvalues(table[k]) for k in [seq, "b0_frequency"] + ([sem] if sem else [])}
    table["ours_vw_seq_b0"] = rules.vovk_wang_score(p[seq], p["b0_frequency"])
    table["ours_cauchy_seq_b0"] = rules.cauchy_score(p[seq], p["b0_frequency"])
    if sem:
        table["ours_vw_3way"] = -np.log(np.mean(np.vstack(list(p.values())), axis=0))
    methods = [k for k in table if k not in ("unit_id", "anomaly", "time_chunk", "crossfit_fold")]
    clusters = np.array([f"c{i // 64:03d}" for i in range(y.size)])
    result = {"units": int(y.size), "positives": int(y.sum()), "aggregate": aggregate,
              "metrics": {m: single_metrics(y, table[m], [0.01, 0.05]) for m in methods}, "vs_baselines": {}}
    for baseline in baseline_windows:
        def stat(yy, s, b=baseline):
            return average_precision(yy, s["ours"]) - average_precision(yy, s[b])
        reps = cluster_bootstrap(y, {"ours": table[primary], baseline: table[baseline]}, clusters, stat,
                                 reps=boot["reps"], seed=boot["seed"])
        result["vs_baselines"][baseline] = summarize_interval(reps, stat(y, {"ours": table[primary],
                                                                             baseline: table[baseline]}))
    result["primary_method"] = primary
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    for flag in ("--original-bundle", "--cohort-bundle", "--cohort-sidecar", "--run", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--fold", required=True)
    parser.add_argument("--arch", required=True)
    parser.add_argument("--aggregate", default="mean")
    parser.add_argument("--primary", default="ours_vw_seq_b0")
    parser.add_argument("--exclude-sidecar", type=Path, action="append", default=[])
    parser.add_argument("--reps", type=int, default=2000)
    args = parser.parse_args(argv)
    tag = {"FOLD-TARGET-ARCH-HDFS": "hdfs", "FOLD-TARGET-ARCH-HADOOP": "hadoop", "FOLD-TARGET-ARCH-BGL": "bgl"}[args.fold]
    excluded = set()
    for sidecar in args.exclude_sidecar:
        for path in sidecar.glob("FOLD-*.json"):
            excluded |= {e["unit_id"] for e in json.loads(path.read_text())["entries"]
                         if e["architecture_id"] == args.arch}
    rows = [r for r in build_cohort(args.cohort_bundle, args.cohort_sidecar, args.fold)
            if r["architecture_id"] == args.arch and r["unit_id"] not in excluded]
    train = train_windows(args.original_bundle, args.fold, args.arch)
    test = [(r["context_messages"], r["target_message"]) for r in rows]
    raw = all_baselines(train, test)
    baseline_windows = {name: {r["window_id"]: float(v) for r, v in zip(rows, values)} for name, values in raw.items()}
    b0 = score_rows(B0(train_messages(args.original_bundle, args.fold, args.arch)), rows)
    ours = {name: load_scores(args.run, name) for name in
            (f"sequence_{tag}_best", f"semantic_{tag}_best_mkmean") if load_scores(args.run, name)}
    ours["b0_frequency"] = {k: v["b0_frequency"] for k, v in b0.items()}
    result = compare(rows, ours, baseline_windows, args.aggregate, {"reps": args.reps, "seed": 42}, args.primary)
    result.update({"fold": args.fold, "arch": args.arch, "train_windows": len(train)})
    args.out.write_text(json.dumps(result, indent=2, default=float))
    print(f"BASELINES_WRITTEN={args.out}")


if __name__ == "__main__":
    main()
