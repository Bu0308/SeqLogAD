"""Streaming content-digest helpers for dataset integrity checks."""

from __future__ import annotations

import hashlib
from pathlib import Path


DEFAULT_CHUNK_SIZE = 1024 * 1024


def digest_file(
    path: str | Path,
    *,
    algorithm: str = "sha256",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> str:
    """Return a streaming hexadecimal digest for a regular file.

    MD5 support exists only for checking source-published archive digests.
    Scientific dataset identity always uses SHA-256.
    """

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    if not file_path.is_file():
        raise IsADirectoryError(f"Expected a regular file: {file_path}")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise ValueError(f"Unsupported digest algorithm: {algorithm}") from exc

    with file_path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file(path: str | Path, *, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    """Return the SHA-256 digest of a file without loading it into memory."""

    return digest_file(path, algorithm="sha256", chunk_size=chunk_size)
