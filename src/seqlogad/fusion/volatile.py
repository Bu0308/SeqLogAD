"""Template-only Semantic scoring: drop volatile identifier tokens from the NLL.

The upstream normaliser leaves file paths and task ids in some messages (HDFS
``allocateBlock: /user/root/rand/_temporary/_task_200811092030_0003_m_000793_0/
part-<NUM>``).  Every such line looks novel to the Semantic expert, so it raises
false alarms on almost every normal block.  This module keeps the frozen
encoder and prompt untouched and only removes the target tokens that belong to
volatile words from the loss, so the score reflects the message template.

The rule is fixed a priori and identical for every system: a word is volatile
when it contains at least ``MIN_DIGITS`` ASCII digits (placeholders such as
``<NUM>`` contain none).
"""
from __future__ import annotations

from seqlogad.semantic.objective import encode_message, literal_text

MIN_DIGITS = 3


def is_volatile(word: str) -> bool:
    return sum(c.isdigit() for c in word) >= MIN_DIGITS


def volatile_spans(clean: str) -> list[tuple[int, int]]:
    spans, start = [], 0
    for word in clean.split(" "):
        if is_volatile(word):
            spans.append((start, start + len(word)))
        start += len(word) + 1
    return spans


def encode_template(tokenizer, text: str, cfg: dict) -> dict:
    """``encode_message`` with volatile-word target tokens set to -100 (falls back if none remain)."""
    encoded = encode_message(tokenizer, text, cfg)
    clean = " ".join(literal_text(text).split()[:encoded["retained_words"]])
    spans = volatile_spans(clean)
    encoded["volatile_tokens"] = 0
    if not spans:
        return encoded
    offsets = tokenizer(clean, add_special_tokens=False, return_offsets_mapping=True)
    if list(offsets["input_ids"]) != tokenizer.encode(clean, add_special_tokens=False):
        raise ValueError("offset tokenisation differs from encode(); cannot align volatile spans")
    start = next(i for i, v in enumerate(encoded["labels"]) if v != -100)
    labels = list(encoded["labels"])
    for i, (a, b) in enumerate(offsets["offset_mapping"]):
        if any(a < hi and b > lo for lo, hi in spans):
            labels[start + i] = -100
    kept = sum(v != -100 for v in labels)
    if kept > 1:  # keep at least one template token besides EOS
        encoded["volatile_tokens"] = sum(v != -100 for v in encoded["labels"]) - kept
        encoded["labels"] = labels
    return encoded
