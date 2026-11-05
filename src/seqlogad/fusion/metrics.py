"""Threshold-free detection metrics and paired uncertainty for fusion claims."""
from __future__ import annotations

import numpy as np
from scipy.stats import norm, rankdata


def _check(y, s):
    labels = np.asarray(y, dtype=bool)
    scores = np.asarray(s, dtype=float)
    if labels.shape != scores.shape or labels.ndim != 1:
        raise ValueError("labels and scores must be aligned vectors")
    if not np.isfinite(scores).all():
        raise ValueError("nonfinite score")
    if labels.all() or not labels.any():
        raise ValueError("metric needs both classes")
    return labels, scores


def average_precision(y, s) -> float:
    """Step-wise AP over distinct thresholds (same definition as scikit-learn)."""
    labels, scores = _check(y, s)
    order = np.argsort(-scores, kind="mergesort")
    sorted_scores, sorted_labels = scores[order], labels[order]
    last = np.r_[np.flatnonzero(np.diff(sorted_scores)), sorted_labels.size - 1]
    tp = np.cumsum(sorted_labels)[last]
    fp = (last + 1) - tp
    precision = tp / (tp + fp)
    recall = tp / labels.sum()
    recall_steps = np.diff(np.r_[0.0, recall])
    return float(np.sum(recall_steps * precision))


def auroc(y, s) -> float:
    """Mann-Whitney AUROC with mid-ranks for ties."""
    labels, scores = _check(y, s)
    ranks = rankdata(scores)
    pos = labels.sum()
    neg = labels.size - pos
    return float((ranks[labels].sum() - pos * (pos + 1) / 2) / (pos * neg))


def recall_at_budget(y, s, budget: float) -> dict:
    """Label-free threshold: flag the top ``budget`` fraction of units."""
    labels, scores = _check(y, s)
    k = max(1, int(np.ceil(budget * scores.size)))
    flagged = np.zeros(scores.size, dtype=bool)
    flagged[np.argsort(-scores, kind="mergesort")[:k]] = True
    return {"budget": budget, "flagged": k,
            "recall": float((flagged & labels).sum() / labels.sum()),
            "precision": float((flagged & labels).sum() / k),
            "fpr": float((flagged & ~labels).sum() / (~labels).sum())}


def delong_paired(y, s_a, s_b) -> dict:
    """DeLong et al. (Biometrics 1988) paired test of AUROC(a) - AUROC(b)."""
    labels, a = _check(y, s_a)
    _, b = _check(y, s_b)
    pos, neg = labels.sum(), (~labels).sum()

    def components(s):
        sp, sn = s[labels], s[~labels]
        v10 = np.array([(np.sum(x > sn) + 0.5 * np.sum(x == sn)) / neg for x in sp])
        v01 = np.array([(np.sum(sp > x) + 0.5 * np.sum(sp == x)) / pos for x in sn])
        return v10, v01

    a10, a01 = components(a)
    b10, b01 = components(b)
    s10 = np.cov(np.vstack([a10, b10]))
    s01 = np.cov(np.vstack([a01, b01]))
    var = (s10[0, 0] + s10[1, 1] - 2 * s10[0, 1]) / pos + (s01[0, 0] + s01[1, 1] - 2 * s01[0, 1]) / neg
    diff = float(a10.mean() - b10.mean())
    if var <= 0:
        return {"delta_auroc": diff, "z": None, "p_two_sided": None}
    z = diff / np.sqrt(var)
    return {"delta_auroc": diff, "z": float(z), "p_two_sided": float(2 * norm.sf(abs(z)))}


def cluster_bootstrap(y, score_map: dict, clusters, statistic, *, reps: int = 2000,
                      seed: int = 42) -> np.ndarray:
    """Paired cluster bootstrap: resample whole clusters, apply ``statistic``.

    ``statistic(y, {name: scores})`` returns a float; resamples lacking a class
    are redrawn so every replicate is defined.
    """
    labels = np.asarray(y, dtype=bool)
    groups = np.asarray(clusters)
    ids, inverse = np.unique(groups, return_inverse=True)
    members = [np.flatnonzero(inverse == i) for i in range(ids.size)]
    rng = np.random.default_rng(seed)
    out = []
    attempts = 0
    while len(out) < reps:
        attempts += 1
        if attempts > reps * 20:
            raise ValueError("bootstrap cannot draw both classes; clusters too coarse")
        take = np.concatenate([members[i] for i in rng.integers(0, ids.size, ids.size)])
        sample_y = labels[take]
        if sample_y.all() or not sample_y.any():
            continue
        out.append(statistic(sample_y, {k: np.asarray(v)[take] for k, v in score_map.items()}))
    return np.asarray(out, dtype=float)


def summarize_interval(values: np.ndarray, point: float, alpha: float = 0.05) -> dict:
    low, high = np.quantile(values, [alpha / 2, 1 - alpha / 2])
    return {"point": float(point), "ci_low": float(low), "ci_high": float(high),
            "one_sided_p_le_0": float((np.sum(values <= 0) + 1) / (values.size + 1)),
            "replicates": int(values.size)}
