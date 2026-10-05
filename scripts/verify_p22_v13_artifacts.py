"""Verify the immutable V13 RunPod upload and source-only label boundary."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from seqlogad.common.checksum import sha256_file


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "outputs/runpod/P2.2-S42-A40-V13"


def members(path):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"ZIP CRC failed: {path}")
        return set(archive.namelist())


def main():
    manifest = json.loads((KIT / "RUNPOD_UPLOAD_MANIFEST.json").read_text())
    assert manifest["encoding_variant"] == "LORA-SEQ-003-v1.3"
    assert manifest["checkpoint_selection"] == "MAX_MACRO_SOURCE_DEVELOPMENT_F1"
    assert manifest["target_label_access"] is False
    assert "recall" in manifest["source_development_metrics"]
    assert manifest["persistent_results"] == "/workspace/SeqLogAD/sequence-v13/P2.2"
    for name, expected in manifest["files"].items():
        path = KIT / name
        assert path.stat().st_size == expected["size"]
        assert sha256_file(path) == expected["sha256"]
        if path.suffix in {".zip", ".whl"}:
            members(path)
    outer = ROOT / "outputs/runpod/P2.2-S42-A40-V13-upload.zip"
    assert members(outer) == set(manifest["files"]) | {"RUNPOD_UPLOAD_MANIFEST.json", "README.md"}
    code_members = members(KIT / "seqlogad-code-all-experts-s42-v13.zip")
    for suffix in (
        "/sequence/source_development.py", "/sequence/source_development_metrics.py",
        "/sequence/source_validation.py", "/configs/models/sequence-reference-v13.yaml",
    ):
        assert any(name.endswith(suffix) for name in code_members), suffix
    label_zip = KIT / "phase2-source-development-v13.zip"
    label_members = members(label_zip)
    assert not any(name.endswith("anomaly_label.csv") or name.endswith("BGL.log")
                   for name in label_members)
    with zipfile.ZipFile(label_zip) as archive:
        prefix = "phase2_source_development_v13/"
        label_manifest = json.loads(archive.read(prefix + "manifest.json"))
        assert label_manifest["target_labels_read"] is False
        assert label_manifest["sequence_bundle_sha256"] == manifest["sequence_bundle_manifest_sha256"]
        for fold_id in label_manifest["folds"]:
            fold = json.loads((ROOT / "data/phase2-sequence/folds" / fold_id / "manifests/fold.json").read_text())
            entries = json.loads(archive.read(prefix + fold_id + ".json"))["entries"]
            assert entries
            assert {row["architecture_id"] for row in entries} <= set(fold["source_architectures"])
            assert all(row["architecture_id"] != fold["target_architecture"] for row in entries)
    notebook = json.loads((KIT / "P2.2_run_all_sequence_lora_s42_v13.ipynb").read_text())
    code = "\n".join("".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code")
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"V13-cell-{index}", "exec")
    assert '"--sequence-candidate", "v13"' in code
    assert '"--metric", "source_development_macro_f1"' in code
    assert '"--metric-direction", "max"' in code
    assert manifest["source_development_manifest_sha256"] in code
    print(json.dumps({"status": "PASS", "upload_sha256": sha256_file(outer),
                      "file_count": len(manifest["files"]),
                      "source_only_folds": len(label_manifest["folds"]),
                      "notebook_cells": len(notebook["cells"])}, sort_keys=True))


if __name__ == "__main__":
    main()
