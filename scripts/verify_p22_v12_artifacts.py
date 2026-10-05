"""Verify the isolated V12 RunPod kit and retained V11 reference bytes."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V11_SHA256 = "bd3cb09f8fe8e726ef3bad7579efa877fed3bbca8970351fbe75d50fbdba2406"


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def verify_zip(path):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None, f"ZIP CRC failed: {path}"
        return set(archive.namelist())


def main():
    kit = ROOT / "outputs/runpod/P2.2-S42-A40-V12"
    outer = ROOT / "outputs/runpod/P2.2-S42-A40-V12-upload.zip"
    previous = ROOT / "outputs/runpod/P2.2-S42-A40-V11-upload.zip"
    assert digest(previous) == V11_SHA256, "V11 reference kit changed"
    manifest = json.loads((kit / "RUNPOD_UPLOAD_MANIFEST.json").read_text())
    assert manifest["encoding_variant"] == "LORA-SEQ-002-v1.2"
    assert manifest["persistent_results"] == "/workspace/SeqLogAD/sequence-v12/P2.2"
    for name, entry in manifest["files"].items():
        path = kit / name
        assert path.stat().st_size == entry["size"]
        assert digest(path) == entry["sha256"]
        if path.suffix in {".zip", ".whl"}:
            verify_zip(path)
    members = verify_zip(outer)
    assert members == set(manifest["files"]) | {"RUNPOD_UPLOAD_MANIFEST.json", "README.md"}
    code_zip = kit / "seqlogad-code-all-experts-s42-v12.zip"
    code_members = verify_zip(code_zip)
    assert any(name.endswith("/sequence/augmentation.py") for name in code_members)
    assert any(name.endswith("/configs/models/sequence-reference-v12.yaml") for name in code_members)
    notebook = json.loads((kit / "P2.2_run_all_sequence_lora_s42_v12.ipynb").read_text())
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"V12-cell-{index}", "exec")
    print(json.dumps({
        "status": "PASS", "v11_retained_sha256": V11_SHA256,
        "v12_upload_sha256": digest(outer),
        "v12_file_count": len(manifest["files"]),
        "notebook_cells": len(notebook["cells"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
