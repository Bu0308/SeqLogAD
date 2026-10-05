"""Scientific checks for source-only F1 selection and threshold-free metrics."""
import json
from pathlib import Path

import polars as pl
import pytest

from seqlogad.common.checksum import sha256_file
from seqlogad.sequence.source_development import _fold_entries, load_source_development, SCHEMA
from seqlogad.sequence.source_development_metrics import source_development_metrics
from seqlogad.sequence.config import development_run_id, load_config
from seqlogad.phase2_execution.runner import run_all_targets


ROOT = Path(__file__).resolve().parents[1]


def test_v13_config_and_runner_require_trusted_source_labels(tmp_path):
    cfg, _ = load_config(ROOT, candidate="v13")
    assert cfg["checkpoint_selection"] == "MAX_MACRO_SOURCE_DEVELOPMENT_F1"
    assert "recall" in cfg["source_development"]["metrics"]
    assert development_run_id("FOLD-TARGET-ARCH-BGL", candidate="v13").endswith("-V13")
    with pytest.raises(ValueError, match="trusted source-development sidecar"):
        run_all_targets(task_id="P2.2", repo_root=ROOT,
                        data_root=tmp_path / "missing-data", output_root=tmp_path / "out",
                        drive_root=tmp_path / "persistent", expected_bundle_sha256="a" * 64,
                        sequence_candidate="v13")


def test_source_metrics_use_unit_mean_and_report_recall():
    labels = {
        "a": {"architecture_id": "ARCH-HDFS", "unit_id": "block-positive",
              "anomaly": True},
        "b": {"architecture_id": "ARCH-HDFS", "unit_id": "block-positive",
              "anomaly": True},
        "c": {"architecture_id": "ARCH-HDFS", "unit_id": "block-negative",
              "anomaly": False},
    }
    scores = [
        {"window_id": "a", "architecture_id": "ARCH-HDFS", "nll": 0.9},
        {"window_id": "b", "architecture_id": "ARCH-HDFS", "nll": 0.7},
        {"window_id": "c", "architecture_id": "ARCH-HDFS", "nll": 0.2},
    ]
    result = source_development_metrics(scores, labels)
    source = result["per_source"]["ARCH-HDFS"]
    assert source["units"] == 2 and source["scored_windows"] == 3
    assert source["threshold"] == pytest.approx(0.8)
    assert source["recall"] == source["precision"] == source["f1"] == 1.0
    assert source["auroc"] == source["average_precision"] == 1.0
    assert result["macro_recall"] == 1.0


def test_source_metrics_ties_and_missing_class_fail_closed():
    labels = {
        "a": {"architecture_id": "ARCH-BGL", "unit_id": "a", "anomaly": True},
        "b": {"architecture_id": "ARCH-BGL", "unit_id": "b", "anomaly": False},
    }
    scores = [{"window_id": key, "architecture_id": "ARCH-BGL", "nll": 0.5}
              for key in labels]
    result = source_development_metrics(scores, labels)["per_source"]["ARCH-BGL"]
    assert result["recall"] == 1.0
    assert result["f1"] == pytest.approx(2 / 3)
    assert result["auroc"] == result["average_precision"] == 0.5
    with pytest.raises(ValueError, match="coverage"):
        source_development_metrics(scores[:1], labels)


def test_source_fold_rejects_target_and_conflicting_unit_labels(tmp_path):
    fold_id = "FOLD-TARGET-ARCH-BGL"
    base = tmp_path / "folds" / fold_id
    (base / "manifests").mkdir(parents=True)
    (base / "sequence/val").mkdir(parents=True)
    (base / "manifests/fold.json").write_text(json.dumps({
        "target_architecture": "ARCH-BGL", "source_architectures": ["ARCH-HDFS"]
    }))
    pl.DataFrame([
        {"window_id": "a", "architecture_id": "ARCH-HDFS", "target_rank": 1,
         "sequence_id": "block-1"},
        {"window_id": "b", "architecture_id": "ARCH-HDFS", "target_rank": 2,
         "sequence_id": "block-1"},
        {"window_id": "c", "architecture_id": "ARCH-HDFS", "target_rank": 3,
         "sequence_id": "block-2"},
    ]).write_parquet(base / "sequence/val/windows.parquet")
    with pytest.raises(ValueError, match="conflicting HDFS block labels"):
        _fold_entries(tmp_path, fold_id, {"ARCH-HDFS": {1: True, 2: False, 3: False}})
    entries = _fold_entries(tmp_path, fold_id, {"ARCH-HDFS": {1: True, 2: True, 3: False}})
    assert len(entries) == 3 and all(row["architecture_id"] == "ARCH-HDFS" for row in entries)


def test_sidecar_loader_checks_bundle_and_target_role(tmp_path):
    fold_id = "FOLD-TARGET-ARCH-BGL"
    data, sidecar = tmp_path / "data", tmp_path / "labels"
    (data / "manifests").mkdir(parents=True)
    (data / "manifests/bundle.json").write_text("{}")
    (data / "folds" / fold_id / "manifests").mkdir(parents=True)
    (data / "folds" / fold_id / "manifests/fold.json").write_text(json.dumps({
        "target_architecture": "ARCH-BGL", "source_architectures": ["ARCH-HDFS"]
    }))
    sidecar.mkdir()
    entries = [
        {"architecture_id": "ARCH-HDFS", "window_id": "positive",
         "target_rank": 1, "unit_id": "block-1", "anomaly": True},
        {"architecture_id": "ARCH-HDFS", "window_id": "negative",
         "target_rank": 2, "unit_id": "block-2", "anomaly": False},
    ]
    name = fold_id + ".json"
    (sidecar / name).write_text(json.dumps({"entries": entries}))
    manifest = {"schema": SCHEMA, "target_labels_used_for_selection": False,
                "sequence_bundle_sha256": sha256_file(data / "manifests/bundle.json"),
                "folds": [fold_id], "files": {name: sha256_file(sidecar / name)}}
    (sidecar / "manifest.json").write_text(json.dumps(manifest))
    selected = [dict(window_id=row["window_id"], architecture_id=row["architecture_id"],
                     target_rank=row["target_rank"]) for row in entries]
    assert len(load_source_development(sidecar, data, fold_id, selected)) == 2
    selected[0]["architecture_id"] = "ARCH-BGL"
    with pytest.raises(ValueError, match="selection identity"):
        load_source_development(sidecar, data, fold_id, selected)
