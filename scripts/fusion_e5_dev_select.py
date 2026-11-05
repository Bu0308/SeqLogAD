"""FUSION-E5-DEV: pick ONE 2-expert fusion configuration on the E4 cohorts (CPU only).

Selection rule fixed in docs/fusion/FUSION_E5_DEV_PLAN.md before scoring:
gain = AP(fused) - max(AP(Seq), AP(Sem variant)); a configuration qualifies when
gain >= -0.02 on all three cohorts and > 0 on at least one BGL cohort; pick the
qualifier with the largest worst-case gain (ties: larger mean gain).  If none
qualifies, the confirmation run is not made.

    PYTHONPATH=src python scripts/fusion_e5_dev_select.py <E5DEV-compact.json.gz> <00_inputs_e4> <out.json>
"""
import gzip
import json
import sys
from pathlib import Path

import numpy as np

from seqlogad.fusion import rules
from seqlogad.fusion.calibration import transductive_pvalues
from seqlogad.fusion.evaluate import single_metrics, unit_table
from seqlogad.fusion.gated_eval import COHORTS, LAYOUT
from seqlogad.fusion.units import build_cohort

R_GRID = (1.0, 0.5, 0.0, -0.5, -1.0, -2.0, -4.0, -8.0, -np.inf)
W_GRID = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)
VARIANTS = ("semantic", "semantic_template")
MARGIN = -0.02


def load(compact: Path) -> dict:
    with gzip.open(compact, "rt") as fh:
        raw = json.load(fh)
    out = {}
    for key, scores in raw.items():
        run, name = key.split("/", 1)
        if name != "manifest":
            out[(run.split("-")[1], name)] = {w: (np.nan if v is None else v) for w, v in scores.items()}
    return out, {k: v for k, v in raw.items() if k.endswith("/manifest")}


def main():
    compact, inputs, out = map(Path, sys.argv[1:4])
    scores, manifests = load(compact)
    cohorts, configs = {}, {}
    for name, (fold, arch, tag, kind, agg) in COHORTS.items():
        bundle, sidecar = (inputs / kind / part for part in LAYOUT[kind])
        rows = [r for r in build_cohort(bundle, sidecar, fold) if r["architecture_id"] == arch]
        run = kind.upper()
        window = {"seq": scores[(run, f"sequence_{tag}_best")]}
        window.update({v: scores[(run, f"{v}_{tag}_best_mkmean")] for v in VARIANTS})
        table, abstained = unit_table(rows, window, agg)
        y = table["anomaly"]
        p = {k: transductive_pvalues(table[k]) for k in window}
        ap = lambda s: single_metrics(y, s, [0.01, 0.05])
        result = {"units": int(y.size), "positives": int(y.sum()), "abstained": abstained,
                  "single": {k: ap(table[k]) for k in window}, "gain": {}}
        for variant in VARIANTS:
            best = max(result["single"]["seq"]["average_precision"], result["single"][variant]["average_precision"])
            grid = {f"{variant}|r={r}|w={w}": rules.generalized_mean_score(p["seq"], p[variant], r, w)
                    for r in R_GRID for w in W_GRID}
            grid[f"{variant}|cauchy"] = rules.cauchy_score(p["seq"], p[variant])
            for key, fused in grid.items():
                m = ap(fused)
                result["gain"][key] = m["average_precision"] - best
                configs.setdefault(key, {})[name] = {"ap": m["average_precision"], "auroc": m["auroc"],
                                                     "gain": m["average_precision"] - best}
        cohorts[name] = result
    names = list(COHORTS)
    summary = {}
    for key, per in configs.items():
        gains = [per[n]["gain"] for n in names]
        summary[key] = {"worst": min(gains), "mean": float(np.mean(gains)),
                        "qualifies": min(gains) >= MARGIN and any(per[n]["gain"] > 0 for n in names if n.startswith("BGL")),
                        **{n: per[n] for n in names}}
    qualifiers = sorted((k for k in summary if summary[k]["qualifies"]),
                        key=lambda k: (summary[k]["worst"], summary[k]["mean"]), reverse=True)
    ranked = sorted(summary, key=lambda k: (summary[k]["worst"], summary[k]["mean"]), reverse=True)
    report = {"plan": "docs/fusion/FUSION_E5_DEV_PLAN.md", "cohorts": cohorts, "n_qualifying": len(qualifiers),
              "selected": qualifiers[0] if qualifiers else None,
              "top_by_worst_case": {k: summary[k] for k in ranked[:15]},
              "qualifiers": {k: summary[k] for k in qualifiers[:15]},
              "manifests": manifests}
    out.write_text(json.dumps(report, indent=2, default=float))
    print(json.dumps({"n_qualifying": len(qualifiers), "selected": report["selected"]}))


if __name__ == "__main__":
    main()
