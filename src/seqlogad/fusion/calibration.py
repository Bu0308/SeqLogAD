"""Label-free conformal tail p-values for HIGHER_IS_MORE_ANOMALOUS scores."""
from __future__ import annotations

import numpy as np


def tail_pvalues(reference: np.ndarray, scores: np.ndarray, *, mid_rank: bool = True) -> np.ndarray:
    """Return p(x) = (1 + #{r >= s(x)}) / (n + 1) against a reference sample.

    Bates et al. (Ann. Stat. 2023, eq. 3) define the conformal p-value with the
    opposite orientation; this module keeps the repository convention that a
    larger score is more anomalous.  With ``mid_rank`` ties between a test score
    and reference scores count one half, which removes the template-level tie
    bias of deterministic NLL scores without changing validity in expectation.
    """
    ref = np.sort(np.asarray(reference, dtype=float))
    values = np.asarray(scores, dtype=float)
    if ref.ndim != 1 or ref.size == 0:
        raise ValueError("calibration reference must be a non-empty vector")
    if not np.isfinite(ref).all() or not np.isfinite(values).all():
        raise ValueError("calibration requires finite scores")
    greater = ref.size - np.searchsorted(ref, values, side="right")
    if mid_rank:
        equal = np.searchsorted(ref, values, side="right") - np.searchsorted(ref, values, side="left")
        count = greater + 0.5 * equal
    else:
        count = greater + (np.searchsorted(ref, values, side="right")
                           - np.searchsorted(ref, values, side="left"))
    return (1.0 + count) / (ref.size + 1.0)


def transductive_pvalues(scores: np.ndarray) -> np.ndarray:
    """Label-free p-values of each unit against the rest of its own cohort.

    Used for source-development cohorts, where no separate unlabeled normal
    buffer exists.  The ranking equals the ECDF rank; no label is touched.
    """
    values = np.asarray(scores, dtype=float)
    if values.size < 2 or not np.isfinite(values).all():
        raise ValueError("transductive calibration needs >= 2 finite scores")
    ordered = np.sort(values)
    right = np.searchsorted(ordered, values, side="right")
    left = np.searchsorted(ordered, values, side="left")
    greater = values.size - right
    others_equal = (right - left) - 1
    # Leave-one-out reference of size n-1, so the denominator is (n-1)+1 = n.
    return (1.0 + greater + 0.5 * others_equal) / values.size


def split_reference(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic disjoint halves of a buffer: (per-expert ECDF, fused threshold)."""
    order = np.random.default_rng(seed).permutation(n)
    half = n // 2
    if half == 0:
        raise ValueError("buffer too small to split")
    return np.sort(order[:half]), np.sort(order[half:])
