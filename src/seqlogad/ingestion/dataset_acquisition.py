"""Safe archive acquisition without extraction or raw-data transformation."""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import BinaryIO, Callable, ContextManager, Literal

from pydantic import BaseModel, ConfigDict

from seqlogad.common.checksum import digest_file
from seqlogad.ingestion.dataset_config import DatasetDefinition, resolve_repository_path
from seqlogad.ingestion.errors import ChecksumMismatchError, DatasetConfigError


OpenUrl = Callable[..., ContextManager[BinaryIO]]


class DownloadResult(BaseModel):
    """Result of a dry-run, existing-file check or completed archive download."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    status: Literal["DRY_RUN", "ALREADY_EXISTS", "DOWNLOADED"]
    destination: str
    size_bytes: int | None


def _verify_source_checksum(path: Path, config: DatasetDefinition) -> None:
    checksum = config.acquisition.source_checksum
    if checksum is None:
        return
    actual = digest_file(path, algorithm=checksum.algorithm)
    if actual != checksum.value:
        raise ChecksumMismatchError(
            f"Source {checksum.algorithm} mismatch for {path.name}: "
            f"expected {checksum.value}, got {actual}"
        )


def download_dataset_archive(
    config: DatasetDefinition,
    *,
    project_root: str | Path,
    dry_run: bool = False,
    force: bool = False,
    timeout_seconds: float = 60.0,
    opener: OpenUrl = urllib.request.urlopen,
) -> DownloadResult:
    """Download a configured archive through a temporary file and atomic rename.

    The function never extracts or transforms the archive. Existing files are
    validated and preserved unless ``force`` is explicitly supplied.
    """

    acquisition = config.acquisition
    if acquisition.method != "archive_download" or not acquisition.url or not acquisition.archive:
        raise DatasetConfigError(f"Dataset {config.key} has no archive download definition")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")

    root = Path(project_root).resolve()
    raw_root = resolve_repository_path(root, config.raw_dir)
    destination = raw_root / acquisition.archive
    relative_destination = destination.relative_to(root).as_posix()

    if destination.exists() and not force:
        _verify_source_checksum(destination, config)
        return DownloadResult(
            dataset_id=config.dataset_id,
            status="ALREADY_EXISTS",
            destination=relative_destination,
            size_bytes=destination.stat().st_size,
        )

    if dry_run:
        return DownloadResult(
            dataset_id=config.dataset_id,
            status="DRY_RUN",
            destination=relative_destination,
            size_bytes=None,
        )

    raw_root.mkdir(parents=True, exist_ok=True)
    partial_path = destination.with_name(destination.name + ".part")
    if partial_path.exists():
        partial_path.unlink()

    try:
        with opener(acquisition.url, timeout=timeout_seconds) as response:
            with partial_path.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        _verify_source_checksum(partial_path, config)
        partial_path.replace(destination)
    except Exception:
        if partial_path.exists():
            partial_path.unlink()
        raise

    return DownloadResult(
        dataset_id=config.dataset_id,
        status="DOWNLOADED",
        destination=relative_destination,
        size_bytes=destination.stat().st_size,
    )
