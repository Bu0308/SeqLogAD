"""Package the isolated Sequence V13R1 F1-development RunPod upload kit."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from build_p22_v13r1_runpod_notebook import NOTEBOOK_NAME, write_r1_notebook
from package_p22_runpod import PMEM_WHEEL_SHA256, PMEM_SOURCE_COMMIT, _deterministic_outer, sha256
from package_phase2_all_experts_colab import package_code
from seqlogad.common.checksum import sha256_file
from seqlogad.phase2_execution.archive import create_zip, seal_tree, verify_zip
from seqlogad.sequence.contracts import validate_bundle


ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "outputs/runpod/P2.2-S42-A40-V13R1"
BUNDLE = ROOT / "outputs/runpod/P2.2-S42-A40-V13R1-upload.zip"
CODE_ZIP = ROOT / "outputs/colab/seqlogad-code-all-experts-s42-v13r1.zip"
DATA_ZIP = ROOT / "outputs/colab/phase2-sequence-s42.zip"
LABEL_ZIP = ROOT / "outputs/colab/phase2-source-development-v13r1.zip"
PMEM_WHEEL = ROOT / "outputs/colab/projmem-0.4.0a1-py3-none-any.whl"
DATA_ROOT = ROOT / "data/phase2-sequence"
LABEL_ROOT = ROOT / "data/phase2-source-dev-v13r1"


def main():
    if sha256_file(PMEM_WHEEL) != PMEM_WHEEL_SHA256:
        raise ValueError("pinned Projmem wheel missing or changed")
    data_hash = sha256_file(DATA_ROOT / "manifests/bundle.json")
    label_manifest = LABEL_ROOT / "manifest.json"
    label_hash = sha256_file(label_manifest)
    label_info = json.loads(label_manifest.read_text())
    if (label_info["sequence_bundle_sha256"] != data_hash
            or label_info["target_labels_used_for_selection"] is not False):
        raise ValueError("source-development sidecar isolation mismatch")
    for fold_id in label_info["folds"]:
        validate_bundle(DATA_ROOT, fold_id, data_hash)
        path = LABEL_ROOT / f"{fold_id}.json"
        if sha256_file(path) != label_info["files"][path.name]:
            raise ValueError("source-development fold digest mismatch")
    package_code(ROOT, CODE_ZIP)
    verify_zip(DATA_ZIP)
    seal_tree(LABEL_ROOT)
    create_zip(LABEL_ROOT, LABEL_ZIP, "phase2_source_development_v13r1")
    notebook_path = write_r1_notebook(
        ROOT, CODE_ZIP, DATA_ZIP, LABEL_ZIP, PMEM_WHEEL, label_hash
    )
    files = {path.name: path for path in (
        notebook_path, CODE_ZIP, DATA_ZIP, LABEL_ZIP, PMEM_WHEEL
    )}
    hashes = {name: sha256(path) for name, path in files.items()}
    code = "\n".join("".join(cell.get("source", [])) for cell in
                     json.loads(notebook_path.read_text())["cells"]
                     if cell["cell_type"] == "code")
    for name in (CODE_ZIP.name, DATA_ZIP.name, LABEL_ZIP.name, PMEM_WHEEL.name):
        if hashes[name] not in code:
            raise ValueError(f"V13R1 notebook does not bind uploaded {name}")
    if label_hash not in code or data_hash not in code:
        raise ValueError("V13R1 notebook does not bind source-development/data manifests")
    manifest = {
        "schema": "SEQLOGAD-RUNPOD-UPLOAD-KIT-1",
        "task_id": "P2.2", "expert_id": "SEQUENCE_LLAMA_REFERENCE",
        "encoding_variant": "LORA-SEQ-003-R1-v1.3.1",
        "checkpoint_selection": "MAX_MACRO_SOURCE_DEVELOPMENT_F1",
        "source_development_metrics": ["accuracy", "precision", "recall", "f1", "auroc", "average_precision"],
        "source_label_status": "SOURCE_VALIDATION_MODEL_SELECTION_ONLY",
        "target_labels_used_for_selection": False,
        "label_provenance": label_info["historical_label_reader"],
        "source_development_manifest_sha256": label_hash,
        "sequence_bundle_manifest_sha256": data_hash,
        "projmem": {"version": "0.4.0a1", "source_commit": PMEM_SOURCE_COMMIT,
                    "capture": "PMEM_RUN_ON_PERSISTENT_NETWORK_VOLUME"},
        "seed": 42, "targets": ["BGL", "HDFS", "HADOOP"],
        "runtime": "RUNPOD", "gpu": "NVIDIA A40 48GB",
        "persistent_results": "/workspace/SeqLogAD/sequence-v13r1/P2.2",
        "files": {name: {"size": path.stat().st_size, "sha256": hashes[name]}
                  for name, path in files.items()},
        "contains_base_model_weights": False,
        "contains_semantic_adapter": False,
        "requires_hf_token_secret": True,
        "scientific_result": "NOT_EVALUATED",
    }
    instructions = f"""# P2.2 S42 V13R1 — RunPod A40 upload kit

1. Create an A40 48 GB Pod with a Network Volume mounted at `/workspace`.
2. Use `runpod/pytorch:1.0.3-cu1281-torch291-ubuntu2404` and map `HF_TOKEN`
   from a RunPod secret.
3. Upload all five files in this directory to `/workspace/uploads`.
4. Open `{NOTEBOOK_NAME}` in JupyterLab and click **Run All Cells**.
5. Stop only when `SAFE_TO_STOP_RUNTIME=YES`.

The notebook verifies the code/data/source-development ZIPs and the pinned
Projmem wheel by SHA-256. V13R1 checkpoints use source-development F1 for early
stopping; NLL, accuracy, precision, recall, AUROC and AP are logged. These are
source-development metrics, not target anomaly evaluation results.

Scientific ZIP: `/workspace/SeqLogAD/sequence-v13r1/P2.2/seqlogad_outputs_P2.2_S42_FINAL.zip`.
Projmem database: `/workspace/SeqLogAD/sequence-v13r1/.pmem/pmem.db`.
Download the entire `sequence-v13r1` directory, including `.pmem`, `attempts`, and `projmem_exports`, with the scientific ZIP. Bootstrap failures are journaled before Projmem installs; their journals are registered in Projmem on the next successful setup. Training attempts stream to `attempts/<id>/training.log`.
"""
    DELIVERY.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=DELIVERY.parent) as folder:
        stage = Path(folder) / DELIVERY.name
        stage.mkdir()
        for name, source in files.items():
            shutil.copy2(source, stage / name)
        (stage / "RUNPOD_UPLOAD_MANIFEST.json").write_text(
            json.dumps(manifest, sort_keys=True, indent=2) + "\n"
        )
        (stage / "README.md").write_text(instructions)
        if DELIVERY.exists():
            raise ValueError("V13R1 delivery exists; preserve it and version a new kit")
        stage.replace(DELIVERY)
    if BUNDLE.exists():
        raise ValueError("V13R1 upload ZIP exists; preserve it and version a new kit")
    _deterministic_outer(DELIVERY, BUNDLE)
    print(json.dumps({"upload_bundle": str(BUNDLE), "sha256": sha256(BUNDLE),
                      "manifest": manifest}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
