"""Day 1 smoke test for the supported Python runtime."""

import sys


def test_python_runtime_meets_project_policy() -> None:
    """The project policy requires Python 3.11 or newer."""
    assert sys.version_info >= (3, 11)
