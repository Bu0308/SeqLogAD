"""Label-free gate for 2-expert fusion (FUSION-E4, docs/fusion/FUSION_E4_GATED_PREREG.md).

The secondary expert is admitted only if its upper tail co-occurs with the
primary expert's upper tail more often than chance on the unlabelled cohort
being scored.  An expert whose extremes are unrelated to the primary's (noise
on that system) is closed out, so the fused score falls back to the primary.

Statistic: fractional top-q overlap O between the two experts (ties at the
boundary share the remaining slots), expected overlap E = k^2 / N under
independence, lift = O / E, and a one-sided permutation p-value.
"""
from __future__ import annotations

import math

import numpy as np

from . import rules

Q, MIN_LIFT, ALPHA, PERMUTATIONS, SEED = 0.05, 2.0, 0.01, 2000, 42


def top_membership(scores: np.ndarray, k: int) -> np.ndarray:
    """Fractional membership in the top-k; boundary ties share the remaining slots."""
    s = np.asarray(scores, dtype=float)
    boundary = np.sort(s)[::-1][k - 1]
    above = s > boundary
    tied = s == boundary
    w = above.astype(float)
    w[tied] = (k - above.sum()) / tied.sum()
    return w


def tail_lift(primary, secondary, q: float = Q, permutations: int = PERMUTATIONS, seed: int = SEED) -> dict:
    a, b = np.asarray(primary, dtype=float), np.asarray(secondary, dtype=float)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("expert score vectors must be aligned 1-D arrays")
    n = a.size
    k = max(1, math.ceil(q * n))
    wa, wb = top_membership(a, k), top_membership(b, k)
    observed = float(wa @ wb)
    expected = k * k / n
    rng = np.random.default_rng(seed)
    null = np.array([wa @ wb[rng.permutation(n)] for _ in range(permutations)])
    p_value = float((1 + np.sum(null >= observed - 1e-12)) / (1 + permutations))
    return {"n": n, "k": k, "q": q, "overlap": observed, "expected": expected,
            "lift": observed / expected, "p_value": p_value, "permutations": permutations}


def is_open(stat: dict, min_lift: float = MIN_LIFT, alpha: float = ALPHA) -> bool:
    return bool(stat["lift"] >= min_lift and stat["p_value"] < alpha)


def gated_score(p_primary, p_secondary, open_: bool) -> np.ndarray:
    """Open: Vovk-Wang mean of the two tail p-values; closed: the primary alone."""
    if open_:
        return rules.vovk_wang_score(p_primary, p_secondary)
    return -np.log(np.asarray(p_primary, dtype=float))
