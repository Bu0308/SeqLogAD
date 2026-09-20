import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import pytest

from seqlogad.phase2_execution import archive, persistence, recovery, runner
from seqlogad.phase2_execution.specs import TARGETS, deterministic_run_id, load_development_spec


ROOT = Path(__file__).parents[1]
NOTEBOOKS = {
    "P2.1": "P2.1_run_all_semantic_s42.ipynb",
    "P2.2": "P2.2_run_all_sequence_lora_s42.ipynb",
    "P2.3": "P2.3_run_all_lightweight_sequence_s42.ipynb",
    "P2.4": "P2.4_run_all_gtat_s42.ipynb",
}


def _tree(tmp_path, name="payload", value="ok"):
    root = tmp_path / name
    root.mkdir()
    (root / "value.txt").write_text(value)
    archive.seal_tree(root)
    return root


def _run_tree(output_root, target, task_id="P2.1", expert_id="SEMANTIC_LLAMA"):
    fold = f"FOLD-TARGET-ARCH-{target}"
    run_id = deterministic_run_id(task_id, target)
    run = output_root / fold / expert_id / run_id
    checkpoint = run / "checkpoints" / "step-100"
    (checkpoint / "adapter").mkdir(parents=True)
    (checkpoint / "adapter" / "adapter_model.safetensors").write_bytes(b"adapter")
    (checkpoint / "state.pt").write_bytes(b"state")
    (checkpoint / "manifest.json").write_text("{}")
    archive.seal_tree(checkpoint)
    (run / "config.yaml").write_text("{}")
    (run / "metrics.json").write_text("{}")
    (run / "manifest.json").write_text(json.dumps({
        "completion_status": "TRAINING_COMPLETED_REQUIRES_REVIEW",
        "real_training_completed": True,
        "best_checkpoint": "step-100",
    }))
    return run


def test_development_amendment_locks_seed_targets_and_preserves_blockers():
    spec = load_development_spec(ROOT)
    assert spec["seed"] == 42
    assert tuple(spec["targets"]) == TARGETS == ("BGL", "HDFS", "HADOOP")
    assert spec["confirmation_seeds_deferred"] == [3407, 8675309]
    assert spec["source_label_status"] == "UNRESOLVED_DENY"
    assert spec["anomaly_labels_allowed"] is False
    assert spec["experts"]["P2.1"]["implementation_status"] == "READY"
    assert spec["experts"]["P2.2"]["implementation_status"] == "READY"
    assert all(spec["experts"][task]["implementation_status"] == "BLOCKED"
               for task in ("P2.3", "P2.4"))


def test_run_ids_are_deterministic_and_seed_42_only():
    assert deterministic_run_id("P2.1", "BGL") == "P2.1-FINAL-BGL-S42"
    assert deterministic_run_id("P2.2", "HDFS") == "P2.2-DEVELOPMENT-HDFS-S42"
    with pytest.raises(ValueError):
        deterministic_run_id("P2.1", "BGL", 3407)
    with pytest.raises(ValueError):
        deterministic_run_id("P2.1", "OPENSTACK")


def test_all_notebooks_parse_compile_and_keep_orchestration_thin():
    for task, name in NOTEBOOKS.items():
        notebook = json.loads((ROOT / "notebooks" / name).read_text())
        assert notebook["nbformat"] == 4
        assert all(not cell.get("outputs") for cell in notebook["cells"])
        code = "\n".join("".join(cell["source"]) for cell in notebook["cells"]
                         if cell["cell_type"] == "code")
        compile(code, name, "exec")
        assert 'SEED = 42' in code
        assert 'TARGETS = ["BGL", "HDFS", "HADOOP"]' in code
        assert "seqlogad.phase2_execution.cli" in code
        assert "3407" not in code and "8675309" not in code
        if task in {"P2.1", "P2.2"}:
            assert 'NOTEBOOK_STATUS = "READY"' in code
            assert 'REQUIRED_GPU = "NVIDIA A40"' in code
            assert 'STATE_ROOT = Path("/workspace/SeqLogAD")' in code
            assert 'PERSISTENT_ROOT = STATE_ROOT' in code
            assert 'SESSION_ROOT = Path("/tmp/seqlogad_sessions")' in code
            assert 'OUTPUT_ROOT = str(SESSION_ROOT / "seqlogad_outputs")' in code
            assert "google.colab" not in code
            assert "drive.mount" not in code
            assert 'os.environ.get("HF_TOKEN")' in code
            assert '"--persistent-root", str(PERSISTENT_ROOT)' in code
            assert 'print("SAFE_TO_STOP_RUNTIME=YES")' in code
            if task == "P2.2":
                assert 'TASK_ID = "P2.2"' in code
                assert 'DATA_ROOT = str(RUNTIME_ROOT / "phase2_sequence")' in code
                assert 'UV_FIX=PASS' in code
        else:
            assert 'NOTEBOOK_STATUS = \'BLOCKED\'' in code
            assert "drive.mount" in code
            assert "SAFE_TO_DISCONNECT_COLAB=YES only if" in code


def test_secure_zip_roundtrip_and_clean_extraction(tmp_path):
    source = _tree(tmp_path)
    path = tmp_path / "payload.zip"
    result = archive.create_zip(source, path)
    assert result["zip_integrity"] == "PASS"
    assert archive.verify_zip(path)["sha256"] == result["sha256"]
    with zipfile.ZipFile(path) as handle:
        handle.extractall(tmp_path / "extracted")
    archive.verify_tree_ledger(tmp_path / "extracted" / "payload")
    (source / "value.txt").touch()
    repeated = archive.create_zip(source, tmp_path / "payload-repeated.zip")
    assert repeated["sha256"] == result["sha256"]


def test_zip_rejects_duplicate_traversal_symlink_secret_and_base_weights(tmp_path):
    duplicate = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(duplicate, "w") as handle:
        handle.writestr("root/a", b"1")
        handle.writestr("root/a", b"2")
    with pytest.raises(ValueError, match="duplicate"):
        archive.verify_zip(duplicate, require_ledger=False)

    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as handle:
        handle.writestr("../a", b"1")
    with pytest.raises(ValueError, match="unsafe"):
        archive.verify_zip(traversal, require_ledger=False)

    symlink = tmp_path / "symlink.zip"
    with zipfile.ZipFile(symlink, "w") as handle:
        info = zipfile.ZipInfo("root/link")
        info.external_attr = (0o120777 << 16)
        handle.writestr(info, "target")
    with pytest.raises(ValueError, match="symlink"):
        archive.verify_zip(symlink, require_ledger=False)

    secret = _tree(tmp_path, "secret", "hf_abcdefghijklmnopqrstuvwxyz123456")
    with pytest.raises(ValueError, match="token"):
        archive.create_zip(secret, tmp_path / "secret.zip")

    weights = tmp_path / "weights"
    weights.mkdir()
    (weights / "model.safetensors").write_bytes(b"base")
    archive.seal_tree(weights)
    with pytest.raises(ValueError, match="forbidden"):
        archive.create_zip(weights, tmp_path / "weights.zip")


def test_atomic_drive_copy_and_sha_mismatch_detection(tmp_path):
    source = _tree(tmp_path, "source")
    local = tmp_path / "local.zip"
    archive.create_zip(source, local)
    destination = tmp_path / "drive" / "artifact.zip"
    first = persistence.publish_atomic(local, destination)
    assert persistence.verify_persisted_zip(destination)["sha256"] == first["sha256"]
    destination.write_bytes(destination.read_bytes() + b"corrupt")
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        persistence.verify_persisted_zip(destination)


def test_recovery_is_bounded_atomic_and_restores_early_state_files(tmp_path):
    run = _run_tree(tmp_path / "outputs", "HDFS")
    (run / "logs").mkdir()
    (run / "logs" / "train.jsonl").write_text('{"step": 100}\n')
    destination = tmp_path / "drive" / "LATEST_RECOVERY.zip"
    receipt = recovery.create_recovery(
        run, run / "checkpoints/step-100", destination,
        task_id="P2.1", target="HDFS", seed=42, best_checkpoint="step-100",
    )
    assert receipt["latest_step"] == 100
    assert not Path(str(destination) + ".previous").exists()
    restored = tmp_path / "restored" / "FOLD-TARGET-ARCH-HDFS" / "SEMANTIC_LLAMA" / run.name
    checkpoint, metadata = recovery.restore_recovery(
        destination, restored, task_id="P2.1", target="HDFS", seed=42, run_id=run.name,
    )
    assert checkpoint.name == "step-100"
    assert (checkpoint / "state.pt").is_file()
    assert metadata["best_checkpoint"] == "step-100"


def test_corrupt_or_wrong_identity_recovery_is_rejected(tmp_path):
    run = _run_tree(tmp_path / "outputs", "HDFS")
    destination = tmp_path / "drive" / "LATEST_RECOVERY.zip"
    recovery.create_recovery(run, run / "checkpoints/step-100", destination,
                             task_id="P2.1", target="HDFS", seed=42,
                             best_checkpoint="step-100")
    with pytest.raises(ValueError, match="identity"):
        recovery.inspect_recovery(destination, task_id="P2.1", target="HADOOP", seed=42)
    destination.write_bytes(destination.read_bytes() + b"broken")
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        recovery.inspect_recovery(destination, task_id="P2.1", target="HDFS", seed=42)


def test_recovery_replaces_previous_snapshot_and_keeps_latest_plus_best(tmp_path):
    run = _run_tree(tmp_path / "outputs", "HDFS")
    second = run / "checkpoints" / "step-200"
    shutil.copytree(run / "checkpoints" / "step-100", second)
    (second / "checksums.sha256").unlink()
    (second / "state.pt").write_bytes(b"state-200")
    archive.seal_tree(second)
    destination = tmp_path / "drive" / "LATEST_RECOVERY.zip"
    recovery.create_recovery(run, run / "checkpoints/step-100", destination,
                             task_id="P2.1", target="HDFS", seed=42,
                             best_checkpoint="step-100")
    receipt = recovery.create_recovery(run, second, destination,
                                       task_id="P2.1", target="HDFS", seed=42,
                                       best_checkpoint="step-100")
    assert receipt["latest_checkpoint"] == "step-200"
    assert not Path(str(destination) + ".previous").exists()
    with zipfile.ZipFile(destination) as handle:
        checkpoints = {
            Path(name).parts[3]
            for name in handle.namelist()
            if name.startswith("seqlogad_recovery/run/checkpoints/")
            and len(Path(name).parts) > 3
        }
    assert checkpoints == {"step-100", "step-200"}


def test_semantic_external_bgl_registration_is_exact_and_requires_no_historical_zip(tmp_path):
    spec = load_development_spec(ROOT)["experts"]["P2.1"]
    registration = spec["external_registrations"]["BGL"]
    assert registration["run_id"] == "P2.1-FINAL-BGL-S42"
    assert registration["selected_checkpoint"] == "step-800"
    assert registration["historical_artifact_required_for_skip"] is False
    state, _ = runner.inspect_target("P2.1", "BGL", tmp_path, registration)
    assert state == "REGISTERED_EXTERNALLY"


def test_external_registration_is_repeatable_but_corruption_fails_closed(tmp_path):
    registration = load_development_spec(ROOT)["experts"]["P2.1"]["external_registrations"]["BGL"]
    path = runner._paths(tmp_path, "P2.1", "BGL")["registration"]
    receipt = dict(registration, schema="SEQLOGAD-EXTERNAL-REGISTRATION-1",
                   task_id="P2.1", target="BGL", seed=42,
                   artifact_embedded=False,
                   integrity="REGISTERED_BY_IMMUTABLE_DIGEST")
    runner._json_atomic(path, receipt)
    assert runner.inspect_target("P2.1", "BGL", tmp_path, registration)[0] == "REGISTERED_EXTERNALLY"
    path.write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        runner.inspect_target("P2.1", "BGL", tmp_path, registration)


def test_completed_skip_recovery_state_and_ambiguous_sidecar_fail_closed(tmp_path):
    paths = runner._paths(tmp_path, "P2.1", "HDFS")
    source = _tree(tmp_path, "target")
    local = tmp_path / "target.zip"
    archive.create_zip(source, local)
    persistence.publish_atomic(local, paths["target_zip"])
    state, _ = runner.inspect_target("P2.1", "HDFS", tmp_path)
    assert state == "COMPLETED"
    paths["target_zip"].unlink()
    with pytest.raises(ValueError, match="sidecar"):
        runner.inspect_target("P2.1", "HDFS", tmp_path)


def test_blocked_experts_stop_before_training(tmp_path):
    for task in ("P2.3", "P2.4"):
        with pytest.raises(runner.ExecutionBlocked):
            runner.run_all_targets(
                task_id=task, repo_root=ROOT, data_root=tmp_path,
                output_root=tmp_path / "out", drive_root=tmp_path / "drive",
                expected_bundle_sha256="0" * 64,
            )


def test_failure_isolation_stops_before_next_target(monkeypatch, tmp_path):
    bundle = tmp_path / "data" / "manifests"
    bundle.mkdir(parents=True)
    (bundle / "bundle.json").write_text("{}")
    digest = hashlib.sha256(b"{}").hexdigest()
    monkeypatch.setattr(runner, "_validate_semantic_data", lambda *_: {})
    monkeypatch.setenv("HF_TOKEN", "test-token-not-a-huggingface-secret")
    calls = []

    def fail(*args, **kwargs):
        calls.append(args[3])
        raise RuntimeError("intentional")

    monkeypatch.setattr(runner, "_semantic_train", fail)
    with pytest.raises(RuntimeError, match="intentional"):
        runner.run_all_targets(
            task_id="P2.1", repo_root=ROOT, data_root=tmp_path / "data",
            output_root=tmp_path / "out", drive_root=tmp_path / "drive",
            expected_bundle_sha256=digest,
        )
    assert calls == ["HDFS"]  # BGL is external; Hadoop is never reached.


def test_successful_semantic_wave_packages_each_target_and_opens_safe_gate(monkeypatch, tmp_path):
    bundle = tmp_path / "data" / "manifests"
    bundle.mkdir(parents=True)
    (bundle / "bundle.json").write_text("{}")
    digest = hashlib.sha256(b"{}").hexdigest()
    monkeypatch.setattr(runner, "_validate_semantic_data", lambda *_: {})
    monkeypatch.setenv("HF_TOKEN", "test-token-not-a-huggingface-secret")

    def complete(repo_root, data_root, output_root, target, expected_bundle_sha256,
                 resume_from, recovery_destination):
        run = _run_tree(Path(output_root), target)
        return {"run_directory": str(run), "metrics": {}}

    monkeypatch.setattr(runner, "_semantic_train", complete)
    result = runner.run_all_targets(
        task_id="P2.1", repo_root=ROOT, data_root=tmp_path / "data",
        output_root=tmp_path / "out", drive_root=tmp_path / "drive",
        expected_bundle_sha256=digest,
    )
    assert result["safe_to_disconnect_colab"] is True
    assert result["targets"]["BGL"]["status"] == "REGISTERED_EXTERNALLY"
    assert result["targets"]["HDFS"]["status"] == "COMPLETED"
    assert result["targets"]["HADOOP"]["status"] == "COMPLETED"
    final = tmp_path / "drive/P2.1/seqlogad_outputs_P2.1_S42_FINAL.zip"
    assert persistence.verify_persisted_zip(final)["zip_integrity"] == "PASS"


def test_successful_sequence_wave_trains_all_targets_without_semantic_registration(monkeypatch, tmp_path):
    bundle = tmp_path / "data" / "manifests"
    bundle.mkdir(parents=True)
    (bundle / "bundle.json").write_text("{}")
    digest = hashlib.sha256(b"{}").hexdigest()
    monkeypatch.setattr(runner, "_validate_sequence_data", lambda *_: {})
    monkeypatch.setenv("HF_TOKEN", "test-token-not-a-huggingface-secret")
    calls = []

    def complete(repo_root, data_root, output_root, target, expected_bundle_sha256,
                 resume_from, recovery_destination):
        calls.append(target)
        run = _run_tree(Path(output_root), target, "P2.2", "SEQUENCE_LLAMA_REFERENCE")
        return {"run_directory": str(run), "metrics": {}}

    monkeypatch.setattr(runner, "_sequence_train", complete)
    result = runner.run_all_targets(
        task_id="P2.2", repo_root=ROOT, data_root=tmp_path / "data",
        output_root=tmp_path / "out", drive_root=tmp_path / "drive",
        expected_bundle_sha256=digest,
    )
    assert calls == ["BGL", "HDFS", "HADOOP"]
    assert all(result["targets"][target]["status"] == "COMPLETED" for target in calls)
    final = tmp_path / "drive/P2.2/seqlogad_outputs_P2.2_S42_FINAL.zip"
    assert persistence.verify_persisted_zip(final)["zip_integrity"] == "PASS"


def test_parallel_expert_namespaces_and_no_checkpoint_dependency():
    spec = load_development_spec(ROOT)
    execution = spec["execution"]
    assert execution["experts_may_use_separate_gpu_runtimes"] is True
    assert execution["primary_runtime"] == "RUNPOD"
    assert execution["required_gpu_for_p2_1"] == "NVIDIA_A40_48GB_NATIVE_BF16"
    assert execution["required_gpu_for_p2_2"] == "NVIDIA_A40_48GB_NATIVE_BF16"
    assert execution["persistent_root"] == "/workspace/SeqLogAD"
    assert execution["active_root"] == "/tmp/seqlogad_outputs"
    assert spec["execution"]["cross_expert_checkpoint_reuse"] is False
    assert len({str(Path("SeqLogAD") / task) for task in spec["experts"]}) == 4
    for task, expert in spec["experts"].items():
        assert expert["final_zip"].startswith(f"seqlogad_outputs_{task}_")
