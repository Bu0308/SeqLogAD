"""Control-flow regression: invalid gradients must never update/checkpoint."""
import json
import sys
from contextlib import nullcontext
from types import SimpleNamespace as NS
import math
import pytest
from seqlogad.semantic import train as module


@pytest.mark.parametrize('norm, succeeds', [(float('inf'), False), (float('nan'), False), (0.5, True)])
def test_optimizer_counts_only_finite_updates(tmp_path, monkeypatch, norm, succeeds):
    calls = []
    class Loss(float):
        def detach(self): return self
    class Scaler:
        def scale(self, value): return NS(backward=lambda: None)
        def unscale_(self, optimizer): calls.append('unscale')
        def get_scale(self): return 1.0
        def step(self, optimizer): calls.append('update')
        def update(self): calls.append('scale_update')
    class Model:
        device = 'fake'
        def train(self): pass
        def parameters(self): return [NS(requires_grad=True)]
        def __call__(self, **kw): return NS(loss=Loss(0.7))
    torch = NS(autocast=lambda *a, **kw: nullcontext(), isfinite=math.isfinite,
               nn=NS(utils=NS(clip_grad_norm_=lambda *a: norm)))
    monkeypatch.setitem(sys.modules, 'torch', torch)
    monkeypatch.setattr(module, 'collate', lambda *a: {})
    monkeypatch.setattr(module, 'assert_isolated', lambda m: None)
    monkeypatch.setattr(module, 'evaluate', lambda *a: 0.5)
    monkeypatch.setattr(module, 'save_checkpoint', lambda *a: calls.append('checkpoint'))
    (tmp_path / 'logs').mkdir()
    cfg = dict(max_steps=1, warmup_steps=0, learning_rate=1e-4,
               gradient_accumulation_steps=2, max_grad_norm=1.0, save_steps=1)
    args = (Model(), NS(pad_token_id=0), 'fp16', [{}], [{}], cfg,
            NS(zero_grad=lambda **kw: None, param_groups=[{}]), Scaler(), tmp_path, {},
            0, {'loss': None, 'checkpoint': None})
    if succeeds:
        _, metrics = module.optimize(*args)
        assert metrics['step'] == 1 and metrics['optimizer_update_applied']
        assert calls.count('update') == calls.count('checkpoint') == 1
    else:
        with pytest.raises(ValueError, match='nonfinite gradients'):
            module.optimize(*args)
        assert 'update' not in calls and 'checkpoint' not in calls
        report = json.loads((tmp_path / 'numerical-failure.json').read_text())
        assert report['completed_steps'] == 0 and report['loss_scale'] == 1
        assert report['optimizer_update_applied'] is False


def test_resume_preserves_patience_history_and_scheduler_checkpoint(tmp_path, monkeypatch):
    saved = {}
    class Loss(float):
        def detach(self): return self
    class Scaler:
        def scale(self, value): return NS(backward=lambda: None)
        def unscale_(self, optimizer): pass
        def get_scale(self): return 1.0
        def step(self, optimizer): pass
        def update(self): pass
    class Model:
        device = 'fake'
        def train(self): pass
        def parameters(self): return [NS(requires_grad=True)]
        def __call__(self, **kw): return NS(loss=Loss(0.2))
    torch = NS(autocast=lambda *a, **kw: nullcontext(), isfinite=math.isfinite,
               nn=NS(utils=NS(clip_grad_norm_=lambda *a: 0.5)))
    monkeypatch.setitem(sys.modules, 'torch', torch)
    monkeypatch.setattr(module, 'collate', lambda *a: {})
    monkeypatch.setattr(module, 'assert_isolated', lambda m: None)
    monkeypatch.setattr(module, 'evaluate_by_source', lambda *a: {
        'aggregate_nll': 0.4895, 'per_source_nll': {'ARCH-HDFS': 0.4895}})
    def capture(*args):
        saved['early'] = args[-2]
        saved['scheduler'] = args[-1]
    monkeypatch.setattr(module, 'save_checkpoint', capture)
    (tmp_path / 'logs').mkdir()
    cfg = dict(max_steps=3, warmup_steps=1, learning_rate=1e-4,
               gradient_accumulation_steps=1, max_grad_norm=1.0, save_steps=1,
               validation_steps=1, early_stopping_patience=3, early_stopping_min_delta=0.001)
    initial = {'stale_evaluations': 2, 'monitor_best': 0.49,
               'validation_history': [{'step': 1}, {'step': 2}]}
    best, metrics = module.optimize(Model(), NS(pad_token_id=0), 'fp16',
        [{'architecture_id': 'ARCH-HDFS'}], [{'architecture_id': 'ARCH-HDFS'}], cfg,
        NS(zero_grad=lambda **kw: None, param_groups=[{}]), Scaler(), tmp_path, {},
        2, {'loss': 0.5, 'checkpoint': 'resume-best'}, initial)
    assert metrics['step'] == 3 and metrics['early_stopping']['triggered'] is True
    assert saved['early']['stale_evaluations'] == 3
    assert len(saved['early']['validation_history']) == 3
    assert saved['scheduler']['last_completed_step'] == 3
    assert best == {'loss': 0.4895, 'checkpoint': 'step-3'}  # selection uses raw minimum
