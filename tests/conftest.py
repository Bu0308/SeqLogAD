"""Shared offline fixtures for Day 2 dataset-tooling tests."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from src.ingestion.dataset_config import DatasetDefinition


FIXTURE_ROOT = Path(__file__).parent / "fixtures/datasets"


@pytest.fixture
def make_dataset_project(tmp_path: Path) -> Callable[[str], tuple[Path, DatasetDefinition]]:
    """Copy a tiny synthetic dataset and return its validated acquisition contract."""

    def _make(fixture_name: str) -> tuple[Path, DatasetDefinition]:
        project_root = tmp_path / fixture_name
        raw_root = project_root / "data/raw/sample"
        raw_root.parent.mkdir(parents=True)
        shutil.copytree(FIXTURE_ROOT / fixture_name, raw_root)
        config = DatasetDefinition.model_validate(
            {
                "key": "sample",
                "dataset_id": "SYNTHETIC_SAMPLE",
                "dataset_name": "Synthetic dataset fixture",
                "dataset_version": "fixture-v1",
                "enabled": True,
                "priority": "P0",
                "source": {
                    "name": "Local test fixture",
                    "reference": "tests/fixtures/datasets",
                    "accessed_on": "2026-08-07",
                },
                "raw_dir": "data/raw/sample",
                "manifest_path": "data/manifests/sample_manifest.json",
                "expected_files": [
                    {
                        "path": "sample.log",
                        "required": True,
                        "role": "log",
                        "description": "Synthetic log fixture.",
                    },
                    {
                        "path": "labels.csv",
                        "required": True,
                        "role": "label",
                        "description": "Synthetic labels fixture.",
                    },
                    {
                        "path": "sample.zip",
                        "required": False,
                        "role": "archive",
                        "description": "Synthetic download target.",
                    },
                ],
                "labels": {
                    "available": True,
                    "file": "labels.csv",
                    "level": "trace",
                    "notes": "Synthetic labels only.",
                },
                "acquisition": {
                    "method": "archive_download",
                    "url": "https://example.invalid/sample.zip",
                    "archive": "sample.zip",
                    "manual_fallback": "Use the committed synthetic fixture.",
                },
                "licensing": {
                    "status": "TEST_FIXTURE",
                    "source_license": "PROJECT_TEST_DATA",
                    "usage_notes": "Synthetic content created for offline tests.",
                    "review_required": False,
                },
            }
        )
        return project_root, config

    return _make
