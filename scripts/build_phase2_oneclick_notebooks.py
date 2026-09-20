"""Generate thin canonical GPU notebooks from the execution amendment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from build_phase2_runpod_notebook import build_notebook as build_runpod_notebook
from build_p22_runpod_notebook import build_notebook as build_p22_runpod_notebook
from seqlogad.common.checksum import sha256_file


NAMES = {
    "P2.1": "P2.1_run_all_semantic_s42.ipynb",
    "P2.2": "P2.2_run_all_sequence_lora_s42.ipynb",
    "P2.3": "P2.3_run_all_lightweight_sequence_s42.ipynb",
    "P2.4": "P2.4_run_all_gtat_s42.ipynb",
}


def cell(kind, source):
    value = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        value.update(execution_count=None, outputs=[])
    return value


def build_notebook(root, task_id, code_zip, data_zip):
    spec = yaml.safe_load((root / "configs/protocols/phase2-development-s42-v1.yaml").read_text())["phase2_development_s42"]
    expert = spec["experts"][task_id]
    ready = expert["implementation_status"] == "READY"
    blockers = expert.get("blockers", [])
    title = {
        "P2.1": "Semantic LoRA",
        "P2.2": "Sequence-LoRA Reference",
        "P2.3": "Lightweight Sequence Expert",
        "P2.4": "GTAT Expert",
    }[task_id]
    requires_token = bool(expert["requires_hf_token"])
    if task_id == "P2.1":
        return build_runpod_notebook(code_zip, data_zip)
    if task_id == "P2.2":
        return build_p22_runpod_notebook(code_zip, data_zip)

    markdown = f"""# {task_id} — {title} — ONE CLICK S42 (Google Colab)

Status: **{'READY' if ready else 'BLOCKED — fail closed'}**.

This notebook is orchestration only. It is locked to seed `42` and runs `BGL → HDFS → HADOOP` sequentially. It persists every authoritative recovery checkpoint and completed target to an expert-specific Google Drive directory.

Human steps:

1. Select an NVIDIA GPU runtime (L4/native BF16 preferred; T4 is conditional on finite FP16 preflight).
2. Upload `{code_zip.name}` and `{data_zip.name}` to `/content`.
3. {'Add `HF_TOKEN` in Colab Secrets.' if requires_token else 'No Hugging Face token is required by the frozen expert contract.'}
4. Click **Run all** once.

Do not edit targets or seed. Blockers: `{', '.join(blockers) if blockers else 'none'}`.
"""
    config = f'''# HUMAN CONFIG — paths only. Seed and targets are protocol-locked.
TASK_ID = {task_id!r}
NOTEBOOK_STATUS = {expert["implementation_status"]!r}
BLOCKERS = {blockers!r}
RUN_MODE = "development"
SEED = 42
TARGETS = ["BGL", "HDFS", "HADOOP"]
DATA_ROOT = "/content/phase2"
OUTPUT_ROOT = "/content/seqlogad_outputs"
REPO_ROOT = "/content/seqlogad_code_all_experts_s42"
PERSIST_TO_DRIVE = True
DRIVE_ROOT = "/content/drive/MyDrive/SeqLogAD"
EXPECTED_CODE_ZIP_SHA256 = {sha256_file(code_zip)!r}
EXPECTED_DATA_ZIP_SHA256 = {sha256_file(data_zip)!r}
EXPECTED_BUNDLE_SHA256 = "3ef2bfe36d2ad68205eea4290a632eb81db0d63acfb76c92f25a3eb96e8205de"
REQUIRES_HF_TOKEN = {requires_token!r}

assert RUN_MODE == "development" and SEED == 42
assert TARGETS == ["BGL", "HDFS", "HADOOP"]
assert PERSIST_TO_DRIVE is True
assert NOTEBOOK_STATUS == "READY", "Notebook is fail-closed: " + ", ".join(BLOCKERS)
'''
    setup = r'''from pathlib import Path, PurePosixPath
import hashlib, os, stat, subprocess, sys, zipfile
from google.colab import drive

drive.mount("/content/drive")

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def locate(expected):
    matches = [p for p in Path("/content").glob("*.zip") if digest(p) == expected]
    assert len(matches) == 1, f"Expected exactly one uploaded ZIP with SHA-256 {expected}; found {matches}"
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
safe_extract(code_zip, "/content")
safe_extract(data_zip, "/content")
assert Path(REPO_ROOT).is_dir() and Path(DATA_ROOT, "manifests/bundle.json").is_file()

def run_live(args, check=True):
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, bufsize=1, env=env) as process:
        for line in process.stdout:
            token = os.environ.get("HF_TOKEN")
            if token:
                line = line.replace(token, "[TOKEN_HIDDEN]")
            print(line, end="", flush=True)
        code = process.wait()
    if check and code:
        raise subprocess.CalledProcessError(code, args)
    return code

assert sys.version_info[:2] == (3, 12), "Use a Colab Python 3.12 runtime"
VENV = Path("/content/seqlogad-venv")
PYTHON = str(VENV / "bin/python")
run_live([sys.executable, "-m", "pip", "install", "virtualenv==20.31.2"])
if not Path(PYTHON).is_file():
    run_live([sys.executable, "-m", "virtualenv", "--python", sys.executable, str(VENV)])
run_live([PYTHON, "-m", "pip", "install", "torch==2.9.1", "--index-url",
          "https://download.pytorch.org/whl/cu128"])
run_live([PYTHON, "-m", "pip", "install", "-e", REPO_ROOT, "packaging>=24,<27"])
run_live([PYTHON, "-c", "from seqlogad.semantic.runtime import install_missing; install_missing(" + repr(REPO_ROOT) + ")"])
'''
    auth = r'''if REQUIRES_HF_TOKEN:
    from google.colab import userdata
    token = userdata.get("HF_TOKEN")
    assert token, "Add HF_TOKEN to Colab Secrets and grant notebook access"
    os.environ["HF_TOKEN"] = token
    run_live([PYTHON, "-m", "seqlogad.semantic.cli", "auth", "--repo-root", REPO_ROOT])
else:
    print("HF_TOKEN=NOT_REQUIRED")
'''
    execute = r'''args = [
    PYTHON, "-m", "seqlogad.phase2_execution.cli",
    "--task-id", TASK_ID,
    "--repo-root", REPO_ROOT,
    "--data-root", DATA_ROOT,
    "--output-root", OUTPUT_ROOT,
    "--drive-root", DRIVE_ROOT,
    "--expected-bundle-sha256", EXPECTED_BUNDLE_SHA256,
]
run_live(args, check=True)
'''
    final = r'''print("====================================")
print("SEQLOGAD COLAB EXECUTION FINISHED")
print("Review the CLI summary immediately above.")
print("SAFE_TO_DISCONNECT_COLAB=YES only if the verified final Drive backup was printed.")
print("====================================")
'''
    cells = [
        cell("markdown", markdown),
        cell("code", config),
        cell("markdown", "## Mount Drive, verify uploads, create the isolated runtime\n"),
        cell("code", setup),
        cell("markdown", "## Secure authentication\n"),
        cell("code", auth),
        cell("markdown", "## Sequential target loop, checkpoint recovery and verified exports\n"),
        cell("code", execute),
        cell("markdown", "## Safe disconnect gate\n"),
        cell("code", final),
    ]
    return {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"name": NAMES[task_id], "provenance": []},
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
    parser.add_argument("--task-id", choices=sorted(NAMES), help="Generate one notebook only")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    code_zip, data_zip = Path(args.code_zip).resolve(), Path(args.data_zip).resolve()
    selected = {args.task_id: NAMES[args.task_id]} if args.task_id else NAMES
    for task_id, name in selected.items():
        notebook = build_notebook(root, task_id, code_zip, data_zip)
        path = root / "notebooks" / name
        path.write_text(json.dumps(notebook, indent=1) + "\n")
        print(path)


if __name__ == "__main__":
    main()
