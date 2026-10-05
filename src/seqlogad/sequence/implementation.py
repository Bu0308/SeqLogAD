"""Bind Sequence execution to the actual packaged Python implementation."""
import hashlib
from pathlib import Path


def implementation_digest(repo_root):
    root = Path(repo_root)
    base = root / "src/seqlogad"
    files = [base / "__init__.py"]
    for package in ("common", "protocol", "semantic", "sequence", "phase2_execution"):
        files.extend((base / package).glob("*.py"))
    files = sorted(files)
    if not files:
        raise ValueError("missing executable code for Sequence identity")
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()
