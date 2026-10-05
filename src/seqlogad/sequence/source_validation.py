"""One-pass next-log validation, with optional source-development labels."""
from __future__ import annotations

import math
from collections import defaultdict

from .objective import collate
from .evaluation_forward import target_token_losses
from .source_development_metrics import source_development_metrics


def score_validation(model, tokenizer, examples, dtype):
    import torch

    was_training = model.training
    model.eval()
    scores = []
    try:
        with torch.no_grad():
            for example in examples:
                batch = {key: value.to(model.device)
                         for key, value in collate([example], tokenizer.pad_token_id).items()}
                losses, _ = target_token_losses(model, batch, dtype)
                value = float(losses.mean())
                if not math.isfinite(value):
                    raise ValueError("nonfinite source validation next-log loss")
                scores.append({"architecture_id": example["architecture_id"],
                               "window_id": example["window_id"], "nll": value})
    finally:
        model.train(was_training)
    return scores


def summarize_validation(scores, development_labels=None):
    per_architecture = defaultdict(list)
    for row in scores:
        per_architecture[row["architecture_id"]].append(row["nll"])
    per_source = {arch: sum(values) / len(values)
                  for arch, values in sorted(per_architecture.items())}
    if not per_source:
        raise ValueError("empty source validation")
    summary = {
        "aggregate_nll": sum(per_source.values()) / len(per_source),
        "per_source_nll": per_source,
        "per_source_perplexity": {
            source: math.exp(value) if value < 700 else None
            for source, value in per_source.items()
        },
        "aggregation": "MEAN_OF_EQUAL_WEIGHT_SOURCE_MEAN_TARGET_TOKEN_NLL",
    }
    if development_labels is not None:
        summary["source_development"] = source_development_metrics(scores, development_labels)
    return summary
