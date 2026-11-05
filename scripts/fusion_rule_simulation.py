"""D-07: choose the primary fusion rule BEFORE any real fusion score exists.

Binormal synthetic experts with shared correlation rho and three complementarity
regimes (AND: both experts see every anomaly; OR: each anomaly is visible to one
expert; MIXED: one third each / both).  Reports the mean fusion gain in AP over
the better single expert across 30 seeds per scenario.  Output: JSON on stdout.
"""
import json

import numpy as np

from seqlogad.fusion import rules
from seqlogad.fusion.calibration import transductive_pvalues as tp
from seqlogad.fusion.metrics import average_precision as ap


def scenario(regime, rho, shift, seed, n=2000, prevalence=0.04):
    rng = np.random.default_rng(seed)
    y = rng.random(n) < prevalence
    shared = rng.normal(size=n)
    e1 = np.sqrt(rho) * shared + np.sqrt(1 - rho) * rng.normal(size=n)
    e2 = np.sqrt(rho) * shared + np.sqrt(1 - rho) * rng.normal(size=n)
    if regime == "AND":
        a, b = e1 + shift * y, e2 + shift * y
    elif regime == "OR":
        k = rng.random(n) < 0.5
        a, b = e1 + shift * (y & k), e2 + shift * (y & ~k)
    else:
        k = rng.random(n)
        a, b = e1 + shift * y * (k < 0.66), e2 + shift * y * (k > 0.33)
    pa, pb = tp(a), tp(b)
    fused = {name: rule(pa, pb) for name, rule in rules.RULES.items()}
    fused["copula_onesided"] = rules.copula_onesided_score(pa, pb, rules.fit_copula(pa, pb))
    fused["zscore_mean"] = rules.zscore_mean(a, b, a, b)
    best = max(ap(y, a), ap(y, b))
    return {name: ap(y, s) - best for name, s in fused.items()}, best


def main():
    out = []
    for regime in ("AND", "OR", "MIXED"):
        for rho in (0.0, 0.5, 0.8):
            for shift in (1.5, 3.0):
                runs = [scenario(regime, rho, shift, seed) for seed in range(30)]
                out.append({"regime": regime, "rho": rho, "shift": shift,
                            "best_single_ap": float(np.mean([r[1] for r in runs])),
                            "mean_gain": {k: float(np.mean([r[0][k] for r in runs])) for k in runs[0][0]}})
    positive = {k: sum(row["mean_gain"][k] > 0 for row in out) for k in out[0]["mean_gain"]}
    print(json.dumps({"scenarios": out, "scenarios_with_positive_gain": positive}, indent=2))


if __name__ == "__main__":
    main()
