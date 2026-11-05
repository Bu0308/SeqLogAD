"""Fail-closed artifact verification and implementation-identity protection."""
import json
import zipfile
from pathlib import Path

import pytest

from seqlogad.common.checksum import sha256_file
from seqlogad.fusion.artifacts import assert_same_base, prepare_expert, safe_extract
from seqlogad.semantic.checkpoint import seal
from seqlogad.sequence.implementation import implementation_digest

REPO = Path(__file__).resolve().parents[2]
V13R1_IMPLEMENTATION = "78a188515d5a74b4ca1bf9c5b763e6e92281ba5746ff22c29e488dbf93dce3e3"


def test_fusion_package_does_not_change_sequence_identity():
    assert implementation_digest(REPO) == V13R1_IMPLEMENTATION


def _checkpoint(root: Path, step: int, identity: dict) -> None:
    folder = root / f"step-{step}"
    (folder / "adapter").mkdir(parents=True)
    (folder / "adapter/adapter_model.safetensors").write_bytes(f"adapter{step}".encode())
    (folder / "state.pt").write_bytes(b"state")
    (folder / "manifest.json").write_text(json.dumps({"identity": identity}))
    seal(folder)


def _zip(folder: Path, archive: Path, arcroot: str) -> Path:
    with zipfile.ZipFile(archive, "w") as handle:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                handle.write(path, f"{arcroot}/{path.relative_to(folder).as_posix()}")
    Path(str(archive) + ".sha256").write_text(f"{sha256_file(archive)}  {archive.name}\n")
    return archive


def _expert_archives(tmp: Path, kind: str, identity: dict, *, tamper: bool = False):
    run = tmp / "build/run"
    _checkpoint(run / "checkpoints", 100, identity)
    (run / "logs").mkdir()
    (run / "logs/train.jsonl").write_text("")
    (run / "metrics.json").write_text("{}")
    (run / "config.yaml").write_text(json.dumps({"model_id": "m", "model_revision": "r",
                                                 "tokenizer_id": "m", "tokenizer_revision": "r"}))
    (run / "manifest.json").write_text(json.dumps({
        "fold_id": "FOLD-TARGET-ARCH-HDFS", "real_training_completed": True, "seed": 42,
        "identity": identity, "best_checkpoint": "step-100", "run_id": f"{kind}-run",
        "precision": "torch.bfloat16", "semantic_adapter_used": False}))
    target = _zip(run, tmp / f"{kind}_target.zip", "RUN")
    rec = tmp / "build/rec"
    _checkpoint(rec / "run/checkpoints", 100, identity)
    _checkpoint(rec / "run/checkpoints", 400, identity)
    if tamper:
        (rec / "run/checkpoints/step-400/adapter/adapter_model.safetensors").write_bytes(b"evil")
    (rec / "RECOVERY.json").write_text(json.dumps({"fold_id": "FOLD-TARGET-ARCH-HDFS",
                                                   "best_checkpoint": "step-100", "latest_checkpoint": "step-400",
                                                   "latest_step": 400}))
    recovery = _zip(rec, tmp / f"{kind}_recovery.zip", "seqlogad_recovery")
    return target, recovery


def test_semantic_bridge_trusts_frozen_identity(tmp_path):
    target, recovery = _expert_archives(tmp_path, "semantic", {"config_sha256": "frozen"})
    expert = prepare_expert("semantic", "FOLD-TARGET-ARCH-HDFS", target, recovery, tmp_path / "w", REPO)
    assert expert["checkpoints"]["best"]["step"] == 100 and expert["checkpoints"]["latest"]["step"] == 400
    assert_same_base([expert, expert])


def test_tampered_latest_checkpoint_is_rejected(tmp_path):
    target, recovery = _expert_archives(tmp_path, "semantic", {"config_sha256": "frozen"}, tamper=True)
    with pytest.raises(ValueError, match="checksum"):
        prepare_expert("semantic", "FOLD-TARGET-ARCH-HDFS", target, recovery, tmp_path / "w", REPO)


def test_sequence_requires_trained_implementation_digest(tmp_path):
    target, recovery = _expert_archives(tmp_path, "sequence", {"implementation_sha256": "other"})
    with pytest.raises(ValueError, match="implementation"):
        prepare_expert("sequence", "FOLD-TARGET-ARCH-HDFS", target, recovery, tmp_path / "w", REPO)


def test_archive_sidecar_and_unsafe_member_rejected(tmp_path):
    target, recovery = _expert_archives(tmp_path, "semantic", {"config_sha256": "frozen"})
    Path(str(target) + ".sha256").write_text(f"{'0' * 64}  {target.name}\n")
    with pytest.raises(ValueError, match="checksum mismatch"):
        prepare_expert("semantic", "FOLD-TARGET-ARCH-HDFS", target, recovery, tmp_path / "w", REPO)
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as handle:
        handle.writestr("../escape.txt", "x")
    with pytest.raises(ValueError, match="unsafe"):
        safe_extract(evil, tmp_path / "out")
