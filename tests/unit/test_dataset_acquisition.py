"""Offline tests for safe archive acquisition behavior."""

from __future__ import annotations

import hashlib
import io
from collections.abc import Callable
from pathlib import Path

import pytest

from seqlogad.ingestion.dataset_acquisition import download_dataset_archive
from seqlogad.ingestion.dataset_config import DatasetDefinition, SourceChecksum
from seqlogad.ingestion.errors import ChecksumMismatchError


ProjectFactory = Callable[[str], tuple[Path, DatasetDefinition]]
ARCHIVE_BYTES = b"synthetic archive bytes"


class FakeResponse(io.BytesIO):
    """A local context-managed byte stream compatible with urlopen usage."""

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


class FailingResponse(FakeResponse):
    """Return one chunk and then simulate an interrupted connection."""

    def __init__(self) -> None:
        super().__init__(ARCHIVE_BYTES)
        self.read_count = 0

    def read(self, size: int = -1) -> bytes:
        self.read_count += 1
        if self.read_count > 1:
            raise OSError("connection interrupted")
        return super().read(5 if size < 0 else min(size, 5))


def _with_checksum(config: DatasetDefinition, digest: str) -> DatasetDefinition:
    return config.model_copy(
        update={
            "acquisition": config.acquisition.model_copy(
                update={
                    "source_checksum": SourceChecksum(algorithm="md5", value=digest)
                }
            )
        }
    )


def test_successful_download_uses_local_mock(make_dataset_project: ProjectFactory) -> None:
    root, config = make_dataset_project("complete_dataset")
    config = _with_checksum(config, hashlib.md5(ARCHIVE_BYTES).hexdigest())
    result = download_dataset_archive(
        config,
        project_root=root,
        opener=lambda *_args, **_kwargs: FakeResponse(ARCHIVE_BYTES),
    )
    assert result.status == "DOWNLOADED"
    assert (root / config.raw_dir / "sample.zip").read_bytes() == ARCHIVE_BYTES
    assert not (root / config.raw_dir / "sample.zip.part").exists()


def test_network_failure_leaves_no_partial_file(make_dataset_project: ProjectFactory) -> None:
    root, config = make_dataset_project("complete_dataset")

    def fail(*_args: object, **_kwargs: object) -> FakeResponse:
        raise OSError("network unavailable")

    with pytest.raises(OSError, match="network unavailable"):
        download_dataset_archive(config, project_root=root, opener=fail)
    assert not (root / config.raw_dir / "sample.zip.part").exists()


def test_interrupted_download_removes_partial_file(make_dataset_project: ProjectFactory) -> None:
    root, config = make_dataset_project("complete_dataset")
    with pytest.raises(OSError, match="connection interrupted"):
        download_dataset_archive(
            config,
            project_root=root,
            opener=lambda *_args, **_kwargs: FailingResponse(),
        )
    assert not (root / config.raw_dir / "sample.zip.part").exists()
    assert not (root / config.raw_dir / "sample.zip").exists()


def test_existing_destination_is_not_overwritten(make_dataset_project: ProjectFactory) -> None:
    root, config = make_dataset_project("complete_dataset")
    destination = root / config.raw_dir / "sample.zip"
    destination.write_bytes(ARCHIVE_BYTES)
    config = _with_checksum(config, hashlib.md5(ARCHIVE_BYTES).hexdigest())
    result = download_dataset_archive(config, project_root=root)
    assert result.status == "ALREADY_EXISTS"
    assert destination.read_bytes() == ARCHIVE_BYTES


def test_checksum_mismatch_removes_download(make_dataset_project: ProjectFactory) -> None:
    root, config = make_dataset_project("complete_dataset")
    config = _with_checksum(config, "0" * 32)
    with pytest.raises(ChecksumMismatchError, match="mismatch"):
        download_dataset_archive(
            config,
            project_root=root,
            opener=lambda *_args, **_kwargs: FakeResponse(ARCHIVE_BYTES),
        )
    assert not (root / config.raw_dir / "sample.zip").exists()
    assert not (root / config.raw_dir / "sample.zip.part").exists()


def test_dry_run_does_not_create_raw_archive(make_dataset_project: ProjectFactory) -> None:
    root, config = make_dataset_project("complete_dataset")
    result = download_dataset_archive(config, project_root=root, dry_run=True)
    assert result.status == "DRY_RUN"
    assert not (root / config.raw_dir / "sample.zip").exists()
