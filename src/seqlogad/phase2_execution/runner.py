"""Sequential three-target execution with persistent fail-closed recovery."""
from __future__ import annotations

import gc
import hashlib
import json
import os
import shutil
from pathlib import Path

from seqlogad.common.checksum import sha256_file

from .artifacts import package_expert, package_target, write_external_registration
from .persistence import publish_atomic, verify_persisted_zip
from .recovery import create_recovery, inspect_recovery, restore_recovery
from .specs import FOLDS, TARGETS, deterministic_run_id, load_development_spec


class ExecutionBlocked(RuntimeError):
    pass


def _json_atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + ".partial")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    digest = sha256_file(temporary)
    os.replace(temporary, path)
    Path(str(path) + ".sha256").write_text(f"{digest}  {path.name}\n")
    if sha256_file(path) != digest:
        raise ValueError("atomic JSON persistence verification failed")
    return path


def _verify_json(path):
    path = Path(path)
    sidecar = Path(str(path) + ".sha256")
    if not path.is_file() or not sidecar.is_file():
        raise ValueError("persistent JSON or checksum sidecar missing")
    digest, name = sidecar.read_text().strip().split("  ", 1)
    if name != path.name or digest != sha256_file(path):
        raise ValueError("persistent JSON checksum mismatch")
    return json.loads(path.read_text())


def _paths(drive_root, task_id, target):
    root = Path(drive_root) / task_id
    return {
        "root": root,
        "target_zip": root / "targets" / f"{task_id}_{target}_S42.zip",
        "recovery_zip": root / "recovery" / target / "LATEST_RECOVERY.zip",
        "registration": root / "targets" / f"{target}-REGISTERED_EXTERNALLY.json",
    }


def inspect_target(task_id, target, drive_root, registration=None):
    paths = _paths(drive_root, task_id, target)
    run_id = deterministic_run_id(task_id, target)
    if registration is not None:
        if paths["target_zip"].exists() or paths["recovery_zip"].exists():
            raise ValueError("external registration conflicts with persisted target state")
        if paths["registration"].exists():
            receipt = _verify_json(paths["registration"])
            expected = dict(
                registration,
                schema="SEQLOGAD-EXTERNAL-REGISTRATION-1",
                task_id=task_id,
                target=target,
                seed=42,
                artifact_embedded=False,
                integrity="REGISTERED_BY_IMMUTABLE_DIGEST",
            )
            if receipt != expected:
                raise ValueError("persistent external registration does not match the frozen amendment")
        elif Path(str(paths["registration"]) + ".sha256").exists():
            raise ValueError("external registration sidecar exists without registration")
        return "REGISTERED_EXTERNALLY", paths
    if paths["target_zip"].exists():
        verify_persisted_zip(paths["target_zip"])
        return "COMPLETED", paths
    if Path(str(paths["target_zip"]) + ".sha256").exists():
        raise ValueError("target ZIP sidecar exists without target ZIP")
    if paths["recovery_zip"].exists():
        inspect_recovery(paths["recovery_zip"], task_id=task_id, target=target,
                         seed=42, run_id=run_id)
        return "INCOMPLETE", paths
    if Path(str(paths["recovery_zip"]) + ".sha256").exists():
        raise ValueError("recovery sidecar exists without recovery ZIP")
    return "NOT_STARTED", paths


def _validate_semantic_data(data_root, expected_bundle_sha256):
    from seqlogad.semantic.contracts import validate_bundle
    return {
        target: validate_bundle(data_root, FOLDS[target], expected_bundle_sha256)
        for target in TARGETS
    }


def _validate_sequence_data(data_root, expected_bundle_sha256):
    from seqlogad.sequence.contracts import validate_bundle
    return {
        target: validate_bundle(data_root, FOLDS[target], expected_bundle_sha256)
        for target in TARGETS
    }


def _semantic_train(repo_root, data_root, output_root, target, expected_bundle_sha256,
                    resume_from, recovery_destination):
    from seqlogad.semantic.train import run_training

    def checkpoint_callback(run, checkpoint, best_checkpoint):
        receipt = create_recovery(
            run, checkpoint, recovery_destination,
            task_id="P2.1", target=target, seed=42, best_checkpoint=best_checkpoint,
        )
        print("PERSISTENT_BACKUP=PASS", flush=True)
        print("BACKUP_TO_DRIVE=PASS", flush=True)
        print(f"PATH={receipt['path']}", flush=True)
        print(f"SIZE={receipt['size']}", flush=True)
        print(f"SHA256={receipt['sha256']}", flush=True)

    return run_training(
        repo_root, data_root, output_root, FOLDS[target],
        deterministic_run_id("P2.1", target),
        overrides={"seed": 42, "training_mode": "QLORA_NF4_DOUBLE_QUANT"},
        resume_from=str(resume_from) if resume_from else None,
        expected_bundle_sha256=expected_bundle_sha256,
        run_mode="final",
        checkpoint_callback=checkpoint_callback,
    )


def _sequence_train(repo_root, data_root, output_root, target, expected_bundle_sha256,
                    resume_from, recovery_destination):
    from seqlogad.sequence.train import run_training

    def checkpoint_callback(run, checkpoint, best_checkpoint):
        receipt = create_recovery(
            run, checkpoint, recovery_destination,
            task_id="P2.2", target=target, seed=42, best_checkpoint=best_checkpoint,
        )
        print("PERSISTENT_BACKUP=PASS", flush=True)
        print(f"PATH={receipt['path']}", flush=True)
        print(f"SIZE={receipt['size']}", flush=True)
        print(f"SHA256={receipt['sha256']}", flush=True)

    return run_training(
        repo_root, data_root, output_root, FOLDS[target],
        deterministic_run_id("P2.2", target),
        overrides={"seed": 42, "training_mode": "QLORA_NF4_DOUBLE_QUANT"},
        resume_from=str(resume_from) if resume_from else None,
        expected_bundle_sha256=expected_bundle_sha256,
        run_mode="development",
        checkpoint_callback=checkpoint_callback,
    )


def cleanup_gpu():
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            free, total = torch.cuda.mem_get_info()
            return {"cuda": True, "free_vram_bytes": free, "total_vram_bytes": total}
    except ImportError:
        pass
    return {"cuda": False}


def run_all_targets(*, task_id, repo_root, data_root, output_root, drive_root,
                    expected_bundle_sha256):
    repo_root, data_root = Path(repo_root), Path(data_root)
    output_root, drive_root = Path(output_root), Path(drive_root)
    amendment = load_development_spec(repo_root)
    spec = amendment["experts"][task_id]
    if spec["implementation_status"] != "READY":
        blockers = ", ".join(spec.get("blockers", []))
        raise ExecutionBlocked(f"{task_id} is fail-closed: {blockers}")
    if task_id not in {"P2.1", "P2.2"}:
        raise ExecutionBlocked(f"{task_id} has no authoritative real trainer")
    if not expected_bundle_sha256:
        raise ValueError("trusted data bundle SHA-256 is required")
    if sha256_file(data_root / "manifests/bundle.json") != expected_bundle_sha256:
        raise ValueError("data bundle SHA-256 mismatch")
    if task_id == "P2.1":
        _validate_semantic_data(data_root, expected_bundle_sha256)
        trainer = _semantic_train
    else:
        _validate_sequence_data(data_root, expected_bundle_sha256)
        trainer = _sequence_train
    if spec["requires_hf_token"] and not os.environ.get("HF_TOKEN"):
        raise ValueError("HF_TOKEN must come from the runtime secret/environment")

    local_export = output_root / "exports" / task_id
    local_export.mkdir(parents=True, exist_ok=True)
    target_results, target_archives, registrations = {}, {}, {}
    for target in TARGETS:
        registration = spec.get("external_registrations", {}).get(target)
        state, paths = inspect_target(task_id, target, drive_root, registration)
        run_id = deterministic_run_id(task_id, target)
        run_directory = output_root / FOLDS[target] / spec["expert_id"] / run_id
        if state == "REGISTERED_EXTERNALLY":
            local_receipt = write_external_registration(local_export, task_id, target, 42, registration)
            persisted = _json_atomic(paths["registration"], json.loads(local_receipt.read_text()))
            _verify_json(persisted)
            registrations[target] = persisted
            target_results[target] = {"status": state, "run_id": run_id}
            print(f"{target}=SKIP_REGISTERED_EXTERNALLY", flush=True)
            continue
        if state == "COMPLETED":
            target_archives[target] = paths["target_zip"]
            target_results[target] = {"status": "SKIPPED_COMPLETED", "run_id": run_id}
            print(f"{target}=SKIP_COMPLETED_VERIFIED", flush=True)
            continue

        resume_from = None
        resumed = False
        if state == "INCOMPLETE":
            if run_directory.exists():
                raise ValueError("ambiguous local run and persistent recovery both exist")
            resume_from, receipt = restore_recovery(
                paths["recovery_zip"], run_directory,
                task_id=task_id, target=target, seed=42, run_id=run_id,
            )
            resumed = True
            print(f"{target}=RESUME_STEP_{receipt['latest_step']}", flush=True)
        elif run_directory.exists():
            raise ValueError("unsealed local run exists without trustworthy recovery")

        try:
            result = trainer(
                repo_root, data_root, output_root, target, expected_bundle_sha256,
                resume_from, paths["recovery_zip"],
            )
            run_directory = Path(result["run_directory"])
            local_target = local_export / paths["target_zip"].name
            package_target(run_directory, local_target)
            persisted = publish_atomic(local_target, paths["target_zip"])
            verify_persisted_zip(paths["target_zip"])
        except Exception:
            print("RUN_COMPLETED_BUT_BACKUP_FAILED_OR_TRAINING_FAILED", flush=True)
            raise
        target_archives[target] = paths["target_zip"]
        target_results[target] = {
            "status": "RESUMED_AND_COMPLETED" if resumed else "COMPLETED",
            "run_id": run_id,
            "target_zip": str(paths["target_zip"]),
            "target_zip_sha256": persisted["sha256"],
        }
        print("PERSISTENT_BACKUP=PASS", flush=True)
        print("BACKUP_TO_DRIVE=PASS", flush=True)
        print(f"PATH={paths['target_zip']}", flush=True)
        print(f"SIZE={persisted['size']}", flush=True)
        print(f"SHA256={persisted['sha256']}", flush=True)
        print(json.dumps(cleanup_gpu(), sort_keys=True), flush=True)

    complete_states = {"REGISTERED_EXTERNALLY", "SKIPPED_COMPLETED", "COMPLETED", "RESUMED_AND_COMPLETED"}
    safe = len(target_results) == len(TARGETS) and all(
        item["status"] in complete_states for item in target_results.values()
    )
    if not safe:
        raise ValueError("not all targets are durably complete or externally registered")
    summary = {
        "schema": "SEQLOGAD-ONECLICK-SUMMARY-1",
        "task_id": task_id,
        "expert_id": spec["expert_id"],
        "run_mode": "development",
        "seed": 42,
        "targets": target_results,
        "source_label_status": amendment["source_label_status"],
        "multi_seed_stability": "NOT_CLAIMED",
        "scientific_result": "NOT_EVALUATED",
        "safe_to_stop_runtime": True,
        "safe_to_disconnect_colab": True,
    }
    final_local = local_export / spec["final_zip"]
    package_expert(task_id, 42, spec["final_zip"], target_archives, registrations,
                   summary, final_local)
    final_drive = Path(drive_root) / task_id / spec["final_zip"]
    final = publish_atomic(final_local, final_drive)
    verify_persisted_zip(final_drive)
    _json_atomic(Path(drive_root) / task_id / "SUMMARY.json", summary)
    print("FINAL_PERSISTENT_BACKUP=PASS", flush=True)
    print("FINAL_BACKUP_TO_DRIVE=PASS", flush=True)
    print(f"FINAL_DRIVE_PATH={final_drive}", flush=True)
    print(f"FINAL_DRIVE_SHA256={final['sha256']}", flush=True)
    print("SAFE_TO_STOP_RUNTIME=YES", flush=True)
    print("SAFE_TO_DISCONNECT_COLAB=YES", flush=True)
    return dict(summary, final_zip=str(final_local), final_zip_size=final["size"],
                final_zip_sha256=final["sha256"], final_drive_path=str(final_drive))
