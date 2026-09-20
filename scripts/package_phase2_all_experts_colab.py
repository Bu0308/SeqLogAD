"""Build the shared Phase-2 seed-42 code upload and audit data-view readiness."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from seqlogad.common.checksum import sha256_file
from seqlogad.phase2_execution.archive import create_zip, seal_tree, verify_zip
from seqlogad.semantic.prepare import git_state


CODE_NAME = "seqlogad-code-all-experts-s42.zip"
DATA_NAME = "phase2-all-experts-s42.zip"


def _copy(source, root, stage):
    target = stage / source.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def package_code(root=Path("."), destination=None):
    root = Path(root).resolve()
    destination = Path(destination or root / "outputs/colab" / CODE_NAME)
    with tempfile.TemporaryDirectory() as folder:
        stage = Path(folder) / "seqlogad_code_all_experts_s42"
        fixed = [
            root / "pyproject.toml",
            root / "configs/models/base-freeze-v1.yaml",
            root / "configs/models/semantic-v1.yaml",
            root / "configs/models/sequence-reference-v1.yaml",
            root / "configs/protocols/phase2-architecture-v1.yaml",
            root / "configs/protocols/phase2-development-s42-v1.yaml",
            root / "src/seqlogad/__init__.py",
        ]
        paths = list(fixed)
        for package in ("common", "protocol", "semantic", "sequence", "phase2_execution"):
            paths.extend(sorted((root / "src/seqlogad" / package).glob("*.py")))
        for source in paths:
            if not source.is_file():
                raise ValueError(f"required code package file missing: {source}")
            _copy(source, root, stage)
        git = git_state(root)
        # Exact packaged-file hashes below are the reproducible code identity.
        # A whole-worktree diff digest would also include notebooks/reports that
        # embed this archive's hash, creating a self-referential package cycle.
        git.pop("diff_sha256", None)
        provenance = {
            "schema": "SEQLOGAD-CODE-PROVENANCE-2",
            "git": git,
            "files": {
                path.relative_to(stage).as_posix(): sha256_file(path)
                for path in sorted(stage.rglob("*")) if path.is_file()
            },
            "real_gpu_training_performed": False,
            "seed": 42,
        }
        (stage / "CODE_PROVENANCE.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
        seal_tree(stage)
        return create_zip(stage, destination, stage.name)


def inspect_data_readiness(root=Path(".")):
    root = Path(root).resolve()
    semantic_zip = root / "outputs/colab/phase2-final.zip"
    if not semantic_zip.is_file():
        return {"ready": False, "blockers": ["SEMANTIC_DATA_PACKAGE_MISSING"]}
    verify_zip(semantic_zip, require_ledger=False)
    blockers = []
    view_roots = {
        "sequence": root / "data/phase2-sequence",
        "graph": root / "data/phase2",
    }
    for fold in ("FOLD-TARGET-ARCH-BGL", "FOLD-TARGET-ARCH-HDFS", "FOLD-TARGET-ARCH-HADOOP"):
        for view, required in {
            "sequence": ("train/windows.parquet", "val/windows.parquet", "metadata/events.parquet", "metadata/view.json"),
            "graph": ("train/graphs.parquet", "val/graphs.parquet", "metadata/nodes.parquet", "metadata/view.json"),
        }.items():
            prepared = view_roots[view]
            if any(not (prepared / "folds" / fold / view / name).is_file() for name in required):
                blockers.append(f"{fold}:{view.upper()}_VIEW_NOT_MATERIALIZED")
    return {
        "ready": not blockers,
        "semantic_zip": str(semantic_zip),
        "semantic_zip_size": semantic_zip.stat().st_size,
        "semantic_zip_sha256": sha256_file(semantic_zip),
        "requested_data_zip": str(root / "outputs/colab" / DATA_NAME),
        "blockers": blockers,
    }


if __name__ == "__main__":
    print(json.dumps({"code": package_code(), "data": inspect_data_readiness()}, indent=2))
