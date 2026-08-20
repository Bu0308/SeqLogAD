"""Canonical event and template contracts for SCHEMA-001.

The models in this module define identities and trust boundaries only. They do
not parse logs, assign partitions, fit Drain3, or read supervision files.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Literal, TypeAlias

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


EVENT_SCHEMA_VERSION = "1.0"
UNSEEN_EVENT_ID = "EVT_UNSEEN"

Sha256Hex: TypeAlias = str
AttributeScalar: TypeAlias = str | int | float | bool | None

_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_EVENT_ID_PATTERN = r"^(?:EVT_UNSEEN|EVT-[0-9a-f]{64})$"
_RECORD_ID_PATTERN = r"^LOG-[0-9a-f]{64}$"
_ATTRIBUTE_NAME_PATTERN = r"^[a-z][a-z0-9_.-]*$"
_LABEL_ATTRIBUTE_TOKENS = frozenset({"label", "anomaly", "groundtruth"})
_LABEL_ATTRIBUTE_NAMES = frozenset(
    {
        "alert",
        "alert_category",
        "alert_marker",
        "ground_truth",
        "is_alert",
        "is_anomaly",
        "source_label",
    }
)


class ScientificPartition(StrEnum):
    """Frozen PROTOCOL-001 top-level partitions."""

    BASE_TRAIN = "BASE_TRAIN"
    FUSION_TRAIN = "FUSION_TRAIN"
    VAL_EXPERT = "VAL_EXPERT"
    VAL_FUSION = "VAL_FUSION"
    TEST = "TEST"


class GroupKind(StrEnum):
    """Dataset grouping identity available before sequence construction."""

    NONE = "none"
    HDFS_BLOCK = "hdfs_block"


class AnomalyLabel(StrEnum):
    """Controlled real-label values; never model features."""

    NORMAL = "normal"
    ANOMALY = "anomaly"


class LabelGranularity(StrEnum):
    """Scientific unit to which a real source label applies."""

    EVENT = "event"
    BLOCK_SESSION = "block_session"


class LabelAccess(StrEnum):
    """Authorized pre-TEST uses of real labels."""

    NORMAL_POOL_FILTERING = "normal_pool_filtering"
    VALIDATION_EVALUATION = "validation_evaluation"


class LabelSourceKind(StrEnum):
    """How a controlled label is represented by the source dataset."""

    EXTERNAL_FILE = "external_file"
    INLINE_FIELD = "inline_field"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_identity_component(value: str, field_name: str) -> str:
    if not value or value != value.strip() or "\x00" in value:
        raise ValueError(f"{field_name} must be non-empty, trimmed, and NUL-free")
    return value


def _validate_repository_relative_path(value: str) -> str:
    if "\\" in value or "\x00" in value:
        raise ValueError("source_file must be a repository-relative POSIX path")
    candidate = PurePosixPath(value)
    if (
        not value
        or candidate.is_absolute()
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or candidate.as_posix() != value
    ):
        raise ValueError("source_file must be a normalized repository-relative POSIX path")
    return value


def build_event_id(
    *,
    parser_version: str,
    normalization_version: str,
    normalized_template: str,
) -> str:
    """Build the frozen deterministic event/template identity."""

    parser_version = _validate_identity_component(parser_version, "parser_version")
    normalization_version = _validate_identity_component(
        normalization_version, "normalization_version"
    )
    if not normalized_template or "\x00" in normalized_template:
        raise ValueError("normalized_template must be non-empty and NUL-free")
    payload = "\x00".join(
        ("drain3", parser_version, normalization_version, normalized_template)
    )
    return f"EVT-{_sha256_text(payload)}"


def build_record_id(
    *,
    dataset_fingerprint: str,
    source_file: str,
    source_line_number: int,
    source_line_sha256: str,
) -> str:
    """Build a deterministic identity for one source log occurrence."""

    if not re.fullmatch(_SHA256_PATTERN, dataset_fingerprint):
        raise ValueError("dataset_fingerprint must be a lowercase SHA-256 digest")
    source_file = _validate_repository_relative_path(source_file)
    if source_line_number < 1:
        raise ValueError("source_line_number must be one-based")
    if not re.fullmatch(_SHA256_PATTERN, source_line_sha256):
        raise ValueError("source_line_sha256 must be a lowercase SHA-256 digest")
    payload = "\x00".join(
        (
            dataset_fingerprint,
            source_file,
            str(source_line_number),
            source_line_sha256,
        )
    )
    return f"LOG-{_sha256_text(payload)}"


class CanonicalSchemaModel(BaseModel):
    """Strict, immutable base with deterministic JSON serialization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    def canonical_json(self) -> str:
        """Serialize with stable key order and no non-finite JSON values."""

        return json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    def canonical_sha256(self) -> str:
        """Hash the canonical JSON representation."""

        return _sha256_text(self.canonical_json())


class EventAttribute(CanonicalSchemaModel):
    """One deterministic, model-safe event attribute."""

    name: str = Field(pattern=_ATTRIBUTE_NAME_PATTERN)
    value: AttributeScalar

    @field_validator("name")
    @classmethod
    def reject_supervision_names(cls, value: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
        tokens = frozenset(token for token in normalized.split("_") if token)
        if normalized in _LABEL_ATTRIBUTE_NAMES or tokens & _LABEL_ATTRIBUTE_TOKENS:
            raise ValueError("supervision/label fields are forbidden in model attributes")
        return value

    @field_validator("value")
    @classmethod
    def reject_non_finite_float(cls, value: AttributeScalar) -> AttributeScalar:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("attribute floats must be finite")
        return value


class EventObservation(CanonicalSchemaModel):
    """Label-isolated source observation retained after metadata extraction."""

    message: str = Field(min_length=1)
    label_isolated: Literal[True] = True
    source_timestamp: str | None = None
    timestamp_utc: AwareDatetime | None = None
    attributes: tuple[EventAttribute, ...] = ()

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("message must be NUL-free")
        return value

    @field_validator("source_timestamp")
    @classmethod
    def validate_source_timestamp(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_identity_component(value, "source_timestamp")

    @field_validator("attributes")
    @classmethod
    def canonicalize_attributes(
        cls, value: tuple[EventAttribute, ...]
    ) -> tuple[EventAttribute, ...]:
        names = [item.name for item in value]
        if len(names) != len(set(names)):
            raise ValueError("attribute names must be unique")
        return tuple(sorted(value, key=lambda item: item.name))


class EventProvenance(CanonicalSchemaModel):
    """Immutable dataset, source-line, chronology, and grouping identity."""

    dataset_key: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    dataset_fingerprint: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    source_file: str
    source_line_number: int = Field(ge=1)
    chronological_index: int = Field(ge=0)
    source_line_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    partition: ScientificPartition
    group_kind: GroupKind = GroupKind.NONE
    group_ids: tuple[str, ...] = ()

    @field_validator("dataset_id", "dataset_version")
    @classmethod
    def validate_dataset_identity(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "dataset_identity")
        return _validate_identity_component(value, field_name)

    @field_validator("source_file")
    @classmethod
    def validate_source_file(cls, value: str) -> str:
        return _validate_repository_relative_path(value)

    @field_validator("group_ids")
    @classmethod
    def validate_group_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(
            _validate_identity_component(item, "group_ids item") for item in value
        )
        if len(normalized) != len(set(normalized)):
            raise ValueError("group_ids must be unique")
        return normalized

    @model_validator(mode="after")
    def validate_group_contract(self) -> "EventProvenance":
        if self.group_kind is GroupKind.NONE and self.group_ids:
            raise ValueError("group_ids must be empty when group_kind is none")
        if self.group_kind is not GroupKind.NONE and not self.group_ids:
            raise ValueError("group_ids are required for a grouped event")
        return self


class EventSupervision(CanonicalSchemaModel):
    """Controlled real-label data kept outside the model-input contract."""

    label: AnomalyLabel
    granularity: LabelGranularity
    access: LabelAccess
    source_kind: LabelSourceKind
    source_reference: str = Field(min_length=1)
    category: str | None = None

    @field_validator("source_reference", "category")
    @classmethod
    def validate_reference(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        field_name = getattr(info, "field_name", "label_reference")
        return _validate_identity_component(value, field_name)


class EventTemplate(CanonicalSchemaModel):
    """Frozen Drain3 template identity independent of discovery order."""

    schema_version: Literal["1.0"] = EVENT_SCHEMA_VERSION
    event_id: str = Field(pattern=_EVENT_ID_PATTERN)
    normalized_template: str = Field(min_length=1)
    parser_name: Literal["drain3"] = "drain3"
    parser_version: str = Field(min_length=1)
    parser_config_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    normalization_version: str = Field(min_length=1)
    normalization_config_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    template_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    fit_partition: ScientificPartition = ScientificPartition.BASE_TRAIN

    @field_validator("normalized_template")
    @classmethod
    def validate_template(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("normalized_template must be NUL-free")
        return value

    @field_validator("parser_version", "normalization_version")
    @classmethod
    def validate_versions(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "version")
        return _validate_identity_component(value, field_name)

    @model_validator(mode="after")
    def validate_frozen_identity(self) -> "EventTemplate":
        if self.fit_partition is not ScientificPartition.BASE_TRAIN:
            raise ValueError("templates may only be fitted in BASE_TRAIN")
        expected_template_hash = _sha256_text(self.normalized_template)
        if self.template_sha256 != expected_template_hash:
            raise ValueError("template_sha256 does not match normalized_template")
        expected_event_id = build_event_id(
            parser_version=self.parser_version,
            normalization_version=self.normalization_version,
            normalized_template=self.normalized_template,
        )
        if self.event_id != expected_event_id:
            raise ValueError("event_id does not match the frozen identity algorithm")
        return self


class EventModelInput(CanonicalSchemaModel):
    """Explicit label-free view consumable by future sequence components."""

    record_id: str = Field(pattern=_RECORD_ID_PATTERN)
    event_id: str = Field(pattern=_EVENT_ID_PATTERN)
    timestamp_utc: AwareDatetime | None = None
    attributes: tuple[EventAttribute, ...] = ()


class LogEvent(CanonicalSchemaModel):
    """Canonical parsed event with isolated provenance and supervision."""

    schema_version: Literal["1.0"] = EVENT_SCHEMA_VERSION
    record_id: str = Field(pattern=_RECORD_ID_PATTERN)
    provenance: EventProvenance
    observation: EventObservation
    event_id: str = Field(pattern=_EVENT_ID_PATTERN)
    parameters: tuple[str, ...] = ()
    parser_state_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    template_registry_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    supervision: EventSupervision | None = None

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any("\x00" in item for item in value):
            raise ValueError("parameters must be NUL-free")
        return value

    @model_validator(mode="after")
    def validate_scientific_boundaries(self) -> "LogEvent":
        expected_record_id = build_record_id(
            dataset_fingerprint=self.provenance.dataset_fingerprint,
            source_file=self.provenance.source_file,
            source_line_number=self.provenance.source_line_number,
            source_line_sha256=self.provenance.source_line_sha256,
        )
        if self.record_id != expected_record_id:
            raise ValueError("record_id does not match source provenance")

        if self.provenance.dataset_key == "hdfs":
            if self.provenance.group_kind is not GroupKind.HDFS_BLOCK:
                raise ValueError("HDFS events require hdfs_block grouping identity")
            if (
                self.supervision is not None
                and self.supervision.granularity is not LabelGranularity.BLOCK_SESSION
            ):
                raise ValueError("HDFS supervision must use block_session granularity")

        if self.provenance.dataset_key == "bgl":
            if self.provenance.group_kind is not GroupKind.NONE:
                raise ValueError("BGL events must not claim pre-window grouping")
            if (
                self.supervision is not None
                and self.supervision.granularity is not LabelGranularity.EVENT
            ):
                raise ValueError("BGL source supervision must use event granularity")

        partition = self.provenance.partition
        if partition is ScientificPartition.TEST:
            if self.supervision is not None:
                raise ValueError("TEST LogEvent records must not expose supervision")
            return self

        if self.provenance.dataset_key in {"hdfs", "bgl"} and self.supervision is None:
            raise ValueError("labeled P0 datasets require controlled non-TEST supervision")

        if partition in {
            ScientificPartition.BASE_TRAIN,
            ScientificPartition.FUSION_TRAIN,
        }:
            if self.supervision is None:
                raise ValueError("training pools require a verified normal label")
            if self.supervision.label is not AnomalyLabel.NORMAL:
                raise ValueError("training pools may contain normal records only")
            if self.supervision.access is not LabelAccess.NORMAL_POOL_FILTERING:
                raise ValueError("training labels are authorized only for normal-pool filtering")

        if partition in {
            ScientificPartition.VAL_EXPERT,
            ScientificPartition.VAL_FUSION,
        } and (
            self.supervision is None
            or self.supervision.access is not LabelAccess.VALIDATION_EVALUATION
        ):
            raise ValueError("validation labels require validation_evaluation access")

        return self

    def to_model_input(self) -> EventModelInput:
        """Return the only supported label-free model-input view."""

        return EventModelInput(
            record_id=self.record_id,
            event_id=self.event_id,
            timestamp_utc=self.observation.timestamp_utc,
            attributes=self.observation.attributes,
        )


__all__ = [
    "AnomalyLabel",
    "AttributeScalar",
    "EVENT_SCHEMA_VERSION",
    "EventAttribute",
    "EventModelInput",
    "EventObservation",
    "EventProvenance",
    "EventSupervision",
    "EventTemplate",
    "GroupKind",
    "LabelAccess",
    "LabelGranularity",
    "LabelSourceKind",
    "LogEvent",
    "ScientificPartition",
    "UNSEEN_EVENT_ID",
    "build_event_id",
    "build_record_id",
]
