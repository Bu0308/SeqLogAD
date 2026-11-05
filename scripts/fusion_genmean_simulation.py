"""Step-2 simulation: is there one generalised-mean rule (r, w) that is safe on both systems?

Synthetic two-expert scores (A = Sequence, B = Semantic) shaped after what E1-E4
measured, scored with the generalised mean family M_r,w (rules.generalized_mean_score):

* BGL_AND   both experts see every anomaly moderately (single AUROC ~0.84).
* BGL_MIXED one third seen by A only, one third by B only, one third by both.
* HDFS_CLEAN A sees ~65% of anomalies strongly (AP ~0.7), B has no signal: the
             Semantic expert after volatile-token removal.
* HDFS_FAKE  as HDFS_CLEAN, but B's top tail is driven by rare-but-normal lines
             that A also scores high: the Semantic expert before the fix.

Criterion (fixed before running): gain = AP(fused) - max(AP(A), AP(B)); a rule
is "safe" when its mean gain is >= -0.02 on every scenario and "useful" when it is
> 0 on at least one.  The minimax rule maximises the worst-scenario gain.
Output: JSON on stdout.
"""
import json

import numpy as np

from seqlogad.fusion import rules
from seqlogad.fusion.calibration import transductive_pvalues as tp
from seqlogad.fusion.metrics import average_precision as ap

R_GRID = (1.0, 0.5, 0.0, -0.5, -1.0, -2.0, -4.0, -8.0, -np.inf)
W_GRID = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)
SEEDS, N = 30, 4000


def scenario(name, seed):
    rng = np.random.default_rng(seed)
    if name.startswith("BGL"):
        y = rng.random(N) < 0.04
        shared = rng.normal(size=N)
        a, b = (np.sqrt(0.3) * shared + np.sqrt(0.7) * rng.normal(size=N) for _ in range(2))
        if name == "BGL_AND":
            return y, a + 1.4 * y, b + 1.4 * y
        k = rng.random(N)
        return y, a + 2.0 * y * (k < 0.66), b + 2.0 * y * (k > 0.33)
    y = rng.random(N) < 0.027
    seen = y & (rng.random(N) < 0.65)
    a = rng.normal(size=N) + 4.0 * seen
    b = rng.normal(size=N)
    if name == "HDFS_FAKE":
        rare = ~y & (rng.random(N) < 0.08)  # rare-but-normal lines: both experts score them high
        a, b = a + 2.5 * rare, b + 2.5 * rare
    return y, a, b


def main():
    names = ("BGL_AND", "BGL_MIXED", "HDFS_CLEAN", "HDFS_FAKE")
    rules_grid = {f"r={r},w={w}": (r, w) for r in R_GRID for w in W_GRID}
    gains = {k: {n: [] for n in names} for k in [*rules_grid, "cauchy"]}
    singles = {n: [] for n in names}
    for n in names:
        for seed in range(SEEDS):
            y, a, b = scenario(n, seed)
            pa, pb = tp(a), tp(b)
            best = max(ap(y, a), ap(y, b))
            singles[n].append((ap(y, a), ap(y, b)))
            for k, (r, w) in rules_grid.items():
                gains[k][n].append(ap(y, rules.generalized_mean_score(pa, pb, r, w)) - best)
            gains["cauchy"][n].append(ap(y, rules.cauchy_score(pa, pb)) - best)
    table = {k: {n: float(np.mean(v)) for n, v in per.items()} for k, per in gains.items()}
    for k, row in table.items():
        row["worst"] = min(row[n] for n in names)
        row["safe"] = all(row[n] >= -0.02 for n in names)
        row["useful"] = any(row[n] > 0 for n in names)
    ranked = sorted(table, key=lambda k: table[k]["worst"], reverse=True)
    print(json.dumps({"single_ap_mean": {n: [float(np.mean([s[i] for s in v])) for i in (0, 1)]
                                         for n, v in singles.items()},
                      "minimax_top10": {k: table[k] for k in ranked[:10]},
                      "reference": {k: table[k] for k in ("r=1.0,w=0.5", "r=-1.0,w=0.5", "r=-inf,w=0.5", "cauchy")},
                      "n_safe_and_useful": sum(table[k]["safe"] and table[k]["useful"] for k in table),
                      "safe_and_useful": [k for k in ranked if table[k]["safe"] and table[k]["useful"]]},
                     indent=1))


if __name__ == "__main__":
    main()
