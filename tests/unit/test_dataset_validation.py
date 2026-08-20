"""Unit tests for dataset configuration and presence states."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from seqlogad.ingestion.dataset_config import DatasetDefinition, load_dataset_config
from seqlogad.ingestion.dataset_validation import DatasetPresenceStatus, validate_dataset_presence
from seqlogad.ingestion.errors import DatasetConfigError


ProjectFactory = Callable[[str], tuple[Path, DatasetDefinition]]


def test_complete_dataset_is_present(make_dataset_project: ProjectFactory) -> None:
    root, config = make_dataset_project("complete_dataset")
    report = validate_dataset_presence(config, project_root=root)
    assert report.status is DatasetPresenceStatus.PRESENT
    assert report.required_present == report.required_count == 2


def test_partial_dataset_reports_missing_file(make_dataset_project: ProjectFactory) -> None:
    root, config = make_dataset_project("partial_dataset")
    report = validate_dataset_presence(config, project_root=root)
    assert report.status is DatasetPresenceStatus.PARTIAL
    assert report.missing_required_files == ["labels.csv"]


def test_missing_dataset_is_missing(make_dataset_project: ProjectFactory) -> None:
    root, config = make_dataset_project("complete_dataset")
    (root / "data/raw/sample/sample.log").unlink()
    (root / "data/raw/sample/labels.csv").unlink()
    report = validate_dataset_presence(config, project_root=root)
    assert report.status is DatasetPresenceStatus.MISSING
    assert report.required_present == 0


def test_malformed_dataset_config_has_domain_error(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "broken.yaml").write_text(
        "dataset:\n  key: broken\n  unexpected: true\n",
        encoding="utf-8",
    )
    with pytest.raises(DatasetConfigError, match="Malformed dataset config"):
        load_dataset_config("broken", config_dir=config_dir)


def test_invalid_dataset_key_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(DatasetConfigError, match="Invalid dataset key"):
        load_dataset_config("../hdfs", config_dir=tmp_path)


def test_unknown_dataset_name_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(DatasetConfigError, match="does not exist"):
        load_dataset_config("unknown", config_dir=tmp_path)


def test_core_dataset_configs_load_and_have_required_files() -> None:
    config_dir = Path(__file__).parents[2] / "configs/datasets"
    hdfs = load_dataset_config("hdfs", config_dir=config_dir)
    bgl = load_dataset_config("bgl", config_dir=config_dir)
    assert [item.path for item in hdfs.expected_files if item.required] == [
        "HDFS.log",
        "preprocessed/anomaly_label.csv",
    ]
    assert [item.path for item in bgl.expected_files if item.required] == ["BGL.log"]
    assert hdfs.raw_dir == "data/raw/hdfs/HDFS_v1"
    assert bgl.raw_dir == "data/raw/bgl/BGL"
