"""B0 label-free baselines fitted only on the same source's SOURCE_TRAIN events.

They answer the control question for every LLM claim: does an expert beat a
frequency / first-order Markov model of the very logs it was trained on?
"""
from __future__ import annotations

import math
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq


def train_messages(data_root: Path, fold_id: str, architecture: str) -> list[tuple[str, str, int]]:
    path = Path(data_root) / "folds" / fold_id / "sequence/metadata/events.parquet"
    table = pq.read_table(path, columns=["architecture_id", "partition", "sequence_id", "rank",
                                         "normalized_message"])
    rows = [(seq, msg, rank) for arch, part, seq, rank, msg in zip(
        *(table[c].to_pylist() for c in ("architecture_id", "partition", "sequence_id", "rank",
                                         "normalized_message")))
            if arch == architecture and part == "SOURCE_TRAIN"]
    if not rows:
        raise ValueError(f"no SOURCE_TRAIN events for {architecture} in {fold_id}")
    return sorted(rows, key=lambda r: (r[0] or "", r[2]))


class B0:
    """-log unigram frequency and -log first-order Markov transition (add-0.5)."""

    def __init__(self, rows: list[tuple[str, str, int]]):
        self.unigram = Counter(msg for _, msg, _ in rows)
        self.total = sum(self.unigram.values())
        self.vocab = len(self.unigram) + 1
        self.bigram, self.context = Counter(), Counter()
        previous = {}
        for seq, msg, _ in rows:
            if seq in previous:
                self.bigram[(previous[seq], msg)] += 1
                self.context[previous[seq]] += 1
            previous[seq] = msg

    def frequency(self, message: str) -> float:
        return -math.log((self.unigram.get(message, 0) + 0.5) / (self.total + 0.5 * self.vocab))

    def markov(self, previous: str | None, message: str) -> float:
        if previous is None:
            return self.frequency(message)
        count = self.bigram.get((previous, message), 0)
        return -math.log((count + 0.5) / (self.context.get(previous, 0) + 0.5 * self.vocab))


def score_rows(model: B0, rows: list[dict]) -> dict[str, dict[str, float]]:
    out = {}
    for row in rows:
        previous = row["context_messages"][-1] if row["context_messages"] else None
        out[row["window_id"]] = {"b0_frequency": model.frequency(row["target_message"]),
                                 "b0_markov": model.markov(previous, row["target_message"])}
    return out
