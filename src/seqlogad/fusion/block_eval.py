"""FUSION-E3-HDFS evaluation: block-level aggregation of every-line scores.

Pre-registration: docs/fusion/FUSION_E3_HDFS_PREREG.md.  Units are HDFS blocks;
bootstrap clusters are 64 consecutive blocks.  Only the registered hypotheses
are decided; everything else is reported as exploratory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from . import rules
from .baselines import B0, score_rows, train_messages
from .calibration import transductive_pvalues
from .confirm_eval import holm
from .evaluate import load_scores, single_metrics, unit_table
from .metrics import auroc, average_precision, cluster_bootstrap, summarize_interval
from .units import build_cohort

FOLD = "FOLD-TARGET-ARCH-HADOOP"
SEQ, SEM = "sequence_hadoop_best", "semantic_hadoop_best_mk42"
NONINFERIORITY_MARGIN = -0.02


def single_window_subset(rows):
    """One deterministic window per block: the E1/E2C-style sampled proxy."""
    best = {}
    for r in rows:
        key = int(hashlib.sha256(f"E3-single|{r['window_id']}".encode()).hexdigest(), 16)
        if r["unit_id"] not in best or key < best[r["unit_id"]][0]:
            best[r["unit_id"]] = (key, r)
    return [v[1] for v in best.values()]


def block_chunks(table, size=64):
    return np.array([f"c{i // size:03d}" for i in range(len(table["unit_id"]))])


def interval(stat, y, scores, clusters, boot):
    point = stat(y, scores)
    reps = cluster_bootstrap(y, scores, clusters, stat, reps=boot["reps"], seed=boot["seed"])
    return summarize_interval(reps, point)


def main(argv=None):
    parser = argparse.ArgumentParser()
    for flag in ("--run", "--block-inputs", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--reps", type=int, default=2000)
    args = parser.parse_args(argv)
    boot = {"reps": args.reps, "seed": 42}
    bundle = args.block_inputs / "phase2_sequence_blocks"
    cohort = build_cohort(bundle, args.block_inputs / "source_dev_blocks", FOLD)
    b0 = score_rows(B0(train_messages(bundle, FOLD, "ARCH-HDFS")), cohort)
    window = {SEQ: load_scores(args.run, SEQ), SEM: load_scores(args.run, SEM),
              "b0_frequency": {k: v["b0_frequency"] for k, v in b0.items()},
              "b0_markov": {k: v["b0_markov"] for k, v in b0.items()}}
    tables = {agg: unit_table(cohort, window, agg)[0] for agg in ("max", "top3", "mean")}
    tables["single"] = unit_table(single_window_subset(cohort), window, "mean")[0]
    order = tables["max"]["unit_id"]
    for agg, table in tables.items():
        index = {u: i for i, u in enumerate(table["unit_id"])}
        if set(index) != set(order):
            raise ValueError(f"block set mismatch for aggregation {agg}")
        take = np.array([index[u] for u in order])
        tables[agg] = {k: (list(np.asarray(v)[take]) if k == "unit_id" else np.asarray(v)[take])
                       for k, v in table.items()}
        if not np.array_equal(tables[agg]["anomaly"], tables["max"]["anomaly"]):
            raise ValueError("label misalignment between aggregations")
    y = tables["max"]["anomaly"]
    clusters = block_chunks(tables["max"])
    methods = {}
    for agg, table in tables.items():
        for name in (SEQ, SEM, "b0_frequency", "b0_markov"):
            methods[f"{name}@{agg}"] = table[name]
    p = {k: transductive_pvalues(methods[k]) for k in (f"{SEQ}@max", "b0_frequency@max", f"{SEM}@max")}
    methods["cauchy_seq_b0@max"] = rules.cauchy_score(p[f"{SEQ}@max"], p["b0_frequency@max"])
    methods["vw_seq_b0@max"] = rules.vovk_wang_score(p[f"{SEQ}@max"], p["b0_frequency@max"])
    methods["cauchy_seq_sem@max"] = rules.cauchy_score(p[f"{SEQ}@max"], p[f"{SEM}@max"])
    methods["vw_3way@max"] = -np.log(np.mean(np.vstack(list(p.values())), axis=0))

    prevalence = float(y.mean())
    tests = {
        "H5a_seq_max_auroc_gt_0.5": interval(lambda yy, s: auroc(yy, s[f"{SEQ}@max"]) - 0.5, y,
                                             {f"{SEQ}@max": methods[f"{SEQ}@max"]}, clusters, boot),
        "H5b_seq_max_ap_gt_prevalence": interval(lambda yy, s: average_precision(yy, s[f"{SEQ}@max"]) - yy.mean(),
                                                 y, {f"{SEQ}@max": methods[f"{SEQ}@max"]}, clusters, boot),
        "H6_seq_max_vs_single": interval(
            lambda yy, s: average_precision(yy, s["a"]) - average_precision(yy, s["b"]), y,
            {"a": methods[f"{SEQ}@max"], "b": methods[f"{SEQ}@single"]}, clusters, boot),
        "H7_cauchy_seq_b0_vs_best": interval(
            lambda yy, s: average_precision(yy, s["f"]) - max(average_precision(yy, s["a"]),
                                                              average_precision(yy, s["b"])), y,
            {"f": methods["cauchy_seq_b0@max"], "a": methods[f"{SEQ}@max"], "b": methods["b0_frequency@max"]},
            clusters, boot),
    }
    report = {"experiment_id": "FUSION-E3-HDFS", "blocks": int(y.size), "anomalous_blocks": int(y.sum()),
              "prevalence": prevalence, "windows": len(cohort),
              "metrics": {m: single_metrics(y, s, [0.01, 0.05]) for m, s in methods.items()},
              "tests": tests,
              "primary_family_holm": holm({k: v["one_sided_p_le_0"] for k, v in tests.items()
                                           if k.startswith(("H5", "H6"))}),
              "H7_noninferior": tests["H7_cauchy_seq_b0_vs_best"]["ci_low"] > NONINFERIORITY_MARGIN}
    args.out.write_text(json.dumps(report, indent=2, default=float))
    print(f"BLOCK_EVALUATION_WRITTEN={args.out}")


if __name__ == "__main__":
    main()
