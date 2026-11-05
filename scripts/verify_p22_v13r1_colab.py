"""Verify the portable V13R1 Colab kit without launching training."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]
READY = ROOT / "outputs/runpod/P2.2-S42-A40-V13R1-READY"
READY_ZIP = ROOT / "outputs/runpod/P2.2-S42-A40-V13R1-READY.zip"
DELIVERY = ROOT / "outputs/colab/P2.2-S42-A40-V13R1-COLAB-READY"
PACKAGE = ROOT / "outputs/colab/P2.2-S42-A40-V13R1-COLAB-READY.zip"
NOTEBOOK = DELIVERY / "P2.2_run_all_sequence_lora_s42_v13r1_colab.ipynb"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    sidecar_hash, sidecar_name = Path(str(PACKAGE) + ".sha256").read_text().strip().split("  ", 1)
    check(sidecar_name == PACKAGE.name and sidecar_hash == sha(PACKAGE.read_bytes()), "package sidecar mismatch")
    with zipfile.ZipFile(PACKAGE) as outer:
        check(outer.testzip() is None, "operator package CRC failure")
        entries = outer.namelist()
        check(len(entries) == len(set(entries)), "duplicate package member")
        check(all(not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts for name in entries), "unsafe outer archive path")
        members = {name: outer.read(name) for name in entries}
    manifest = json.loads(members["COLAB_UPLOAD_MANIFEST.json"])
    check(manifest["trainer_payload_unchanged"] is True, "trainer identity not declared")
    for name, record in manifest["files"].items():
        check(name in members, f"manifest member absent: {name}")
        check(sha(members[name]) == record["sha256"], f"manifest hash mismatch: {name}")
        check(len(members[name]) == record["size"], f"manifest size mismatch: {name}")
    check(manifest["input_ready_zip_sha256"] == "a17a0949bd7743a263267460d35ff9182fccc9b601420f6edb923b465076c14c", "wrong READY input pinned")
    check(sha(READY_ZIP.read_bytes()) == manifest["input_ready_zip_sha256"], "source READY ZIP changed")

    with zipfile.ZipFile(READY_ZIP) as ready:
        check(ready.testzip() is None, "READY ZIP CRC failure")
        original_manifest = json.loads(ready.read("RUNPOD_UPLOAD_MANIFEST.json"))
        for name, record in original_manifest["files"].items():
            check(sha(ready.read(name)) == record["sha256"], f"READY input checksum failure: {name}")

    notebook = json.loads(members[NOTEBOOK.name])
    check(notebook["nbformat"] == 4 and len(notebook["cells"]) == 15, "unexpected notebook structure")
    cell_sources = []
    for i, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            source = "".join(cell["source"])
            compile(source, f"colab-cell-{i}", "exec")
            cell_sources.append(source)
    config = "".join(notebook["cells"][1]["source"])
    setup = "".join(notebook["cells"][5]["source"])
    auth = "".join(notebook["cells"][7]["source"])
    training = "".join(notebook["cells"][10]["source"])
    final = "".join(notebook["cells"][14]["source"])
    check("drive.mount(\"/content/drive\")" in config, "Drive is not mounted")
    check("NOTEBOOK_PATH.is_file()" in config, "operator notebook path is not checked")
    check("EXPECTED_READY_ZIP_SHA256" in setup and "safe_extract(READY_ARCHIVE" in setup, "READY package not safely extracted")
    check("EXPECTED_COLLECTOR_SHA256" in setup and "COLLECTOR_B64" not in setup, "embedded collector verification missing")
    check("SUPPORTED_GPU_FAMILIES!r" in setup and all(name in config for name in ("NVIDIA A100", "NVIDIA H100")), "A100/H100 preflight missing")
    check("MIN_VRAM_GIB" in setup and "native_bf16" in setup, "VRAM/BF16 preflight missing")
    check("userdata.get(\"HF_TOKEN\")" in auth and "os.environ[\"HF_TOKEN\"] = token" in auth, "Colab secret auth missing")
    check("P2.2 Sequence V13R1 Colab attempt" in training and "--metrics" in training, "Colab Projmem training run missing")
    check("COLLECT_READY=YES" in final and "files.download(str(final_archive))" in final, "save/download finalizer missing")
    check("/workspace/" not in config + setup + final, "RunPod-only output path remains")
    check("target_metrics" in members["COLAB_UPLOAD_MANIFEST.json"].decode() or "NOT_EVALUATED" in members["HUONG_DAN_COLAB_V13R1_VI.md"].decode(), "target evaluation status missing")

    # Compile the generated inner GPU probe after f-string interpolation.
    tree = ast.parse(setup)
    assign = next(n for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "hardware_check" for t in n.targets))
    ns = {"SUPPORTED_GPU_FAMILIES": ("NVIDIA A100", "NVIDIA H100"), "MIN_VRAM_GIB": 40}
    exec(compile(ast.Module(body=[assign], type_ignores=[]), "hardware-probe", "exec"), ns)
    check("textwrap.dedent(hardware_check)" in setup, "hardware probe is not normalized before execution")
    compile(textwrap.dedent(ns["hardware_check"]), "inner-hardware-probe", "exec")

    guide = members["HUONG_DAN_COLAB_V13R1_VI.md"].decode()
    check("Windows" in guide and "macOS" in guide, "cross-platform guide missing")
    check("không thể tự đóng tab" in guide, "browser tab limitation missing")
    check("HF_TOKEN" in guide and "COLLECT_READY=YES" in guide, "operator gates missing")
    print(json.dumps({"status": "PASS", "package_sha256": sidecar_hash,
                      "package_bytes": PACKAGE.stat().st_size, "member_count": len(entries),
                      "notebook_cells": len(notebook["cells"]), "trainer_payloads": len(original_manifest["files"]),
                      "gpu_probe": "A100/H100 >=40GiB native BF16 compiles", "training_executed": False}, indent=2))


if __name__ == "__main__":
    main()
