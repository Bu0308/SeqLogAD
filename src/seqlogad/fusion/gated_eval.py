"""FUSION-E4 evaluation: label-free gated 2-expert fusion vs. each expert and paper baselines.

Pre-registration: docs/fusion/FUSION_E4_GATED_PREREG.md.  The gate is decided
once per cohort from unlabelled scores (gate.py); labels are read only after
every score, gate decision and fused score is fixed.  Units: BGL line (mean of
its single window), HDFS block (max over its lines, as pre-registered in E3).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from . import gate, rules
from .baselines import B0, score_rows, train_messages
from .baselines_eval import train_windows
from .calibration import transductive_pvalues
from .confirm_eval import holm
from .evaluate import load_scores, single_metrics, unit_table
from .metrics import average_precision, cluster_bootstrap, summarize_interval
from .paper_baselines import all_baselines
from .units import build_cohort

NONINFERIORITY_MARGIN = 0.02
COHORTS = {  # name: (fold, architecture, score tag, cohort kind, unit aggregate)
    "BGL@HDFS-fold": ("FOLD-TARGET-ARCH-HDFS", "ARCH-BGL", "hdfs", "bgl", "mean"),
    "BGL@HADOOP-fold": ("FOLD-TARGET-ARCH-HADOOP", "ARCH-BGL", "hadoop", "bgl", "mean"),
    "HDFS@HADOOP-fold": ("FOLD-TARGET-ARCH-HADOOP", "ARCH-HDFS", "hadoop", "hdfs", "max"),
}
LAYOUT = {"bgl": ("phase2_sequence_confirm", "source_dev_confirm"),
          "hdfs": ("phase2_sequence_blocks", "source_dev_blocks")}
BASELINES = ("deeplog_du2017", "pca_xu2009", "iforest_liu2008", "knn_tfidf_k4", "b0_frequency", "b0_markov")


def fused_methods(seq: np.ndarray, sem: np.ndarray) -> tuple[dict, dict]:
    """Every fused score is a function of unlabelled expert scores only."""
    p_seq, p_sem = transductive_pvalues(seq), transductive_pvalues(sem)
    stat = gate.tail_lift(seq, sem)
    decision = {"primary": gate.is_open(stat)}
    methods = {"gated_vw": gate.gated_score(p_seq, p_sem, decision["primary"]),
               "ungated_vw": rules.vovk_wang_score(p_seq, p_sem),
               "ungated_cauchy": rules.cauchy_score(p_seq, p_sem)}
    for lift in (1.5, 3.0):  # exploratory sensitivity of the threshold
        decision[f"lift{lift}"] = gate.is_open(stat, min_lift=lift)
        methods[f"gated_vw_lift{lift}"] = gate.gated_score(p_seq, p_sem, decision[f"lift{lift}"])
    return methods, {"statistic": stat, "open": decision}


def ap_difference(a: str, b: str, shift: float = 0.0):
    return lambda y, s: average_precision(y, s[a]) - average_precision(y, s[b]) + shift


def evaluate_cohort(name, spec, run, inputs, original, boot):
    fold, arch, tag, kind, agg = spec
    bundle, sidecar = (inputs / kind / part for part in LAYOUT[kind])
    rows = [r for r in build_cohort(bundle, sidecar, fold) if r["architecture_id"] == arch]
    seq, sem = f"sequence_{tag}_best", f"semantic_{tag}_best_mkmean"
    window = {seq: load_scores(run, seq), sem: load_scores(run, sem)}
    train = train_windows(original, fold, arch)
    raw = all_baselines(train, [(r["context_messages"], r["target_message"]) for r in rows])
    window.update({k: {r["window_id"]: float(v) for r, v in zip(rows, vals)} for k, vals in raw.items()})
    b0 = score_rows(B0(train_messages(original, fold, arch)), rows)
    window.update({k: {w: v[k] for w, v in b0.items()} for k in ("b0_frequency", "b0_markov")})
    table, abstained = unit_table(rows, window, agg)
    fused, gate_info = fused_methods(table[seq], table[sem])
    table.update(fused)
    y = table["anomaly"]  # labels enter here, after the gate and every score are fixed
    clusters = np.array([f"c{i // 64:03d}" for i in range(y.size)])
    methods = [seq, sem, *fused, *BASELINES]
    report = {"fold": fold, "architecture": arch, "aggregate": agg, "units": int(y.size),
              "positives": int(y.sum()), "windows": len(rows), "abstained": abstained, "gate": gate_info,
              "metrics": {m: single_metrics(y, table[m], [0.01, 0.05]) for m in methods}, "tests": {}}

    scores = {m: table[m] for m in methods}

    def interval(stat):
        return summarize_interval(cluster_bootstrap(y, scores, clusters, stat, **boot), stat(y, scores))

    if arch == "ARCH-BGL":
        report["tests"]["H9_gain_vs_best_expert"] = interval(
            lambda yy, s: average_precision(yy, s["gated_vw"]) - max(average_precision(yy, s[seq]),
                                                                    average_precision(yy, s[sem])))
    else:
        report["tests"]["H10_noninferior_vs_sequence"] = interval(
            ap_difference("gated_vw", seq, NONINFERIORITY_MARGIN))
    report["tests"]["X_ungated_vw_gain_vs_best_expert"] = interval(
        lambda yy, s: average_precision(yy, s["ungated_vw"]) - max(average_precision(yy, s[seq]),
                                                                  average_precision(yy, s[sem])))
    report["vs_baselines"] = {b: interval(ap_difference("gated_vw", b)) for b in BASELINES}
    report["sequence_vs_baselines"] = {b: interval(ap_difference(seq, b)) for b in BASELINES}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    for flag in ("--run-bgl", "--run-hdfs", "--e4-inputs", "--original-bundle", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--reps", type=int, default=2000)
    args = parser.parse_args(argv)
    boot = {"reps": args.reps, "seed": 42}
    runs = {"bgl": args.run_bgl, "hdfs": args.run_hdfs}
    cohorts = {name: evaluate_cohort(name, spec, runs[spec[3]], args.e4_inputs, args.original_bundle, boot)
               for name, spec in COHORTS.items()}
    primary = {f"{name}:{test}": result["one_sided_p_le_0"]
               for name, c in cohorts.items() for test, result in c["tests"].items() if test.startswith("H")}
    secondary = {f"{name}:{b}": r["one_sided_p_le_0"] for name, c in cohorts.items()
                 for b, r in c["vs_baselines"].items()}
    gate_prediction = {name: c["gate"]["open"]["primary"] == (c["architecture"] == "ARCH-BGL")
                       for name, c in cohorts.items()}
    report = {"experiment_id": "FUSION-E4-GATED", "cohorts": cohorts, "H8_gate_prediction": gate_prediction,
              "primary_family_holm": holm(primary), "secondary_family_holm": holm(secondary)}
    args.out.write_text(json.dumps(report, indent=2, default=float))
    print(f"GATED_EVALUATION_WRITTEN={args.out}")


if __name__ == "__main__":
    main()
