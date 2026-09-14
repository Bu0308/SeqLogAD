"""Deterministic denoising of one message, never a sequence of log events."""
import hashlib
import random
import re


def literal_text(text):
    # Escape only upstream control-token syntax; never extend tokenizer vocabulary.
    return text.replace('<|', '< |').replace('|>', '| >')


def corrupt(words, seed, fraction):
    rng = random.Random(int(hashlib.sha256((' '.join(words) + str(seed)).encode()).hexdigest(), 16))
    count = max(1, round(len(words) * fraction))
    masked = set(rng.sample(range(len(words)), min(count, len(words))))
    return ' '.join('[MASK]' if i in masked else w for i, w in enumerate(words))


def encode_message(tokenizer, text, cfg):
    words = literal_text(text).split()
    if not words:
        raise ValueError('empty semantic text: abstain')
    # Finite decreasing prefix search; no implicit tokenizer truncation/packing.
    keep = len(words)
    while keep:
        clean = ' '.join(words[:keep])
        prompt = 'Restore the log message:\n' + corrupt(words[:keep], cfg['seed'], cfg['mask_fraction']) + '\nOriginal:\n'
        prefix = [tokenizer.bos_token_id] + tokenizer.encode(prompt, add_special_tokens=False)
        target = tokenizer.encode(clean, add_special_tokens=False)
        complete = keep == len(words)
        if complete:
            target += [tokenizer.eos_token_id]
        ids = prefix + target
        if len(ids) <= cfg['context_length']:
            return {'input_ids': ids, 'attention_mask': [1] * len(ids),
                    'labels': [-100] * len(prefix) + target,
                    'coverage': keep / len(words), 'retained_words': keep,
                    'original_words': len(words), 'complete': complete}
        keep -= max(1, (len(ids) - cfg['context_length']) // 4)
    raise ValueError('no message content fits context: abstain')


def collate(rows, pad_token_id):
    import torch
    width = max(len(r['input_ids']) for r in rows)
    batch = {}
    for field, pad in [('input_ids', pad_token_id), ('attention_mask', 0), ('labels', -100)]:
        batch[field] = torch.tensor([r[field] + [pad] * (width - len(r[field])) for r in rows], dtype=torch.long)
    return batch


def select_records(data_root, fold_id, partition, per_source, seed):
    import polars as pl
    from pathlib import Path
    if partition not in ('train', 'val'):
        raise ValueError('only source train/validation permitted')
    path = Path(data_root) / 'folds' / fold_id / 'semantic' / partition / 'records.parquet'
    frame = pl.read_parquet(path)
    selected = []
    for arch in sorted(frame['architecture_id'].unique()):
        subset = frame.filter(pl.col('architecture_id') == arch)
        subset = subset.sort('rank')
        sampler = random.Random(int(hashlib.sha256(f'{seed}:{arch}:{partition}'.encode()).hexdigest(), 16))
        positions = sampler.sample(range(subset.height), min(per_source, subset.height))
        subset = subset[positions]
        selected.extend(subset.select('architecture_id', 'rank', 'normalized_message').to_dicts())
    return selected
