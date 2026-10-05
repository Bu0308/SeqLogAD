"""Independently verify the V13R1 upload kit and packaged execution identity."""
import json
from pathlib import Path
import tempfile
import zipfile

from seqlogad.common.checksum import sha256_file
from seqlogad.sequence.implementation import implementation_digest


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "outputs/runpod/P2.2-S42-A40-V13R1"


def members(path):
    with zipfile.ZipFile(path) as handle:
        assert handle.testzip() is None
        return set(handle.namelist())


def main():
    manifest = json.loads((KIT / "RUNPOD_UPLOAD_MANIFEST.json").read_text())
    assert manifest["encoding_variant"] == "LORA-SEQ-003-R1-v1.3.1"
    assert manifest["checkpoint_selection"] == "MAX_MACRO_SOURCE_DEVELOPMENT_F1"
    assert manifest["target_labels_used_for_selection"] is False
    assert "recall" in manifest["source_development_metrics"]
    assert manifest["persistent_results"] == "/workspace/SeqLogAD/sequence-v13r1/P2.2"
    for name, expected in manifest["files"].items():
        path = KIT / name
        assert path.stat().st_size == expected["size"]
        assert sha256_file(path) == expected["sha256"]
        if path.suffix in {".zip", ".whl"}:
            members(path)
    outer = ROOT / "outputs/runpod/P2.2-S42-A40-V13R1-upload.zip"
    assert members(outer) == set(manifest["files"]) | {"RUNPOD_UPLOAD_MANIFEST.json", "README.md"}
    assert sha256_file(ROOT / "outputs/runpod/P2.2-S42-A40-V13-upload.zip") == (
        "4b21251d68f9bc0117c7ff21c7fb42aae30efbebf43f824c76e505781578bc34"
    )
    code_zip = KIT / "seqlogad-code-all-experts-s42-v13r1.zip"
    code_members = members(code_zip)
    for suffix in (
        "/sequence/evaluation_forward.py", "/sequence/implementation.py",
        "/sequence/optimization.py", "/phase2_execution/durable_attempt.py",
        "/configs/models/sequence-reference-v13r1.yaml",
    ):
        assert any(name.endswith(suffix) for name in code_members), suffix
    with tempfile.TemporaryDirectory() as folder, zipfile.ZipFile(code_zip) as handle:
        handle.extractall(folder)
        packaged_root = Path(folder) / "seqlogad_code_all_experts_s42"
        assert implementation_digest(packaged_root) == implementation_digest(ROOT)
    label_zip = KIT / "phase2-source-development-v13r1.zip"
    assert not any(name.endswith("anomaly_label.csv") or name.endswith("BGL.log")
                   for name in members(label_zip))
    with zipfile.ZipFile(label_zip) as handle:
        prefix = "phase2_source_development_v13r1/"
        label_manifest = json.loads(handle.read(prefix + "manifest.json"))
        assert label_manifest["target_labels_used_for_selection"] is False
        assert "target_labels_read" not in label_manifest
        assert label_manifest["sequence_bundle_sha256"] == manifest["sequence_bundle_manifest_sha256"]
        assert sha256_file(ROOT / "data/phase2-source-dev-v13r1/manifest.json") == (
            manifest["source_development_manifest_sha256"]
        )
        for fold_id in label_manifest["folds"]:
            fold = json.loads((ROOT / "data/phase2-sequence/folds" / fold_id /
                               "manifests/fold.json").read_text())
            entries = json.loads(handle.read(prefix + fold_id + ".json"))["entries"]
            assert entries
            assert {row["architecture_id"] for row in entries} <= set(fold["source_architectures"])
            assert all(row["architecture_id"] != fold["target_architecture"] for row in entries)
    notebook = json.loads((KIT / "P2.2_run_all_sequence_lora_s42_v13r1.ipynb").read_text())
    code = "\n".join("".join(cell["source"]) for cell in notebook["cells"]
                     if cell["cell_type"] == "code")
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"V13R1-cell-{index}", "exec")
    assert '"--sequence-candidate", "v13r1"' in code
    assert code.count('"init", "--name", "SeqLogAD Sequence V13R1"') == 1
    assert '"--metrics"' in code and "durable_attempt" in code
    assert "journal(\"STARTED\")" in code and "journal(\"COMPLETED\")" in code
    assert manifest["source_development_manifest_sha256"] in code
    print(json.dumps({"status": "PASS", "upload_sha256": sha256_file(outer),
                      "file_count": len(manifest["files"]),
                      "source_only_folds": len(label_manifest["folds"]),
                      "notebook_cells": len(notebook["cells"])}))


if __name__ == "__main__":
    main()
