"""Pre-registered fusion rules over two calibrated experts.

Every rule returns an anomaly score where larger means more anomalous.  Rules
named ``*_pvalue`` additionally define a merged p-value; only Vovk-Wang
averaging is valid under arbitrary dependence (Biometrika 2020).
"""
from __future__ import annotations

import numpy as np
from scipy.special import ndtri

EPS = 1e-12


def _as_pair(p_a, p_b):
    a, b = np.asarray(p_a, dtype=float), np.asarray(p_b, dtype=float)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("fusion inputs must be aligned vectors")
    if ((a <= 0) | (a > 1) | (b <= 0) | (b > 1)).any():
        raise ValueError("p-values must lie in (0, 1]")
    return a, b


def zscore_mean(raw_a, raw_b, ref_a, ref_b):
    """Simple fusion baseline: mean of reference-standardised raw NLL scores."""
    out = []
    for raw, ref in ((raw_a, ref_a), (raw_b, ref_b)):
        ref = np.asarray(ref, dtype=float)
        scale = ref.std()
        if not np.isfinite(scale) or scale <= 0:
            raise ValueError("degenerate reference for z-score fusion")
        out.append((np.asarray(raw, dtype=float) - ref.mean()) / scale)
    return 0.5 * (out[0] + out[1])


def vovk_wang_pvalue(p_a, p_b):
    """Merged p = min(1, 2 * mean(p)); valid for any dependence between experts."""
    a, b = _as_pair(p_a, p_b)
    return np.minimum(1.0, a + b)


def vovk_wang_score(p_a, p_b):
    """Ranking score of the arithmetic-mean merge (unclipped to keep ties apart)."""
    a, b = _as_pair(p_a, p_b)
    return -np.log(0.5 * (a + b))


def generalized_mean_score(p_a, p_b, r: float, w: float = 0.5):
    """-log of the weighted generalised mean M_r = (w a^r + (1-w) b^r)^(1/r) of two p-values.

    r = 1 is Vovk-Wang averaging (an "AND"-like rule), r = -1 the harmonic mean,
    r = 0 the weighted geometric mean, r -> -inf the minimum ("OR"-like).  Vovk &
    Wang (Biometrika 2020) give the constant that makes every M_r a valid p-value
    under arbitrary dependence; a constant does not change the ranking, so it is
    omitted here.  ``w`` is the weight of the first expert.
    """
    a, b = _as_pair(p_a, p_b)
    if not 0.0 <= w <= 1.0:
        raise ValueError("weight must lie in [0, 1]")
    if w in (0.0, 1.0):
        return -np.log(a if w == 1.0 else b)
    if r == 0:
        return -(w * np.log(a) + (1 - w) * np.log(b))
    if np.isinf(r):
        return -np.log(np.minimum(a, b) if r < 0 else np.maximum(a, b))
    # log-sum-exp form keeps very negative r numerically stable
    terms = np.vstack([np.log(w + EPS) + r * np.log(a), np.log(1 - w + EPS) + r * np.log(b)])
    top = terms.max(0)
    return -(top + np.log(np.exp(terms - top).sum(0))) / r


def bonferroni_min_score(p_a, p_b):
    """Sensitivity rule: 2 * min(p); the weakest merge in Gupta et al. (EMNLP 2025)."""
    a, b = _as_pair(p_a, p_b)
    return -np.log(np.minimum(1.0, 2.0 * np.minimum(a, b)))


def cauchy_score(p_a, p_b):
    """Primary ranking rule: Cauchy combination (Liu & Xie, JASA 2020).

    Its p-value is only asymptotically valid, so thresholds come from
    re-conformalising the fused score, never from this formula.  It was chosen
    a priori because in the AND / OR / mixed complementarity simulation
    (docs/fusion/FUSION_RESEARCH_DECISION_LOG.md, D-07) it was the only rule
    with a positive mean fusion gain in all 18 scenarios.
    """
    a, b = _as_pair(p_a, p_b)
    a, b = np.clip(a, EPS, 1 - EPS), np.clip(b, EPS, 1 - EPS)
    return 0.5 * (np.tan((0.5 - a) * np.pi) + np.tan((0.5 - b) * np.pi))


def fisher_score(p_a, p_b):
    """Sensitivity rule: -log(p_a) - log(p_b) (ranking only; not valid as a p-value here)."""
    a, b = _as_pair(p_a, p_b)
    return -np.log(a) - np.log(b)


def stouffer_score(p_a, p_b):
    """Sensitivity rule: sum of gaussianised p-values (ranking only)."""
    a, b = _as_pair(p_a, p_b)
    return gaussianise(a) + gaussianise(b)


def gaussianise(p):
    """Map a tail p-value to a standard-normal deviation (larger = more anomalous)."""
    return ndtri(1.0 - np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS))


def fit_copula(ref_p_a, ref_p_b):
    """Label-free Gaussian-copula correlation estimated on a reference sample."""
    za, zb = gaussianise(ref_p_a), gaussianise(ref_p_b)
    rho = float(np.corrcoef(za, zb)[0, 1])
    if not np.isfinite(rho):
        raise ValueError("degenerate copula reference")
    return float(np.clip(rho, -0.95, 0.95))


def copula_onesided_score(p_a, p_b, rho):
    """One-sided Mahalanobis distance of (z_a+, z_b+) under the normal correlation.

    Clipping at zero ignores units that are *more* typical than normal on an
    expert, so the rule cannot flag low-low units.  With rho > 0 a unit that is
    extreme on only one expert scores higher than under the plain sum, which is
    the disagreement (burst vs. context-break) pattern predicted for the experts.
    """
    a, b = _as_pair(p_a, p_b)
    za, zb = np.maximum(gaussianise(a), 0.0), np.maximum(gaussianise(b), 0.0)
    det = 1.0 - rho * rho
    return (za * za - 2 * rho * za * zb + zb * zb) / det


RULES = {
    "cauchy": cauchy_score,
    "vovk_wang_mean": vovk_wang_score,
    "bonferroni_min": bonferroni_min_score,
    "fisher": fisher_score,
    "stouffer": stouffer_score,
}
