"""Uncalibrated next-log evidence; never an anomaly probability."""
from __future__ import annotations

import math

from .objective import collate, encode_window


def score_next_log(model, tokenizer, cfg, context_messages, target_message, metadata):
    import torch

    common = dict(
        schema_version="SEQUENCE-EVIDENCE-1",
        expert_id="SEQUENCE_LLAMA_REFERENCE",
        expert_role="SEQUENCE",
        score_direction="HIGHER_IS_MORE_ANOMALOUS",
        score_calibrated=None,
        calibration_status="NOT_CALIBRATED",
        uncertainty=None,
        uncertainty_method="TARGET_TOKEN_NLL_DISPERSION_NOT_CALIBRATED_CONFIDENCE",
        model_revision=cfg["model_revision"],
        **metadata,
    )
    try:
        encoded = encode_window(tokenizer, context_messages, target_message, cfg)
    except ValueError as exc:
        return dict(
            common, score_raw=None, coverage=0.0, evidence=[], localisation=[],
            status="ABSTAIN", reason=str(exc),
        )
    model.eval()
    batch = {key: value.to(model.device)
             for key, value in collate([encoded], tokenizer.pad_token_id).items()}
    with torch.no_grad():
        logits = model(**batch).logits[:, :-1].float()
        labels = batch["labels"][:, 1:]
        mask = labels != -100
        losses = torch.nn.functional.cross_entropy(
            logits.transpose(1, 2), labels, reduction="none", ignore_index=-100
        )
        values = losses[mask].cpu().tolist()
    if not values:
        raise ValueError("no next-log target token was scored")
    mean = sum(values) / len(values)
    if not math.isfinite(mean):
        raise ValueError("nonfinite next-log inference score")
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    positions = mask[0].nonzero().flatten().cpu().tolist()
    top = sorted(zip(positions, values), key=lambda item: -item[1])[:5]
    complete = encoded["complete"]
    return dict(
        common,
        score_raw=mean,
        uncertainty=variance ** 0.5,
        coverage=encoded["coverage"],
        evidence=[{
            "kind": "mean_next_log_target_token_nll",
            "value": mean,
            "tokens_scored": len(values),
            "original_context_records": encoded["original_context_records"],
            "retained_context_records": encoded["retained_context_records"],
            "original_target_words": encoded["original_target_words"],
            "retained_target_words": encoded["retained_target_words"],
        }],
        localisation=[{"target_token_position_in_model_input": position + 1, "nll": value}
                      for position, value in top],
        status="VALID" if complete else "LOW_COVERAGE",
        reason=None if complete else "OLDEST_CONTEXT_OR_TARGET_SUFFIX_CROPPED",
    )
