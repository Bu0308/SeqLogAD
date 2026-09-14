"""Uncalibrated reconstruction evidence, not a probability of anomaly."""
import math
from .objective import encode_message, collate


def score_message(model, tokenizer, cfg, text, metadata):
    import torch
    common = dict(schema_version='SEMANTIC-EVIDENCE-1', expert_id='SEMANTIC_LLAMA', expert_role='SEMANTIC',
        score_direction='HIGHER_IS_MORE_ANOMALOUS', score_calibrated=None, calibration_status='NOT_CALIBRATED',
        uncertainty=None, uncertainty_method='TOKEN_NLL_DISPERSION_NOT_CALIBRATED_CONFIDENCE',
        model_revision=cfg['model_revision'], **metadata)
    try:
        encoded = encode_message(tokenizer, text, cfg)
    except ValueError as exc:
        return dict(common, score_raw=None, coverage=0.0, evidence=[], localisation=[], status='ABSTAIN', reason=str(exc))
    model.eval()
    batch = {k: v.to(model.device) for k, v in collate([encoded], tokenizer.pad_token_id).items()}
    with torch.no_grad():
        logits = model(**batch).logits[:, :-1].float()
        labels = batch['labels'][:, 1:]
        mask = labels != -100
        losses = torch.nn.functional.cross_entropy(logits.transpose(1, 2), labels, reduction='none', ignore_index=-100)
        values = losses[mask].cpu().tolist()
    mean = sum(values) / len(values)
    if not math.isfinite(mean):
        raise ValueError('nonfinite inference score')
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    positions = mask[0].nonzero().flatten().cpu().tolist()
    top = sorted(zip(positions, values), key=lambda item: -item[1])[:5]
    return dict(common, score_raw=mean, uncertainty=variance ** 0.5, coverage=encoded['coverage'],
        evidence=[{'kind': 'mean_reconstruction_token_nll', 'value': mean, 'tokens_scored': len(values),
                   'corruption_seed': cfg['seed'], 'original_words': encoded['original_words'],
                   'retained_words': encoded['retained_words']}],
        localisation=[{'token_position_in_model_input': pos + 1, 'nll': value} for pos, value in top],
        status='VALID' if encoded['complete'] else 'LOW_COVERAGE',
        reason=None if encoded['complete'] else 'HEAD_CROP; suffix not scored')
