"""Assemble the verified P2.1 RunPod upload kit without model weights."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "outputs/runpod/P2.1-S42-A40"
BUNDLE = ROOT / "outputs/runpod/P2.1-S42-A40-upload.zip"
FILES = {
    "P2.1_run_all_semantic_s42.ipynb": ROOT / "notebooks/P2.1_run_all_semantic_s42.ipynb",
    "seqlogad-code-all-experts-s42.zip": ROOT / "outputs/colab/seqlogad-code-all-experts-s42.zip",
    "phase2-final.zip": ROOT / "outputs/colab/phase2-final.zip",
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    for source in FILES.values():
        if not source.is_file():
            raise FileNotFoundError(source)

    notebook = json.loads(FILES["P2.1_run_all_semantic_s42.ipynb"].read_text())
    code = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    hashes = {name: sha256(source) for name, source in FILES.items()}
    if hashes["seqlogad-code-all-experts-s42.zip"] not in code:
        raise ValueError("notebook does not bind the current code ZIP")
    if hashes["phase2-final.zip"] not in code:
        raise ValueError("notebook does not bind the current data ZIP")

    runtime_root = (
        "/workspace/SeqLogAD/runtime/"
        f"{hashes['seqlogad-code-all-experts-s42.zip'][:12]}-"
        f"{hashes['phase2-final.zip'][:12]}"
    )
    manifest = {
        "schema": "SEQLOGAD-RUNPOD-UPLOAD-KIT-1",
        "task_id": "P2.1",
        "seed": 42,
        "runtime": "RUNPOD",
        "gpu": "NVIDIA A40 48GB",
        "network_volume_mount": "/workspace",
        "runtime_root": runtime_root,
        "dataset_after_extraction": f"{runtime_root}/phase2",
        "code_after_extraction": f"{runtime_root}/seqlogad_code_all_experts_s42",
        "persistent_results": "/workspace/SeqLogAD/P2.1",
        "files": {
            name: {"size": source.stat().st_size, "sha256": hashes[name]}
            for name, source in FILES.items()
        },
        "contains_base_model_weights": False,
        "requires_hf_token_secret": True,
        "scientific_result": "NOT_EVALUATED",
    }
    instructions = f"""# P2.1 S42 — RunPod A40 upload kit

Dataset: `phase2-final.zip`. The notebook verifies SHA-256
`{hashes['phase2-final.zip']}` and extracts it to `{runtime_root}/phase2`.
You do not need to unzip it manually.

1. Create one RunPod Pod with NVIDIA A40 48 GB and a Network Volume mounted at `/workspace`.
2. Use an image with Python 3.12. The notebook installs the frozen PyTorch CUDA 12.8 environment.
3. Create RunPod secret `huggingface_token` and map it to environment variable `HF_TOKEN`.
4. Create `/workspace/uploads` and upload the three files in this directory there.
5. Open `P2.1_run_all_semantic_s42.ipynb` in JupyterLab and choose **Run All Cells**.
6. Stop the Pod only after `FINAL_PERSISTENT_BACKUP=PASS` and `SAFE_TO_STOP_RUNTIME=YES`.

Final artifact: `/workspace/SeqLogAD/P2.1/seqlogad_outputs_P2.1_S42_FINAL.zip`.
BGL-S42 is registered and skipped; the notebook trains/resumes HDFS-S42 and Hadoop-S42.
"""

    DELIVERY.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=DELIVERY.parent) as folder:
        stage = Path(folder) / DELIVERY.name
        stage.mkdir()
        for name, source in FILES.items():
            shutil.copy2(source, stage / name)
        (stage / "RUNPOD_UPLOAD_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        (stage / "README.md").write_text(instructions)
        if DELIVERY.exists():
            shutil.rmtree(DELIVERY)
        stage.replace(DELIVERY)

    temporary_bundle = Path(str(BUNDLE) + ".partial")
    temporary_bundle.unlink(missing_ok=True)
    with zipfile.ZipFile(temporary_bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(DELIVERY.iterdir()):
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    temporary_bundle.replace(BUNDLE)
    result = {
        "delivery_directory": str(DELIVERY),
        "upload_bundle": str(BUNDLE),
        "upload_bundle_size": BUNDLE.stat().st_size,
        "upload_bundle_sha256": sha256(BUNDLE),
        "manifest": manifest,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
