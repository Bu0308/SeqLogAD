"""Secure deterministic artifact ZIP creation and verification."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from seqlogad.common.checksum import sha256_file


TOKEN_PATTERN = re.compile(rb"hf_[A-Za-z0-9]{20,}")
FORBIDDEN_NAMES = {".env", "credentials.json", "service-account.json"}
BASE_WEIGHT_PATTERNS = (
    re.compile(r"(^|/)pytorch_model(?:-\d+-of-\d+)?\.bin$"),
    re.compile(r"(^|/)model(?:-\d+-of-\d+)?\.safetensors$"),
    re.compile(r"(^|/)consolidated(?:\.\d+)?\.pth$"),
)


def _safe_member(name):
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"unsafe ZIP member: {name!r}")
    return path


def _forbidden_name(name):
    lowered = name.lower()
    if PurePosixPath(lowered).name in FORBIDDEN_NAMES:
        return True
    if any(part in {".cache", "huggingface", "hub"} for part in PurePosixPath(lowered).parts):
        return True
    return any(pattern.search(lowered) for pattern in BASE_WEIGHT_PATTERNS)


def _scan_token_stream(handle):
    tail = b""
    while True:
        block = handle.read(1024 * 1024)
        if not block:
            return
        candidate = tail + block
        if TOKEN_PATTERN.search(candidate):
            raise ValueError("secret/HF token detected in archive")
        tail = candidate[-128:]


def seal_tree(root):
    root = Path(root)
    ledger = root / "checksums.sha256"
    files = {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path != ledger
    }
    ledger.write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(files.items())))
    return files


def verify_tree_ledger(root, ledger=None):
    root = Path(root)
    ledger = Path(ledger) if ledger else root / "checksums.sha256"
    if not ledger.is_file():
        raise ValueError(f"missing checksum ledger: {root}")
    declared = {}
    for line in ledger.read_text().splitlines():
        digest, name = line.split("  ", 1)
        _safe_member(name)
        if name in declared:
            raise ValueError("duplicate checksum ledger entry")
        path = root / name
        if not path.is_file() or path.is_symlink() or sha256_file(path) != digest:
            raise ValueError(f"checksum mismatch: {name}")
        declared[name] = digest
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != ledger
    }
    if set(declared) != actual:
        raise ValueError("checksum ledger is not exhaustive")
    return declared


def create_zip(source_root, destination, archive_root=None):
    source = Path(source_root)
    destination = Path(destination)
    if not source.is_dir() or source.is_symlink():
        raise ValueError("archive source must be a real directory")
    if archive_root is None:
        archive_root = source.name
    _safe_member(archive_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".partial")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as handle:
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise ValueError("archive symlink forbidden")
            if not path.is_file():
                continue
            relative = path.relative_to(source).as_posix()
            name = f"{archive_root}/{relative}"
            _safe_member(name)
            if _forbidden_name(name):
                raise ValueError(f"forbidden archive member: {name}")
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            handle.writestr(info, path.read_bytes())
    verify_zip(temporary)
    os.replace(temporary, destination)
    return verify_zip(destination)


def verify_zip(archive, require_ledger=True):
    archive = Path(archive)
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("ZIP is missing or is a symlink")
    with zipfile.ZipFile(archive) as handle:
        infos = handle.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ValueError("duplicate ZIP member")
        for info in infos:
            _safe_member(info.filename)
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError("ZIP symlink forbidden")
            if _forbidden_name(info.filename):
                raise ValueError(f"forbidden archive member: {info.filename}")
            if not info.is_dir():
                with handle.open(info) as member:
                    _scan_token_stream(member)
        broken = handle.testzip()
        if broken:
            raise ValueError(f"ZIP CRC failure: {broken}")
        roots = {PurePosixPath(name).parts[0] for name in names if _safe_member(name).parts}
        if len(roots) != 1:
            raise ValueError("ZIP must have exactly one root directory")
        with tempfile.TemporaryDirectory() as folder:
            handle.extractall(folder)
            root = Path(folder) / next(iter(roots))
            ledgers = sorted(root.rglob("checksums.sha256"))
            if require_ledger and not ledgers:
                raise ValueError("ZIP contains no checksum ledger")
            for ledger in ledgers:
                try:
                    verify_tree_ledger(ledger.parent, ledger)
                except ValueError as local_error:
                    if ledger.parent == root:
                        raise
                    try:
                        verify_tree_ledger(root, ledger)
                    except ValueError:
                        raise local_error
    return {
        "path": str(archive),
        "size": archive.stat().st_size,
        "sha256": sha256_file(archive),
        "zip_integrity": "PASS",
    }


def copy_tree_selected(source, destination, exclude_top=()):
    source, destination = Path(source), Path(destination)
    excluded = set(exclude_top)
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if relative.parts and relative.parts[0] in excluded:
            continue
        target = destination / relative
        if path.is_symlink():
            raise ValueError("symlink forbidden in artifact tree")
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
