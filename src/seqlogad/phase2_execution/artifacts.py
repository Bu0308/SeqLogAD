"""Per-target and per-expert scientific artifact exports."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from .archive import copy_tree_selected, create_zip, seal_tree


def package_target(run_directory, destination):
    run = Path(run_directory)
    manifest_path = run / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("completed run manifest missing")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("completion_status") != "TRAINING_COMPLETED_REQUIRES_REVIEW":
        raise ValueError("run is not completed")
    if manifest.get("real_training_completed") is not True:
        raise ValueError("future run metadata must mark real training completed")
    selected_name = manifest.get("best_checkpoint")
    selected = run / "checkpoints" / selected_name
    if not selected.is_dir():
        raise ValueError("selected checkpoint missing")
    with tempfile.TemporaryDirectory() as folder:
        stage = Path(folder) / run.name
        copy_tree_selected(run, stage, exclude_top={"checkpoints"})
        (stage / "checksums.sha256").unlink(missing_ok=True)
        shutil.copytree(selected, stage / "checkpoints" / selected.name)
        seal_tree(stage)
        return create_zip(stage, destination, run.name)


def write_external_registration(directory, task_id, target, seed, registration):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    required = {"run_id", "status", "selected_checkpoint", "adapter_sha256",
                "historical_archive_sha256", "historical_artifact_required_for_skip"}
    if set(registration) != required or registration["status"] != "PASS":
        raise ValueError("external registration is incomplete")
    receipt = dict(registration, schema="SEQLOGAD-EXTERNAL-REGISTRATION-1",
                   task_id=task_id, target=target, seed=seed,
                   artifact_embedded=False, integrity="REGISTERED_BY_IMMUTABLE_DIGEST")
    path = directory / f"{target}-REGISTERED_EXTERNALLY.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return path


def package_expert(task_id, seed, final_name, target_artifacts, registrations,
                   summary, destination):
    if seed != 42:
        raise ValueError("development expert package is seed-42 only")
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder) / f"{task_id}_S42"
        (root / "targets").mkdir(parents=True)
        for target, archive in sorted(target_artifacts.items()):
            shutil.copy2(archive, root / "targets" / Path(archive).name)
            sidecar = Path(str(archive) + ".sha256")
            if sidecar.is_file():
                shutil.copy2(sidecar, root / "targets" / sidecar.name)
        for target, receipt in sorted(registrations.items()):
            shutil.copy2(receipt, root / "targets" / Path(receipt).name)
        (root / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        seal_tree(root)
        result = create_zip(root, destination, root.name)
    if Path(destination).name != final_name:
        raise ValueError("final expert ZIP name differs from frozen development amendment")
    return result
