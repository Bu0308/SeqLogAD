"""CPU evaluation of FUSION-E1 from persisted per-unit scores (no GPU needed)."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import spearmanr

from . import rules
from .baselines import B0, score_rows, train_messages
from .calibration import transductive_pvalues
from .learned import crossfit_scores
from .metrics import (auroc, average_precision, cluster_bootstrap, delong_paired,
                      recall_at_budget, summarize_interval)
from .units import build_cohort

FOLD_TAG = {"FOLD-TARGET-ARCH-HDFS": "hdfs", "FOLD-TARGET-ARCH-HADOOP": "hadoop",
            "FOLD-TARGET-ARCH-BGL": "bgl"}


def load_scores(run: Path, name: str) -> dict[str, float]:
    path = run / "scores" / f"{name}.jsonl"
    if not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    return {r["window_id"]: (r["nll_mean"] if r["status"] != "ABSTAIN" else np.nan) for r in rows}


AGGREGATORS = {
    "mean": np.mean,
    "max": np.max,
    "top3": lambda v: float(np.mean(np.sort(v)[-3:])),
}


def unit_table(rows: list[dict], window_scores: dict[str, dict[str, float]], aggregate: str = "mean"):
    """Per-unit aggregate of window scores (default mean, as at V13R1 selection).

    Abstentions are excluded inside a unit; a unit with no valid window is imputed
    with the cohort median.
    """
    reduce = AGGREGATORS[aggregate]
    units = defaultdict(list)
    for row in rows:
        units[row["unit_id"]].append(row)
    ids = sorted(units, key=lambda u: units[u][0]["target_rank"])
    table = {"unit_id": ids,
             "anomaly": np.array([units[u][0]["anomaly"] for u in ids]),
             "time_chunk": np.array([units[u][0]["time_chunk"] for u in ids]),
             "crossfit_fold": np.array([units[u][0]["crossfit_fold"] for u in ids])}
    abstained = {}
    for name, scores in window_scores.items():
        values = []
        for u in ids:
            finite = [v for v in (scores.get(r["window_id"], np.nan) for r in units[u]) if np.isfinite(v)]
            values.append(reduce(np.asarray(finite)) if finite else np.nan)
        values = np.asarray(values, dtype=float)
        missing = ~np.isfinite(values)
        abstained[name] = int(missing.sum())
        values[missing] = np.nanmedian(values) if (~missing).any() else 0.0
        table[name] = values
    return table, abstained


def single_metrics(y, s, budgets):
    return {"average_precision": average_precision(y, s), "auroc": auroc(y, s),
            **{f"at_{int(b * 100)}pct": recall_at_budget(y, s, b) for b in budgets}}


def fuse(table: dict, sem: str, seq: str, sem_base: str, seq_base: str) -> dict[str, np.ndarray]:
    p = {k: transductive_pvalues(table[k]) for k in (sem, seq)}
    lr = {k: transductive_pvalues(table[k] - table[b]) for k, b in ((sem, sem_base), (seq, seq_base))}
    rho = rules.fit_copula(p[sem], p[seq])
    out = {name: rule(p[sem], p[seq]) for name, rule in rules.RULES.items()}
    out.update({
        "lr_cauchy": rules.cauchy_score(lr[sem], lr[seq]),
        "lr_vovk_wang_mean": rules.vovk_wang_score(lr[sem], lr[seq]),
        "copula_onesided": rules.copula_onesided_score(p[sem], p[seq], rho),
        "zscore_mean": rules.zscore_mean(table[sem], table[seq], table[sem], table[seq]),
        "lr_semantic_only": -np.log(lr[sem]), "lr_sequence_only": -np.log(lr[seq]),
    })
    features = np.column_stack([rules.gaussianise(p[sem]), rules.gaussianise(p[seq])])
    learned, weights = crossfit_scores(features, table["anomaly"], table["crossfit_fold"])
    out["learned_logistic"] = learned
    return out, {"copula_rho": rho, "learned_weights": weights}


def complementarity(table, sem, seq, budget=0.05):
    y = table["anomaly"]
    ps, pq = transductive_pvalues(table[sem]), transductive_pvalues(table[seq])
    k = max(1, int(np.ceil(budget * y.size)))
    top_s = set(np.argsort(ps, kind="mergesort")[:k])
    top_q = set(np.argsort(pq, kind="mergesort")[:k])
    pos = set(np.flatnonzero(y))
    return {
        "spearman_normals": float(spearmanr(ps[~y], pq[~y]).statistic),
        "spearman_positives": float(spearmanr(ps[y], pq[y]).statistic) if y.sum() > 2 else None,
        "top_budget_jaccard_label_free": len(top_s & top_q) / len(top_s | top_q),
        "positives_caught_at_budget": {"semantic_only": len((top_s - top_q) & pos),
                                       "sequence_only": len((top_q - top_s) & pos),
                                       "both": len(top_s & top_q & pos),
                                       "neither": len(pos - top_s - top_q), "total": len(pos)},
    }


def gain_statistic(fused: str, singles: tuple[str, str]):
    def statistic(y, scores):
        return (average_precision(y, scores[fused])
                - max(average_precision(y, scores[s]) for s in singles))
    return statistic


GAIN_RULES = ("cauchy", "lr_cauchy", "vovk_wang_mean", "bonferroni_min", "copula_onesided",
              "zscore_mean", "learned_logistic")
# E1.1 (post hoc, exploratory): Sequence fused with the label-free B0 baseline is
# compared against the better of its own two components.
B0_GAIN_RULES = ("sequence_plus_b0", "sequence_plus_b0_vw")


def evaluate_source(table, names, budgets, boot):
    sem, seq = names["semantic"], names["sequence"]
    fused, extra = fuse(table, sem, seq, names["semantic_base"], names["sequence_base"])
    controls = {
        "sequence_best_plus_latest": rules.cauchy_score(transductive_pvalues(table[seq]),
                                                        transductive_pvalues(table[names["sequence_latest"]])),
        "semantic_plus_b0": rules.cauchy_score(transductive_pvalues(table[sem]),
                                               transductive_pvalues(table["b0_frequency"])),
        "sequence_plus_b0": rules.cauchy_score(transductive_pvalues(table[seq]),
                                               transductive_pvalues(table["b0_frequency"])),
        "sequence_plus_b0_vw": rules.vovk_wang_score(transductive_pvalues(table[seq]),
                                                     transductive_pvalues(table["b0_frequency"])),
    }
    y = table["anomaly"]
    methods = {key: table[key] for key in table if key not in
               ("unit_id", "anomaly", "time_chunk", "crossfit_fold")}
    methods.update(fused)
    methods.update(controls)
    result = {"units": int(y.size), "positives": int(y.sum()),
              "metrics": {m: single_metrics(y, s, budgets) for m, s in methods.items()},
              "fusion_details": extra, "complementarity": complementarity(table, sem, seq)}
    gains = {}
    specs = [(rule, (sem, seq)) for rule in GAIN_RULES]
    specs += [(rule, (seq, "b0_frequency")) for rule in B0_GAIN_RULES]
    for rule, singles in specs:
        point = gain_statistic(rule, singles)(y, methods)
        reps = cluster_bootstrap(y, {rule: methods[rule], **{s: methods[s] for s in singles}},
                                 table["time_chunk"], gain_statistic(rule, singles),
                                 reps=boot["reps"], seed=boot["seed"])
        gains[rule] = {"compared_to": list(singles),
                       "fusion_gain_ap": summarize_interval(reps, point),
                       "delong_vs_semantic": delong_paired(y, methods[rule], table[sem]),
                       "delong_vs_sequence": delong_paired(y, methods[rule], table[seq])}
    result["fusion_gain"] = gains
    return result


def flat_summary(report: dict) -> dict[str, float]:
    """Numeric scalars for Projmem ``--metrics`` (AP of experts, primary fusion gains)."""
    out = {}
    for fold_id, fold in report["folds"].items():
        tag = FOLD_TAG[fold_id]
        for arch, source in fold["sources"].items():
            key = f"{tag}_{arch.removeprefix('ARCH-').lower()}"
            for method, values in source["metrics"].items():
                out[f"{key}_ap_{method}"] = values["average_precision"]
            for rule, gain in source["fusion_gain"].items():
                out[f"{key}_gain_ap_{rule}"] = gain["fusion_gain_ap"]["point"]
                out[f"{key}_gain_ap_{rule}_ci_low"] = gain["fusion_gain_ap"]["ci_low"]
    return out


def main(argv=None):
    parser = argparse.ArgumentParser()
    for flag in ("--run", "--inputs", "--config", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    args = parser.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    ev = cfg["evaluation"]
    data = args.inputs / cfg["data"]["sequence_bundle"]
    sidecar = args.inputs / cfg["data"]["source_development"]
    report = {"experiment_id": cfg["experiment_id"], "primary_metric": ev["primary_metric"],
              "semantic_variant": ev.get("semantic_variant", "best"), "folds": {}}
    for fold_id, spec in cfg["artifacts"].items():
        tag = FOLD_TAG[fold_id]
        cohort = build_cohort(data, sidecar, fold_id)
        has_semantic = "semantic" in spec
        variant = ev.get("semantic_variant", "best")
        names = {"semantic": f"semantic_{tag}_{variant}" if has_semantic else "semantic_base",
                 "sequence": f"sequence_{tag}_best", "sequence_latest": f"sequence_{tag}_latest",
                 "semantic_base": "semantic_base", "sequence_base": "sequence_base"}
        window = {n: load_scores(args.run, n) for n in
                  {*names.values(), f"semantic_{tag}_latest"} if load_scores(args.run, n)}
        fold_report = {"semantic_expert": "TRAINED" if has_semantic else "BASE_MODEL_ONLY_EXPLORATORY",
                       "sources": {}}
        for arch in sorted({r["architecture_id"] for r in cohort}):
            rows = [r for r in cohort if r["architecture_id"] == arch
                    and (ev["report_units"] != "fresh" or not r["selection_cohort"])]
            b0 = score_rows(B0(train_messages(data, fold_id, arch)), rows)
            scores = dict(window)
            scores["b0_frequency"] = {k: v["b0_frequency"] for k, v in b0.items()}
            scores["b0_markov"] = {k: v["b0_markov"] for k, v in b0.items()}
            table, abstained = unit_table(rows, scores)
            source = evaluate_source(table, names, ev["budgets"], ev["bootstrap"])
            source["abstained_units"] = abstained
            fold_report["sources"][arch] = source
        report["folds"][fold_id] = fold_report
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=float))
    args.out.with_name("summary.json").write_text(json.dumps(flat_summary(report), indent=2, sort_keys=True))
    print(f"EVALUATION_WRITTEN={args.out}")


if __name__ == "__main__":
    main()
