"""Build the labelled source-development cohort shared by both experts.

Every fold-independent SOURCE_VALIDATION window of a labelled source (BGL lines,
HDFS blocks) is hydrated with its context and target text.  The 512 windows per
source that already selected the Sequence checkpoint are flagged
``selection_cohort`` so that fusion results can be reported on fresh units only.
No target-architecture record or label is read here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from seqlogad.common.checksum import sha256_file

LABELLED = ("ARCH-BGL", "ARCH-HDFS")
SELECTION_PER_SOURCE = 512
SELECTION_SEED = 42
CHUNK_WINDOWS = 64


def _sidecar(sidecar_root: Path, fold_id: str, bundle_sha: str) -> dict[str, dict]:
    manifest = json.loads((sidecar_root / "manifest.json").read_text())
    if manifest.get("target_labels_used_for_selection") is not False:
        raise ValueError("source-development sidecar is not source-only")
    if manifest["sequence_bundle_sha256"] != bundle_sha:
        raise ValueError("source-development sidecar does not match the sequence bundle")
    name = f"{fold_id}.json"
    if sha256_file(sidecar_root / name) != manifest["files"][name]:
        raise ValueError("source-development fold checksum mismatch")
    entries = json.loads((sidecar_root / name).read_text())["entries"]
    return {row["window_id"]: row for row in entries}


def selection_window_ids(data_root: Path, fold_id: str) -> set[str]:
    """Re-derive the exact windows used for V13R1 checkpoint selection."""
    from seqlogad.sequence.objective import select_windows

    rows = select_windows(data_root, fold_id, "val", SELECTION_PER_SOURCE, SELECTION_SEED,
                          replacement=False)
    return {row["window_id"] for row in rows}


def build_cohort(data_root: str | Path, sidecar_root: str | Path, fold_id: str) -> list[dict]:
    data, sidecar = Path(data_root), Path(sidecar_root)
    bundle_sha = sha256_file(data / "manifests/bundle.json")
    fold = json.loads((data / "folds" / fold_id / "manifests/fold.json").read_text())
    labels = _sidecar(sidecar, fold_id, bundle_sha)
    root = data / "folds" / fold_id / "sequence"
    windows = pq.read_table(root / "val/windows.parquet").to_pylist()
    windows = [w for w in windows if w["window_id"] in labels]
    if {w["architecture_id"] for w in windows} & {fold["target_architecture"]}:
        raise ValueError("target architecture leaked into source-development cohort")
    events = pq.read_table(root / "metadata/events.parquet",
                           columns=["architecture_id", "partition", "rank", "normalized_message"])
    text = {}
    wanted = {(w["architecture_id"], r) for w in windows for r in [*w["context_ranks"], w["target_rank"]]}
    for arch, part, rank, message in zip(*(events[c].to_pylist() for c in
                                           ("architecture_id", "partition", "rank", "normalized_message"))):
        if part == "SOURCE_VALIDATION" and (arch, rank) in wanted:
            text[(arch, rank)] = message
    if len(text) != len(wanted):
        raise ValueError("cohort windows reference unresolved events")
    selected = selection_window_ids(data, fold_id)
    cohort = []
    for arch in sorted({w["architecture_id"] for w in windows}):
        rows = sorted((w for w in windows if w["architecture_id"] == arch),
                      key=lambda w: (w["target_rank"], w["window_id"]))
        for position, w in enumerate(rows):
            entry = labels[w["window_id"]]
            if entry["target_rank"] != w["target_rank"]:
                raise ValueError("label sidecar rank mismatch")
            chunk = position // CHUNK_WINDOWS
            cohort.append({
                "fold_id": fold_id, "architecture_id": arch, "window_id": w["window_id"],
                "unit_id": entry["unit_id"], "target_rank": w["target_rank"],
                "anomaly": bool(entry["anomaly"]),
                "context_messages": [text[(arch, r)] for r in w["context_ranks"]],
                "target_message": text[(arch, w["target_rank"])],
                "selection_cohort": w["window_id"] in selected,
                "time_chunk": f"{arch}:{chunk:03d}",
                "crossfit_fold": 0 if position < len(rows) // 2 else 1,
            })
    return cohort


def strip_labels(cohort: list[dict]) -> list[dict]:
    """Copy of the cohort without labels; this is all the GPU scorer receives."""
    return [{k: v for k, v in row.items() if k != "anomaly"} for row in cohort]
