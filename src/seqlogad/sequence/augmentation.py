"""Label-free causal context views for V12 Sequence training only."""
from __future__ import annotations

import random

from .objective import encode_window


def sample_training_view(encoded, raw_window, tokenizer, cfg, rng=random):
    """Choose a full or shorter suffix without changing the target or boundary."""
    contexts = [message for message in raw_window["context_messages"]
                if message and message.strip()]
    if not contexts:
        raise ValueError("V12 training window has no predecessor")
    policy = cfg["training_context_views"]
    short_lengths = [length for length in policy["short_lengths"] if length < len(contexts)]
    if not short_lengths or rng.random() < policy["full_context_probability"]:
        return encoded, {"requested_context_records": len(contexts), "view": "full"}
    length = rng.choice(short_lengths)
    view = encode_window(tokenizer, contexts[-length:], raw_window["target_message"], cfg)
    return view, {"requested_context_records": length, "view": "short"}
