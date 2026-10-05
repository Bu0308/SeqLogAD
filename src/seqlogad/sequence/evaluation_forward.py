"""Identical precision and token-loss semantics for validation and inference."""


def target_token_losses(model, batch, dtype):
    import torch

    with torch.no_grad():
        with torch.autocast("cuda", dtype=dtype):
            logits = model(**{key: value for key, value in batch.items()
                              if key != "labels"}).logits
        labels = batch["labels"][:, 1:]
        mask = labels != -100
        losses = torch.nn.functional.cross_entropy(
            logits[:, :-1].float().transpose(1, 2), labels,
            reduction="none", ignore_index=-100,
        )
    return losses[mask], mask
