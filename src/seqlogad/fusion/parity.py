"""Fail-closed parity: the bridge must reproduce selection-time numbers first.

If batched scoring through the bridge does not reproduce the metrics that the
training runs recorded for their own best checkpoints, every downstream fusion
number would be untrustworthy, so the scoring run aborts.
"""
from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

from .metrics import auroc, average_precision


def _row_at(train_log: str, step: int) -> dict:
    with open(train_log) as handle:
        rows = [json.loads(line) for line in handle]
    hits = [r for r in rows if r.get("step") == step]
    if len(hits) != 1:
        raise ValueError(f"train log lacks a unique row for step {step}")
    return hits[0]


def unit_scores(rows: list[dict], scores: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    """Mean window score per unit (BGL line, HDFS block), as at selection time."""
    by_unit, label = defaultdict(list), {}
    for row in rows:
        by_unit[row["unit_id"]].append(scores[row["window_id"]])
        label[row["unit_id"]] = row["anomaly"]
    units = sorted(by_unit)
    return (np.array([label[u] for u in units]), np.array([np.mean(by_unit[u]) for u in units]))


def _close(got: float, ref: float, rel: float, absolute: float) -> bool:
    return abs(got - ref) <= max(rel * abs(ref), absolute)


def sequence_parity(expert: dict, cohort: list[dict], scores: dict[str, float],
                    tolerance_metric: float, tolerance_rel: float, tolerance_abs: float) -> dict:
    recorded = expert["metrics"]["best"]["source_development"]["per_source"]
    log_row = _row_at(expert["train_log"], expert["checkpoints"]["best"]["step"])
    report = {}
    for arch, ref in recorded.items():
        rows = [r for r in cohort if r["architecture_id"] == arch and r["selection_cohort"]]
        y, s = unit_scores(rows, scores)
        got = {"auroc": auroc(y, s), "average_precision": average_precision(y, s),
               "mean_window_nll": float(np.mean([scores[r["window_id"]] for r in rows]))}
        ref_nll = log_row["per_source_validation_next_log_nll"][arch]
        ok = (abs(got["auroc"] - ref["auroc"]) <= tolerance_metric
              and abs(got["average_precision"] - ref["average_precision"]) <= tolerance_metric
              and _close(got["mean_window_nll"], ref_nll, tolerance_rel, tolerance_abs))
        report[arch] = {"recorded": {"auroc": ref["auroc"], "average_precision": ref["average_precision"],
                                     "mean_window_nll": ref_nll}, "reproduced": got, "pass": bool(ok)}
    return report


def semantic_parity(expert: dict, per_source_nll: dict[str, float], tolerance_rel: float,
                    tolerance_abs: float) -> dict:
    log_row = _row_at(expert["train_log"], expert["checkpoints"]["best"]["step"])
    recorded = log_row["per_source_validation_reconstruction_nll"]
    report = {}
    for arch, ref in recorded.items():
        got = per_source_nll[arch]
        report[arch] = {"recorded": ref, "reproduced": got,
                        "pass": bool(_close(got, ref, tolerance_rel, tolerance_abs))}
    return report


def all_pass(report: dict) -> bool:
    return all(item["pass"] for fold in report.values() for item in fold.values())
