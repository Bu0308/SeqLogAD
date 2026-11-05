"""Batched, per-token scoring with the exact training-time encodings.

The repository scorers forward one example at a time.  This module reuses the
same encoders (``encode_message`` / ``encode_window``) and the same loss
semantics (cross-entropy in float32 over label tokens, autocast forward) but
packs right-padded examples into token-budgeted batches.  Right padding with an
attention mask leaves every real position's causal computation unchanged.
"""
from __future__ import annotations

import math
from contextlib import nullcontext

import numpy as np

from seqlogad.semantic.objective import collate, encode_message
from seqlogad.sequence.objective import encode_window

from .volatile import encode_template


def encode(kind: str, tokenizer, cfg: dict, row: dict) -> dict:
    """Encode one cohort row for ``kind`` in {'semantic', 'sequence'}; never raises."""
    try:
        if kind == "semantic":
            encoded = encode_message(tokenizer, row["target_message"], cfg)
        elif kind == "semantic_template":
            encoded = encode_template(tokenizer, row["target_message"], cfg)
        elif kind == "sequence":
            encoded = encode_window(tokenizer, row["context_messages"], row["target_message"], cfg)
        else:
            raise KeyError(kind)
    except ValueError as exc:
        return {"window_id": row["window_id"], "status": "ABSTAIN", "reason": str(exc)}
    encoded["window_id"] = row["window_id"]
    encoded["status"] = "VALID" if encoded["complete"] else "LOW_COVERAGE"
    return encoded


def make_batches(examples: list[dict], token_budget: int) -> list[list[dict]]:
    """Length-sorted batches whose padded size stays within ``token_budget``."""
    ordered = sorted(examples, key=lambda e: len(e["input_ids"]))
    batches, current = [], []
    for example in ordered:
        width = max([len(example["input_ids"])] + [len(e["input_ids"]) for e in current])
        if current and width * (len(current) + 1) > token_budget:
            batches.append(current)
            current = []
        current.append(example)
    if current:
        batches.append(current)
    return batches


def _autocast(device, dtype):
    import torch

    if dtype is None or device.type != "cuda":
        return nullcontext()
    return torch.autocast("cuda", dtype=dtype)


def score_batch(model, batch_examples: list[dict], pad_token_id: int, dtype,
                keep_hidden: bool) -> list[dict]:
    import torch

    device = next(model.parameters()).device
    batch = {k: v.to(device) for k, v in collate(batch_examples, pad_token_id).items()}
    with torch.no_grad(), _autocast(device, dtype):
        outputs = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"],
                        output_hidden_states=keep_hidden)
    labels = batch["labels"][:, 1:]
    mask = labels != -100
    logits = outputs.logits[:, :-1].float()
    losses = torch.nn.functional.cross_entropy(
        logits.transpose(1, 2), labels, reduction="none", ignore_index=-100)
    hidden = outputs.hidden_states[-1][:, :-1].float() if keep_hidden else None
    results = []
    for row, example in enumerate(batch_examples):
        token = losses[row][mask[row]].cpu().numpy().astype(np.float64)
        if token.size == 0 or not np.isfinite(token).all():
            raise ValueError(f"no finite target token for {example['window_id']}")
        result = {
            "window_id": example["window_id"], "status": example["status"],
            "coverage": example["coverage"], "n_tokens": int(token.size),
            "nll_mean": float(token.mean()), "nll_sum": float(token.sum()),
            "nll_first": float(token[0]), "nll_max": float(token.max()),
            "token_nll": [round(float(v), 6) for v in token],
            "input_tokens": len(example["input_ids"]),
        }
        if keep_hidden:
            result["hidden"] = hidden[row][mask[row]].mean(0).cpu().numpy().astype(np.float16)
        results.append(result)
    return results


def score_examples(model, examples: list[dict], pad_token_id: int, dtype, *,
                   token_budget: int = 4096, keep_hidden: bool = False,
                   progress=None) -> list[dict]:
    """Score every encoded example; abstentions are passed through, never dropped."""
    valid = [e for e in examples if e["status"] != "ABSTAIN"]
    out = [{"window_id": e["window_id"], "status": "ABSTAIN", "reason": e["reason"]}
           for e in examples if e["status"] == "ABSTAIN"]
    batches = make_batches(valid, token_budget)
    model.eval()
    for index, chunk in enumerate(batches):
        out.extend(score_batch(model, chunk, pad_token_id, dtype, keep_hidden))
        if progress is not None:
            progress(index + 1, len(batches))
    for row in out:
        if row["status"] != "ABSTAIN" and not math.isfinite(row["nll_mean"]):
            raise ValueError("nonfinite score")
    return out


def unique_examples(examples: list[dict]) -> tuple[list[dict], dict[str, list[str]]]:
    """One representative per distinct encoding; maps representative id -> all window ids."""
    first, groups, reps = {}, {}, []
    for e in examples:
        key = ("ABSTAIN", e["window_id"]) if e["status"] == "ABSTAIN" else (
            tuple(e["input_ids"]), tuple(e["labels"]))
        if key not in first:
            first[key] = e["window_id"]
            groups[e["window_id"]] = []
            reps.append(e)
        groups[first[key]].append(e["window_id"])
    return reps, groups


def expand_scores(scored: list[dict], groups: dict[str, list[str]]) -> list[dict]:
    return [dict(row, window_id=wid) for row in scored for wid in groups[row["window_id"]]]


def score_unique(model, examples: list[dict], pad_token_id: int, dtype, **kwargs) -> list[dict]:
    """``score_examples`` on distinct encodings only (HDFS repeats most messages)."""
    reps, groups = unique_examples(examples)
    return expand_scores(score_examples(model, reps, pad_token_id, dtype, **kwargs), groups)
