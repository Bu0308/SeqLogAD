"""Thresholded source-development metrics at each dataset's labeled unit."""
from __future__ import annotations

from collections import defaultdict


def _binary_metrics(items: list[tuple[float, bool]]) -> dict:
    if not items or {label for _, label in items} != {False, True}:
        raise ValueError("source development requires both anomaly classes")
    ranked = sorted(items, key=lambda item: -item[0])
    positive = sum(label for _, label in ranked)
    negative = len(ranked) - positive
    tp = fp = 0
    best = None
    ap = 0.0
    index = 0
    while index < len(ranked):
        threshold = ranked[index][0]
        previous_tp = tp
        while index < len(ranked) and ranked[index][0] == threshold:
            if ranked[index][1]:
                tp += 1
            else:
                fp += 1
            index += 1
        precision = tp / (tp + fp)
        recall = tp / positive
        f1 = 2 * tp / (2 * tp + fp + positive - tp)
        ap += precision * (tp - previous_tp) / positive
        candidate = {"threshold": threshold, "precision": precision,
                     "recall": recall, "f1": f1,
                     "accuracy": (tp + negative - fp) / len(ranked)}
        if best is None or f1 > best["f1"]:
            best = candidate
    # Mann-Whitney form with half-credit for equal scores.
    auc_wins = 0.0
    seen_negative = 0
    for score in sorted({score for score, _ in items}):
        group = [label for value, label in items if value == score]
        group_positive = sum(group)
        group_negative = len(group) - group_positive
        auc_wins += group_positive * (seen_negative + group_negative / 2)
        seen_negative += group_negative
    return dict(best, auroc=auc_wins / (positive * negative),
                average_precision=ap, positives=positive, negatives=negative,
                units=len(ranked))


def source_development_metrics(window_scores: list[dict], labels: dict[str, dict]) -> dict:
    """Aggregate HDFS by block, BGL by line, then macro-average source F1."""
    grouped = defaultdict(lambda: defaultdict(list))
    seen_windows = set()
    for row in window_scores:
        window_id = row["window_id"]
        if window_id not in labels:
            continue
        if window_id in seen_windows:
            raise ValueError("duplicate source development score")
        seen_windows.add(window_id)
        entry = labels[window_id]
        if row["architecture_id"] != entry["architecture_id"]:
            raise ValueError("source development score architecture mismatch")
        value = float(row["nll"])
        if not -float("inf") < value < float("inf"):
            raise ValueError("nonfinite source development anomaly score")
        grouped[entry["architecture_id"]][entry["unit_id"]].append((value, entry["anomaly"]))
    if seen_windows != set(labels):
        raise ValueError("source development score coverage is incomplete")
    if not grouped:
        raise ValueError("no scored source development windows")
    per_source = {}
    for arch, units in sorted(grouped.items()):
        items = []
        for rows in units.values():
            if len({label for _, label in rows}) != 1:
                raise ValueError("contradictory labels in one source development unit")
            items.append((sum(value for value, _ in rows) / len(rows), rows[0][1]))
        per_source[arch] = _binary_metrics(items)
        per_source[arch]["scored_windows"] = sum(map(len, units.values()))
        per_source[arch]["labeled_windows"] = sum(
            entry["architecture_id"] == arch for entry in labels.values()
        )
    expected = {entry["architecture_id"] for entry in labels.values()}
    if set(per_source) != expected:
        raise ValueError("one labeled source has no valid scored windows")
    names = ("f1", "precision", "recall", "accuracy", "auroc", "average_precision")
    return {
        "aggregation": "MACRO_MEAN_OF_PER_SOURCE_BEST_F1_AT_LABELED_UNIT",
        "per_source": per_source,
        **{f"macro_{name}": sum(row[name] for row in per_source.values()) / len(per_source)
           for name in names},
    }
