"""Verified extraction of trained expert runs (best from target ZIP, latest from recovery ZIP).

Semantic bridge: ``SemanticExpert.from_checkpoint`` recomputes the config hash
after ``config.yaml`` was annotated with ``real_training_completed`` and so
rejects valid runs (reproduced: manifest 6a1baa87..., recomputed 866364ba...).
Like ``SequenceExpert`` this bridge trusts the frozen ``manifest['identity']``
plus the per-checkpoint checksum ledger, and never edits the hashed packages.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path, PurePosixPath

from seqlogad.common.checksum import sha256_file
from seqlogad.semantic.checkpoint import verify_checkpoint
from seqlogad.semantic.contracts import read

MODEL_KEYS = ("model_id", "model_revision", "tokenizer_id", "tokenizer_revision")


def verify_sidecar(path: Path) -> str:
    """Check ``<file>.sha256`` written as '<digest>  <name>' and return the digest."""
    sidecar = Path(str(path) + ".sha256")
    digest, name = sidecar.read_text().strip().split("  ", 1)
    if name != path.name or sha256_file(path) != digest:
        raise ValueError(f"checksum mismatch: {path.name}")
    return digest


def safe_extract(archive: Path, destination: Path) -> Path:
    if destination.exists():
        raise ValueError(f"refusing to overwrite extraction: {destination}")
    with zipfile.ZipFile(archive) as handle:
        if handle.testzip() is not None:
            raise ValueError(f"corrupt archive: {archive.name}")
        names = handle.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate archive member")
        for name in names:
            part = PurePosixPath(name)
            if part.is_absolute() or ".." in part.parts or "\\" in name:
                raise ValueError(f"unsafe archive member: {name}")
        destination.mkdir(parents=True)
        handle.extractall(destination)
    return destination


def _single_run(root: Path) -> Path:
    runs = [p.parent for p in root.glob("*/manifest.json")]
    if len(runs) != 1:
        raise ValueError("expected exactly one completed run in target archive")
    return runs[0]


def prepare_expert(kind: str, fold_id: str, target_zip: Path, recovery_zip: Path,
                   workdir: Path, repo_root: Path) -> dict:
    if kind not in {"semantic", "sequence"}:
        raise ValueError(kind)
    verify_sidecar(target_zip)
    verify_sidecar(recovery_zip)
    stem = f"{kind}-{fold_id}"
    run = _single_run(safe_extract(target_zip, workdir / f"{stem}-target"))
    recovery_root = safe_extract(recovery_zip, workdir / f"{stem}-recovery") / "seqlogad_recovery"
    manifest = read(run / "manifest.json")
    cfg = read(run / "config.yaml")
    receipt = json.loads((recovery_root / "RECOVERY.json").read_text())
    if manifest["fold_id"] != fold_id or receipt["fold_id"] != fold_id:
        raise ValueError("fold identity mismatch")
    if manifest.get("real_training_completed") is not True or manifest.get("seed") != 42:
        raise ValueError("incomplete or wrong-seed run")
    identity = manifest["identity"]
    best_name = manifest["best_checkpoint"]
    if receipt["best_checkpoint"] != best_name:
        raise ValueError("recovery best checkpoint differs from completed run")
    best = run / "checkpoints" / best_name
    latest = recovery_root / "run/checkpoints" / receipt["latest_checkpoint"]
    for checkpoint in (best, latest):
        verify_checkpoint(checkpoint, identity)
    recovery_best = recovery_root / "run/checkpoints" / best_name
    adapter = "adapter/adapter_model.safetensors"
    if sha256_file(recovery_best / adapter) != sha256_file(best / adapter):
        raise ValueError("best adapter differs between target and recovery archives")
    if kind == "sequence":
        from seqlogad.sequence.implementation import implementation_digest

        if identity.get("implementation_sha256") != implementation_digest(repo_root):
            raise ValueError("Sequence scoring code differs from the trained implementation")
        if manifest.get("semantic_adapter_used") is not False:
            raise ValueError("Sequence run does not prove adapter isolation")
    return {
        "kind": kind, "fold_id": fold_id, "run_id": manifest["run_id"], "cfg": cfg,
        "precision": manifest["precision"],
        "checkpoints": {
            "best": {"path": str(best), "step": int(best_name.split("-")[1]),
                     "adapter_sha256": sha256_file(best / adapter)},
            "latest": {"path": str(latest), "step": int(receipt["latest_step"]),
                       "adapter_sha256": sha256_file(latest / adapter)},
        },
        "target_zip_sha256": sha256_file(target_zip),
        "recovery_zip_sha256": sha256_file(recovery_zip),
        "train_log": str(run / "logs/train.jsonl"),
        "metrics": json.loads((run / "metrics.json").read_text()),
    }


def assert_same_base(experts: list[dict]) -> dict:
    reference = {key: experts[0]["cfg"][key] for key in MODEL_KEYS}
    for expert in experts[1:]:
        if any(expert["cfg"][key] != value for key, value in reference.items()):
            raise ValueError("experts were trained on different frozen bases")
    precisions = {expert["precision"] for expert in experts}
    if len(precisions) != 1:
        raise ValueError(f"experts were trained with different precision: {precisions}")
    return reference
