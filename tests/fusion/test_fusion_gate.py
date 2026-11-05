import numpy as np

from seqlogad.fusion import gate
from seqlogad.fusion.scorer import expand_scores, unique_examples


def test_top_membership_shares_boundary_ties():
    w = gate.top_membership(np.array([5.0, 4.0, 4.0, 4.0, 1.0]), 2)
    assert np.allclose(w, [1, 1 / 3, 1 / 3, 1 / 3, 0])
    assert np.isclose(w.sum(), 2)


def test_gate_opens_for_concordant_tails_and_closes_for_noise():
    rng = np.random.default_rng(0)
    signal = rng.normal(size=4000)
    concordant = gate.tail_lift(signal + rng.normal(scale=0.5, size=4000), signal, permutations=500)
    noise = gate.tail_lift(signal, rng.normal(size=4000), permutations=500)
    assert gate.is_open(concordant) and concordant["lift"] > 3
    assert not gate.is_open(noise) and 0.5 < noise["lift"] < 1.5


def test_constant_secondary_cannot_open_the_gate():
    stat = gate.tail_lift(np.arange(1000.0), np.zeros(1000), permutations=200)
    assert np.isclose(stat["lift"], 1.0) and not gate.is_open(stat)


def test_closed_gate_falls_back_to_primary_ranking():
    p_primary, p_secondary = np.array([0.1, 0.5, 0.9]), np.array([0.9, 0.1, 0.5])
    closed = gate.gated_score(p_primary, p_secondary, False)
    assert list(np.argsort(-closed)) == [0, 1, 2]
    opened = gate.gated_score(p_primary, p_secondary, True)
    assert np.allclose(opened, -np.log(0.5 * (p_primary + p_secondary)))


def test_dedupe_scores_each_encoding_once_and_expands_to_every_window():
    examples = [
        {"window_id": "w1", "status": "VALID", "input_ids": [1, 2], "labels": [-100, 2]},
        {"window_id": "w2", "status": "VALID", "input_ids": [1, 2], "labels": [-100, 2]},
        {"window_id": "w3", "status": "VALID", "input_ids": [1, 3], "labels": [-100, 3]},
        {"window_id": "w4", "status": "ABSTAIN", "reason": "empty"},
        {"window_id": "w5", "status": "ABSTAIN", "reason": "empty"},
    ]
    reps, groups = unique_examples(examples)
    assert [e["window_id"] for e in reps] == ["w1", "w3", "w4", "w5"]
    scored = [{"window_id": e["window_id"], "nll_mean": float(i)} for i, e in enumerate(reps)]
    expanded = {r["window_id"]: r["nll_mean"] for r in expand_scores(scored, groups)}
    assert expanded == {"w1": 0.0, "w2": 0.0, "w3": 1.0, "w4": 2.0, "w5": 3.0}
