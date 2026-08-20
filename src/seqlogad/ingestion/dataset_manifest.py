"""Deterministic dataset manifest generation and integrity verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from seqlogad.common.checksum import sha256_file
from seqlogad.ingestion.dataset_config import (
    DatasetDefinition,
    ExpectedFile,
    resolve_repository_path,
)
from seqlogad.ingestion.dataset_validation import validate_dataset_presence
from seqlogad.ingestion.errors import ManifestValidationError


MANIFEST_SCHEMA_VERSION = "1.0"
EncodingStatus = Literal["UTF8_COMPATIBLE", "NON_UTF8", "NOT_APPLICABLE", "UNKNOWN"]


class ManifestSource(BaseModel):
    """Source and usage provenance copied from version-controlled config."""

    model_config = ConfigDict(extra="forbid")

    name: str
    reference: str
    record_doi: str | None
    accessed_on: str
    acquired_at_utc: str | None
    source_archive: str | None
    source_archive_checksum: str | None
    license_status: str
    usage_notes: str


class ManifestFile(BaseModel):
    """Content identity and basic metadata for one raw file."""

    model_config = ConfigDict(extra="forbid")

    path: str
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    role: Literal["log", "label", "metadata", "archive"]
    extension: str
    compression: str | None
    encoding_status: EncodingStatus


class ManifestStatistics(BaseModel):
    """Simple file statistics that do not define scientific identity."""

    model_config = ConfigDict(extra="forbid")

    file_count: int = Field(ge=0)
    total_bytes: int = Field(ge=0)


class ManifestIntegrity(BaseModel):
    """Integrity state observed while creating a manifest."""

    model_config = ConfigDict(extra="forbid")

    all_required_files_present: bool
    all_hashes_computed: bool


class DatasetManifest(BaseModel):
    """Version 1.0 raw-dataset manifest."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    dataset_id: str
    dataset_name: str
    dataset_version: str
    source: ManifestSource
    raw_root: str
    files: list[ManifestFile]
    statistics: ManifestStatistics
    integrity: ManifestIntegrity
    dataset_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class ManifestVerificationReport(BaseModel):
    """Non-mutating comparison of a manifest against current raw bytes."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    valid: bool
    required_files_present: bool
    missing_files: list[str]
    size_mismatches: list[str]
    checksum_mismatches: list[str]
    fingerprint_matches: bool
    expected_fingerprint: str
    actual_fingerprint: str | None


def dataset_fingerprint(files: list[ManifestFile]) -> str:
    """Hash a sorted path/content-hash list into a stable dataset identity."""

    identity_lines = sorted(f"{item.path}:{item.sha256}" for item in files)
    payload = "\n".join(identity_lines).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _compression_type(path: Path) -> str | None:
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes[-2:] == [".tar", ".gz"]:
        return "tar.gz"
    if not suffixes:
        return None
    return {
        ".zip": "zip",
        ".gz": "gzip",
        ".bz2": "bzip2",
        ".xz": "xz",
        ".tar": "tar",
    }.get(suffixes[-1])


def inspect_utf8_compatibility(path: str | Path) -> EncodingStatus:
    """Read a text-like file without modifying it and report UTF-8 compatibility."""

    file_path = Path(path)
    if _compression_type(file_path) is not None:
        return "NOT_APPLICABLE"
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            while handle.read(1024 * 1024):
                pass
    except UnicodeDecodeError:
        return "NON_UTF8"
    except OSError:
        return "UNKNOWN"
    return "UTF8_COMPATIBLE"


def _role_for_path(relative_to_raw: str, expected: dict[str, ExpectedFile]) -> str:
    item = expected.get(relative_to_raw)
    return item.role if item is not None else "metadata"


def _iter_raw_files(raw_root: Path) -> list[Path]:
    if not raw_root.is_dir():
        return []
    files: list[Path] = []
    for path in raw_root.rglob("*"):
        if path.is_symlink():
            raise ManifestValidationError(f"Raw dataset symlinks are not supported: {path}")
        if not path.is_file():
            continue
        if path.name in {".gitkeep", "README.md"} or path.name.endswith(".part"):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(raw_root).as_posix())


def build_dataset_manifest(
    config: DatasetDefinition,
    *,
    project_root: str | Path,
) -> DatasetManifest:
    """Build a deterministic manifest in memory without modifying raw data."""

    root = Path(project_root).resolve()
    raw_root = resolve_repository_path(root, config.raw_dir)
    expected = {item.path: item for item in config.expected_files}
    manifest_files: list[ManifestFile] = []

    for file_path in _iter_raw_files(raw_root):
        relative_to_raw = file_path.relative_to(raw_root).as_posix()
        project_relative = file_path.relative_to(root).as_posix()
        role = _role_for_path(relative_to_raw, expected)
        encoding = (
            inspect_utf8_compatibility(file_path)
            if role in {"log", "label", "metadata"}
            else "NOT_APPLICABLE"
        )
        manifest_files.append(
            ManifestFile(
                path=project_relative,
                size_bytes=file_path.stat().st_size,
                sha256=sha256_file(file_path),
                role=role,
                extension="".join(file_path.suffixes).lower(),
                compression=_compression_type(file_path),
                encoding_status=encoding,
            )
        )

    presence = validate_dataset_presence(config, project_root=root)
    source_checksum = config.acquisition.source_checksum
    archive_checksum = (
        f"{source_checksum.algorithm}:{source_checksum.value}"
        if source_checksum is not None
        else None
    )
    total_bytes = sum(item.size_bytes for item in manifest_files)

    return DatasetManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        dataset_id=config.dataset_id,
        dataset_name=config.dataset_name,
        dataset_version=config.dataset_version,
        source=ManifestSource(
            name=config.source.name,
            reference=config.source.reference,
            record_doi=config.source.record_doi,
            accessed_on=config.source.accessed_on,
            acquired_at_utc=config.acquisition.acquired_at_utc,
            source_archive=config.acquisition.archive,
            source_archive_checksum=archive_checksum,
            license_status=config.licensing.status,
            usage_notes=config.licensing.usage_notes,
        ),
        raw_root=config.raw_dir,
        files=manifest_files,
        statistics=ManifestStatistics(
            file_count=len(manifest_files),
            total_bytes=total_bytes,
        ),
        integrity=ManifestIntegrity(
            all_required_files_present=presence.status.value == "PRESENT",
            all_hashes_computed=True,
        ),
        dataset_fingerprint=dataset_fingerprint(manifest_files),
    )


def manifest_json(manifest: DatasetManifest) -> str:
    """Serialize a manifest with stable key and file ordering."""

    payload = manifest.model_dump(mode="json")
    payload["files"] = sorted(payload["files"], key=lambda item: item["path"])
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_dataset_manifest(
    manifest: DatasetManifest,
    path: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Atomically write a manifest, refusing overwrite by default."""

    manifest_path = Path(path)
    if manifest_path.exists() and not overwrite:
        raise FileExistsError(f"Manifest already exists: {manifest_path}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    temporary_path.write_text(manifest_json(manifest), encoding="utf-8")
    temporary_path.replace(manifest_path)
    return manifest_path


def load_dataset_manifest(path: str | Path) -> DatasetManifest:
    """Load a strict versioned manifest from JSON."""

    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise ManifestValidationError(f"Manifest does not exist: {manifest_path}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return DatasetManifest.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ManifestValidationError(f"Invalid manifest: {manifest_path}") from exc


def verify_dataset_manifest(
    config: DatasetDefinition,
    *,
    project_root: str | Path,
    manifest_path: str | Path | None = None,
) -> ManifestVerificationReport:
    """Re-hash raw files and report integrity without editing the manifest."""

    root = Path(project_root).resolve()
    selected_path = (
        Path(manifest_path)
        if manifest_path is not None
        else resolve_repository_path(root, config.manifest_path)
    )
    manifest = load_dataset_manifest(selected_path)
    if manifest.dataset_id != config.dataset_id:
        raise ManifestValidationError(
            f"Manifest dataset_id {manifest.dataset_id!r} does not match {config.dataset_id!r}"
        )

    missing: list[str] = []
    size_mismatches: list[str] = []
    checksum_mismatches: list[str] = []
    actual_files: list[ManifestFile] = []

    for item in manifest.files:
        file_path = resolve_repository_path(root, item.path)
        if not file_path.is_file():
            missing.append(item.path)
            continue
        actual_size = file_path.stat().st_size
        actual_hash = sha256_file(file_path)
        if actual_size != item.size_bytes:
            size_mismatches.append(item.path)
        if actual_hash != item.sha256:
            checksum_mismatches.append(item.path)
        actual_files.append(item.model_copy(update={"size_bytes": actual_size, "sha256": actual_hash}))

    presence = validate_dataset_presence(config, project_root=root)
    actual_fingerprint = None if missing else dataset_fingerprint(actual_files)
    fingerprint_matches = actual_fingerprint == manifest.dataset_fingerprint
    valid = not (
        missing
        or size_mismatches
        or checksum_mismatches
        or presence.missing_required_files
        or not fingerprint_matches
    )

    return ManifestVerificationReport(
        dataset_id=config.dataset_id,
        valid=valid,
        required_files_present=not presence.missing_required_files,
        missing_files=sorted(set(missing + presence.missing_required_files)),
        size_mismatches=sorted(size_mismatches),
        checksum_mismatches=sorted(checksum_mismatches),
        fingerprint_matches=fingerprint_matches,
        expected_fingerprint=manifest.dataset_fingerprint,
        actual_fingerprint=actual_fingerprint,
    )
