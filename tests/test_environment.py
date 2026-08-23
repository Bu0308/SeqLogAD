"""ENV-001 smoke tests for the installed package and dependency contract."""

import importlib.metadata
import os
import subprocess
import sys
from pathlib import Path

from packaging.version import Version


def test_python_runtime_meets_project_policy() -> None:
    """The tested project environment is Python 3.12.x."""
    assert (3, 12) <= sys.version_info[:2] < (3, 13)


def test_canonical_package_and_dependency_contract() -> None:
    """Core packages import under seqlogad and match declared compatibility bounds."""

    import drain3
    import pyarrow
    import seqlogad
    from seqlogad.common import checksum
    from seqlogad.ingestion import dataset_manifest

    assert seqlogad is not None
    assert checksum is not None
    assert dataset_manifest is not None
    assert drain3 is not None
    assert importlib.metadata.version("seqlogad") == "0.1.0"
    assert Version("17") <= Version(pyarrow.__version__) < Version("20")
    assert Version("0.9") <= Version(importlib.metadata.version("drain3")) < Version("1")


def test_import_contract_is_independent_of_repository_cwd(tmp_path: Path) -> None:
    """Editable installation must expose imports without PYTHONPATH or cwd tricks."""

    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import seqlogad; "
                "import seqlogad.common.checksum; "
                "import seqlogad.ingestion.dataset_manifest; "
                "import seqlogad.cli.verify_dataset; "
                "import seqlogad.cli.fit_parser"
            ),
        ],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_installed_cli_help_runs_outside_repository(tmp_path: Path) -> None:
    """The packaged verifier CLI must load safely from an unrelated directory."""

    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-m", "seqlogad.cli.verify_dataset", "--help"],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "--project-root" in result.stdout

    parser_result = subprocess.run(
        [sys.executable, "-m", "seqlogad.cli.fit_parser", "--help"],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert parser_result.returncode == 0, parser_result.stderr
    assert "--project-root" in parser_result.stdout
