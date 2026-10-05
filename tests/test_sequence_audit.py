"""Regressions from the independent V13 architecture/runtime audit."""
import json
import math
import sys
from contextlib import nullcontext
from types import SimpleNamespace as NS

import pytest

from seqlogad.sequence import optimization as module
from seqlogad.sequence.source_development_metrics import source_development_metrics


def test_missing_negative_score_cannot_improve_selected_development_f1():
    labels = {key: {"architecture_id": "ARCH-BGL", "unit_id": key,
                    "anomaly": key == "p"} for key in ("p", "n1", "n2")}
    scores = [{"window_id": key, "architecture_id": "ARCH-BGL", "nll": score}
              for key, score in [("p", 0.8), ("n1", 0.2)]]
    with pytest.raises(ValueError, match="coverage"):
        source_development_metrics(scores, labels)


@pytest.mark.parametrize("completed,stale", [(3, 0), (2, 3)])
def test_terminal_recovery_never_performs_another_optimizer_update(tmp_path, monkeypatch, completed, stale):
    monkeypatch.setitem(sys.modules, "torch", NS())
    (tmp_path / "logs").mkdir()
    metrics = {"step": completed, "source_development_macro_f1": 0.7,
               "early_stopping": {"triggered": stale == 3}}
    (tmp_path / "logs/train.jsonl").write_text(json.dumps(metrics) + "\n")
    cfg = {"max_steps": 3, "early_stopping_patience": 3}
    best = {"f1": 0.7, "checkpoint": "step-1"}
    state = {"stale_evaluations": stale, "monitor_best": 0.7, "validation_history": []}
    # A terminal checkpoint should finalize from persisted metrics without even
    # needing a forward or optimizer object.
    actual_best, actual_metrics = module.optimize(
        None, None, None, [], [], cfg, None, None, tmp_path, {}, completed,
        best, state, raw_train_windows={}, development_labels={"p": {}},
    )
    assert actual_best == best
    assert actual_metrics["step"] == completed


def test_checkpoint_callback_receives_current_step_metrics(tmp_path, monkeypatch):
    class Loss(float):
        def detach(self): return self
    class Model:
        device = "fake"
        def train(self): pass
        def parameters(self): return [NS(requires_grad=True)]
        def __call__(self, **kwargs): return NS(loss=Loss(0.2))
    scaler = NS(scale=lambda value: NS(backward=lambda: None), unscale_=lambda opt: None,
                get_scale=lambda: 1.0, step=lambda opt: None, update=lambda: None)
    torch = NS(autocast=lambda *a, **kw: nullcontext(), isfinite=math.isfinite,
               nn=NS(utils=NS(clip_grad_norm_=lambda *a: 0.5)))
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setattr(module, "collate", lambda *a: {})
    monkeypatch.setattr(module, "assert_isolated", lambda model: None)
    monkeypatch.setattr(module, "sample_training_view", lambda row, *a: (row, {
        "view": "full", "requested_context_records": 1}))
    monkeypatch.setattr(module, "save_checkpoint", lambda *a, **kw: None)
    monkeypatch.setattr(module, "evaluate_by_source", lambda *a: {
        "aggregate_nll": 0.2, "per_source_nll": {"ARCH-BGL": 0.2},
        "per_source_perplexity": {"ARCH-BGL": math.exp(0.2)}})
    (tmp_path / "logs").mkdir()
    row = {"architecture_id": "ARCH-BGL", "window_id": "w"}
    cfg = dict(max_steps=1, warmup_steps=1, learning_rate=1e-4,
               gradient_accumulation_steps=1, max_grad_norm=1.0,
               validation_steps=1, early_stopping_patience=3, early_stopping_min_delta=0)
    def callback(run, checkpoint, best):
        rows = [json.loads(line) for line in (run / "logs/train.jsonl").read_text().splitlines()]
        assert rows[-1]["step"] == 1
        assert rows[-1]["source_validation_next_log_nll"] == 0.2
    module.optimize(Model(), NS(pad_token_id=0), "bf16", [row], [row], cfg,
                    NS(zero_grad=lambda **kw: None, param_groups=[{}]), scaler,
                    tmp_path, {}, 0, {"loss": None, "checkpoint": None},
                    checkpoint_callback=callback, raw_train_windows={("ARCH-BGL", "w"): row})


def test_metric_auc_matches_pairwise_oracle_and_ap_threshold_oracle():
    import random
    from seqlogad.sequence.source_development_metrics import _binary_metrics
    rng = random.Random(42)
    for _ in range(100):
        items = [(rng.randrange(4), bool(rng.randrange(2))) for _ in range(20)]
        if len({label for _, label in items}) != 2:
            continue
        positives = [s for s, y in items if y]
        negatives = [s for s, y in items if not y]
        expected_auc = sum((a > b) + 0.5 * (a == b) for a in positives for b in negatives)
        expected_auc /= len(positives) * len(negatives)
        thresholds = sorted({s for s, _ in items}, reverse=True)
        previous_recall = expected_ap = 0
        for threshold in thresholds:
            predicted = [y for score, y in items if score >= threshold]
            recall = sum(predicted) / len(positives)
            expected_ap += (recall - previous_recall) * sum(predicted) / len(predicted)
            previous_recall = recall
        actual = _binary_metrics(items)
        assert actual['auroc'] == pytest.approx(expected_auc)
        assert actual['average_precision'] == pytest.approx(expected_ap)


def test_terminal_resume_requires_its_own_persisted_metric_row(tmp_path):
    from seqlogad.sequence.recovery_state import terminal_metrics
    (tmp_path / 'logs').mkdir()
    (tmp_path / 'logs/train.jsonl').write_text('{"step": 2}\n')
    with pytest.raises(ValueError, match='matching persisted metrics'):
        terminal_metrics(tmp_path, 3, {'max_steps': 3, 'early_stopping_patience': 3}, {})
