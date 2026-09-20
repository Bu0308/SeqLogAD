"""Create and restore bounded, resumable training snapshots."""
from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from .archive import copy_tree_selected, create_zip, seal_tree, verify_zip
from .persistence import publish_atomic, verify_persisted_zip


ROOT_NAME = "seqlogad_recovery"


def _checkpoint_step(path):
    name = Path(path).name
    if not name.startswith("step-") or not name[5:].isdigit():
        raise ValueError("recovery checkpoint must use step-N identity")
    return int(name[5:])


def create_recovery(run_directory, checkpoint_directory, destination, *, task_id,
                    target, seed, best_checkpoint):
    run = Path(run_directory)
    checkpoint = Path(checkpoint_directory)
    if checkpoint.parent != run / "checkpoints":
        raise ValueError("checkpoint is outside its run directory")
    best = run / "checkpoints" / best_checkpoint
    if not checkpoint.is_dir() or not best.is_dir():
        raise ValueError("latest/best checkpoint missing")
    with tempfile.TemporaryDirectory() as folder:
        stage = Path(folder) / ROOT_NAME
        restored_run = stage / "run"
        copy_tree_selected(run, restored_run, exclude_top={"checkpoints"})
        (restored_run / "checksums.sha256").unlink(missing_ok=True)
        for selected in {checkpoint, best}:
            shutil.copytree(selected, restored_run / "checkpoints" / selected.name)
        receipt = {
            "schema": "SEQLOGAD-RECOVERY-1",
            "task_id": task_id,
            "target": target,
            "seed": seed,
            "run_id": run.name,
            "fold_id": run.parents[1].name,
            "expert_id": run.parent.name,
            "latest_checkpoint": checkpoint.name,
            "latest_step": _checkpoint_step(checkpoint),
            "best_checkpoint": best.name,
            "base_weights_included": False,
        }
        (stage / "RECOVERY.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        seal_tree(restored_run)
        seal_tree(stage)
        local = Path(folder) / "LATEST_RECOVERY.zip"
        create_zip(stage, local, ROOT_NAME)
        published = publish_atomic(local, destination)
    return dict(receipt, path=str(destination), size=published["size"], sha256=published["sha256"])


def inspect_recovery(archive, *, task_id, target, seed, run_id=None):
    verify_persisted_zip(archive)
    with zipfile.ZipFile(archive) as handle:
        receipt = json.loads(handle.read(f"{ROOT_NAME}/RECOVERY.json"))
    expected = {"schema": "SEQLOGAD-RECOVERY-1", "task_id": task_id,
                "target": target, "seed": seed, "base_weights_included": False}
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise ValueError("recovery identity mismatch")
    if run_id is not None and receipt.get("run_id") != run_id:
        raise ValueError("recovery run_id mismatch")
    return receipt


def restore_recovery(archive, output_run_directory, *, task_id, target, seed, run_id):
    receipt = inspect_recovery(archive, task_id=task_id, target=target, seed=seed, run_id=run_id)
    output = Path(output_run_directory)
    if output.exists():
        raise ValueError("local run directory exists while restoring persistent recovery")
    with tempfile.TemporaryDirectory() as folder:
        with zipfile.ZipFile(archive) as handle:
            handle.extractall(folder)
        source = Path(folder) / ROOT_NAME / "run"
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, output)
    latest = output / "checkpoints" / receipt["latest_checkpoint"]
    if not latest.is_dir():
        raise ValueError("restored latest checkpoint missing")
    return latest, receipt
