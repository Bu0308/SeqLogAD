"""FUSION-E2-CONFIRM evaluation: only the pre-registered hypotheses, Holm-corrected.

Pre-registration: docs/fusion/FUSION_E2_CONFIRM_PREREG.md (hashes frozen before
any confirmation score existed).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from . import rules
from .baselines import B0, score_rows, train_messages
from .calibration import transductive_pvalues
from .evaluate import FOLD_TAG, load_scores, single_metrics, unit_table
from .metrics import average_precision, cluster_bootstrap, summarize_interval
from .units import build_cohort

ALPHA = 0.05
NONINFERIORITY_MARGIN = -0.02


def _p(table, key):
    return transductive_pvalues(table[key])


def _mean_p_score(*ps):
    return -np.log(np.mean(np.vstack(ps), axis=0))


def _gain(table, fused, singles, boot):
    def stat(y, s):
        return average_precision(y, s[fused]) - max(average_precision(y, s[k]) for k in singles)
    point = stat(table["anomaly"], table)
    reps = cluster_bootstrap(table["anomaly"], {k: table[k] for k in (fused, *singles)}, table["time_chunk"],
                             stat, reps=boot["reps"], seed=boot["seed"])
    return summarize_interval(reps, point)


def _paired(table, a, b, boot):
    def stat(y, s):
        return average_precision(y, s[a]) - average_precision(y, s[b])
    point = stat(table["anomaly"], table)
    reps = cluster_bootstrap(table["anomaly"], {a: table[a], b: table[b]}, table["time_chunk"],
                             stat, reps=boot["reps"], seed=boot["seed"])
    return summarize_interval(reps, point)


def holm(pvalues: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    order = sorted(pvalues, key=pvalues.get)
    out, still = {}, True
    for i, key in enumerate(order):
        still = still and pvalues[key] <= alpha / (len(order) - i)
        out[key] = still
    return out


def evaluate_fold_source(rows, scores, tag, boot, budgets):
    table, abstained = unit_table(rows, scores)
    seq, sem, sem1 = f"sequence_{tag}_best", f"semantic_{tag}_best_mkmean", f"semantic_{tag}_best_mk42"
    p = {k: _p(table, k) for k in (seq, "b0_frequency") + ((sem,) if sem in table else ())}
    table["vw_seq_b0"] = rules.vovk_wang_score(p[seq], p["b0_frequency"])
    table["cauchy_seq_b0"] = rules.cauchy_score(p[seq], p["b0_frequency"])
    tests = {"H1_vw_seq_b0": _gain(table, "vw_seq_b0", (seq, "b0_frequency"), boot),
             "H4_cauchy_seq_b0_vs_seq": _paired(table, "cauchy_seq_b0", seq, boot)}
    if sem in table:
        table["vw_sem_seq"] = rules.vovk_wang_score(p[sem], p[seq])
        table["vw_3way"] = _mean_p_score(p[sem], p[seq], p["b0_frequency"])
        tests["H2_vw_sem_seq"] = _gain(table, "vw_sem_seq", (sem, seq), boot)
        tests["H3_sem_mk8_vs_mk1"] = _paired(table, sem, sem1, boot)
        tests["H3b_sem_mk8_vs_b0"] = _paired(table, sem, "b0_frequency", boot)
        tests["X_vw_3way_vs_best_single"] = _gain(table, "vw_3way", (sem, seq, "b0_frequency"), boot)
    y = table["anomaly"]
    methods = [k for k in table if k not in ("unit_id", "anomaly", "time_chunk", "crossfit_fold")]
    return {"units": int(y.size), "positives": int(y.sum()), "abstained": abstained,
            "metrics": {m: single_metrics(y, table[m], budgets) for m in methods}, "tests": tests}


def main(argv=None):
    parser = argparse.ArgumentParser()
    for flag in ("--run", "--confirm-inputs", "--original-inputs", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--reps", type=int, default=2000)
    args = parser.parse_args(argv)
    boot, budgets = {"reps": args.reps, "seed": 42}, [0.01, 0.05]
    bundle = args.confirm_inputs / "phase2_sequence_confirm"
    sidecar = args.confirm_inputs / "source_dev_confirm"
    report = {"experiment_id": "FUSION-E2-CONFIRM", "results": {}}
    for fold_id, tag in FOLD_TAG.items():
        cohort = build_cohort(bundle, sidecar, fold_id)
        original = build_cohort(args.original_inputs / "phase2_sequence",
                                args.original_inputs / "phase2_source_development_v13r1", fold_id)
        used_units = {(r["architecture_id"], r["unit_id"]) for r in original}
        names = [f"sequence_{tag}_best", f"semantic_{tag}_best_mkmean", f"semantic_{tag}_best_mk42"]
        window = {n: load_scores(args.run, n) for n in names if load_scores(args.run, n)}
        for arch in sorted({r["architecture_id"] for r in cohort}):
            rows = [r for r in cohort if r["architecture_id"] == arch
                    and (arch, r["unit_id"]) not in used_units]
            b0 = score_rows(B0(train_messages(bundle, fold_id, arch)), rows)
            scores = dict(window, b0_frequency={k: v["b0_frequency"] for k, v in b0.items()})
            key = f"{fold_id}|{arch}"
            report["results"][key] = evaluate_fold_source(rows, scores, tag, boot, budgets)
            report["results"][key]["excluded_overlapping_units"] = len(
                {r["unit_id"] for r in cohort if r["architecture_id"] == arch}) - report["results"][key]["units"]
    primary = {f"{k}|{h}": v["tests"][h]["one_sided_p_le_0"] for k, v in report["results"].items()
               if k.endswith("ARCH-BGL") and "ARCH-BGL" in k for h in ("H1_vw_seq_b0", "H2_vw_sem_seq")
               if h in v["tests"]}
    report["primary_family_holm"] = {"pvalues": primary, "rejected_at_0.05": holm(primary)}
    report["H4_noninferiority"] = {k: {"ci_low": v["tests"]["H4_cauchy_seq_b0_vs_seq"]["ci_low"],
                                       "noninferior": v["tests"]["H4_cauchy_seq_b0_vs_seq"]["ci_low"]
                                       > NONINFERIORITY_MARGIN}
                                   for k, v in report["results"].items() if k.endswith("ARCH-HDFS")}
    args.out.write_text(json.dumps(report, indent=2, default=float))
    print(f"CONFIRM_EVALUATION_WRITTEN={args.out}")


if __name__ == "__main__":
    main()
