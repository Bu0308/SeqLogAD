"""Published-baseline re-implementations behave sensibly on a synthetic log stream."""
import numpy as np
import pytest

pytest.importorskip("sklearn")

from seqlogad.fusion.paper_baselines import (Vocab, count_matrix, iforest_scores, knn_tfidf_scores,  # noqa: E402
                                             pca_scores)
from seqlogad.fusion.metrics import auroc  # noqa: E402


def _stream(rng, n, anomaly_rate=0.0):
    normal = ["open file <NUM>", "read block <NUM>", "close file <NUM>", "ack <NUM>"]
    windows, labels = [], []
    for _ in range(n):
        context = [normal[i % 4] for i in range(rng.integers(1, 9))]
        bad = rng.random() < anomaly_rate
        target = "kernel panic unexpected fault" if bad else normal[len(context) % 4]
        windows.append((context, target))
        labels.append(bad)
    return windows, np.array(labels)


def test_baselines_rank_novel_events_above_normal():
    rng = np.random.default_rng(0)
    train, _ = _stream(rng, 400)
    test, y = _stream(rng, 300, anomaly_rate=0.1)
    vocab = Vocab([m for c, t in train for m in [*c, t]])
    a, b = count_matrix(train, vocab), count_matrix(test, vocab)
    assert auroc(y, pca_scores(a, b)) > 0.9
    # Isolation Forest cannot split on a feature that is constant (0) in training,
    # so a never-seen template is invisible to it; test it on count anomalies instead.
    burst = [(["ack <NUM>"] * 8, "ack <NUM>") if bad else w for w, bad in zip(test, y)]
    assert auroc(y, iforest_scores(a, count_matrix(burst, vocab))) > 0.7
    assert auroc(y, knn_tfidf_scores([t for _, t in train], [t for _, t in test])) > 0.9


def test_deeplog_runs_when_torch_available():
    pytest.importorskip("torch")
    from seqlogad.fusion.paper_baselines import deeplog_scores
    rng = np.random.default_rng(1)
    train, _ = _stream(rng, 300)
    test, y = _stream(rng, 200, anomaly_rate=0.1)
    vocab = Vocab([m for c, t in train for m in [*c, t]])
    assert auroc(y, deeplog_scores(train, test, vocab, epochs=3)) > 0.8
