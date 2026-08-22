"""Partition, sequence, localization, and mutation contracts for SCHEMA-002.

These models validate already-prepared synthetic records. They do not split
datasets, build sequences, mutate events, or access labels from storage.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from enum import StrEnum
from typing import Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from seqlogad.common.schemas.events import (
    AnomalyLabel,
    AttributeScalar,
    CanonicalSchemaModel,
    LabelAccess,
    LabelSourceKind,
    ScientificPartition,
)


SEQUENCE_SCHEMA_VERSION = "1.0"
MUTATION_SCHEMA_VERSION = "1.0"
SEQUENCE_DESTRUCTION_SCHEMA_VERSION = "1.0"

ProtocolVersion: TypeAlias = Literal["1.0", "1.1"]
Sha256Hex: TypeAlias = str

ACTIVE_PROTOCOL_VERSION: ProtocolVersion = "1.1"

_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_EVENT_ID_PATTERN = r"^(?:EVT_UNSEEN|EVT-[0-9a-f]{64})$"
_RECORD_ID_PATTERN = r"^LOG-[0-9a-f]{64}$"
_SPLIT_ID_PATTERN = r"^SPLIT-[0-9a-f]{64}$"
_PARTITION_ASSIGNMENT_ID_PATTERN = r"^PART-[0-9a-f]{64}$"
_SEQUENCE_ID_PATTERN = r"^SEQ-[0-9a-f]{64}$"
_MUTATION_ID_PATTERN = r"^MUT-[0-9a-f]{64}$"
_SEQUENCE_DESTRUCTION_ID_PATTERN = r"^CTRL-KT3-[0-9a-f]{64}$"
_PARAMETER_NAME_PATTERN = r"^[a-z][a-z0-9_.-]*$"

_TARGET_PARTITION_RATIOS = {
    ScientificPartition.BASE_TRAIN: 0.60,
    ScientificPartition.FUSION_TRAIN: 0.10,
    ScientificPartition.VAL_EXPERT: 0.10,
    ScientificPartition.VAL_FUSION: 0.10,
    ScientificPartition.TEST: 0.10,
}


class PartitionUnitKind(StrEnum):
    """Atomic raw unit assigned or excluded by the future splitter."""

    HDFS_BLOCK_COMPONENT = "hdfs_block_component"
    BGL_RAW_RANGE = "bgl_raw_range"


class PartitionDisposition(StrEnum):
    """Outcome of one atomic partition-assignment decision."""

    ASSIGNED = "assigned"
    PURGED_BOUNDARY = "purged_boundary"
    DROPPED_SHORT_WINDOW = "dropped_short_window"
    DROPPED_RESIDUAL_WINDOW = "dropped_residual_window"


class SequenceStrategy(StrEnum):
    """Frozen dataset-specific parent-sequence strategies."""

    HDFS_BLOCK_SESSION = "hdfs_block_session"
    BGL_FIXED_PARENT_WINDOW = "bgl_fixed_parent_window"


class LabelAggregationRule(StrEnum):
    """How event/source labels produce one parent-sequence label."""

    HDFS_BLOCK_SOURCE_LABEL = "hdfs_block_source_label"
    BGL_ANY_SOURCE_ALERT = "bgl_any_source_alert"


class LocalizationSource(StrEnum):
    """Provenance of coordinate-aware localization targets."""

    SYNTHETIC_MUTATION = "synthetic_mutation"
    REAL_SOURCE_ALERT = "real_source_alert"


class MutationOperation(StrEnum):
    """Frozen PROTOCOL-001 synthetic mutation families."""

    MISSING = "missing"
    EXTRA = "extra"
    REPEATED = "repeated"
    REPLACEMENT = "replacement"
    REORDER = "reorder"


class SequenceDestructionStatus(StrEnum):
    """Outcome of one KT-3 order-destruction attempt."""

    APPLIED = "applied"
    NOOP_UNPERTURBABLE = "noop_unperturbable"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _validate_text(value: str, field_name: str) -> str:
    if not value or value != value.strip() or "\x00" in value:
        raise ValueError(f"{field_name} must be non-empty, trimmed, and NUL-free")
    return value


def build_split_manifest_id(split_manifest_sha256: str) -> str:
    """Represent a split-manifest content hash as a stable artifact ID."""

    if not re.fullmatch(_SHA256_PATTERN, split_manifest_sha256):
        raise ValueError("split_manifest_sha256 must be a lowercase SHA-256 digest")
    return f"SPLIT-{split_manifest_sha256}"


def hash_event_ids(event_ids: tuple[str, ...]) -> str:
    """Hash an ordered, non-empty event-ID sequence."""

    if not event_ids:
        raise ValueError("event_ids must not be empty")
    if any(not re.fullmatch(_EVENT_ID_PATTERN, item) for item in event_ids):
        raise ValueError("event_ids contain an invalid event identity")
    return _sha256_text("\x00".join(event_ids))


def hash_event_multiset(event_ids: tuple[str, ...]) -> str:
    """Hash an event multiset while deliberately ignoring event order."""

    return hash_event_ids(tuple(sorted(event_ids)))


def build_partition_assignment_id(
    *,
    dataset_fingerprint: str,
    split_manifest_id: str,
    unit_kind: PartitionUnitKind,
    unit_key: str,
    chronological_start: int,
    chronological_end: int,
    disposition: PartitionDisposition,
    partition: ScientificPartition | None,
    member_group_ids: tuple[str, ...],
    reason: str | None,
) -> str:
    """Build a deterministic raw-unit partition-decision identity."""

    if not re.fullmatch(_SHA256_PATTERN, dataset_fingerprint):
        raise ValueError("dataset_fingerprint must be a lowercase SHA-256 digest")
    if not re.fullmatch(_SPLIT_ID_PATTERN, split_manifest_id):
        raise ValueError("split_manifest_id must be a valid SPLIT identity")
    unit_key = _validate_text(unit_key, "unit_key")
    if chronological_start < 0 or chronological_end < chronological_start:
        raise ValueError("chronological range is invalid")
    payload = {
        "chronological_end": chronological_end,
        "chronological_start": chronological_start,
        "dataset_fingerprint": dataset_fingerprint,
        "disposition": disposition.value,
        "member_group_ids": list(member_group_ids),
        "partition": None if partition is None else partition.value,
        "reason": reason,
        "split_manifest_id": split_manifest_id,
        "unit_key": unit_key,
        "unit_kind": unit_kind.value,
    }
    return f"PART-{_sha256_text(_canonical_json(payload))}"


def build_sequence_id(
    *,
    dataset_fingerprint: str,
    partition_assignment_id: str,
    strategy: SequenceStrategy,
    source_key: str,
    record_ids: tuple[str, ...],
) -> str:
    """Build an ordered parent-sequence identity."""

    if not re.fullmatch(_SHA256_PATTERN, dataset_fingerprint):
        raise ValueError("dataset_fingerprint must be a lowercase SHA-256 digest")
    if not re.fullmatch(_PARTITION_ASSIGNMENT_ID_PATTERN, partition_assignment_id):
        raise ValueError("partition_assignment_id must be a valid PART identity")
    source_key = _validate_text(source_key, "source_key")
    if not record_ids or any(
        not re.fullmatch(_RECORD_ID_PATTERN, item) for item in record_ids
    ):
        raise ValueError("record_ids must be non-empty valid LOG identities")
    payload = {
        "dataset_fingerprint": dataset_fingerprint,
        "partition_assignment_id": partition_assignment_id,
        "record_ids": list(record_ids),
        "source_key": source_key,
        "strategy": strategy.value,
    }
    return f"SEQ-{_sha256_text(_canonical_json(payload))}"


class PartitionIdentity(CanonicalSchemaModel):
    """Versioned split and assignment identity carried by a sequence."""

    protocol_id: Literal["PROTOCOL-001"] = "PROTOCOL-001"
    protocol_version: ProtocolVersion
    split_manifest_id: str = Field(pattern=_SPLIT_ID_PATTERN)
    split_manifest_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    assignment_id: str = Field(pattern=_PARTITION_ASSIGNMENT_ID_PATTERN)
    partition: ScientificPartition
    target_ratio: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_frozen_partition(self) -> "PartitionIdentity":
        if self.split_manifest_id != build_split_manifest_id(
            self.split_manifest_sha256
        ):
            raise ValueError("split_manifest_id does not match split manifest hash")
        expected_ratio = _TARGET_PARTITION_RATIOS[self.partition]
        if abs(self.target_ratio - expected_ratio) > 1e-12:
            raise ValueError("target_ratio does not match PROTOCOL-001")
        return self


def build_active_partition_identity(
    *,
    split_manifest_sha256: str,
    assignment_id: str,
    partition: ScientificPartition,
) -> PartitionIdentity:
    """Build a current artifact identity pinned to active Protocol v1.1."""

    return PartitionIdentity(
        protocol_version=ACTIVE_PROTOCOL_VERSION,
        split_manifest_id=build_split_manifest_id(split_manifest_sha256),
        split_manifest_sha256=split_manifest_sha256,
        assignment_id=assignment_id,
        partition=partition,
        target_ratio=_TARGET_PARTITION_RATIOS[partition],
    )


class PartitionAssignment(CanonicalSchemaModel):
    """One assigned or deliberately excluded atomic raw unit."""

    schema_version: Literal["1.0"] = SEQUENCE_SCHEMA_VERSION
    assignment_id: str = Field(pattern=_PARTITION_ASSIGNMENT_ID_PATTERN)
    dataset_fingerprint: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    split_manifest_id: str = Field(pattern=_SPLIT_ID_PATTERN)
    unit_kind: PartitionUnitKind
    unit_key: str = Field(min_length=1)
    chronological_start: int = Field(ge=0)
    chronological_end: int = Field(ge=0)
    source_line_start: int = Field(ge=1)
    source_line_end: int = Field(ge=1)
    event_count: int = Field(ge=0)
    disposition: PartitionDisposition
    partition: ScientificPartition | None = None
    member_group_ids: tuple[str, ...] = ()
    reason: str | None = None

    @field_validator("unit_key", "reason")
    @classmethod
    def validate_text_fields(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        field_name = getattr(info, "field_name", "text")
        return _validate_text(value, field_name)

    @field_validator("member_group_ids")
    @classmethod
    def canonicalize_group_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_validate_text(item, "member_group_ids item") for item in value)
        if len(normalized) != len(set(normalized)):
            raise ValueError("member_group_ids must be unique")
        return tuple(sorted(normalized))

    @model_validator(mode="after")
    def validate_assignment(self) -> "PartitionAssignment":
        if self.chronological_end < self.chronological_start:
            raise ValueError("chronological_end must not precede chronological_start")
        if self.source_line_end < self.source_line_start:
            raise ValueError("source_line_end must not precede source_line_start")

        if self.disposition is PartitionDisposition.ASSIGNED:
            if self.partition is None or self.reason is not None:
                raise ValueError("assigned units require partition and no exclusion reason")
            if self.event_count < 1:
                raise ValueError("assigned units must contain at least one event")
        else:
            if self.partition is not None or self.reason is None:
                raise ValueError("excluded units require reason and no partition")

        if self.unit_kind is PartitionUnitKind.HDFS_BLOCK_COMPONENT:
            if not self.member_group_ids:
                raise ValueError("HDFS components require member_group_ids")
            if self.disposition in {
                PartitionDisposition.DROPPED_SHORT_WINDOW,
                PartitionDisposition.DROPPED_RESIDUAL_WINDOW,
            }:
                raise ValueError("HDFS components cannot use BGL residual dispositions")
            if (
                self.disposition is PartitionDisposition.PURGED_BOUNDARY
                and self.event_count < 1
            ):
                raise ValueError("purged HDFS components must contain source events")

        if self.unit_kind is PartitionUnitKind.BGL_RAW_RANGE:
            if self.member_group_ids:
                raise ValueError("BGL raw ranges cannot contain HDFS group IDs")
            if self.disposition is PartitionDisposition.PURGED_BOUNDARY:
                raise ValueError("BGL raw ranges do not use HDFS boundary purge")
            if self.disposition is PartitionDisposition.DROPPED_SHORT_WINDOW:
                if self.event_count >= 20:
                    raise ValueError("dropped BGL residual windows must be shorter than 20")
            if self.disposition is PartitionDisposition.DROPPED_RESIDUAL_WINDOW:
                if not 1 <= self.event_count < 100:
                    raise ValueError(
                        "Protocol v1.1 dropped BGL residuals must contain 1 to 99 events"
                    )

        expected_id = build_partition_assignment_id(
            dataset_fingerprint=self.dataset_fingerprint,
            split_manifest_id=self.split_manifest_id,
            unit_kind=self.unit_kind,
            unit_key=self.unit_key,
            chronological_start=self.chronological_start,
            chronological_end=self.chronological_end,
            disposition=self.disposition,
            partition=self.partition,
            member_group_ids=self.member_group_ids,
            reason=self.reason,
        )
        if self.assignment_id != expected_id:
            raise ValueError("assignment_id does not match partition decision")
        return self


class LocalizationCoordinates(CanonicalSchemaModel):
    """Coordinate-family-aware localization with explicit unsupported state.

    ``None`` means a coordinate family is unavailable/unsupported. An empty
    tuple means it is supported but has no affected position for this record.
    """

    source: LocalizationSource
    sequence_level: bool
    token_positions: tuple[int, ...] | None = None
    gap_positions: tuple[int, ...] | None = None
    transition_positions: tuple[int, ...] | None = None

    @field_validator("token_positions", "gap_positions", "transition_positions")
    @classmethod
    def canonicalize_positions(
        cls, value: tuple[int, ...] | None
    ) -> tuple[int, ...] | None:
        if value is None:
            return None
        if any(item < 0 for item in value):
            raise ValueError("localization positions must be non-negative")
        if len(value) != len(set(value)):
            raise ValueError("localization positions must be unique")
        return tuple(sorted(value))

    @model_validator(mode="after")
    def require_supported_signal(self) -> "LocalizationCoordinates":
        families = (
            self.token_positions,
            self.gap_positions,
            self.transition_positions,
        )
        if not self.sequence_level and all(item is None for item in families):
            raise ValueError("localization must expose sequence or coordinate support")
        return self

    def validate_for_observed_length(self, observed_length: int) -> None:
        """Validate zero-based coordinates against an observed sequence."""

        if observed_length < 1:
            raise ValueError("observed_length must be positive")
        if self.token_positions is not None and any(
            item >= observed_length for item in self.token_positions
        ):
            raise ValueError("token position is outside observed sequence")
        if self.gap_positions is not None and any(
            item > observed_length for item in self.gap_positions
        ):
            raise ValueError("gap position is outside observed sequence")
        max_transition_count = max(0, observed_length - 1)
        if self.transition_positions is not None and any(
            item >= max_transition_count for item in self.transition_positions
        ):
            raise ValueError("transition position is outside observed sequence")


class SequenceSupervision(CanonicalSchemaModel):
    """Controlled real parent-sequence label, absent from TEST records."""

    label: AnomalyLabel
    access: LabelAccess
    aggregation_rule: LabelAggregationRule
    source_kind: LabelSourceKind
    source_reference: str = Field(min_length=1)
    real_localization: LocalizationCoordinates | None = None

    @field_validator("source_reference")
    @classmethod
    def validate_source_reference(cls, value: str) -> str:
        return _validate_text(value, "source_reference")

    @model_validator(mode="after")
    def validate_real_localization(self) -> "SequenceSupervision":
        if self.real_localization is None:
            return self
        if self.real_localization.source is not LocalizationSource.REAL_SOURCE_ALERT:
            raise ValueError("real sequence supervision requires real_source_alert coordinates")
        if not self.real_localization.sequence_level:
            raise ValueError("real source alert localization must mark sequence anomaly")
        if self.real_localization.token_positions is None:
            raise ValueError("real source alert localization requires token coordinates")
        if self.label is not AnomalyLabel.ANOMALY:
            raise ValueError("real source alert localization requires anomaly label")
        if not self.real_localization.token_positions:
            raise ValueError("real source alert localization requires an alert token")
        if self.real_localization.gap_positions is not None:
            raise ValueError("real source labels do not provide gap localization")
        if self.real_localization.transition_positions is not None:
            raise ValueError("real source labels do not provide transition localization")
        return self


class SequenceModelInput(CanonicalSchemaModel):
    """Explicit unpadded, label-free parent-sequence view."""

    sequence_id: str = Field(pattern=_SEQUENCE_ID_PATTERN)
    event_ids: tuple[str, ...] = Field(min_length=1)
    valid_length: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_model_input(self) -> "SequenceModelInput":
        hash_event_ids(self.event_ids)
        if self.valid_length != len(self.event_ids):
            raise ValueError("valid_length must match unpadded event_ids")
        return self


class EventSequence(CanonicalSchemaModel):
    """One deterministic HDFS block or BGL parent sequence."""

    schema_version: Literal["1.0"] = SEQUENCE_SCHEMA_VERSION
    sequence_id: str = Field(pattern=_SEQUENCE_ID_PATTERN)
    dataset_key: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    dataset_fingerprint: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    partition_identity: PartitionIdentity
    strategy: SequenceStrategy
    source_key: str = Field(min_length=1)
    record_ids: tuple[str, ...] = Field(min_length=1)
    event_ids: tuple[str, ...] = Field(min_length=1)
    source_line_numbers: tuple[int, ...] = Field(min_length=1)
    chronological_indices: tuple[int, ...] = Field(min_length=1)
    content_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    parser_state_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    template_registry_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    target_window_size: int | None = Field(default=None, ge=1)
    is_residual_window: bool = False
    supervision: SequenceSupervision | None = None

    @field_validator("dataset_id", "dataset_version", "source_key")
    @classmethod
    def validate_identity_text(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "identity")
        return _validate_text(value, field_name)

    @field_validator("record_ids")
    @classmethod
    def validate_record_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not re.fullmatch(_RECORD_ID_PATTERN, item) for item in value):
            raise ValueError("record_ids contain an invalid LOG identity")
        if len(value) != len(set(value)):
            raise ValueError("record_ids must be unique within a sequence")
        return value

    @field_validator("event_ids")
    @classmethod
    def validate_event_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not re.fullmatch(_EVENT_ID_PATTERN, item) for item in value):
            raise ValueError("event_ids contain an invalid event identity")
        return value

    @field_validator("source_line_numbers")
    @classmethod
    def validate_source_lines(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if any(item < 1 for item in value):
            raise ValueError("source_line_numbers must be one-based")
        if any(right <= left for left, right in zip(value, value[1:])):
            raise ValueError("source_line_numbers must be strictly increasing")
        return value

    @field_validator("chronological_indices")
    @classmethod
    def validate_chronology(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if any(item < 0 for item in value):
            raise ValueError("chronological_indices must be non-negative")
        if any(right <= left for left, right in zip(value, value[1:])):
            raise ValueError("chronological_indices must be strictly increasing")
        return value

    @model_validator(mode="after")
    def validate_sequence_contract(self) -> "EventSequence":
        lengths = {
            len(self.record_ids),
            len(self.event_ids),
            len(self.source_line_numbers),
            len(self.chronological_indices),
        }
        if len(lengths) != 1:
            raise ValueError("sequence-aligned fields must have equal lengths")
        sequence_length = len(self.event_ids)

        if self.content_sha256 != hash_event_ids(self.event_ids):
            raise ValueError("content_sha256 does not match ordered event_ids")

        if self.strategy is SequenceStrategy.HDFS_BLOCK_SESSION:
            if self.dataset_key != "hdfs":
                raise ValueError("hdfs_block_session strategy requires HDFS dataset")
            if self.target_window_size is not None or self.is_residual_window:
                raise ValueError("HDFS block sequences are variable-length, not windows")
            if self.supervision is not None:
                if (
                    self.supervision.aggregation_rule
                    is not LabelAggregationRule.HDFS_BLOCK_SOURCE_LABEL
                ):
                    raise ValueError("HDFS sequences require block-source aggregation")
                if self.supervision.source_kind is not LabelSourceKind.EXTERNAL_FILE:
                    raise ValueError("HDFS sequences require external-file supervision")
                if self.supervision.real_localization is not None:
                    raise ValueError("HDFS real labels do not provide localization")

        if self.strategy is SequenceStrategy.BGL_FIXED_PARENT_WINDOW:
            if self.dataset_key != "bgl":
                raise ValueError("bgl_fixed_parent_window strategy requires BGL dataset")
            if self.target_window_size != 100:
                raise ValueError("BGL target_window_size is frozen at 100")
            if self.partition_identity.protocol_version == ACTIVE_PROTOCOL_VERSION:
                if self.is_residual_window or sequence_length != 100:
                    raise ValueError(
                        "Protocol v1.1 BGL parent windows must contain exactly 100 events"
                    )
            else:
                if sequence_length > 100:
                    raise ValueError("BGL parent windows cannot exceed 100 events")
                if self.is_residual_window:
                    if not 20 <= sequence_length < 100:
                        raise ValueError(
                            "BGL residual windows must contain 20 to 99 events"
                        )
                elif sequence_length != 100:
                    raise ValueError(
                        "non-residual BGL parent windows must contain 100 events"
                    )
            if self.supervision is not None:
                if (
                    self.supervision.aggregation_rule
                    is not LabelAggregationRule.BGL_ANY_SOURCE_ALERT
                ):
                    raise ValueError("BGL sequences require any-source-alert aggregation")
                if self.supervision.source_kind is not LabelSourceKind.INLINE_FIELD:
                    raise ValueError("BGL sequences require inline-field supervision")
                if self.supervision.real_localization is not None:
                    self.supervision.real_localization.validate_for_observed_length(
                        sequence_length
                    )

        partition = self.partition_identity.partition
        if partition is ScientificPartition.TEST:
            if self.supervision is not None:
                raise ValueError("TEST EventSequence records must not expose supervision")
        elif self.dataset_key in {"hdfs", "bgl"} and self.supervision is None:
            raise ValueError("labeled P0 sequences require controlled non-TEST supervision")

        if partition in {
            ScientificPartition.BASE_TRAIN,
            ScientificPartition.FUSION_TRAIN,
        } and (
            self.supervision is None
            or self.supervision.label is not AnomalyLabel.NORMAL
            or self.supervision.access is not LabelAccess.NORMAL_POOL_FILTERING
        ):
            raise ValueError("training sequences require normal-pool-filtering supervision")

        if partition in {
            ScientificPartition.VAL_EXPERT,
            ScientificPartition.VAL_FUSION,
        } and (
            self.supervision is None
            or self.supervision.access is not LabelAccess.VALIDATION_EVALUATION
        ):
            raise ValueError("validation sequences require validation_evaluation access")

        expected_sequence_id = build_sequence_id(
            dataset_fingerprint=self.dataset_fingerprint,
            partition_assignment_id=self.partition_identity.assignment_id,
            strategy=self.strategy,
            source_key=self.source_key,
            record_ids=self.record_ids,
        )
        if self.sequence_id != expected_sequence_id:
            raise ValueError("sequence_id does not match sequence provenance")
        return self

    def to_model_input(self) -> SequenceModelInput:
        """Return an unpadded label-free parent sequence."""

        return SequenceModelInput(
            sequence_id=self.sequence_id,
            event_ids=self.event_ids,
            valid_length=len(self.event_ids),
        )


class MutationParameter(CanonicalSchemaModel):
    """One canonical operation parameter used in mutation identity."""

    name: str = Field(pattern=_PARAMETER_NAME_PATTERN)
    value: AttributeScalar

    @field_validator("value")
    @classmethod
    def reject_non_finite_float(cls, value: AttributeScalar) -> AttributeScalar:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("mutation parameter floats must be finite")
        return value


def build_mutation_id(
    *,
    source_sequence_id: str,
    generator_version: str,
    seed: int,
    operation: MutationOperation,
    ordinal: int,
    parameters: tuple[MutationParameter, ...],
    expected_event_ids_sha256: str,
    observed_event_ids_sha256: str,
    expected_length: int,
    observed_length: int,
    localization: LocalizationCoordinates,
) -> str:
    """Build a deterministic synthetic mutation identity."""

    if not re.fullmatch(_SEQUENCE_ID_PATTERN, source_sequence_id):
        raise ValueError("source_sequence_id must be a valid SEQ identity")
    generator_version = _validate_text(generator_version, "generator_version")
    if seed < 0 or ordinal < 0:
        raise ValueError("seed and ordinal must be non-negative")
    if not re.fullmatch(_SHA256_PATTERN, expected_event_ids_sha256):
        raise ValueError("expected_event_ids_sha256 must be a lowercase SHA-256 digest")
    if not re.fullmatch(_SHA256_PATTERN, observed_event_ids_sha256):
        raise ValueError("observed_event_ids_sha256 must be a lowercase SHA-256 digest")
    if expected_length < 1 or observed_length < 1:
        raise ValueError("mutation lengths must be positive")
    parameter_names = [item.name for item in parameters]
    if len(parameter_names) != len(set(parameter_names)):
        raise ValueError("mutation parameter names must be unique")
    canonical_parameters = tuple(sorted(parameters, key=lambda item: item.name))
    payload = {
        "generator_version": generator_version,
        "operation": operation.value,
        "ordinal": ordinal,
        "parameters": [
            item.model_dump(mode="json") for item in canonical_parameters
        ],
        "expected_event_ids_sha256": expected_event_ids_sha256,
        "expected_length": expected_length,
        "localization": localization.model_dump(mode="json"),
        "observed_event_ids_sha256": observed_event_ids_sha256,
        "observed_length": observed_length,
        "seed": seed,
        "source_sequence_id": source_sequence_id,
    }
    return f"MUT-{_sha256_text(_canonical_json(payload))}"


class MutationRecord(CanonicalSchemaModel):
    """Deterministic synthetic anomaly provenance and localization target."""

    schema_version: Literal["1.0"] = MUTATION_SCHEMA_VERSION
    mutation_id: str = Field(pattern=_MUTATION_ID_PATTERN)
    source_sequence_id: str = Field(pattern=_SEQUENCE_ID_PATTERN)
    source_partition: ScientificPartition
    source_label: Literal[AnomalyLabel.NORMAL] = AnomalyLabel.NORMAL
    dataset_fingerprint: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    split_manifest_id: str = Field(pattern=_SPLIT_ID_PATTERN)
    generator_version: str = Field(min_length=1)
    seed: int = Field(ge=0)
    operation: MutationOperation
    ordinal: int = Field(ge=0)
    parameters: tuple[MutationParameter, ...]
    expected_event_ids_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    observed_event_ids_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    expected_length: int = Field(ge=1)
    observed_length: int = Field(ge=1)
    localization: LocalizationCoordinates
    synthetic: Literal[True] = True

    @field_validator("generator_version")
    @classmethod
    def validate_generator_version(cls, value: str) -> str:
        return _validate_text(value, "generator_version")

    @field_validator("parameters")
    @classmethod
    def canonicalize_parameters(
        cls, value: tuple[MutationParameter, ...]
    ) -> tuple[MutationParameter, ...]:
        names = [item.name for item in value]
        if len(names) != len(set(names)):
            raise ValueError("mutation parameter names must be unique")
        return tuple(sorted(value, key=lambda item: item.name))

    @model_validator(mode="after")
    def validate_mutation_contract(self) -> "MutationRecord":
        if self.source_partition is ScientificPartition.TEST:
            raise ValueError("TEST mutations are forbidden before final evaluation")
        if self.expected_event_ids_sha256 == self.observed_event_ids_sha256:
            raise ValueError("no-op mutations are forbidden")
        if self.localization.source is not LocalizationSource.SYNTHETIC_MUTATION:
            raise ValueError("MutationRecord requires synthetic_mutation localization")
        if not self.localization.sequence_level:
            raise ValueError("synthetic mutations must mark sequence-level anomaly")
        if any(
            item is None
            for item in (
                self.localization.token_positions,
                self.localization.gap_positions,
                self.localization.transition_positions,
            )
        ):
            raise ValueError("synthetic mutations require all coordinate families")

        tokens = self.localization.token_positions or ()
        gaps = self.localization.gap_positions or ()
        transitions = self.localization.transition_positions or ()

        if self.operation is MutationOperation.MISSING:
            if self.observed_length != self.expected_length - 1 or not gaps or tokens:
                raise ValueError("missing mutation requires -1 length and gap-only target")
        elif self.operation in {MutationOperation.EXTRA, MutationOperation.REPEATED}:
            if self.observed_length != self.expected_length + 1 or not tokens or gaps:
                raise ValueError("extra/repeated mutation requires +1 length and token target")
        elif self.operation is MutationOperation.REPLACEMENT:
            if (
                self.observed_length != self.expected_length
                or not tokens
                or not transitions
                or gaps
            ):
                raise ValueError(
                    "replacement mutation requires equal length plus token/transition targets"
                )
        elif self.operation is MutationOperation.REORDER:
            if (
                self.observed_length != self.expected_length
                or not tokens
                or not transitions
                or gaps
            ):
                raise ValueError(
                    "reorder mutation requires equal length plus token/transition targets"
                )

        self.localization.validate_for_observed_length(self.observed_length)
        expected_id = build_mutation_id(
            source_sequence_id=self.source_sequence_id,
            generator_version=self.generator_version,
            seed=self.seed,
            operation=self.operation,
            ordinal=self.ordinal,
            parameters=self.parameters,
            expected_event_ids_sha256=self.expected_event_ids_sha256,
            observed_event_ids_sha256=self.observed_event_ids_sha256,
            expected_length=self.expected_length,
            observed_length=self.observed_length,
            localization=self.localization,
        )
        if self.mutation_id != expected_id:
            raise ValueError("mutation_id does not match mutation provenance")
        return self


def build_sequence_destruction_id(
    *,
    source_sequence_id: str,
    source_parent_key: str,
    source_partition_identity: PartitionIdentity,
    dataset_fingerprint: str,
    generator_version: str,
    seed: int,
    original_event_ids_sha256: str,
    destroyed_event_ids_sha256: str,
    original_event_multiset_sha256: str,
    destroyed_event_multiset_sha256: str,
    original_length: int,
    destroyed_length: int,
    status: SequenceDestructionStatus,
    no_op_reason: str | None,
) -> str:
    """Build deterministic provenance identity for one KT-3 control."""

    if not re.fullmatch(_SEQUENCE_ID_PATTERN, source_sequence_id):
        raise ValueError("source_sequence_id must be a valid SEQ identity")
    source_parent_key = _validate_text(source_parent_key, "source_parent_key")
    generator_version = _validate_text(generator_version, "generator_version")
    if source_partition_identity.protocol_version != ACTIVE_PROTOCOL_VERSION:
        raise ValueError("KT-3 controls require active Protocol v1.1 identity")
    if not re.fullmatch(_SHA256_PATTERN, dataset_fingerprint):
        raise ValueError("dataset_fingerprint must be a lowercase SHA-256 digest")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    for field_name, value in (
        ("original_event_ids_sha256", original_event_ids_sha256),
        ("destroyed_event_ids_sha256", destroyed_event_ids_sha256),
        ("original_event_multiset_sha256", original_event_multiset_sha256),
        ("destroyed_event_multiset_sha256", destroyed_event_multiset_sha256),
    ):
        if not re.fullmatch(_SHA256_PATTERN, value):
            raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    if original_length < 1 or destroyed_length < 1:
        raise ValueError("sequence-destruction lengths must be positive")
    if no_op_reason is not None:
        no_op_reason = _validate_text(no_op_reason, "no_op_reason")

    payload = {
        "dataset_fingerprint": dataset_fingerprint,
        "destroyed_event_ids_sha256": destroyed_event_ids_sha256,
        "destroyed_event_multiset_sha256": destroyed_event_multiset_sha256,
        "destroyed_length": destroyed_length,
        "generator_version": generator_version,
        "no_op_reason": no_op_reason,
        "original_event_ids_sha256": original_event_ids_sha256,
        "original_event_multiset_sha256": original_event_multiset_sha256,
        "original_length": original_length,
        "seed": seed,
        "source_parent_key": source_parent_key,
        "source_partition_identity": source_partition_identity.model_dump(mode="json"),
        "source_sequence_id": source_sequence_id,
        "status": status.value,
    }
    return f"CTRL-KT3-{_sha256_text(_canonical_json(payload))}"


class SequenceDestructionRecord(CanonicalSchemaModel):
    """Provenance for KT-3 order destruction; never a synthetic anomaly label."""

    schema_version: Literal["1.0"] = SEQUENCE_DESTRUCTION_SCHEMA_VERSION
    control_id: str = Field(pattern=_SEQUENCE_DESTRUCTION_ID_PATTERN)
    source_sequence_id: str = Field(pattern=_SEQUENCE_ID_PATTERN)
    source_parent_key: str = Field(min_length=1)
    source_partition_identity: PartitionIdentity
    dataset_fingerprint: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    generator_version: str = Field(min_length=1)
    seed: int = Field(ge=0)
    original_event_ids_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    destroyed_event_ids_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    original_event_multiset_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    destroyed_event_multiset_sha256: Sha256Hex = Field(pattern=_SHA256_PATTERN)
    original_length: int = Field(ge=1)
    destroyed_length: int = Field(ge=1)
    status: SequenceDestructionStatus
    no_op_reason: str | None = None
    source_label: AnomalyLabel | None = None
    label_access: LabelAccess | None = None
    raw_data_mutated: Literal[False] = False

    @field_validator("source_parent_key", "generator_version", "no_op_reason")
    @classmethod
    def validate_control_text(
        cls, value: str | None, info: object
    ) -> str | None:
        if value is None:
            return None
        field_name = getattr(info, "field_name", "text")
        return _validate_text(value, field_name)

    @model_validator(mode="after")
    def validate_sequence_destruction(self) -> "SequenceDestructionRecord":
        partition = self.source_partition_identity.partition
        if self.source_partition_identity.protocol_version != ACTIVE_PROTOCOL_VERSION:
            raise ValueError("KT-3 controls require active Protocol v1.1 identity")
        if partition not in {
            ScientificPartition.VAL_EXPERT,
            ScientificPartition.TEST,
        }:
            raise ValueError("KT-3 controls are restricted to VAL_EXPERT or TEST")

        if partition is ScientificPartition.TEST:
            if self.source_label is not None or self.label_access is not None:
                raise ValueError("TEST KT-3 records must not expose supervision")
        elif (
            self.source_label is None
            or self.label_access is not LabelAccess.VALIDATION_EVALUATION
        ):
            raise ValueError(
                "VAL_EXPERT KT-3 records require validation-only source supervision"
            )

        if self.original_length != self.destroyed_length:
            raise ValueError("KT-3 must preserve sequence length")
        if (
            self.original_event_multiset_sha256
            != self.destroyed_event_multiset_sha256
        ):
            raise ValueError("KT-3 must preserve the event multiset")

        is_no_op = (
            self.original_event_ids_sha256 == self.destroyed_event_ids_sha256
        )
        if self.status is SequenceDestructionStatus.APPLIED:
            if is_no_op or self.no_op_reason is not None:
                raise ValueError(
                    "applied KT-3 controls require changed order and no no-op reason"
                )
        elif not is_no_op or self.no_op_reason is None:
            raise ValueError(
                "noop KT-3 controls require unchanged order and a recorded reason"
            )

        expected_id = build_sequence_destruction_id(
            source_sequence_id=self.source_sequence_id,
            source_parent_key=self.source_parent_key,
            source_partition_identity=self.source_partition_identity,
            dataset_fingerprint=self.dataset_fingerprint,
            generator_version=self.generator_version,
            seed=self.seed,
            original_event_ids_sha256=self.original_event_ids_sha256,
            destroyed_event_ids_sha256=self.destroyed_event_ids_sha256,
            original_event_multiset_sha256=self.original_event_multiset_sha256,
            destroyed_event_multiset_sha256=self.destroyed_event_multiset_sha256,
            original_length=self.original_length,
            destroyed_length=self.destroyed_length,
            status=self.status,
            no_op_reason=self.no_op_reason,
        )
        if self.control_id != expected_id:
            raise ValueError("control_id does not match KT-3 provenance")
        return self


__all__ = [
    "ACTIVE_PROTOCOL_VERSION",
    "EventSequence",
    "LabelAggregationRule",
    "LocalizationCoordinates",
    "LocalizationSource",
    "MUTATION_SCHEMA_VERSION",
    "MutationOperation",
    "MutationParameter",
    "MutationRecord",
    "ProtocolVersion",
    "PartitionAssignment",
    "PartitionDisposition",
    "PartitionIdentity",
    "PartitionUnitKind",
    "SEQUENCE_SCHEMA_VERSION",
    "SEQUENCE_DESTRUCTION_SCHEMA_VERSION",
    "SequenceDestructionRecord",
    "SequenceDestructionStatus",
    "SequenceModelInput",
    "SequenceStrategy",
    "SequenceSupervision",
    "build_active_partition_identity",
    "build_mutation_id",
    "build_partition_assignment_id",
    "build_sequence_id",
    "build_sequence_destruction_id",
    "build_split_manifest_id",
    "hash_event_ids",
    "hash_event_multiset",
]
