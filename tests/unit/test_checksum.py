"""Unit tests for streaming file digests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from seqlogad.common.checksum import sha256_file


def test_known_small_file(tmp_path: Path) -> None:
    path = tmp_path / "hello.txt"
    path.write_bytes(b"hello")
    assert sha256_file(path) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty"
    path.write_bytes(b"")
    assert sha256_file(path) == hashlib.sha256(b"").hexdigest()


def test_binary_file(tmp_path: Path) -> None:
    content = bytes(range(256))
    path = tmp_path / "binary.bin"
    path.write_bytes(content)
    assert sha256_file(path, chunk_size=17) == hashlib.sha256(content).hexdigest()


def test_same_content_has_same_hash(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.write_bytes(b"same")
    second.write_bytes(b"same")
    assert sha256_file(first) == sha256_file(second)


def test_changed_content_has_different_hash(tmp_path: Path) -> None:
    path = tmp_path / "mutable"
    path.write_bytes(b"before")
    before = sha256_file(path)
    path.write_bytes(b"after")
    assert sha256_file(path) != before


def test_missing_file_has_explicit_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="File does not exist"):
        sha256_file(tmp_path / "missing")
