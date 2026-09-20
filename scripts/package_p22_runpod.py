"""Assemble the verified P2.2 Sequence-LoRA RunPod A40 upload kit."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from build_p22_runpod_notebook import NOTEBOOK_NAME, build_notebook
from package_phase2_all_experts_colab import package_code
from seqlogad.common.checksum import sha256_file
from seqlogad.phase2_execution.archive import create_zip, verify_zip
from seqlogad.sequence.contracts import validate_bundle


ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "outputs/runpod/P2.2-S42-A40"
BUNDLE = ROOT / "outputs/runpod/P2.2-S42-A40-upload.zip"
CODE_ZIP = ROOT / "outputs/colab/seqlogad-code-all-experts-s42.zip"
DATA_ZIP = ROOT / "outputs/colab/phase2-sequence-s42.zip"
DATA_ROOT = ROOT / "data/phase2-sequence"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _deterministic_outer(directory: Path, destination: Path) -> None:
    temporary = Path(str(destination) + ".partial")
    temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.iterdir()):
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    temporary.replace(destination)


def main():
    bundle_hash = sha256_file(DATA_ROOT / "manifests/bundle.json")
    for fold in ("FOLD-TARGET-ARCH-BGL", "FOLD-TARGET-ARCH-HDFS", "FOLD-TARGET-ARCH-HADOOP"):
        validate_bundle(DATA_ROOT, fold, bundle_hash)
    package_code(ROOT, CODE_ZIP)
    create_zip(DATA_ROOT, DATA_ZIP, "phase2_sequence")
    verify_zip(CODE_ZIP)
    verify_zip(DATA_ZIP)
    notebook_path = ROOT / "notebooks" / NOTEBOOK_NAME
    notebook_path.write_text(json.dumps(build_notebook(CODE_ZIP, DATA_ZIP), indent=1) + "\n")
    files = {
        NOTEBOOK_NAME: notebook_path,
        CODE_ZIP.name: CODE_ZIP,
        DATA_ZIP.name: DATA_ZIP,
    }
    hashes = {name: sha256(path) for name, path in files.items()}
    code = "\n".join(
        "".join(cell.get("source", []))
        for cell in json.loads(notebook_path.read_text())["cells"]
        if cell["cell_type"] == "code"
    )
    for name in (CODE_ZIP.name, DATA_ZIP.name):
        if hashes[name] not in code:
            raise ValueError(f"P2.2 notebook does not bind current {name}")
    if bundle_hash not in code:
        raise ValueError("P2.2 notebook does not bind current bundle manifest")

    runtime_root = f"/workspace/SeqLogAD/runtime/{hashes[CODE_ZIP.name][:12]}-{hashes[DATA_ZIP.name][:12]}"
    manifest = {
        "schema": "SEQLOGAD-RUNPOD-UPLOAD-KIT-1",
        "task_id": "P2.2",
        "expert_id": "SEQUENCE_LLAMA_REFERENCE",
        "seed": 42,
        "targets": ["BGL", "HDFS", "HADOOP"],
        "runtime": "RUNPOD",
        "gpu": "NVIDIA A40 48GB",
        "network_volume_mount": "/workspace",
        "runtime_root": runtime_root,
        "dataset_after_extraction": f"{runtime_root}/phase2_sequence",
        "code_after_extraction": f"{runtime_root}/seqlogad_code_all_experts_s42",
        "persistent_results": "/workspace/SeqLogAD/P2.2",
        "bundle_manifest_sha256": bundle_hash,
        "files": {
            name: {"size": path.stat().st_size, "sha256": hashes[name]}
            for name, path in files.items()
        },
        "contains_base_model_weights": False,
        "contains_semantic_adapter": False,
        "requires_hf_token_secret": True,
        "source_label_status": "UNRESOLVED_DENY",
        "scientific_result": "NOT_EVALUATED",
    }
    instructions = f"""# P2.2 S42 — RunPod A40 upload kit

1. Create one RunPod A40 48 GB Pod with a Network Volume mounted at `/workspace`.
2. Use `runpod/pytorch:1.0.3-cu1281-torch291-ubuntu2404`.
3. Map a RunPod secret to environment variable `HF_TOKEN`.
4. Upload the three files in this directory into `/workspace/uploads`.
5. Open `{NOTEBOOK_NAME}` in JupyterLab and click **Run All Cells** once.
6. Stop only after `SAFE_TO_STOP_RUNTIME=YES`.

The notebook verifies code `{hashes[CODE_ZIP.name]}`, data `{hashes[DATA_ZIP.name]}`
and bundle manifest `{bundle_hash}` before loading the model. Interrupted targets
resume from `/workspace/SeqLogAD/P2.2/recovery`.

Final artifact: `/workspace/SeqLogAD/P2.2/seqlogad_outputs_P2.2_S42_FINAL.zip`.
"""
    DELIVERY.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=DELIVERY.parent) as folder:
        stage = Path(folder) / DELIVERY.name
        stage.mkdir()
        for name, source in files.items():
            shutil.copy2(source, stage / name)
        (stage / "RUNPOD_UPLOAD_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        (stage / "README.md").write_text(instructions)
        if DELIVERY.exists():
            shutil.rmtree(DELIVERY)
        stage.replace(DELIVERY)
    _deterministic_outer(DELIVERY, BUNDLE)
    print(json.dumps({
        "delivery_directory": str(DELIVERY),
        "upload_bundle": str(BUNDLE),
        "upload_bundle_size": BUNDLE.stat().st_size,
        "upload_bundle_sha256": sha256(BUNDLE),
        "manifest": manifest,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
