"""Label-fitted comparator: L2 logistic weights over gaussianised expert scores.

With 10-80 source positives per cohort the events-per-variable budget allows
about two fitted weights, so this comparator is deliberately tiny and always
cross-fitted (out-of-fold predictions only).  It exists to show whether a
learned weighting beats the parameter-free rules, not as the primary method.
"""
from __future__ import annotations

import numpy as np

from .calibration import transductive_pvalues


def fit_logistic(features: np.ndarray, labels: np.ndarray, l2: float = 1.0,
                 iterations: int = 50) -> np.ndarray:
    """Newton-Raphson for L2-penalised logistic regression; bias unpenalised."""
    x = np.column_stack([np.ones(len(features)), np.asarray(features, dtype=float)])
    y = np.asarray(labels, dtype=float)
    if y.min() == y.max():
        raise ValueError("logistic fit needs both classes")
    w = np.zeros(x.shape[1])
    penalty = np.full(x.shape[1], l2)
    penalty[0] = 0.0
    for _ in range(iterations):
        p = 1.0 / (1.0 + np.exp(-np.clip(x @ w, -30, 30)))
        gradient = x.T @ (p - y) + penalty * w
        hessian = (x * (p * (1 - p))[:, None]).T @ x + np.diag(penalty + 1e-9)
        step = np.linalg.solve(hessian, gradient)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w


def crossfit_scores(features: np.ndarray, labels: np.ndarray, folds: np.ndarray,
                    l2: float = 1.0) -> tuple[np.ndarray, list[list[float]]]:
    """Out-of-fold scores; each fold is predicted by a model fitted elsewhere.

    Folds are scored by different models whose intercepts and scales differ,
    so raw linear scores cannot be pooled into one ranking (E1 defect D-15).
    Each fold's scores are therefore mapped to label-free within-fold tail
    ranks, -log p, before pooling.
    """
    feats = np.asarray(features, dtype=float)
    y = np.asarray(labels, dtype=bool)
    groups = np.asarray(folds)
    out = np.full(len(y), np.nan)
    weights = []
    for group in np.unique(groups):
        test = groups == group
        w = fit_logistic(feats[~test], y[~test], l2=l2)
        linear = np.column_stack([np.ones(test.sum()), feats[test]]) @ w
        out[test] = -np.log(transductive_pvalues(linear))
        weights.append([float(v) for v in w])
    return out, weights
