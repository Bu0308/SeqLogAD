"""Generate the seed-42 P2.2 one-click RunPod A40 notebook."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from seqlogad.common.checksum import sha256_file


NOTEBOOK_NAME = "P2.2_run_all_sequence_lora_s42.ipynb"


def cell(kind, source):
    value = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        value.update(execution_count=None, outputs=[])
    return value


def build_notebook(code_zip, data_zip):
    code_hash = sha256_file(code_zip)
    data_hash = sha256_file(data_zip)
    markdown = f"""# P2.2 — Sequence-LoRA Reference — ONE CLICK S42 (RunPod A40)

Status: **READY**. This notebook trains/resumes `BGL → HDFS → HADOOP` with seed
`42`. Every checkpoint and completed target is persisted below
`/workspace/SeqLogAD/P2.2`. It never loads the P2.1 Semantic adapter.

Before clicking **Run All**:

1. Deploy one NVIDIA **A40 48 GB** Pod with a Network Volume at `/workspace`.
   Use `runpod/pytorch:1.0.3-cu1281-torch291-ubuntu2404`.
2. Map a RunPod secret to environment variable `HF_TOKEN`.
3. Upload `{code_zip.name}` and `{data_zip.name}` to `/workspace/uploads`.
4. Upload/open this notebook in JupyterLab and click **Run All** once.

After interruption, restart with the same Network Volume and click **Run All**
again. Stop only after `SAFE_TO_STOP_RUNTIME=YES`.
"""
    config = f'''# HUMAN CONFIG — no fold/seed editing is required.
from pathlib import Path
import os, uuid

TASK_ID = "P2.2"
NOTEBOOK_STATUS = "READY"
BLOCKERS = []
RUN_MODE = "development"
SEED = 42
TARGETS = ["BGL", "HDFS", "HADOOP"]
UPLOAD_ROOT = Path("/workspace/uploads")
STATE_ROOT = Path("/workspace/SeqLogAD")
PERSISTENT_ROOT = STATE_ROOT
HF_HOME = STATE_ROOT / "hf-cache"
VENV = STATE_ROOT / "venv-py312"
RUNTIME_ROOT = STATE_ROOT / "runtime" / "{code_hash[:12]}-{data_hash[:12]}"
REPO_ROOT = str(RUNTIME_ROOT / "seqlogad_code_all_experts_s42")
DATA_ROOT = str(RUNTIME_ROOT / "phase2_sequence")
SESSION_ROOT = Path("/tmp/seqlogad_sessions") / uuid.uuid4().hex
OUTPUT_ROOT = str(SESSION_ROOT / "seqlogad_outputs")
EXPECTED_CODE_ZIP_SHA256 = {code_hash!r}
EXPECTED_DATA_ZIP_SHA256 = {data_hash!r}
EXPECTED_BUNDLE_SHA256 = "1268b669a8b1b474658cfa7daa6556c987b0f31f07e0101ed30af250a8d7f129"
REQUIRED_GPU = "NVIDIA A40"
MIN_VRAM_GIB = 40

assert RUN_MODE == "development" and SEED == 42
assert TARGETS == ["BGL", "HDFS", "HADOOP"]
assert NOTEBOOK_STATUS == "READY", "Notebook is fail-closed: " + ", ".join(BLOCKERS)
assert UPLOAD_ROOT.is_dir(), "RunPod Network Volume must be mounted at /workspace"
for directory in (STATE_ROOT, PERSISTENT_ROOT, HF_HOME, SESSION_ROOT):
    directory.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(HF_HOME)
print({{"session_root": str(SESSION_ROOT), "persistent_root": str(PERSISTENT_ROOT)}})
'''
    uv_fix = r'''# RunPod images may install `uv` outside sys.executable's directory.
import shutil, sys
from pathlib import Path

uv_real = shutil.which("uv")
if uv_real:
    uv_expected = Path(sys.executable).parent / "uv"
    if not uv_expected.exists():
        uv_expected.symlink_to(uv_real)
    print("UV_FIX=PASS", {"uv_real": uv_real, "uv_expected": str(uv_expected)})
else:
    print("UV_FIX=DEFERRED_UNTIL_BOOTSTRAP")
'''
    setup = r'''from pathlib import PurePosixPath
import hashlib, json, shutil, stat, subprocess, sys, zipfile

def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()

def locate(expected):
    matches = [path for path in UPLOAD_ROOT.glob("*.zip") if digest(path) == expected]
    assert len(matches) == 1, f"Expected one upload with SHA-256 {expected}; found {matches}"
    return matches[0]

def safe_extract(archive, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as handle:
        infos = handle.infolist()
        names = [item.filename for item in infos]
        assert len(names) == len(set(names)), "Duplicate ZIP member"
        for item in infos:
            member = PurePosixPath(item.filename)
            assert not member.is_absolute() and ".." not in member.parts and "\\" not in item.filename
            assert ((item.external_attr >> 16) & 0o170000) != stat.S_IFLNK, "ZIP symlink forbidden"
        assert handle.testzip() is None, "ZIP CRC failure"
        handle.extractall(destination)

code_zip = locate(EXPECTED_CODE_ZIP_SHA256)
data_zip = locate(EXPECTED_DATA_ZIP_SHA256)
marker = RUNTIME_ROOT / "EXTRACTION.json"
expected_marker = {"code_sha256": EXPECTED_CODE_ZIP_SHA256, "data_sha256": EXPECTED_DATA_ZIP_SHA256}
if RUNTIME_ROOT.exists():
    assert marker.is_file(), f"Unverified runtime directory exists: {RUNTIME_ROOT}"
    assert json.loads(marker.read_text()) == expected_marker, "Runtime extraction identity mismatch"
else:
    partial = RUNTIME_ROOT.with_name(RUNTIME_ROOT.name + ".partial")
    if partial.exists():
        shutil.rmtree(partial)
    partial.mkdir(parents=True)
    safe_extract(code_zip, partial)
    safe_extract(data_zip, partial)
    assert (partial / "seqlogad_code_all_experts_s42").is_dir()
    assert (partial / "phase2_sequence/manifests/bundle.json").is_file()
    (partial / "EXTRACTION.json").write_text(json.dumps(expected_marker, sort_keys=True) + "\n")
    partial.rename(RUNTIME_ROOT)

assert Path(REPO_ROOT).is_dir()
assert Path(DATA_ROOT, "manifests/bundle.json").is_file()
print({"code_zip": str(code_zip), "data_zip": str(data_zip), "extraction": "PASS"})

def isolated_env():
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    return env

def run_live(args, check=True):
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, bufsize=1, env=isolated_env()) as process:
        for line in process.stdout:
            token = os.environ.get("HF_TOKEN")
            if token:
                line = line.replace(token, "[TOKEN_HIDDEN]")
            print(line, end="", flush=True)
        code = process.wait()
    if check and code:
        raise subprocess.CalledProcessError(code, args)
    return code

run_live(["nvidia-smi"])
PYTHON = str(VENV / "bin/python")
if not Path(PYTHON).is_file():
    if sys.version_info[:2] == (3, 12):
        run_live([sys.executable, "-m", "pip", "install", "virtualenv==20.31.2"])
        run_live([sys.executable, "-m", "virtualenv", "--python", sys.executable, str(VENV)])
    else:
        run_live([sys.executable, "-m", "pip", "install", "uv==0.8.17"])
        uv_real = shutil.which("uv")
        assert uv_real, "uv bootstrap executable missing"
        uv_expected = Path(sys.executable).parent / "uv"
        if not uv_expected.exists():
            uv_expected.symlink_to(uv_real)
        run_live([str(uv_expected), "python", "install", "3.12"])
        run_live([str(uv_expected), "venv", "--python", "3.12", "--seed", str(VENV)])

run_live([PYTHON, "-c", "import sys; assert sys.version_info[:2] == (3, 12); print(sys.version)"])
run_live([PYTHON, "-m", "pip", "install", "torch==2.9.1", "--index-url",
          "https://download.pytorch.org/whl/cu128"])
run_live([PYTHON, "-m", "pip", "install", "-e", REPO_ROOT, "packaging>=24,<27"])
run_live([PYTHON, "-c", "from seqlogad.semantic.runtime import install_missing; install_missing(" + repr(REPO_ROOT) + ")"])
hardware_check = f"""
import json, torch
assert torch.cuda.is_available(), "CUDA is unavailable"
name = torch.cuda.get_device_name(0)
free, total = torch.cuda.mem_get_info(0)
native_bf16 = torch.cuda.is_bf16_supported(including_emulation=False)
assert {REQUIRED_GPU!r} in name, f"Expected {REQUIRED_GPU}, got {{name}}"
assert total >= {MIN_VRAM_GIB} * 1024**3, f"Expected at least {MIN_VRAM_GIB} GiB VRAM"
assert native_bf16, "Native BF16 is required"
print(json.dumps({{"gpu": name, "free_vram_bytes": free, "total_vram_bytes": total,
                  "native_bf16": native_bf16, "torch": torch.__version__,
                  "cuda": torch.version.cuda}}, indent=2))
"""
run_live([PYTHON, "-c", hardware_check])
run_live([PYTHON, "-m", "seqlogad.sequence.cli", "environment", "--repo-root", REPO_ROOT])
'''
    auth = r'''token = os.environ.get("HF_TOKEN")
assert token, "Set HF_TOKEN as a RunPod environment secret; never paste it into the notebook"
run_live([PYTHON, "-m", "seqlogad.sequence.cli", "auth", "--repo-root", REPO_ROOT])
'''
    execute = r'''args = [
    PYTHON, "-m", "seqlogad.phase2_execution.cli",
    "--task-id", TASK_ID,
    "--repo-root", REPO_ROOT,
    "--data-root", DATA_ROOT,
    "--output-root", OUTPUT_ROOT,
    "--persistent-root", str(PERSISTENT_ROOT),
    "--expected-bundle-sha256", EXPECTED_BUNDLE_SHA256,
]
run_live(args, check=True)
'''
    final = r'''final_zip = PERSISTENT_ROOT / TASK_ID / "seqlogad_outputs_P2.2_S42_FINAL.zip"
final_sidecar = Path(str(final_zip) + ".sha256")
assert final_zip.is_file() and final_sidecar.is_file(), "Verified final P2.2 ZIP is missing"
declared_hash, declared_name = final_sidecar.read_text().strip().split("  ", 1)
assert declared_name == final_zip.name and digest(final_zip) == declared_hash
shutil.rmtree(SESSION_ROOT)
print("====================================")
print("SEQLOGAD P2.2 RUNPOD EXECUTION SUMMARY")
print(f"FINAL_ZIP={final_zip}")
print(f"FINAL_ZIP_SIZE={final_zip.stat().st_size}")
print(f"FINAL_ZIP_SHA256={declared_hash}")
print("PERSISTENT_STORAGE_VERIFIED=YES")
print("SAFE_TO_STOP_RUNTIME=YES")
print("====================================")
'''
    return {
        "cells": [
            cell("markdown", markdown),
            cell("code", config),
            cell("markdown", "## Apply the verified RunPod uv compatibility repair\n"),
            cell("code", uv_fix),
            cell("markdown", "## Verify uploads, extract atomically and build the frozen runtime\n"),
            cell("code", setup),
            cell("markdown", "## Secure Hugging Face authentication\n"),
            cell("code", auth),
            cell("markdown", "## Sequential target loop with persistent recovery\n"),
            cell("code", execute),
            cell("markdown", "## Final persistent-integrity and safe-stop gate\n"),
            cell("code", final),
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--code-zip", required=True)
    parser.add_argument("--data-zip", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    notebook = build_notebook(Path(args.code_zip).resolve(), Path(args.data_zip).resolve())
    path = root / "notebooks" / NOTEBOOK_NAME
    path.write_text(json.dumps(notebook, indent=1) + "\n")
    print(path)


if __name__ == "__main__":
    main()
