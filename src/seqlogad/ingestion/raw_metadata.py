"""Parser-independent raw metadata extraction for META-001.

Only structural source metadata is extracted. This module never reads anomaly
labels, fits a parser, assigns scientific partitions, creates templates, or
builds final event sequences/windows.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from seqlogad.common.schemas import build_record_id
from seqlogad.ingestion.dataset_config import DatasetDefinition, resolve_repository_path
from seqlogad.ingestion.dataset_manifest import load_dataset_manifest
from seqlogad.ingestion.errors import MetadataExtractionError


METADATA_SCHEMA_VERSION = "1.0"
METADATA_CONTRACT_ID = "META-001"
BGL_TIMESTAMP_FORMAT = "%Y-%m-%d-%H.%M.%S.%f"

_SHA256 = r"^[0-9a-f]{64}$"
_SOURCE_ID = r"^META-SOURCE-[0-9a-f]{64}$"
_COMPONENT_ID = r"^HDFS-COMP-[0-9a-f]{64}$"
_CHRONOLOGY_ID = r"^BGL-CHRON-[0-9a-f]{64}$"
_BLOCK_CANDIDATE = re.compile(r"(?<![A-Za-z0-9_])blk_[A-Za-z0-9_-]*")
_BLOCK_TOKEN = re.compile(r"blk_-?[0-9]+")


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_relative_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or "\x00" in value
        or candidate.is_absolute()
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or candidate.as_posix() != value
    ):
        raise ValueError("path must be normalized repository-relative POSIX")
    return value


def _block_sort_key(block_id: str) -> tuple[int, str]:
    if _BLOCK_TOKEN.fullmatch(block_id) is None:
        raise ValueError(f"invalid normalized HDFS block ID: {block_id!r}")
    return int(block_id.removeprefix("blk_")), block_id


class MetadataModel(BaseModel):
    """Strict immutable metadata record with canonical JSON support."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    def canonical_json(self) -> str:
        return _canonical_json(self.model_dump(mode="json"))

    def canonical_sha256(self) -> str:
        return _sha256_text(self.canonical_json())


class LineEnding(StrEnum):
    LF = "LF"
    CRLF = "CRLF"
    CR = "CR"
    NONE = "NONE"


class DecodeStatus(StrEnum):
    UTF8 = "UTF8"
    DECODE_ERROR = "DECODE_ERROR"


class HdfsAssignmentStatus(StrEnum):
    ASSIGNED = "ASSIGNED"
    UNASSIGNED = "UNASSIGNED"


class HdfsUnassignedReason(StrEnum):
    NO_BLOCK_ID = "NO_BLOCK_ID"
    MALFORMED_BLOCK_TOKEN = "MALFORMED_BLOCK_TOKEN"
    DECODE_ERROR = "DECODE_ERROR"


class HdfsIssue(StrEnum):
    DUPLICATE_BLOCK_ID = "DUPLICATE_BLOCK_ID"
    MULTIPLE_BLOCK_IDS = "MULTIPLE_BLOCK_IDS"
    MALFORMED_BLOCK_TOKEN = "MALFORMED_BLOCK_TOKEN"
    MISSING_LINE_TERMINATOR = "MISSING_LINE_TERMINATOR"


class BglTimestampStatus(StrEnum):
    PARSED = "PARSED"
    MALFORMED_TIMESTAMP = "MALFORMED_TIMESTAMP"
    DECODE_ERROR = "DECODE_ERROR"


class BglIssue(StrEnum):
    TIMESTAMP_REGRESSION = "TIMESTAMP_REGRESSION"
    MISSING_LINE_TERMINATOR = "MISSING_LINE_TERMINATOR"


def build_metadata_source_id(
    *,
    dataset_key: str,
    dataset_id: str,
    dataset_version: str,
    dataset_fingerprint: str,
    source_file: str,
    source_file_sha256: str,
) -> str:
    """Identify one verified raw log source without machine-local paths."""

    payload = {
        "dataset_fingerprint": dataset_fingerprint,
        "dataset_id": dataset_id,
        "dataset_key": dataset_key,
        "dataset_version": dataset_version,
        "source_file": _safe_relative_path(source_file),
        "source_file_sha256": source_file_sha256,
    }
    return f"META-SOURCE-{_sha256_text(_canonical_json(payload))}"


def build_hdfs_component_id(block_ids: tuple[str, ...]) -> str:
    """Identify a connected component only from canonical block membership."""

    canonical = tuple(sorted(set(block_ids), key=_block_sort_key))
    if not canonical or canonical != block_ids:
        raise ValueError("component block IDs must be non-empty, unique, and sorted")
    payload = {"block_ids": list(block_ids)}
    return f"HDFS-COMP-{_sha256_text(_canonical_json(payload))}"


def build_bgl_chronology_id(
    *,
    source_file: str,
    original_line_index: int,
    timestamp_iso: str | None,
) -> str:
    """Identify structural chronology without the inline anomaly-label value."""

    if original_line_index < 0:
        raise ValueError("original_line_index must be non-negative")
    payload = {
        "original_line_index": original_line_index,
        "source_file": _safe_relative_path(source_file),
        "timestamp_iso": timestamp_iso,
    }
    return f"BGL-CHRON-{_sha256_text(_canonical_json(payload))}"


class MetadataSource(MetadataModel):
    """Verified raw-log identity used by every metadata record."""

    schema_version: Literal["1.0"] = METADATA_SCHEMA_VERSION
    contract_id: Literal["META-001"] = METADATA_CONTRACT_ID
    source_id: str = Field(pattern=_SOURCE_ID)
    dataset_key: Literal["hdfs", "bgl"]
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    dataset_fingerprint: str = Field(pattern=_SHA256)
    source_file: str
    source_file_sha256: str = Field(pattern=_SHA256)

    @field_validator("source_file")
    @classmethod
    def validate_source_file(cls, value: str) -> str:
        return _safe_relative_path(value)

    @model_validator(mode="after")
    def validate_identity(self) -> "MetadataSource":
        expected = build_metadata_source_id(
            dataset_key=self.dataset_key,
            dataset_id=self.dataset_id,
            dataset_version=self.dataset_version,
            dataset_fingerprint=self.dataset_fingerprint,
            source_file=self.source_file,
            source_file_sha256=self.source_file_sha256,
        )
        if self.source_id != expected:
            raise ValueError("source_id does not match verified source fields")
        return self


class HdfsComponentMetadata(MetadataModel):
    """One atomic connected component of HDFS block/session identifiers."""

    schema_version: Literal["1.0"] = METADATA_SCHEMA_VERSION
    contract_id: Literal["META-001"] = METADATA_CONTRACT_ID
    source_id: str = Field(pattern=_SOURCE_ID)
    dataset_fingerprint: str = Field(pattern=_SHA256)
    component_id: str = Field(pattern=_COMPONENT_ID)
    block_ids: tuple[str, ...] = Field(min_length=1)
    chronological_start: int = Field(ge=0)
    source_line_start: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_component(self) -> "HdfsComponentMetadata":
        canonical = tuple(sorted(set(self.block_ids), key=_block_sort_key))
        if self.block_ids != canonical:
            raise ValueError("block_ids must be unique and canonically ordered")
        if self.chronological_start != self.source_line_start - 1:
            raise ValueError("component chronology must use source-line order")
        if self.component_id != build_hdfs_component_id(self.block_ids):
            raise ValueError("component_id does not match members")
        return self


class HdfsLineMetadata(MetadataModel):
    """Label-free HDFS structural metadata for one raw source line."""

    schema_version: Literal["1.0"] = METADATA_SCHEMA_VERSION
    contract_id: Literal["META-001"] = METADATA_CONTRACT_ID
    dataset_key: Literal["hdfs"] = "hdfs"
    source_id: str = Field(pattern=_SOURCE_ID)
    dataset_fingerprint: str = Field(pattern=_SHA256)
    source_file: str
    record_id: str = Field(pattern=r"^LOG-[0-9a-f]{64}$")
    source_line_number: int = Field(ge=1)
    chronological_index: int = Field(ge=0)
    source_line_sha256: str = Field(pattern=_SHA256)
    line_ending: LineEnding
    decode_status: DecodeStatus
    raw_block_tokens: tuple[str, ...] = ()
    block_ids: tuple[str, ...] = ()
    duplicate_block_ids: tuple[str, ...] = ()
    malformed_block_tokens: tuple[str, ...] = ()
    component_id: str | None = Field(default=None, pattern=_COMPONENT_ID)
    assignment_status: HdfsAssignmentStatus
    unassigned_reason: HdfsUnassignedReason | None = None
    issues: tuple[HdfsIssue, ...] = ()

    @field_validator("source_file")
    @classmethod
    def validate_source_file(cls, value: str) -> str:
        return _safe_relative_path(value)

    @model_validator(mode="after")
    def validate_line(self) -> "HdfsLineMetadata":
        if self.chronological_index != self.source_line_number - 1:
            raise ValueError("HDFS chronology must equal zero-based source order")
        expected = build_record_id(
            dataset_fingerprint=self.dataset_fingerprint,
            source_file=self.source_file,
            source_line_number=self.source_line_number,
            source_line_sha256=self.source_line_sha256,
        )
        if self.record_id != expected:
            raise ValueError("record_id does not match source occurrence")
        if self.block_ids != tuple(sorted(set(self.block_ids), key=_block_sort_key)):
            raise ValueError("block_ids must be unique and sorted")
        expected_duplicates = tuple(
            sorted(set(self.duplicate_block_ids), key=_block_sort_key)
        )
        if self.duplicate_block_ids != expected_duplicates:
            raise ValueError("duplicate_block_ids must be unique and sorted")
        expected_issues = tuple(sorted(set(self.issues), key=lambda item: item.value))
        if self.issues != expected_issues:
            raise ValueError("issues must be unique and sorted")
        if self.assignment_status is HdfsAssignmentStatus.ASSIGNED:
            if not self.block_ids or self.component_id is None or self.unassigned_reason:
                raise ValueError("assigned line requires block/component identity")
        elif self.block_ids or self.component_id is not None or not self.unassigned_reason:
            raise ValueError("unassigned line requires an explicit reason")
        return self


class BglLineMetadata(MetadataModel):
    """Label-independent BGL chronology metadata for one raw source line."""

    schema_version: Literal["1.0"] = METADATA_SCHEMA_VERSION
    contract_id: Literal["META-001"] = METADATA_CONTRACT_ID
    dataset_key: Literal["bgl"] = "bgl"
    source_id: str = Field(pattern=_SOURCE_ID)
    dataset_fingerprint: str = Field(pattern=_SHA256)
    source_file: str
    record_id: str = Field(pattern=r"^LOG-[0-9a-f]{64}$")
    chronology_id: str = Field(pattern=_CHRONOLOGY_ID)
    source_line_number: int = Field(ge=1)
    original_line_index: int = Field(ge=0)
    chronological_rank: int = Field(ge=0)
    source_line_sha256: str = Field(pattern=_SHA256)
    line_ending: LineEnding
    decode_status: DecodeStatus
    source_epoch_seconds: int | None = None
    source_timestamp: str | None = None
    timestamp_iso: str | None = None
    timestamp_status: BglTimestampStatus
    issues: tuple[BglIssue, ...] = ()

    @field_validator("source_file")
    @classmethod
    def validate_source_file(cls, value: str) -> str:
        return _safe_relative_path(value)

    @model_validator(mode="after")
    def validate_chronology(self) -> "BglLineMetadata":
        expected_index = self.source_line_number - 1
        if (
            self.original_line_index != expected_index
            or self.chronological_rank != expected_index
        ):
            raise ValueError("BGL rank must preserve zero-based source order")
        expected_record = build_record_id(
            dataset_fingerprint=self.dataset_fingerprint,
            source_file=self.source_file,
            source_line_number=self.source_line_number,
            source_line_sha256=self.source_line_sha256,
        )
        if self.record_id != expected_record:
            raise ValueError("record_id does not match source occurrence")
        expected_chronology = build_bgl_chronology_id(
            source_file=self.source_file,
            original_line_index=self.original_line_index,
            timestamp_iso=self.timestamp_iso,
        )
        if self.chronology_id != expected_chronology:
            raise ValueError("chronology_id does not match structural fields")
        if self.timestamp_status is BglTimestampStatus.PARSED:
            if self.source_timestamp is None or self.timestamp_iso is None:
                raise ValueError("parsed timestamp requires source and ISO values")
        elif self.timestamp_iso is not None:
            raise ValueError("unparsed timestamp cannot claim an ISO value")
        expected_issues = tuple(sorted(set(self.issues), key=lambda item: item.value))
        if self.issues != expected_issues:
            raise ValueError("issues must be unique and sorted")
        return self


class MetadataFileArtifact(MetadataModel):
    path: str
    sha256: str = Field(pattern=_SHA256)
    record_count: int = Field(ge=0)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _safe_relative_path(value)


class MetadataArtifactSummary(MetadataModel):
    """Metadata-only extraction summary; never a scientific split/result."""

    schema_version: Literal["1.0"] = METADATA_SCHEMA_VERSION
    contract_id: Literal["META-001"] = METADATA_CONTRACT_ID
    source: MetadataSource
    complete: bool
    lines_observed: int = Field(ge=0)
    counts: dict[str, int]
    generated_files: tuple[MetadataFileArtifact, ...] = ()
    labels_used: Literal[False] = False
    parser_used: Literal[False] = False
    scientific_split_created: Literal[False] = False
    test_partition_assigned: Literal[False] = False

    @field_validator("counts")
    @classmethod
    def validate_counts(cls, value: dict[str, int]) -> dict[str, int]:
        if any(not key or count < 0 for key, count in value.items()):
            raise ValueError("counts must have non-empty keys and non-negative values")
        return dict(sorted(value.items()))

    @field_validator("generated_files")
    @classmethod
    def sort_files(
        cls, value: tuple[MetadataFileArtifact, ...]
    ) -> tuple[MetadataFileArtifact, ...]:
        paths = [item.path for item in value]
        if len(paths) != len(set(paths)):
            raise ValueError("generated file paths must be unique")
        return tuple(sorted(value, key=lambda item: item.path))


@dataclass(frozen=True)
class HdfsComponentIndex:
    block_to_component: dict[str, str]
    components: tuple[HdfsComponentMetadata, ...]
    lines_scanned: int
    complete: bool


@dataclass(frozen=True, slots=True)
class HdfsStructuralReference:
    """Minimal META-001 projection consumed by the raw splitter.

    Assigned records deliberately omit their raw-record identity because the
    frozen split payload identifies their connected component plus raw and
    eligible chronology.  Structurally unassigned records retain ``record_id``
    so exclusions remain fully attributable.  No message, label, parser, or
    partition value is exposed.
    """

    chronological_index: int
    component_id: str | None
    record_id: str | None
    assignment_status: HdfsAssignmentStatus
    unassigned_reason: HdfsUnassignedReason | None


@dataclass(frozen=True)
class _DecodedLine:
    sha256: str
    ending: LineEnding
    status: DecodeStatus
    text: str | None


@dataclass(frozen=True)
class _HdfsTokens:
    raw: tuple[str, ...]
    normalized: tuple[str, ...]
    duplicates: tuple[str, ...]
    malformed: tuple[str, ...]


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def add(self, item: str) -> None:
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0

    def find(self, item: str) -> str:
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root] or (
            self.rank[left_root] == self.rank[right_root]
            and left_root > right_root
        ):
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


def resolve_metadata_source(
    config: DatasetDefinition,
    *,
    project_root: str | Path,
) -> tuple[MetadataSource, Path]:
    """Resolve exactly one configured raw log against its verified manifest."""

    if config.key not in {"hdfs", "bgl"}:
        raise MetadataExtractionError(f"unsupported META-001 dataset: {config.key}")
    root = Path(project_root).resolve()
    manifest = load_dataset_manifest(resolve_repository_path(root, config.manifest_path))
    if (
        manifest.dataset_id != config.dataset_id
        or manifest.dataset_version != config.dataset_version
    ):
        raise MetadataExtractionError("dataset config and manifest identity differ")
    configured_logs = [
        item for item in config.expected_files if item.required and item.role == "log"
    ]
    if len(configured_logs) != 1:
        raise MetadataExtractionError("exactly one required raw log is required")
    source_file = (
        PurePosixPath(config.raw_dir) / configured_logs[0].path
    ).as_posix()
    manifest_logs = [item for item in manifest.files if item.path == source_file]
    if len(manifest_logs) != 1 or manifest_logs[0].role != "log":
        raise MetadataExtractionError("configured raw log is absent from manifest")
    source_path = resolve_repository_path(root, source_file)
    if not source_path.is_file():
        raise MetadataExtractionError(f"raw log is missing: {source_file}")
    source_hash = manifest_logs[0].sha256
    source_id = build_metadata_source_id(
        dataset_key=config.key,
        dataset_id=config.dataset_id,
        dataset_version=config.dataset_version,
        dataset_fingerprint=manifest.dataset_fingerprint,
        source_file=source_file,
        source_file_sha256=source_hash,
    )
    return (
        MetadataSource(
            source_id=source_id,
            dataset_key=config.key,
            dataset_id=config.dataset_id,
            dataset_version=config.dataset_version,
            dataset_fingerprint=manifest.dataset_fingerprint,
            source_file=source_file,
            source_file_sha256=source_hash,
        ),
        source_path,
    )


def _decode_line(raw_line: bytes) -> _DecodedLine:
    if raw_line.endswith(b"\r\n"):
        ending, content = LineEnding.CRLF, raw_line[:-2]
    elif raw_line.endswith(b"\n"):
        ending, content = LineEnding.LF, raw_line[:-1]
    elif raw_line.endswith(b"\r"):
        ending, content = LineEnding.CR, raw_line[:-1]
    else:
        ending, content = LineEnding.NONE, raw_line
    try:
        text, status = content.decode("utf-8"), DecodeStatus.UTF8
    except UnicodeDecodeError:
        text, status = None, DecodeStatus.DECODE_ERROR
    return _DecodedLine(hashlib.sha256(raw_line).hexdigest(), ending, status, text)


def _hdfs_tokens(text: str | None) -> _HdfsTokens:
    if text is None:
        return _HdfsTokens((), (), (), ())
    candidates = tuple(match.group(0) for match in _BLOCK_CANDIDATE.finditer(text))
    raw = tuple(item for item in candidates if _BLOCK_TOKEN.fullmatch(item))
    malformed = tuple(item for item in candidates if not _BLOCK_TOKEN.fullmatch(item))
    occurrences = tuple(
        f"blk_{int(item.removeprefix('blk_'))}" for item in raw
    )
    counts: dict[str, int] = {}
    for item in occurrences:
        counts[item] = counts.get(item, 0) + 1
    normalized = tuple(sorted(counts, key=_block_sort_key))
    duplicates = tuple(
        sorted((item for item, count in counts.items() if count > 1), key=_block_sort_key)
    )
    return _HdfsTokens(raw, normalized, duplicates, malformed)


def _iter_lines(path: Path, max_lines: int | None = None) -> Iterator[tuple[int, bytes]]:
    if max_lines is not None and max_lines < 1:
        raise ValueError("max_lines must be positive")
    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if max_lines is not None and line_number > max_lines:
                break
            yield line_number, raw_line


def scan_hdfs_components(
    log_path: str | Path,
    source: MetadataSource,
    *,
    max_lines: int | None = None,
) -> HdfsComponentIndex:
    """First pass: union co-occurring blocks while retaining no raw text."""

    if source.dataset_key != "hdfs":
        raise MetadataExtractionError("HDFS scan requires an HDFS source")
    union_find = _UnionFind()
    first_line: dict[str, int] = {}
    lines_scanned = 0
    for line_number, raw_line in _iter_lines(Path(log_path), max_lines):
        lines_scanned = line_number
        tokens = _hdfs_tokens(_decode_line(raw_line).text)
        for block_id in tokens.normalized:
            union_find.add(block_id)
            first_line.setdefault(block_id, line_number)
        for block_id in tokens.normalized[1:]:
            union_find.union(tokens.normalized[0], block_id)

    by_root: dict[str, list[str]] = {}
    for block_id in union_find.parent:
        by_root.setdefault(union_find.find(block_id), []).append(block_id)

    components: list[HdfsComponentMetadata] = []
    block_to_component: dict[str, str] = {}
    for members in by_root.values():
        block_ids = tuple(sorted(members, key=_block_sort_key))
        component_id = build_hdfs_component_id(block_ids)
        source_line_start = min(first_line[item] for item in block_ids)
        components.append(
            HdfsComponentMetadata(
                source_id=source.source_id,
                dataset_fingerprint=source.dataset_fingerprint,
                component_id=component_id,
                block_ids=block_ids,
                chronological_start=source_line_start - 1,
                source_line_start=source_line_start,
            )
        )
        for block_id in block_ids:
            block_to_component[block_id] = component_id
    return HdfsComponentIndex(
        block_to_component=dict(
            sorted(block_to_component.items(), key=lambda item: _block_sort_key(item[0]))
        ),
        components=tuple(
            sorted(
                components,
                key=lambda item: (item.chronological_start, item.component_id),
            )
        ),
        lines_scanned=lines_scanned,
        complete=max_lines is None,
    )


def _hdfs_line(
    raw_line: bytes,
    line_number: int,
    source: MetadataSource,
    index: HdfsComponentIndex,
) -> HdfsLineMetadata:
    decoded = _decode_line(raw_line)
    tokens = _hdfs_tokens(decoded.text)
    issues: set[HdfsIssue] = set()
    if tokens.duplicates:
        issues.add(HdfsIssue.DUPLICATE_BLOCK_ID)
    if len(tokens.normalized) > 1:
        issues.add(HdfsIssue.MULTIPLE_BLOCK_IDS)
    if tokens.malformed:
        issues.add(HdfsIssue.MALFORMED_BLOCK_TOKEN)
    if decoded.ending is LineEnding.NONE:
        issues.add(HdfsIssue.MISSING_LINE_TERMINATOR)

    component_id: str | None = None
    reason: HdfsUnassignedReason | None = None
    if tokens.normalized:
        component_ids = {
            index.block_to_component.get(block_id) for block_id in tokens.normalized
        }
        if None in component_ids or len(component_ids) != 1:
            raise MetadataExtractionError(
                f"inconsistent HDFS component index at line {line_number}"
            )
        component_id = next(iter(component_ids))
        status = HdfsAssignmentStatus.ASSIGNED
    else:
        status = HdfsAssignmentStatus.UNASSIGNED
        if decoded.status is DecodeStatus.DECODE_ERROR:
            reason = HdfsUnassignedReason.DECODE_ERROR
        elif tokens.malformed:
            reason = HdfsUnassignedReason.MALFORMED_BLOCK_TOKEN
        else:
            reason = HdfsUnassignedReason.NO_BLOCK_ID

    record_id = build_record_id(
        dataset_fingerprint=source.dataset_fingerprint,
        source_file=source.source_file,
        source_line_number=line_number,
        source_line_sha256=decoded.sha256,
    )
    return HdfsLineMetadata(
        source_id=source.source_id,
        dataset_fingerprint=source.dataset_fingerprint,
        source_file=source.source_file,
        record_id=record_id,
        source_line_number=line_number,
        chronological_index=line_number - 1,
        source_line_sha256=decoded.sha256,
        line_ending=decoded.ending,
        decode_status=decoded.status,
        raw_block_tokens=tokens.raw,
        block_ids=tokens.normalized,
        duplicate_block_ids=tokens.duplicates,
        malformed_block_tokens=tokens.malformed,
        component_id=component_id,
        assignment_status=status,
        unassigned_reason=reason,
        issues=tuple(sorted(issues, key=lambda item: item.value)),
    )


def iter_hdfs_metadata(
    log_path: str | Path,
    source: MetadataSource,
    component_index: HdfsComponentIndex,
    *,
    max_lines: int | None = None,
) -> Iterator[HdfsLineMetadata]:
    """Second pass: emit every HDFS line with final component membership."""

    for line_number, raw_line in _iter_lines(Path(log_path), max_lines):
        yield _hdfs_line(raw_line, line_number, source, component_index)


def iter_hdfs_structural_references(
    log_path: str | Path,
    source: MetadataSource,
    component_index: HdfsComponentIndex,
    *,
    max_lines: int | None = None,
) -> Iterator[HdfsStructuralReference]:
    """Stream the exact label-free META-001 fields required by SPLIT-001.

    This avoids constructing millions of full Pydantic metadata records while
    retaining the same token normalization, component map, source chronology,
    and explicit unassigned reasons as :func:`iter_hdfs_metadata`.
    """

    if source.dataset_key != "hdfs":
        raise MetadataExtractionError("HDFS references require an HDFS source")
    for line_number, raw_line in _iter_lines(Path(log_path), max_lines):
        decoded = _decode_line(raw_line)
        tokens = _hdfs_tokens(decoded.text)
        if tokens.normalized:
            component_ids = {
                component_index.block_to_component.get(block_id)
                for block_id in tokens.normalized
            }
            if None in component_ids or len(component_ids) != 1:
                raise MetadataExtractionError(
                    f"inconsistent HDFS component index at line {line_number}"
                )
            yield HdfsStructuralReference(
                chronological_index=line_number - 1,
                component_id=next(iter(component_ids)),
                record_id=None,
                assignment_status=HdfsAssignmentStatus.ASSIGNED,
                unassigned_reason=None,
            )
            continue

        if decoded.status is DecodeStatus.DECODE_ERROR:
            reason = HdfsUnassignedReason.DECODE_ERROR
        elif tokens.malformed:
            reason = HdfsUnassignedReason.MALFORMED_BLOCK_TOKEN
        else:
            reason = HdfsUnassignedReason.NO_BLOCK_ID
        record_id = build_record_id(
            dataset_fingerprint=source.dataset_fingerprint,
            source_file=source.source_file,
            source_line_number=line_number,
            source_line_sha256=decoded.sha256,
        )
        yield HdfsStructuralReference(
            chronological_index=line_number - 1,
            component_id=None,
            record_id=record_id,
            assignment_status=HdfsAssignmentStatus.UNASSIGNED,
            unassigned_reason=reason,
        )


def _parse_bgl_timestamp(
    text: str | None,
) -> tuple[int | None, str | None, str | None, datetime | None, BglTimestampStatus]:
    if text is None:
        return None, None, None, None, BglTimestampStatus.DECODE_ERROR
    fields = text.split(maxsplit=5)
    if len(fields) < 5:
        return None, None, None, None, BglTimestampStatus.MALFORMED_TIMESTAMP
    try:
        epoch_seconds: int | None = int(fields[1])
    except ValueError:
        epoch_seconds = None
    source_timestamp = fields[4]
    try:
        parsed = datetime.strptime(source_timestamp, BGL_TIMESTAMP_FORMAT)
    except ValueError:
        return (
            epoch_seconds,
            source_timestamp,
            None,
            None,
            BglTimestampStatus.MALFORMED_TIMESTAMP,
        )
    return (
        epoch_seconds,
        source_timestamp,
        parsed.isoformat(timespec="microseconds"),
        parsed,
        BglTimestampStatus.PARSED,
    )


def _bgl_line(
    raw_line: bytes,
    line_number: int,
    source: MetadataSource,
    previous_timestamp: datetime | None,
) -> tuple[BglLineMetadata, datetime | None]:
    decoded = _decode_line(raw_line)
    epoch, source_timestamp, timestamp_iso, parsed, status = _parse_bgl_timestamp(
        decoded.text
    )
    issues: set[BglIssue] = set()
    if decoded.ending is LineEnding.NONE:
        issues.add(BglIssue.MISSING_LINE_TERMINATOR)
    if parsed is not None and previous_timestamp is not None and parsed < previous_timestamp:
        issues.add(BglIssue.TIMESTAMP_REGRESSION)
    record_id = build_record_id(
        dataset_fingerprint=source.dataset_fingerprint,
        source_file=source.source_file,
        source_line_number=line_number,
        source_line_sha256=decoded.sha256,
    )
    chronology_id = build_bgl_chronology_id(
        source_file=source.source_file,
        original_line_index=line_number - 1,
        timestamp_iso=timestamp_iso,
    )
    metadata = BglLineMetadata(
        source_id=source.source_id,
        dataset_fingerprint=source.dataset_fingerprint,
        source_file=source.source_file,
        record_id=record_id,
        chronology_id=chronology_id,
        source_line_number=line_number,
        original_line_index=line_number - 1,
        chronological_rank=line_number - 1,
        source_line_sha256=decoded.sha256,
        line_ending=decoded.ending,
        decode_status=decoded.status,
        source_epoch_seconds=epoch,
        source_timestamp=source_timestamp,
        timestamp_iso=timestamp_iso,
        timestamp_status=status,
        issues=tuple(sorted(issues, key=lambda item: item.value)),
    )
    return metadata, parsed if parsed is not None else previous_timestamp


def extract_bgl_line_metadata(
    raw_line: bytes,
    *,
    line_number: int,
    source: MetadataSource,
) -> BglLineMetadata:
    """Extract one BGL line while ignoring the first-field label value."""

    if source.dataset_key != "bgl":
        raise MetadataExtractionError("BGL extraction requires a BGL source")
    metadata, _ = _bgl_line(raw_line, line_number, source, None)
    return metadata


def iter_bgl_metadata(
    log_path: str | Path,
    source: MetadataSource,
    *,
    max_lines: int | None = None,
) -> Iterator[BglLineMetadata]:
    """Stream BGL metadata in authoritative source-line chronology."""

    if source.dataset_key != "bgl":
        raise MetadataExtractionError("BGL extraction requires a BGL source")
    previous_timestamp: datetime | None = None
    for line_number, raw_line in _iter_lines(Path(log_path), max_lines):
        metadata, previous_timestamp = _bgl_line(
            raw_line, line_number, source, previous_timestamp
        )
        yield metadata


def summarize_hdfs_metadata(
    log_path: str | Path,
    source: MetadataSource,
    *,
    max_lines: int,
) -> MetadataArtifactSummary:
    """Bounded structural dry-run; no artifact or split is created."""

    index = scan_hdfs_components(log_path, source, max_lines=max_lines)
    assigned = unassigned = observed = 0
    for item in iter_hdfs_metadata(
        log_path, source, index, max_lines=max_lines
    ):
        observed += 1
        if item.assignment_status is HdfsAssignmentStatus.ASSIGNED:
            assigned += 1
        else:
            unassigned += 1
    return MetadataArtifactSummary(
        source=source,
        complete=False,
        lines_observed=observed,
        counts={
            "assigned_lines": assigned,
            "components_in_bounded_prefix": len(index.components),
            "unassigned_lines": unassigned,
        },
    )


def summarize_bgl_metadata(
    log_path: str | Path,
    source: MetadataSource,
    *,
    max_lines: int,
) -> MetadataArtifactSummary:
    """Bounded chronology dry-run; no artifact or split is created."""

    observed = parsed = malformed = regressions = 0
    for item in iter_bgl_metadata(log_path, source, max_lines=max_lines):
        observed += 1
        if item.timestamp_status is BglTimestampStatus.PARSED:
            parsed += 1
        else:
            malformed += 1
        if BglIssue.TIMESTAMP_REGRESSION in item.issues:
            regressions += 1
    return MetadataArtifactSummary(
        source=source,
        complete=False,
        lines_observed=observed,
        counts={
            "parsed_timestamps": parsed,
            "retained_malformed_timestamps": malformed,
            "timestamp_regressions": regressions,
        },
    )


def _write_jsonl(
    path: Path, records: Iterator[MetadataModel]
) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    with path.open("xb") as handle:
        for record in records:
            payload = (record.canonical_json() + "\n").encode("utf-8")
            handle.write(payload)
            digest.update(payload)
            count += 1
    return count, digest.hexdigest()


def _temporary_output(output_dir: Path) -> Path:
    if output_dir.exists():
        raise FileExistsError(f"metadata output already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_dir.parent / f".{output_dir.name}.tmp"
    if temporary.exists():
        raise FileExistsError(f"metadata temporary output already exists: {temporary}")
    temporary.mkdir()
    return temporary


def _write_summary(path: Path, summary: MetadataArtifactSummary) -> None:
    payload = json.dumps(
        summary.model_dump(mode="json"),
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    path.write_text(payload, encoding="utf-8")


def write_hdfs_metadata_artifact(
    log_path: str | Path,
    source: MetadataSource,
    output_dir: str | Path,
) -> MetadataArtifactSummary:
    """Write complete HDFS metadata atomically and refuse overwrite."""

    destination = Path(output_dir)
    temporary = _temporary_output(destination)
    try:
        index = scan_hdfs_components(log_path, source)
        component_count, component_hash = _write_jsonl(
            temporary / "components.jsonl", iter(index.components)
        )
        counters = {"assigned_lines": 0, "unassigned_lines": 0}

        def counted() -> Iterator[HdfsLineMetadata]:
            for item in iter_hdfs_metadata(log_path, source, index):
                key = (
                    "assigned_lines"
                    if item.assignment_status is HdfsAssignmentStatus.ASSIGNED
                    else "unassigned_lines"
                )
                counters[key] += 1
                yield item

        line_count, line_hash = _write_jsonl(temporary / "lines.jsonl", counted())
        counters["components"] = component_count
        summary = MetadataArtifactSummary(
            source=source,
            complete=True,
            lines_observed=line_count,
            counts=counters,
            generated_files=(
                MetadataFileArtifact(
                    path="components.jsonl",
                    sha256=component_hash,
                    record_count=component_count,
                ),
                MetadataFileArtifact(
                    path="lines.jsonl",
                    sha256=line_hash,
                    record_count=line_count,
                ),
            ),
        )
        _write_summary(temporary / "summary.json", summary)
        temporary.replace(destination)
        return summary
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def write_bgl_metadata_artifact(
    log_path: str | Path,
    source: MetadataSource,
    output_dir: str | Path,
) -> MetadataArtifactSummary:
    """Write complete BGL chronology metadata atomically and refuse overwrite."""

    destination = Path(output_dir)
    temporary = _temporary_output(destination)
    try:
        counters = {
            "parsed_timestamps": 0,
            "retained_malformed_timestamps": 0,
            "timestamp_regressions": 0,
        }

        def counted() -> Iterator[BglLineMetadata]:
            for item in iter_bgl_metadata(log_path, source):
                if item.timestamp_status is BglTimestampStatus.PARSED:
                    counters["parsed_timestamps"] += 1
                else:
                    counters["retained_malformed_timestamps"] += 1
                if BglIssue.TIMESTAMP_REGRESSION in item.issues:
                    counters["timestamp_regressions"] += 1
                yield item

        line_count, line_hash = _write_jsonl(temporary / "lines.jsonl", counted())
        summary = MetadataArtifactSummary(
            source=source,
            complete=True,
            lines_observed=line_count,
            counts=counters,
            generated_files=(
                MetadataFileArtifact(
                    path="lines.jsonl",
                    sha256=line_hash,
                    record_count=line_count,
                ),
            ),
        )
        _write_summary(temporary / "summary.json", summary)
        temporary.replace(destination)
        return summary
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


__all__ = [
    "BGL_TIMESTAMP_FORMAT",
    "BglIssue",
    "BglLineMetadata",
    "BglTimestampStatus",
    "DecodeStatus",
    "HdfsAssignmentStatus",
    "HdfsComponentIndex",
    "HdfsComponentMetadata",
    "HdfsIssue",
    "HdfsLineMetadata",
    "HdfsStructuralReference",
    "HdfsUnassignedReason",
    "LineEnding",
    "METADATA_CONTRACT_ID",
    "METADATA_SCHEMA_VERSION",
    "MetadataArtifactSummary",
    "MetadataFileArtifact",
    "MetadataSource",
    "build_bgl_chronology_id",
    "build_hdfs_component_id",
    "build_metadata_source_id",
    "extract_bgl_line_metadata",
    "iter_bgl_metadata",
    "iter_hdfs_metadata",
    "iter_hdfs_structural_references",
    "resolve_metadata_source",
    "scan_hdfs_components",
    "summarize_bgl_metadata",
    "summarize_hdfs_metadata",
    "write_bgl_metadata_artifact",
    "write_hdfs_metadata_artifact",
]
