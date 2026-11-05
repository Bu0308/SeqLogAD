"""Numerical contracts of calibration, fusion rules, metrics and the learned comparator."""
from itertools import product

import numpy as np
import pytest

from seqlogad.fusion import rules
from seqlogad.fusion.calibration import split_reference, tail_pvalues, transductive_pvalues
from seqlogad.fusion.learned import crossfit_scores, fit_logistic
from seqlogad.fusion.metrics import (auroc, average_precision, cluster_bootstrap, delong_paired,
                                     recall_at_budget, summarize_interval)


def test_tail_pvalue_definition_and_midrank():
    ref = np.array([1.0, 2.0, 2.0, 3.0])
    p = tail_pvalues(ref, np.array([0.0, 2.0, 5.0]))
    assert p[0] == pytest.approx(5 / 5)          # all four reference scores are >= 0
    assert p[1] == pytest.approx((1 + 1 + 0.5 * 2) / 5)
    assert p[2] == pytest.approx(1 / 5)


def test_tail_pvalues_are_super_uniform_under_exchangeability():
    rng = np.random.default_rng(0)
    hits = []
    for _ in range(400):
        ref = rng.normal(size=199)
        hits.append(tail_pvalues(ref, rng.normal(size=1))[0] <= 0.05)
    assert np.mean(hits) <= 0.05 + 0.03


def test_transductive_matches_leave_one_out_loop():
    scores = np.array([0.3, 0.1, 0.3, 0.9, 0.5])
    loop = [tail_pvalues(np.delete(scores, i), scores[i:i + 1])[0] for i in range(scores.size)]
    assert np.allclose(transductive_pvalues(scores), loop)


def test_split_reference_is_disjoint_and_deterministic():
    a, b = split_reference(11, 42)
    assert not set(a) & set(b) and len(a) + len(b) == 11
    assert np.array_equal(a, split_reference(11, 42)[0])


def test_vovk_wang_merge_is_valid_under_strong_dependence():
    rng = np.random.default_rng(1)
    from scipy.stats import norm

    z = rng.normal(size=20000)
    p1 = norm.sf(z)
    p2 = norm.sf(0.95 * z + np.sqrt(1 - 0.95 ** 2) * rng.normal(size=z.size))
    merged = rules.vovk_wang_pvalue(p1, p2)
    assert np.mean(merged <= 0.05) <= 0.05


def test_rules_are_monotone_in_each_expert():
    for rule in (rules.vovk_wang_score, rules.bonferroni_min_score, rules.cauchy_score):
        assert rule(np.array([0.1]), np.array([0.5]))[0] >= rule(np.array([0.5]), np.array([0.5]))[0]
        assert rule(np.array([0.5]), np.array([0.1]))[0] >= rule(np.array([0.5]), np.array([0.5]))[0]
    rho = 0.6
    one_sided = rules.copula_onesided_score(np.array([0.9, 0.9]), np.array([0.9, 0.01]), rho)
    assert one_sided[0] == 0.0 and one_sided[1] > 0.0


def test_copula_rejects_degenerate_reference():
    with pytest.raises(ValueError):
        rules.fit_copula(np.full(10, 0.5), np.full(10, 0.5))


def brute_auroc(y, s):
    pos, neg = s[y], s[~y]
    return np.mean([(a > b) + 0.5 * (a == b) for a, b in product(pos, neg)])


def test_auroc_and_average_precision_against_brute_force():
    y = np.array([1, 0, 1, 0, 0, 1, 0], dtype=bool)
    s = np.array([0.9, 0.8, 0.8, 0.3, 0.2, 0.7, 0.1])
    assert auroc(y, s) == pytest.approx(brute_auroc(y, s))
    # thresholds 0.9 (1/1), 0.8 (2/3), 0.7 (3/4): AP = 1/3*1 + 1/3*2/3 + 1/3*3/4
    assert average_precision(y, s) == pytest.approx((1 + 2 / 3 + 3 / 4) / 3)


def test_metrics_reject_single_class_and_nonfinite():
    with pytest.raises(ValueError):
        auroc(np.zeros(3, bool), np.arange(3.0))
    with pytest.raises(ValueError):
        average_precision(np.array([1, 0], bool), np.array([np.nan, 1.0]))


def test_recall_at_budget_counts():
    y = np.array([1, 0, 0, 0, 1, 0, 0, 0, 0, 0], dtype=bool)
    s = np.arange(10.0)[::-1]
    out = recall_at_budget(y, s, 0.2)
    assert out["flagged"] == 2 and out["recall"] == 0.5 and out["precision"] == 0.5


def test_delong_identical_scores_zero_difference():
    rng = np.random.default_rng(3)
    y = rng.random(200) < 0.2
    s = rng.normal(size=200) + y
    out = delong_paired(y, s, s)
    assert out["delta_auroc"] == pytest.approx(0.0)


def test_cluster_bootstrap_resamples_whole_clusters():
    y = np.array([0, 1, 0, 1, 0, 0], dtype=bool)
    clusters = np.array(["a", "a", "b", "b", "c", "c"])
    reps = cluster_bootstrap(y, {"s": np.arange(6.0)}, clusters,
                             lambda yy, ss: float(yy.size), reps=50, seed=0)
    assert set(np.unique(reps)) <= {6.0}
    summary = summarize_interval(reps - 6.0, 0.0)
    assert summary["replicates"] == 50


def test_logistic_recovers_signal_and_crossfit_is_out_of_fold():
    rng = np.random.default_rng(4)
    x = rng.normal(size=(600, 2))
    y = (x @ np.array([2.0, 0.0]) + rng.normal(size=600)) > 1.5
    w = fit_logistic(x, y, l2=0.1)
    assert w[1] > 1.0 and abs(w[2]) < 0.5
    folds = np.r_[np.zeros(300), np.ones(300)]
    scores, weights = crossfit_scores(x, y, folds)
    assert len(weights) == 2 and np.isfinite(scores).all()
    assert auroc(y, scores) > 0.8


@pytest.mark.parametrize("regime", ["OR", "AND"])
def test_cauchy_gains_in_both_complementarity_regimes(regime):
    from seqlogad.fusion.evaluate import evaluate_source
    rng = np.random.default_rng(5)
    n = 1200
    y = rng.random(n) < 0.06
    kind = rng.random(n) < 0.5 if regime == "OR" else np.ones(n, bool)
    other = ~kind if regime == "OR" else np.ones(n, bool)
    shared = rng.normal(size=n)
    table = {"anomaly": y, "time_chunk": np.repeat(np.arange(40), n // 40).astype(str),
             "crossfit_fold": (np.arange(n) >= n // 2).astype(int), "unit_id": list(range(n))}
    table["sem"] = 0.3 * shared + rng.normal(size=n) + 2.5 * (y & kind)
    table["seq"] = 0.3 * shared + rng.normal(size=n) + 2.5 * (y & other)
    for name in ("sem_base", "seq_base", "seq_latest", "b0_frequency"):
        table[name] = rng.normal(size=n)
    names = {"semantic": "sem", "sequence": "seq", "semantic_base": "sem_base",
             "sequence_base": "seq_base", "sequence_latest": "seq_latest"}
    out = evaluate_source(table, names, [0.05], {"reps": 200, "seed": 0})
    gains = {k: v["fusion_gain_ap"]["point"] for k, v in out["fusion_gain"].items()}
    assert gains["cauchy"] > 0.02
    if regime == "OR":
        assert gains["vovk_wang_mean"] < 0            # averaging dilutes one-expert anomalies
        caught = out["complementarity"]["positives_caught_at_budget"]
        assert caught["semantic_only"] > 0 and caught["sequence_only"] > 0
    else:
        assert gains["vovk_wang_mean"] > 0.02


def test_crossfit_pooling_is_robust_to_fold_specific_intercepts():
    """Regression for D-15: folds with very different base rates must still pool."""
    rng = np.random.default_rng(7)
    x = rng.normal(size=(1000, 2))
    folds = np.r_[np.zeros(500), np.ones(500)]
    shift = np.where(folds == 0, 2.5, 0.0)                 # fold 0 has far more anomalies
    y = (x @ np.array([1.5, 0.5]) + shift + rng.normal(size=1000)) > 3.0
    scores, _ = crossfit_scores(x, y, folds)
    within = [auroc(y[folds == g], scores[folds == g]) for g in (0, 1)]
    assert auroc(y, scores) > min(within) - 0.1          # pooled ranking no longer collapses


def test_multimask_aggregate_mean_max_and_abstention():
    from seqlogad.fusion.run_multimask import aggregate, check_consistency
    per_seed = {42: {"a": {"status": "VALID", "nll_mean": 1.0}, "b": {"status": "ABSTAIN"}},
                43: {"a": {"status": "VALID", "nll_mean": 3.0}, "b": {"status": "ABSTAIN"}}}
    out = aggregate(per_seed)
    mean = {r["window_id"]: r for r in out["mkmean"]}
    assert mean["a"]["nll_mean"] == 2.0 and mean["b"]["status"] == "ABSTAIN"
    assert {r["window_id"]: r for r in out["mkmax"]}["a"]["nll_mean"] == 3.0
    assert check_consistency(per_seed[42], {"a": 1.0005}) == pytest.approx(5e-4)
