"""Six isolated ordered-context controls; never selection or natural truth."""
from __future__ import annotations


BASE_CONTEXT = [
    "job submitted to scheduler",
    "worker allocated for job",
    "input block opened",
    "input block processed",
]
BASE_TARGET = "job completed successfully"


def _cases():
    return [
        ("event_permutation", list(reversed(BASE_CONTEXT)), BASE_TARGET),
        ("missing_event", [BASE_CONTEXT[0], BASE_CONTEXT[2], BASE_CONTEXT[3]], BASE_TARGET),
        ("duplicate_event", BASE_CONTEXT + [BASE_CONTEXT[-1]], BASE_TARGET),
        ("unexpected_next_event", BASE_CONTEXT, "permission denied while deleting cluster metadata"),
        ("long_range_dependency_violation", ["job cancelled by operator"] + BASE_CONTEXT[1:], BASE_TARGET),
        ("locally_plausible_globally_invalid", BASE_CONTEXT[1:] + [BASE_CONTEXT[0]], BASE_TARGET),
    ]


def run_probes(score):
    intact = score(BASE_CONTEXT, BASE_TARGET)
    results = []
    for kind, context, target in _cases():
        changed = score(context, target)
        delta = None
        if intact["score_raw"] is not None and changed["score_raw"] is not None:
            delta = changed["score_raw"] - intact["score_raw"]
        results.append({"kind": kind, "intact": intact, "changed": changed, "delta": delta})
    return {
        "scope": "SYNTHETIC_SEQUENCE_DIAGNOSTIC_ONLY",
        "used_for_training_or_selection": False,
        "natural_anomaly_performance": None,
        "results": results,
    }
