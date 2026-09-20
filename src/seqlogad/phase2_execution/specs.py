"""Authoritative seed-42 development-wave identities."""
from pathlib import Path

import yaml


TARGETS = ("BGL", "HDFS", "HADOOP")
FOLDS = {target: f"FOLD-TARGET-ARCH-{target}" for target in TARGETS}
TASKS = ("P2.1", "P2.2", "P2.3", "P2.4")


def load_development_spec(repo_root):
    path = Path(repo_root) / "configs/protocols/phase2-development-s42-v1.yaml"
    spec = yaml.safe_load(path.read_text())["phase2_development_s42"]
    if spec["status"] != "ACTIVE_EXECUTION_AMENDMENT":
        raise ValueError("seed-42 development execution amendment is not active")
    if spec["seed"] != 42 or tuple(spec["targets"]) != TARGETS:
        raise ValueError("development seed/target contract changed")
    if spec["source_label_status"] != "UNRESOLVED_DENY" or spec["anomaly_labels_allowed"]:
        raise ValueError("label-access contract changed")
    if spec["confirmation_seeds_deferred"] != [3407, 8675309]:
        raise ValueError("confirmation-seed deferral changed")
    return spec


def expert_spec(repo_root, task_id):
    if task_id not in TASKS:
        raise ValueError("unknown Phase-2 expert task")
    return load_development_spec(repo_root)["experts"][task_id]


def deterministic_run_id(task_id, target, seed=42):
    if target not in TARGETS or seed != 42:
        raise ValueError("development execution is locked to seed 42 and three target folds")
    if task_id == "P2.1":
        return f"P2.1-FINAL-{target}-S42"
    return f"{task_id}-DEVELOPMENT-{target}-S42"
