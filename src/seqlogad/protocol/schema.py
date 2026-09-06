"""LOG-UNIFY-001 — canonical multi-source log record contract (Excel P1.3).

Every active architecture maps into this one record shape.  Three properties are
enforced by the model itself rather than by convention:

1. **Raw text survives.**  ``raw_message_sha256`` binds the exact source bytes and
   ``canonical_message`` is derived from them by the versioned NUL codec, so the
   original content is always recoverable or provable.
2. **Missing data is typed, never invented.**  Optional fields are explicitly
   nullable and every record carries a ``parse_status`` / ``timestamp_status``, so a
   line that could not be parsed is *counted*, not silently dropped.
3. **No labels.**  There is no label field, and attribute names that look like
   supervision are rejected, so a target label cannot ride into an adaptation path
   inside a record.
"""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from seqlogad.protocol.architectures import ParseStatus, TimestampStatus
from seqlogad.protocol.nul import NormalizationStatus


LOG_UNIFY_SCHEMA_VERSION = "1.0"
LOG_UNIFY_CONTRACT_ID = "LOG-UNIFY-001"

_SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]

_LABEL_TOKENS = frozenset({"label", "anomaly", "groundtruth", "ground_truth", "target_label", "is_anomaly"})


class SchemaViolation(ValueError):
    """Raised when a record would break the unified contract."""


class CanonicalModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=False)

    def canonical_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

    def canonical_sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


class MessageRepresentation(CanonicalModel):
    """Present only when the NUL codec changed the bytes (omission means UNCHANGED)."""

    policy_id: Literal["CANONICAL-NUL-DECISION-001"] = "CANONICAL-NUL-DECISION-001"
    policy_version: Literal["seqlogad-nul-escape-v1"] = "seqlogad-nul-escape-v1"
    status: Literal["NUL_ESCAPED"] = "NUL_ESCAPED"
    raw_message_sha256: _SHA256


class CanonicalLogRecord(CanonicalModel):
    """One raw source line, represented once, with no supervision attached."""

    schema_version: Literal["1.0"] = LOG_UNIFY_SCHEMA_VERSION

    # --- identity and provenance (always required) ---------------------------
    dataset_id: str = Field(min_length=1)
    architecture_id: str = Field(pattern=r"^ARCH-[A-Z0-9_]+$")
    source_file: str = Field(min_length=1)
    source_line_number: int = Field(ge=1)
    source_order: int = Field(ge=0, description="Chronological rank within the architecture.")

    # --- declared-nullable observation fields --------------------------------
    timestamp_utc: str | None = None
    timestamp_status: TimestampStatus
    level: str | None = None
    service: str | None = None
    component: str | None = None
    node_id: str | None = None
    session_id: str | None = None
    trace_id: str | None = None

    # --- message layers -------------------------------------------------------
    canonical_message: str
    raw_message_sha256: _SHA256
    normalized_message: str
    normalizer_version: str = Field(min_length=1)
    message_representation: MessageRepresentation | None = None

    # --- optional derived template (Drain3 is auxiliary, never authoritative) --
    template_id: str | None = None
    template_source: str | None = None

    parse_status: ParseStatus

    @field_validator("source_file")
    @classmethod
    def reject_absolute_path(cls, value: str) -> str:
        if value.startswith("/") or value.startswith("~") or ".." in value.split("/"):
            raise SchemaViolation("source_file must be a repository-relative path")
        return value

    @field_validator("canonical_message")
    @classmethod
    def reject_nul(cls, value: str) -> str:
        if "\x00" in value:
            raise SchemaViolation(
                "canonical_message must be NUL-free; apply seqlogad-nul-escape-v1 first"
            )
        return value

    @model_validator(mode="after")
    def validate_contract(self) -> "CanonicalLogRecord":
        if self.timestamp_status is TimestampStatus.PARSED and self.timestamp_utc is None:
            raise SchemaViolation("timestamp_status PARSED requires a timestamp")
        if self.timestamp_status is not TimestampStatus.PARSED and self.timestamp_utc is not None:
            raise SchemaViolation("only PARSED records may carry a timestamp")
        if self.message_representation is not None:
            if self.message_representation.raw_message_sha256 != self.raw_message_sha256:
                raise SchemaViolation("representation hash must match raw_message_sha256")
        if self.template_id is not None and self.template_source is None:
            raise SchemaViolation("template_id requires a declared template_source")
        for field_name in type(self).model_fields:
            if any(token in field_name.lower() for token in _LABEL_TOKENS):
                raise SchemaViolation(
                    f"field {field_name} looks like supervision; labels are evaluation-only"
                )
        return self

    @property
    def message_representation_status(self) -> NormalizationStatus:
        """Omission is defined as UNCHANGED by the manifest-bound NUL policy."""

        if self.message_representation is None:
            return NormalizationStatus.UNCHANGED
        return NormalizationStatus.NUL_ESCAPED


class SourceMapping(CanonicalModel):
    """Per-architecture field mapping contract required by Excel P1.3."""

    architecture_id: str
    dataset_id: str
    adapter: str
    required_present: tuple[str, ...]
    declared_absent: tuple[str, ...]
    derived: dict[str, str]
    label_field_stripped: str | None = None
    notes: str = ""


SOURCE_MAPPINGS: dict[str, SourceMapping] = {
    "ARCH-HDFS": SourceMapping(
        architecture_id="ARCH-HDFS",
        dataset_id="HDFS_v1",
        adapter="hdfs",
        required_present=("timestamp_utc", "level", "service", "component", "canonical_message"),
        declared_absent=("node_id", "trace_id"),
        derived={
            "timestamp_utc": "date+time fields, yymmdd HHMMSS, interpreted as UTC",
            "service": "first dotted segment of the component field",
            "session_id": "first blk_<id> token in the message, else null",
        },
        label_field_stripped=None,
        notes="Ground truth lives in a separate CSV keyed by block id, never in the line.",
    ),
    "ARCH-BGL": SourceMapping(
        architecture_id="ARCH-BGL",
        dataset_id="BGL",
        adapter="bgl",
        required_present=("timestamp_utc", "level", "service", "component", "node_id", "canonical_message"),
        declared_absent=("session_id", "trace_id"),
        derived={
            "timestamp_utc": "field 4, %Y-%m-%d-%H.%M.%S.%f, interpreted as UTC",
            "service": "field 6 (record type, e.g. RAS)",
            "component": "field 7 (e.g. KERNEL)",
            "node_id": "field 3 (physical location)",
        },
        label_field_stripped="field_0_alert_marker",
        notes="Field 0 is the inline alert marker; the adapter drops it before any use.",
    ),
    "ARCH-HADOOP": SourceMapping(
        architecture_id="ARCH-HADOOP",
        dataset_id="Hadoop",
        adapter="hadoop",
        required_present=("canonical_message",),
        declared_absent=(),
        derived={
            "timestamp_utc": "leading %Y-%m-%d %H:%M:%S,%f, interpreted as UTC",
            "service": "package segment after org.apache.hadoop.",
            "session_id": "application_<id> directory name",
            "trace_id": "container log file stem",
            "node_id": "thread name in square brackets",
        },
        label_field_stripped=None,
        notes=(
            "Wrapped stack-trace lines are emitted as CONTINUATION records with a null "
            "timestamp, so one raw line still yields exactly one canonical record."
        ),
    ),
    "ARCH-OPENSTACK": SourceMapping(
        architecture_id="ARCH-OPENSTACK",
        dataset_id="OpenStack",
        adapter="openstack",
        required_present=("timestamp_utc", "level", "service", "component", "canonical_message"),
        declared_absent=("node_id",),
        derived={
            "timestamp_utc": "%Y-%m-%d %H:%M:%S.%f, interpreted as UTC",
            "service": "log-file prefix before '.log' (nova-api, nova-compute, ...)",
            "session_id": "[instance: <uuid>] marker when present",
            "trace_id": "req-<uuid> request identifier when present",
        },
        label_field_stripped=None,
        notes="Ground truth is an external list of anomalous instance UUIDs.",
    ),
}


def build_record(
    *,
    dataset_id: str,
    architecture_id: str,
    source_order: int,
    raw_record,
    canonicalized,
    normalized_message: str,
    normalizer_version: str,
    timestamp_utc: str | None,
) -> CanonicalLogRecord:
    """Assemble one validated canonical record from adapter + codec + normaliser output."""

    representation = None
    block = canonicalized.representation_block()
    if block is not None:
        representation = MessageRepresentation(raw_message_sha256=block["raw_message_sha256"])
    return CanonicalLogRecord(
        dataset_id=dataset_id,
        architecture_id=architecture_id,
        source_file=raw_record.source_file,
        source_line_number=raw_record.source_line_number,
        source_order=source_order,
        timestamp_utc=timestamp_utc,
        timestamp_status=raw_record.timestamp_status,
        level=raw_record.level,
        service=raw_record.service,
        component=raw_record.component,
        node_id=raw_record.node_id,
        session_id=raw_record.session_id,
        trace_id=raw_record.trace_id,
        canonical_message=canonicalized.canonical_message,
        raw_message_sha256=canonicalized.raw_message_sha256,
        normalized_message=normalized_message,
        normalizer_version=normalizer_version,
        message_representation=representation,
        parse_status=raw_record.parse_status,
    )


__all__ = [
    "LOG_UNIFY_CONTRACT_ID",
    "LOG_UNIFY_SCHEMA_VERSION",
    "SOURCE_MAPPINGS",
    "CanonicalLogRecord",
    "MessageRepresentation",
    "SchemaViolation",
    "SourceMapping",
    "build_record",
]
