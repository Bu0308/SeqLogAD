"""Causal next-log encoding with target-only loss and explicit coverage."""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

import polars as pl

from seqlogad.semantic.objective import collate, literal_text

from .contracts import PARTITIONS


def select_windows(data_root, fold_id, partition, per_source, seed, *, replacement):
    if partition not in PARTITIONS:
        raise ValueError("only source train/validation permitted")
    root = Path(data_root) / "folds" / fold_id / "sequence"
    windows = pl.read_parquet(root / f"{partition}/windows.parquet")
    selected = []
    for architecture in sorted(windows["architecture_id"].unique()):
        source = windows.filter(pl.col("architecture_id") == architecture).sort("target_rank")
        rng = random.Random(int(hashlib.sha256(
            f"P2.2:{seed}:{architecture}:{partition}".encode()
        ).hexdigest(), 16))
        if replacement:
            positions = [rng.randrange(source.height) for _ in range(per_source)]
        else:
            positions = rng.sample(range(source.height), min(per_source, source.height))
        selected.extend(source[positions].to_dicts())

    hydrated = []
    events_path = root / "metadata/events.parquet"
    for architecture in sorted({row["architecture_id"] for row in selected}):
        rows = [row for row in selected if row["architecture_id"] == architecture]
        required = {rank for row in rows for rank in list(row["context_ranks"]) + [row["target_rank"]]}
        events = pl.scan_parquet(events_path).filter(
            (pl.col("architecture_id") == architecture)
            & (pl.col("partition") == PARTITIONS[partition])
            & pl.col("rank").is_in(required)
        ).collect()
        by_rank = {item["rank"]: item["normalized_message"] for item in events.to_dicts()}
        if set(by_rank) != required:
            raise ValueError("selected sequence windows have unresolved event references")
        for row in rows:
            row["context_messages"] = [by_rank[rank] for rank in row["context_ranks"]]
            row["target_message"] = by_rank[row["target_rank"]]
            hydrated.append(row)
    return hydrated


def _prompt(messages):
    lines = ["Previous log messages in chronological order:"]
    lines.extend(f"[{index}] {literal_text(message)}" for index, message in enumerate(messages, 1))
    lines.append("Next log message:")
    return "\n".join(lines) + "\n"


def encode_window(tokenizer, context_messages, target_message, cfg):
    contexts = [message for message in context_messages if message and message.strip()]
    target_words = literal_text(target_message).split()
    if not contexts:
        raise ValueError("sequence window has no usable predecessor")
    if not target_words:
        raise ValueError("sequence target is empty")
    original_context = len(contexts)
    while contexts:
        prompt_ids = [tokenizer.bos_token_id] + tokenizer.encode(
            _prompt(contexts), add_special_tokens=False
        )
        keep = len(target_words)
        while keep:
            target_ids = tokenizer.encode(" ".join(target_words[:keep]), add_special_tokens=False)
            complete = keep == len(target_words)
            if complete:
                target_ids += [tokenizer.eos_token_id]
            ids = prompt_ids + target_ids
            if len(ids) <= cfg["context_length"]:
                return {
                    "input_ids": ids,
                    "attention_mask": [1] * len(ids),
                    "labels": [-100] * len(prompt_ids) + target_ids,
                    "coverage": keep / len(target_words),
                    "retained_target_words": keep,
                    "original_target_words": len(target_words),
                    "retained_context_records": len(contexts),
                    "original_context_records": original_context,
                    "complete": complete and len(contexts) == original_context,
                }
            keep -= max(1, (len(ids) - cfg["context_length"]) // 4)
        if len(contexts) == 1:
            break
        contexts = contexts[1:]
    raise ValueError("no causal context plus target content fits token horizon")
