"""Dataset presence validation with PRESENT, PARTIAL and MISSING states."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from seqlogad.ingestion.dataset_config import DatasetDefinition, resolve_repository_path


class DatasetPresenceStatus(str, Enum):
    """Completeness state for required raw dataset files."""

    PRESENT = "PRESENT"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class DatasetPresenceReport(BaseModel):
    """Machine-readable required/optional file presence report."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    status: DatasetPresenceStatus
    required_count: int
    required_present: int
    missing_required_files: list[str]
    missing_optional_files: list[str]


def validate_dataset_presence(
    config: DatasetDefinition,
    *,
    project_root: str | Path,
) -> DatasetPresenceReport:
    """Return dataset completeness without modifying any raw file."""

    raw_root = resolve_repository_path(project_root, config.raw_dir)
    required = [item for item in config.expected_files if item.required]
    optional = [item for item in config.expected_files if not item.required]

    missing_required = [
        item.path for item in required if not (raw_root / item.path).is_file()
    ]
    missing_optional = [
        item.path for item in optional if not (raw_root / item.path).is_file()
    ]
    present_count = len(required) - len(missing_required)

    if present_count == len(required):
        status = DatasetPresenceStatus.PRESENT
    elif present_count == 0:
        status = DatasetPresenceStatus.MISSING
    else:
        status = DatasetPresenceStatus.PARTIAL

    return DatasetPresenceReport(
        dataset_id=config.dataset_id,
        status=status,
        required_count=len(required),
        required_present=present_count,
        missing_required_files=sorted(missing_required),
        missing_optional_files=sorted(missing_optional),
    )
