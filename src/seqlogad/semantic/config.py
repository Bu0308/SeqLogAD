"""Resolved P2.1 configuration: immutable infrastructure, explicit run conditions."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import yaml

MODEL = 'meta-llama/Llama-3.1-8B'
REVISION = 'd04e592bb4f6aa9cfee91e2e20afa771667e1d4b'


def final_run_id(fold_id, seed):
    target = fold_id.removeprefix('FOLD-TARGET-ARCH-')
    if target not in {'HDFS', 'BGL', 'HADOOP'}:
        raise ValueError('fold is not in frozen final matrix')
    return f'P2.1-FINAL-{target}-S{seed}'


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def load_config(repo_root, overrides=None, run_mode='pilot'):
    root = Path(repo_root)
    cfg = yaml.safe_load((root / 'configs/models/semantic-v1.yaml').read_text())['semantic']
    base = yaml.safe_load((root / cfg['base_contract']).read_text())['base_freeze']
    if base['status'] != 'PASS' or not base['model']['base_weights_immutable'] or not base['peft']['adapter_isolation']:
        raise ValueError('base freeze not ready')
    fields = base['required_metadata']
    if any(fields[k] != v for k, v in [('base_model_identifier', MODEL), ('tokenizer_identifier', MODEL),
          ('model_revision_commit', REVISION), ('tokenizer_revision_commit', REVISION)]):
        raise ValueError('frozen base identity changed')
    cfg = deepcopy(cfg)
    final_protocol = cfg.pop('final_protocol')
    if run_mode not in {'pilot', 'final'}:
        raise ValueError('run_mode must be pilot or final')
    if run_mode == 'final':
        if final_protocol.get('status') != 'FROZEN':
            raise ValueError('final protocol is not frozen')
        for key in ['train_records_per_source', 'validation_records_per_source', 'max_steps',
                    'gradient_accumulation_steps', 'learning_rate', 'warmup_steps',
                    'context_length', 'validation_steps', 'save_steps',
                    'early_stopping_patience', 'early_stopping_min_delta']:
            cfg[key] = final_protocol[key]
        cfg.update(final_protocol['lora'])
        cfg['checkpoint_selection'] = final_protocol['checkpoint_selection']
        cfg['final_target_folds'] = final_protocol['target_folds']
        cfg['final_seeds'] = final_protocol['seeds']
        cfg['source_balancing'] = final_protocol['source_balancing']
        cfg['tie_breaking'] = final_protocol['tie_breaking']
    cfg['run_mode'] = run_mode
    if cfg.get('fp16_initial_scale') != 1.0 or cfg.get('fp16_growth_interval') != 2000:
        raise ValueError('unexpected pilot numerical policy')
    if cfg.get('numerical_failure_policy') != 'ABORT_NO_SKIPPED_UPDATES':
        raise ValueError('numerical guard must remain enabled')
    allowed = {'seed', 'training_mode', 'context_length', 'rank', 'alpha', 'dropout', 'learning_rate',
               'gradient_accumulation_steps', 'max_steps', 'warmup_steps', 'save_steps', 'validation_steps',
               'train_records_per_source', 'validation_records_per_source'}
    if set(overrides or {}) - allowed:
        raise ValueError('unsupported/immutable override')
    if run_mode == 'final' and set(overrides or {}) - {'seed', 'training_mode'}:
        raise ValueError('final mode accepts only preregistered seed and training mode')
    cfg.update(overrides or {})
    modes = [base['quantization']['default_training_mode'], base['quantization']['low_memory_mode']]
    if cfg['training_mode'] not in modes:
        raise ValueError('unfrozen training mode')
    limit = 1024 if cfg['training_mode'] == modes[1] else 2048
    if not 64 <= cfg['context_length'] <= limit or not 0 <= cfg['dropout'] < 1:
        raise ValueError('invalid context/dropout')
    for key in ['rank', 'alpha', 'max_steps', 'save_steps', 'validation_steps', 'gradient_accumulation_steps',
                'train_records_per_source', 'validation_records_per_source']:
        if not isinstance(cfg[key], int) or cfg[key] <= 0:
            raise ValueError(f'invalid {key}')
    if not 0 < cfg['learning_rate'] <= 0.001 or not 0 <= cfg['warmup_steps'] <= cfg['max_steps']:
        raise ValueError('invalid optimizer schedule')
    if cfg['run_mode'] == 'final' and cfg['seed'] not in final_protocol['seeds']:
        raise ValueError('final seed is not preregistered')
    if cfg['run_mode'] == 'final' and cfg['save_steps'] != cfg['validation_steps']:
        raise ValueError('final checkpoint and validation intervals must coincide')
    cfg.update(model_id=MODEL, model_revision=REVISION, tokenizer_id=MODEL, tokenizer_revision=REVISION,
               base_config_sha256=hashlib.sha256((root / 'configs/models/base-freeze-v1.yaml').read_bytes()).hexdigest())
    return cfg, base
