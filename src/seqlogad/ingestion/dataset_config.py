"""Minimal, validated loading for per-dataset acquisition configuration."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from seqlogad.ingestion.errors import DatasetConfigError


FileRole = Literal["log", "label", "metadata", "archive"]


def _validate_relative_path(value: str, field_name: str) -> str:
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{field_name} must be a repository-relative safe path")
    if not candidate.parts:
        raise ValueError(f"{field_name} must not be empty")
    return candidate.as_posix()


class SourceChecksum(BaseModel):
    """Checksum published by the dataset source for the downloadable archive."""

    model_config = ConfigDict(extra="forbid")

    algorithm: Literal["md5", "sha256"]
    value: str = Field(min_length=32, max_length=64)

    @field_validator("value")
    @classmethod
    def validate_hex_digest(cls, value: str) -> str:
        normalized = value.lower()
        if not re.fullmatch(r"[0-9a-f]+", normalized):
            raise ValueError("checksum value must be hexadecimal")
        return normalized


class DatasetSource(BaseModel):
    """Canonical source references for a dataset snapshot."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    record_doi: str | None = None
    accessed_on: str = Field(min_length=10)


class ExpectedFile(BaseModel):
    """A required or optional file expected below the dataset raw root."""

    model_config = ConfigDict(extra="forbid")

    path: str
    required: bool
    role: FileRole
    description: str = ""

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _validate_relative_path(value, "expected_files.path")


class LabelDefinition(BaseModel):
    """Known label location and granularity without parsing semantics."""

    model_config = ConfigDict(extra="forbid")

    available: bool
    file: str | None = None
    level: str | None = None
    notes: str = ""

    @field_validator("file")
    @classmethod
    def validate_file(cls, value: str | None) -> str | None:
        return None if value is None else _validate_relative_path(value, "labels.file")


class AcquisitionDefinition(BaseModel):
    """Safe archive acquisition metadata."""

    model_config = ConfigDict(extra="forbid")

    method: Literal["archive_download", "manual"]
    url: str | None = None
    archive: str | None = None
    source_checksum: SourceChecksum | None = None
    manual_fallback: str
    acquired_at_utc: str | None = None

    @field_validator("archive")
    @classmethod
    def validate_archive(cls, value: str | None) -> str | None:
        return None if value is None else _validate_relative_path(value, "acquisition.archive")


class LicensingDefinition(BaseModel):
    """Verified usage note without guessing an SPDX license."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(min_length=1)
    source_license: str = Field(min_length=1)
    usage_notes: str = Field(min_length=1)
    review_required: bool


class DatasetDefinition(BaseModel):
    """Version-controlled acquisition contract for one dataset."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(pattern=r"^[a-z0-9_-]+$")
    dataset_id: str = Field(min_length=1)
    dataset_name: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    enabled: bool
    priority: Literal["P0", "P1", "P2", "P3"]
    source: DatasetSource
    raw_dir: str
    manifest_path: str
    expected_files: list[ExpectedFile] = Field(min_length=1)
    labels: LabelDefinition
    acquisition: AcquisitionDefinition
    licensing: LicensingDefinition

    @field_validator("raw_dir", "manifest_path")
    @classmethod
    def validate_repository_path(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "path")
        return _validate_relative_path(value, field_name)

    @model_validator(mode="after")
    def validate_file_contract(self) -> "DatasetDefinition":
        paths = [item.path for item in self.expected_files]
        if len(paths) != len(set(paths)):
            raise ValueError("expected_files paths must be unique")
        if not any(item.required for item in self.expected_files):
            raise ValueError("at least one expected file must be required")
        if self.labels.available and self.labels.file not in paths:
            raise ValueError("labels.file must appear in expected_files")
        return self


def load_dataset_config(
    dataset_key: str,
    *,
    config_dir: str | Path = Path("configs/datasets"),
) -> DatasetDefinition:
    """Load and validate one dataset definition by key."""

    if not re.fullmatch(r"[a-z0-9_-]+", dataset_key):
        raise DatasetConfigError(f"Invalid dataset key: {dataset_key!r}")

    config_path = Path(config_dir) / f"{dataset_key}.yaml"
    if not config_path.is_file():
        raise DatasetConfigError(f"Dataset config does not exist: {config_path}")

    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise DatasetConfigError(f"Could not read dataset config: {config_path}") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("dataset"), dict):
        raise DatasetConfigError(f"Config must contain a dataset mapping: {config_path}")

    try:
        definition = DatasetDefinition.model_validate(payload["dataset"])
    except ValidationError as exc:
        raise DatasetConfigError(f"Malformed dataset config {config_path}: {exc}") from exc

    if definition.key != dataset_key:
        raise DatasetConfigError(
            f"Dataset key mismatch: requested {dataset_key!r}, config has {definition.key!r}"
        )
    return definition


def resolve_repository_path(project_root: str | Path, relative_path: str) -> Path:
    """Resolve a validated repository-relative path without allowing traversal."""

    root = Path(project_root).resolve()
    resolved = (root / relative_path).resolve()
    if not resolved.is_relative_to(root):
        raise DatasetConfigError(f"Path escapes project root: {relative_path}")
    return resolved
