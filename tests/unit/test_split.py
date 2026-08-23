"""Synthetic-only SPLIT-001 generation, reconciliation, and guard tests."""

from __future__ import annotations

import ast
import inspect
import json
import shutil
from pathlib import Path

import pytest
import yaml

from seqlogad.common.schemas import ScientificPartition
from seqlogad.evaluation.split import (
    SplitError,
    compare_split_artifacts,
    cumulative_floor_boundaries,
    generate_split_artifact,
    iter_partition_assignments,
    nominal_partition_index,
    split_status,
    validate_frozen_split_prerequisites,
    validate_split_artifact,
)
from seqlogad.evaluation.test_seal import TestAccessDeniedError
from seqlogad.ingestion.dataset_config import DatasetDefinition
from seqlogad.ingestion.dataset_manifest import (
    build_dataset_manifest,
    write_dataset_manifest,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _dataset_definition(dataset: str) -> DatasetDefinition:
    is_hdfs = dataset == "hdfs"
    raw_dir = f"data/raw/{dataset}/synthetic"
    expected = [
        {
            "path": "HDFS.log" if is_hdfs else "BGL.log",
            "required": True,
            "role": "log",
            "description": "Synthetic structural fixture",
        }
    ]
    if is_hdfs:
        expected.append(
            {
                "path": "anomaly_label.csv",
                "required": True,
                "role": "label",
                "description": "Sentinel label file that splitter must not open",
            }
        )
    return DatasetDefinition.model_validate(
        {
            "key": dataset,
            "dataset_id": f"SYNTHETIC_{dataset.upper()}",
            "dataset_name": f"Synthetic {dataset}",
            "dataset_version": "fixture-v1",
            "enabled": True,
            "priority": "P0",
            "source": {
                "name": "Synthetic fixture",
                "reference": "tests/unit/test_split.py",
                "accessed_on": "2026-08-23",
            },
            "raw_dir": raw_dir,
            "manifest_path": f"data/manifests/{dataset}_manifest.json",
            "expected_files": expected,
            "labels": {
                "available": True,
                "file": "anomaly_label.csv" if is_hdfs else "BGL.log",
                "level": "block" if is_hdfs else "line",
                "notes": "Never consumed by SPLIT-001",
            },
            "acquisition": {
                "method": "manual",
                "manual_fallback": "Synthetic test fixture",
            },
            "licensing": {
                "status": "TEST_FIXTURE",
                "source_license": "PROJECT_TEST_DATA",
                "usage_notes": "Synthetic content",
                "review_required": False,
            },
        }
    )


def _project(tmp_path: Path, dataset: str, raw_bytes: bytes) -> tuple[Path, Path]:
    root = tmp_path / f"project-{dataset}"
    (root / "configs/protocols").mkdir(parents=True)
    (root / "configs/datasets").mkdir()
    for name in (
        "protocol-v1.1.yaml",
        "effect-001.yaml",
        "split-clarification-v1.yaml",
    ):
        shutil.copy2(PROJECT_ROOT / "configs/protocols" / name, root / "configs/protocols" / name)
    definition = _dataset_definition(dataset)
    raw_root = root / definition.raw_dir
    raw_root.mkdir(parents=True)
    log_path = raw_root / ("HDFS.log" if dataset == "hdfs" else "BGL.log")
    log_path.write_bytes(raw_bytes)
    if dataset == "hdfs":
        (raw_root / "anomaly_label.csv").write_text(
            "BlockId,Label\nblk_1,Normal\n", encoding="utf-8"
        )
    (root / "configs/datasets" / f"{dataset}.yaml").write_text(
        yaml.safe_dump({"dataset": definition.model_dump(mode="json")}, sort_keys=False),
        encoding="utf-8",
    )
    manifest = build_dataset_manifest(definition, project_root=root)
    write_dataset_manifest(manifest, root / definition.manifest_path)
    return root, log_path


def _hdfs_fixture() -> bytes:
    # Twenty eligible ranks. blk_99 occupies ranks 11/12 and is purged at 60%.
    lines = []
    for rank in range(20):
        block = "blk_99" if rank in {11, 12} else f"blk_{rank}"
        lines.append(f"source message {block}\n".encode())
    lines.insert(5, b"structurally invalid line without block\n")
    return b"".join(lines)


def _bgl_fixture(label: str = "-") -> bytes:
    return b"".join(
        f"{label} arbitrary bytes ignored by raw-rank splitter {index}\n".encode()
        for index in range(1037)
    )


def test_frozen_boundary_arithmetic_and_zero_length_partitions() -> None:
    assert cumulative_floor_boundaries(20) == (0, 12, 14, 16, 18, 20)
    assert cumulative_floor_boundaries(3) == (0, 1, 2, 2, 2, 3)
    assert [nominal_partition_index(rank, cumulative_floor_boundaries(3)) for rank in range(3)] == [0, 1, 4]
    with pytest.raises(ValueError):
        cumulative_floor_boundaries(-1)


def test_prerequisites_are_frozen_and_human_authorized() -> None:
    result = validate_frozen_split_prerequisites(PROJECT_ROOT)
    assert result["protocol"]["version"] == "1.1"
    assert result["effect"]["status"] == "FROZEN_HUMAN_APPROVED"
    assert result["split"]["split_execution_authorized"] is True


def test_split_module_has_no_parser_model_or_label_input_dependency() -> None:
    from seqlogad.evaluation import split as split_module

    tree = ast.parse(Path(split_module.__file__).read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert all(not item.startswith("seqlogad.parsing") for item in imported)
    assert all(not item.startswith("seqlogad.models") for item in imported)
    parameters = inspect.signature(generate_split_artifact).parameters
    assert all("label" not in name and "parser" not in name for name in parameters)


def test_hdfs_real_workflow_on_synthetic_bytes_is_atomic_and_reconciled(tmp_path: Path) -> None:
    root, _ = _project(tmp_path, "hdfs", _hdfs_fixture())
    output = root / "data/processed/splits/hdfs"
    generated = generate_split_artifact(
        project_root=root,
        dataset_key="hdfs",
        output_directory=output,
        generated_at_utc="2026-08-23T00:00:00Z",
    )
    verified = validate_split_artifact(output)
    semantics = generated["dataset_semantics"]
    assert semantics["total_raw_lines"] == 21
    assert semantics["eligible_lines_pre_purge"] == 20
    assert semantics["structurally_ineligible_lines"] == 1
    assert semantics["purged_component_count"] == 1
    assert semantics["purged_boundary_eligible_lines"] == 2
    assert semantics["assigned_eligible_lines"] == 18
    assert verified["status"] == "VERIFIED"
    assert verified["test_status"] == "SEALED"
    assert verified["never_opened"] is True
    with pytest.raises(TestAccessDeniedError):
        list(iter_partition_assignments(output, ScientificPartition.TEST))
    assert list(iter_partition_assignments(output, ScientificPartition.BASE_TRAIN))


def test_bgl_split_first_then_per_partition_windows_and_residuals(tmp_path: Path) -> None:
    root, _ = _project(tmp_path, "bgl", _bgl_fixture())
    output = root / "data/processed/splits/bgl"
    generated = generate_split_artifact(
        project_root=root,
        dataset_key="bgl",
        output_directory=output,
        generated_at_utc="2026-08-23T00:00:00Z",
    )
    verified = validate_split_artifact(output)
    semantics = generated["dataset_semantics"]
    assert semantics["boundaries"] == [0, 622, 725, 829, 933, 1037]
    assert list(semantics["partition_raw_line_counts"].values()) == [622, 103, 104, 104, 104]
    assert list(semantics["partition_complete_parent_window_counts"].values()) == [6, 1, 1, 1, 1]
    assert list(semantics["partition_residual_line_counts"].values()) == [22, 3, 4, 4, 4]
    assert verified["structural_reconciliation"] == {
        "complete_windows": 10,
        "retained_lines": 1000,
        "residual_lines": 37,
    }


@pytest.mark.parametrize(("dataset", "raw"), [("hdfs", _hdfs_fixture()), ("bgl", _bgl_fixture())])
def test_split_regeneration_is_deterministic(tmp_path: Path, dataset: str, raw: bytes) -> None:
    root, _ = _project(tmp_path, dataset, raw)
    first = root / "first"
    second = root / "second"
    generate_split_artifact(
        project_root=root,
        dataset_key=dataset,
        output_directory=first,
        generated_at_utc="2026-08-23T00:00:00Z",
    )
    generate_split_artifact(
        project_root=root,
        dataset_key=dataset,
        output_directory=second,
        generated_at_utc="2026-08-23T00:01:00Z",
    )
    comparison = compare_split_artifacts(first, second)
    assert comparison == {"deterministic": True, "mismatches": []}
    assert split_status(first)["test_status"] == "SEALED"
    assert split_status(second)["test_status"] == "SEALED"


def test_hdfs_label_file_is_not_opened_by_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = _project(tmp_path, "hdfs", _hdfs_fixture())
    forbidden = (root / "data/raw/hdfs/synthetic/anomaly_label.csv").resolve()
    original_open = Path.open

    def guarded_open(path: Path, *args: object, **kwargs: object):
        if path.resolve() == forbidden:
            raise AssertionError("SPLIT-001 attempted to open HDFS labels")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    generate_split_artifact(
        project_root=root,
        dataset_key="hdfs",
        output_directory=root / "split",
        generated_at_utc="2026-08-23T00:00:00Z",
    )


def test_bgl_inline_label_change_cannot_change_structural_allocation() -> None:
    # The splitter accepts only source-line count for BGL allocation/windowing.
    from seqlogad.evaluation import split as split_module

    assert inspect.signature(split_module._bgl_decisions).parameters.keys() == {
        "log_path",
        "source",
        "partition_spools",
        "exclusion_spool",
    }
    assert _bgl_fixture("-").count(b"\n") == _bgl_fixture("ALERT").count(b"\n")


def test_corrupted_partition_record_fails_validation(tmp_path: Path) -> None:
    root, _ = _project(tmp_path, "bgl", _bgl_fixture())
    output = root / "split"
    generate_split_artifact(
        project_root=root,
        dataset_key="bgl",
        output_directory=output,
        generated_at_utc="2026-08-23T00:00:00Z",
    )
    path = output / "partitions/BASE_TRAIN.jsonl"
    first, *rest = path.read_text(encoding="utf-8").splitlines()
    record = json.loads(first)
    record["raw_line_count"] = 99
    path.write_text("\n".join([json.dumps(record), *rest]) + "\n", encoding="utf-8")
    with pytest.raises(SplitError):
        validate_split_artifact(output)


def test_substituted_sealed_test_content_fails_structural_verification(tmp_path: Path) -> None:
    root, _ = _project(tmp_path, "bgl", _bgl_fixture())
    output = root / "split"
    generate_split_artifact(
        project_root=root,
        dataset_key="bgl",
        output_directory=output,
        generated_at_utc="2026-08-23T00:00:00Z",
    )
    with (output / "sealed/TEST.jsonl").open("ab") as handle:
        handle.write(b'{"substituted":true}\n')
    with pytest.raises(SplitError):
        validate_split_artifact(output)


def test_status_never_opens_test(tmp_path: Path) -> None:
    root, _ = _project(tmp_path, "bgl", _bgl_fixture())
    output = root / "split"
    generate_split_artifact(
        project_root=root,
        dataset_key="bgl",
        output_directory=output,
        generated_at_utc="2026-08-23T00:00:00Z",
    )
    assert split_status(output)["test_status"] == "SEALED"
    assert (output / "test-access-audit.jsonl").read_bytes() == b""
