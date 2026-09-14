"""Single-GPU semantic QLoRA execution. Importing this module never loads weights."""
import json
import math
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from .config import identity, load_config, final_run_id
from .contracts import dump, validate_bundle
from .objective import select_records, encode_message, collate
from .model import load_model, assert_isolated, precision
from .checkpoint import save_checkpoint, verify_checkpoint, seal, verify_seal
from .runtime import seed_all, export_environment
from seqlogad.common.checksum import sha256_file


RUN_ID_PATTERN = re.compile(r'[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*')


def validate_run_id(run_id):
    """Accept one conservative path component, including frozen `P2.1` IDs."""
    if not isinstance(run_id, str) or RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise ValueError('unsafe run_id')
    return run_id


def encoded_records(records, tokenizer, cfg):
    encoded, rejected = [], []
    for row in records:
        try:
            example = encode_message(tokenizer, row['normalized_message'], cfg)
            example['architecture_id'] = row['architecture_id']
            encoded.append(example)
        except ValueError as exc:
            rejected.append({'architecture_id': row['architecture_id'], 'rank': row['rank'], 'reason': str(exc)})
    if not encoded:
        raise ValueError('all records abstained')
    return encoded, rejected


def evaluate(model, tokenizer, examples, dtype):
    import torch
    model.eval()
    scores = []
    with torch.no_grad():
        for example in examples:
            batch = {k: v.to(model.device) for k, v in collate([example], tokenizer.pad_token_id).items()}
            with torch.autocast('cuda', dtype=dtype):
                loss = model(**batch).loss
            value = float(loss)
            if not math.isfinite(value):
                raise ValueError('nonfinite source validation loss')
            scores.append(value)
    model.train()
    return sum(scores) / len(scores)


def evaluate_by_source(model, tokenizer, examples, dtype):
    sources = sorted({row.get('architecture_id', 'UNKNOWN') for row in examples})
    per_source = {source: evaluate(model, tokenizer,
        [row for row in examples if row.get('architecture_id', 'UNKNOWN') == source], dtype) for source in sources}
    return {'aggregate_nll': evaluate(model, tokenizer, examples, dtype),
            'per_source_nll': per_source, 'aggregation': 'MEAN_OVER_ACCEPTED_MESSAGES'}


def preflight(model, tokenizer, examples, dtype):
    """Actual finite forward/backward check, no optimizer update."""
    import torch
    example = max(examples, key=lambda row: len(row['input_ids']))
    model.train(); model.zero_grad(set_to_none=True)
    batch = {k: v.to(model.device) for k, v in collate([example], tokenizer.pad_token_id).items()}
    with torch.autocast('cuda', dtype=dtype):
        loss = model(**batch).loss
    if not torch.isfinite(loss):
        raise ValueError('preflight loss nonfinite; choose native BF16 hardware')
    loss.backward()
    if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in model.parameters()):
        raise ValueError('preflight gradients nonfinite; choose native BF16 hardware')
    model.zero_grad(set_to_none=True)
    return {'loss': float(loss), 'tokens': len(example['input_ids']), 'finite': True}


def run_engineering_evaluation(repo_root, data_root, fold_id, run_directory,
                               checkpoint_name='step-300', expected_bundle_sha256=None):
    """GPU-only, label-free base versus selected-adapter evidence."""
    import torch
    run = Path(run_directory)
    manifest = json.loads((run / 'manifest.json').read_text())
    cfg = json.loads((run / 'config.yaml').read_text())
    defaults, base = load_config(repo_root, run_mode='pilot')
    for key in ['model_id', 'model_revision', 'tokenizer_id', 'tokenizer_revision']:
        if cfg[key] != defaults[key]:
            raise ValueError('pilot differs from frozen base identity')
    validation = validate_bundle(data_root, fold_id, expected_bundle_sha256)
    selected = select_records(data_root, fold_id, 'val', cfg['validation_records_per_source'], cfg['seed'])
    checkpoint = run / 'checkpoints' / checkpoint_name
    verify_checkpoint(checkpoint, manifest['identity'])
    model, tokenizer, dtype = load_model(cfg, base, base_only=True)
    examples, rejected = encoded_records(selected, tokenizer, cfg)
    base_metrics = evaluate_by_source(model, tokenizer, examples, dtype)
    del model
    torch.cuda.empty_cache()
    model, tokenizer, dtype = load_model(cfg, base, checkpoint / 'adapter')
    adapter_metrics = evaluate_by_source(model, tokenizer, examples, dtype)
    from .scoring import score_message
    from .diagnostics import run_probes
    checkpoint_hash = sha256_file(checkpoint / 'adapter/adapter_model.safetensors')
    metadata = {'fold_id': fold_id, 'architecture_id': 'SYNTHETIC', 'unit_id': 'probe',
        'record_ids': [], 'checkpoint_sha256': checkpoint_hash,
        'input_manifest_sha256': validation['bundle_sha256'], 'context_config_sha256': identity(cfg)}
    probes = run_probes(lambda text: score_message(model, tokenizer, cfg, text, metadata))
    result = {'scope': 'ENGINEERING_LABEL_FREE_NOT_ANOMALY_PERFORMANCE',
        'fold_id': fold_id, 'checkpoint': checkpoint_name, 'checkpoint_sha256': checkpoint_hash,
        'validation_records_per_source': cfg['validation_records_per_source'],
        'rejected': rejected, 'step0_frozen_base': base_metrics,
        'selected_adapter': adapter_metrics, 'probes': probes}
    dump(run / f'engineering-evaluation-{checkpoint_name}.json', result)
    seal(run)
    return result


def run_training(repo_root, data_root, output_root, fold_id, run_id, overrides=None,
                 resume_from=None, expected_bundle_sha256=None, run_mode='pilot'):
    import torch
    cfg, base = load_config(repo_root, overrides, run_mode=run_mode)
    validation = validate_bundle(data_root, fold_id, expected_bundle_sha256)
    if not expected_bundle_sha256:
        raise ValueError('set trusted EXPECTED_BUNDLE_SHA256 from local preparation report')
    validate_run_id(run_id)
    if run_mode == 'final':
        if fold_id not in cfg['final_target_folds']:
            raise ValueError('fold is not in frozen final matrix')
        if run_id != final_run_id(fold_id, cfg['seed']):
            raise ValueError('final run_id does not match frozen fold/seed matrix')
    run = Path(output_root) / fold_id / cfg['expert_id'] / run_id
    run.mkdir(parents=True, exist_ok=False)  # Resume creates a new run with explicit parent.
    (run / 'logs').mkdir()
    (run / 'checkpoints').mkdir()
    run_identity = {'config_sha256': identity(cfg), 'bundle_sha256': validation['bundle_sha256'], 'fold_id': fold_id, 'precision': str(precision(torch))}
    resume = verify_checkpoint(resume_from, run_identity) if resume_from else None
    dump(run / 'config.yaml', cfg)  # JSON is a valid YAML subset.
    export_environment(run)
    selected = {p: select_records(data_root, fold_id, p, cfg['train_records_per_source'] if p == 'train'
                else cfg['validation_records_per_source'], cfg['seed']) for p in ('train', 'val')}
    dump(run / 'selection.json', {p: [{'architecture_id': r['architecture_id'], 'rank': r['rank']} for r in rows]
                                for p, rows in selected.items()})
    seed_all(cfg['seed'])
    torch.cuda.reset_peak_memory_stats(); start = time.monotonic()
    model, tokenizer, dtype = load_model(cfg, base, Path(resume_from) / 'adapter' if resume_from else None)
    train, rejected_train = encoded_records(selected['train'], tokenizer, cfg)
    val, rejected_val = encoded_records(selected['val'], tokenizer, cfg)
    dump(run / 'coverage.json', {'train_rejected': rejected_train, 'val_rejected': rejected_val,
        'train_mean_coverage': sum(r['coverage'] for r in train) / len(train),
        'val_mean_coverage': sum(r['coverage'] for r in val) / len(val)})
    dump(run / 'preflight.json', preflight(model, tokenizer, train, dtype))
    # Reset RNG after preflight; resumption then restores exact training RNG state.
    seed_all(cfg['seed'])
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=cfg['learning_rate'], weight_decay=cfg['weight_decay'])
    scaler = torch.amp.GradScaler('cuda', enabled=(dtype == torch.float16),
        init_scale=cfg['fp16_initial_scale'], growth_interval=cfg['fp16_growth_interval'])
    first, best = 0, {'loss': None, 'checkpoint': None}
    early_state = {'stale_evaluations': 0, 'monitor_best': None, 'validation_history': []}
    if resume:
        state = torch.load(Path(resume_from) / 'state.pt', map_location='cpu', weights_only=True)
        optimizer.load_state_dict(state['optimizer']); scaler.load_state_dict(state['scaler'])
        torch.set_rng_state(state['torch_rng']); torch.cuda.set_rng_state_all(state['cuda_rng'])
        random.setstate(state['python_rng']); first = state['step']; best = state['best']
        early_state = state.get('early_stopping', early_state)
        if run_mode == 'final' and not {'stale_evaluations', 'monitor_best', 'validation_history'} <= set(early_state):
            raise ValueError('final resume checkpoint lacks complete early-stopping state')
        scheduler_state = state.get('scheduler', {})
        if run_mode == 'final' and scheduler_state.get('last_completed_step') != first:
            raise ValueError('final resume checkpoint lacks matching scheduler state')
        if first >= cfg['max_steps']:
            raise ValueError('checkpoint already completed configured budget')
        # Portable best state: always retain prior best adapter with resumed output.
        import shutil
        previous_best = Path(resume_from).parent / best['checkpoint'] if best['checkpoint'] else Path(resume_from)
        if not previous_best.exists():
            raise ValueError('resume requires prior best checkpoint directory')
        shutil.copytree(previous_best, run / 'checkpoints/resume-best')
        best['checkpoint'] = 'resume-best'
    try:
        best, metrics = optimize(model, tokenizer, dtype, train, val, cfg, optimizer, scaler,
                                 run, run_identity, first, best, early_state)
        selected_checkpoint = run / 'checkpoints' / best['checkpoint']
        from safetensors.torch import load_file
        from peft import set_peft_model_state_dict
        set_peft_model_state_dict(model,
            load_file(str(selected_checkpoint / 'adapter/adapter_model.safetensors')),
            adapter_name='semantic')
        from .scoring import score_message
        # All post-training diagnostics use the deterministically selected checkpoint.
        final = selected_checkpoint
        sample = selected['val'][0]
        evidence = score_message(model, tokenizer, cfg, sample['normalized_message'],
            {'fold_id': fold_id, 'architecture_id': sample['architecture_id'], 'unit_id': str(sample['rank']),
             'record_ids': [f"{sample['architecture_id']}:{sample['rank']}"],
             'checkpoint_sha256': sha256_file(final / 'adapter/adapter_model.safetensors'),
             'input_manifest_sha256': validation['bundle_sha256'], 'context_config_sha256': identity(cfg)})
        dump(run / 'sanity-evidence.json', evidence)
        from .diagnostics import run_probes
        probe_metadata = {k: v for k, v in evidence.items() if k in
            ['fold_id', 'checkpoint_sha256', 'input_manifest_sha256', 'context_config_sha256']}
        probe_metadata.update(architecture_id='SYNTHETIC', unit_id='probe', record_ids=[])
        dump(run / 'semantic-probes.json', run_probes(lambda text: score_message(
            model, tokenizer, cfg, text, probe_metadata)))
        torch.cuda.synchronize()
        metrics.update(runtime_seconds=time.monotonic() - start, best=best,
            peak_vram_allocated=torch.cuda.max_memory_allocated(), peak_vram_reserved=torch.cuda.max_memory_reserved())
        dump(run / 'metrics.json', metrics)
        from .prepare import git_state
        manifest = dict(run_id=run_id, fold_id=fold_id, expert_id=cfg['expert_id'], identity=run_identity,
            base_model_id=cfg['model_id'], base_model_revision=cfg['model_revision'], tokenizer_id=cfg['tokenizer_id'],
            tokenizer_revision=cfg['tokenizer_revision'], seed=cfg['seed'], training_mode=cfg['training_mode'],
            precision=str(dtype), adapter_config=cfg, resume_parent=str(resume_from) if resume_from else None,
            data_manifest_sha256=validation['bundle_sha256'], data_manifest_path='manifests/bundle.json',
            git=git_state(repo_root), timestamp_utc=datetime.now(timezone.utc).isoformat(),
            completion_status='TRAINING_COMPLETED_REQUIRES_REVIEW', scientific_results='NOT_EVALUATED',
            environment='environment.json', metrics='metrics.json', dependency_lock='dependency-lock.txt',
            checkpoint=str(final.relative_to(run)), best_checkpoint=best['checkpoint'],
            checkpoint_sha256=sha256_file(final / 'adapter/adapter_model.safetensors'),
            metadata_file_sha256={key: base['revision_policy'][key] for key in
                                 ['model_config_sha256', 'tokenizer_config_sha256']})
        dump(run / 'manifest.json', manifest)
        seal(run)
        verify_seal(run, require_nested_ledgers=(run_mode == 'final'))
        return {'run_directory': str(run), 'metrics': metrics}
    except Exception as exc:
        dump(run / 'failure.json', {'type': type(exc).__name__, 'message': str(exc), 'training_completed': False})
        raise


def optimize(model, tokenizer, dtype, train, val, cfg, optimizer, scaler, run, run_identity, first, best,
             early_state=None):
    import torch
    model.train()
    early_state = dict(early_state or {})
    stale_evaluations = early_state.get('stale_evaluations', 0)
    monitor_best = early_state.get('monitor_best')
    validation_history = list(early_state.get('validation_history', []))
    train_by_source = {source: [row for row in train if row.get('architecture_id', 'UNKNOWN') == source]
                       for source in sorted({row.get('architecture_id', 'UNKNOWN') for row in train})}
    source_ids = sorted(train_by_source)
    for step in range(first, cfg['max_steps']):
        optimizer.zero_grad(set_to_none=True); losses = []
        warmup = max(1, cfg['warmup_steps'])
        factor = (step + 1) / warmup if step < cfg['warmup_steps'] else (cfg['max_steps'] - step) / max(1, cfg['max_steps'] - cfg['warmup_steps'])
        for group in optimizer.param_groups:
            group['lr'] = cfg['learning_rate'] * min(1.0, factor)
        for _ in range(cfg['gradient_accumulation_steps']):
            source = source_ids[random.randrange(len(source_ids))]
            pool = train_by_source[source]
            example = pool[random.randrange(len(pool))]  # Balanced independent messages; no event-order context.
            batch = {k: v.to(model.device) for k, v in collate([example], tokenizer.pad_token_id).items()}
            with torch.autocast('cuda', dtype=dtype):
                loss = model(**batch).loss
            if not torch.isfinite(loss):
                dump(run / 'numerical-failure.json', {'step_attempt': step + 1,
                    'completed_steps': step, 'phase': 'forward', 'precision': str(dtype),
                    'loss_scale': scaler.get_scale()})
                raise ValueError('nonfinite training loss; see numerical-failure.json')
            losses.append(float(loss.detach()))
            scaler.scale(loss / cfg['gradient_accumulation_steps']).backward()
        scaler.unscale_(optimizer)
        norm = torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], cfg['max_grad_norm'])
        if not torch.isfinite(norm):
            dump(run / 'numerical-failure.json', {'step_attempt': step + 1,
                'completed_steps': step, 'phase': 'backward', 'precision': str(dtype),
                'loss_scale': scaler.get_scale(), 'optimizer_update_applied': False})
            raise ValueError('nonfinite gradients; no update applied; see numerical-failure.json. '
                             'FP16 may be unstable: use native BF16 hardware; do not bypass guard.')
        scaler.step(optimizer); scaler.update(); assert_isolated(model)
        metrics = {'step': step + 1, 'train_reconstruction_nll': sum(losses) / len(losses),
                   'loss_scale': scaler.get_scale(), 'gradient_norm': float(norm),
                   'optimizer_update_applied': True}
        should_stop = False
        validation_steps = cfg.get('validation_steps', cfg['save_steps'])
        if (step + 1) % validation_steps == 0 or step + 1 == cfg['max_steps']:
            validation = evaluate_by_source(model, tokenizer, val, dtype)
            loss_val = validation['aggregate_nll']
            metrics['source_validation_reconstruction_nll'] = loss_val
            metrics['per_source_validation_reconstruction_nll'] = validation['per_source_nll']
            checkpoint = run / 'checkpoints' / f'step-{step + 1}'
            minimum_delta = cfg.get('early_stopping_min_delta', 0.0)
            selection_improved = best['loss'] is None or loss_val < best['loss']
            if selection_improved:  # strict comparison preserves earliest-step tie break
                best = {'loss': loss_val, 'checkpoint': checkpoint.name}
            monitor_improved = monitor_best is None or loss_val < monitor_best - minimum_delta
            if monitor_improved:
                monitor_best = loss_val
                stale_evaluations = 0
            else:
                stale_evaluations += 1
            validation_history.append({'step': step + 1, 'aggregate_nll': loss_val,
                'per_source_nll': validation['per_source_nll'],
                'selection_improved': selection_improved, 'patience_improved': monitor_improved})
            patience = cfg.get('early_stopping_patience')
            should_stop = patience is not None and stale_evaluations >= patience
            metrics['early_stopping'] = {'stale_evaluations': stale_evaluations,
                'patience': patience, 'minimum_delta': minimum_delta,
                'triggered': should_stop}
            current_early_state = {'stale_evaluations': stale_evaluations,
                'monitor_best': monitor_best, 'validation_history': validation_history}
            scheduler_state = {'kind': 'LINEAR_WARMUP_THEN_LINEAR_DECAY',
                'last_completed_step': step + 1, 'learning_rate_factor': min(1.0, factor)}
            save_checkpoint(model, optimizer, scaler, checkpoint, step + 1, run_identity, best,
                            current_early_state, scheduler_state)
        with (run / 'logs/train.jsonl').open('a') as handle:
            handle.write(json.dumps(metrics) + '\n')
        print(json.dumps(metrics), flush=True)
        if should_stop:
            break
    return best, metrics
