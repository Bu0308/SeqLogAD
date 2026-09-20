"""Generate the seed-42 P2.1 one-click RunPod notebook."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from seqlogad.common.checksum import sha256_file


NOTEBOOK_NAME = "P2.1_run_all_semantic_s42.ipynb"


def cell(kind, source):
    value = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        value.update(execution_count=None, outputs=[])
    return value


def build_notebook(code_zip, data_zip):
    code_hash = sha256_file(code_zip)
    data_hash = sha256_file(data_zip)
    markdown = f"""# P2.1 — Semantic LoRA — ONE CLICK S42 (RunPod A40)

Status: **READY**. This notebook runs `BGL (registered externally) → HDFS → HADOOP`
with seed `42`. HDFS/Hadoop checkpoints and completed artifacts are persisted below
`/workspace/SeqLogAD/persistent/P2.1`.

Before clicking **Run All**:

1. Deploy one NVIDIA **A40 48 GB** Pod with a **Network Volume mounted at `/workspace`**.
   Native BF16 is mandatory. The matching RunPod image is
   `runpod/pytorch:1.0.3-cu1281-torch291-ubuntu2404`.
2. Add `HF_TOKEN` as a RunPod environment secret. Never paste it into a cell.
3. Upload `{code_zip.name}` and `{data_zip.name}` into `/workspace/uploads`.
4. Upload/open this notebook in JupyterLab and click **Run All** once.

If the Pod stops, deploy/restart with the same Network Volume, reopen this notebook,
and click **Run All**. A verified `LATEST_RECOVERY.zip` resumes the interrupted target.
Do not terminate the Pod until `SAFE_TO_STOP_RUNTIME=YES` is printed.
"""
    config = f'''# HUMAN CONFIG — no fold/seed editing is required.
from pathlib import Path
import os, uuid

TASK_ID = "P2.1"
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
DATA_ROOT = str(RUNTIME_ROOT / "phase2")
SESSION_ROOT = Path("/tmp/seqlogad_sessions") / uuid.uuid4().hex
OUTPUT_ROOT = str(SESSION_ROOT / "seqlogad_outputs")
EXPECTED_CODE_ZIP_SHA256 = {code_hash!r}
EXPECTED_DATA_ZIP_SHA256 = {data_hash!r}
EXPECTED_BUNDLE_SHA256 = "3ef2bfe36d2ad68205eea4290a632eb81db0d63acfb76c92f25a3eb96e8205de"
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
    assert len(matches) == 1, (
        f"Upload exactly one ZIP with SHA-256 {expected} into /workspace/uploads; "
        f"found {matches}"
    )
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
expected_marker = {
    "code_sha256": EXPECTED_CODE_ZIP_SHA256,
    "data_sha256": EXPECTED_DATA_ZIP_SHA256,
}
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
    assert (partial / "phase2/manifests/bundle.json").is_file()
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
        uv = str(Path(sys.executable).parent / "uv")
        assert Path(uv).is_file(), "uv bootstrap executable missing"
        run_live([uv, "python", "install", "3.12"])
        run_live([uv, "venv", "--python", "3.12", "--seed", str(VENV)])

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
assert total >= {MIN_VRAM_GIB} * 1024**3, f"Expected at least {MIN_VRAM_GIB} GiB VRAM, got {{total / 1024**3:.2f}}"
assert native_bf16, "Native BF16 is required"
print(json.dumps({{"gpu": name, "free_vram_bytes": free, "total_vram_bytes": total,
                  "native_bf16": native_bf16, "torch": torch.__version__,
                  "cuda": torch.version.cuda}}, indent=2))
"""
run_live([PYTHON, "-c", hardware_check])
run_live([PYTHON, "-m", "seqlogad.semantic.cli", "environment", "--repo-root", REPO_ROOT])
'''
    auth = r'''token = os.environ.get("HF_TOKEN")
assert token, (
    "Set HF_TOKEN as a RunPod environment secret, restart the Pod if necessary, "
    "and never paste the token into this notebook"
)
run_live([PYTHON, "-m", "seqlogad.semantic.cli", "auth", "--repo-root", REPO_ROOT])
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
    final = r'''final_zip = PERSISTENT_ROOT / TASK_ID / "seqlogad_outputs_P2.1_S42_FINAL.zip"
final_sidecar = Path(str(final_zip) + ".sha256")
assert final_zip.is_file() and final_sidecar.is_file(), "Verified final persistent ZIP is missing"
declared_hash, declared_name = final_sidecar.read_text().strip().split("  ", 1)
assert declared_name == final_zip.name and digest(final_zip) == declared_hash
shutil.rmtree(SESSION_ROOT)
print("====================================")
print("SEQLOGAD RUNPOD EXECUTION SUMMARY")
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
