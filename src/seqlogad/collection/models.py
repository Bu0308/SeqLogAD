"""Validated companion-manifest records for observing v2 work.

These records describe process evidence; they never contain raw log events or
target labels used during adaptation. Projmem-native exports, when available,
are imported as a distinct source badge rather than being recreated here.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SourceBadge = Literal["projmem_native", "research_manifest", "aletheia_derived"]


def _non_empty(value: str) -> str:
    if not value.strip():
        raise ValueError("value must not be empty")
    return value


class CollectionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = Field(min_length=1)
    created_at_utc: datetime
    provenance_source: SourceBadge = "research_manifest"
    recorder: str = Field(min_length=1)
    recorded_late: bool = False
    supersedes_id: str | None = None

    _validate_text = field_validator("recorder", "schema_version")(_non_empty)


class ArchitectureRecord(CollectionRecord):
    schema_version: Literal["aletheia-architecture-v1"] = "aletheia-architecture-v1"
    architecture_id: str
    title: str
    mechanism_summary: str
    components: tuple[str, ...] = ()
    parent_architecture_id: str | None = None
    change_from_parent: str | None = None
    decision_evidence: tuple[str, ...] = ()
    git_commit: str | None = None
    status: str = "active"

    _validate_fields = field_validator("architecture_id", "title", "mechanism_summary")(_non_empty)


class VariantRecord(CollectionRecord):
    schema_version: Literal["aletheia-variant-v1"] = "aletheia-variant-v1"
    variant_id: str
    architecture_id: str
    parameter_changes: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    change_reason: str
    parent_variant_id: str | None = None
    config_path: str
    config_sha256: str

    _validate_fields = field_validator("variant_id", "architecture_id", "change_reason", "config_path", "config_sha256")(_non_empty)


class DatasetSnapshotRecord(CollectionRecord):
    schema_version: Literal["aletheia-dataset-v1"] = "aletheia-dataset-v1"
    dataset_id: str
    source_systems: tuple[str, ...]
    collection_start_utc: datetime
    collection_end_utc: datetime
    extraction_query_hash: str | None = None
    raw_manifest_path: str | None = None
    raw_manifest_sha256: str | None = None
    processed_manifest_path: str | None = None
    processed_manifest_sha256: str | None = None
    event_count: int = Field(ge=0)
    source_count: int = Field(ge=0)
    privacy_class: str
    license_or_permission: str
    event_schema_id: str
    transform_id: str
    known_exclusions: tuple[str, ...] = ()

    @field_validator("dataset_id", "privacy_class", "license_or_permission", "event_schema_id", "transform_id")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _non_empty(value)


class EventSchemaRecord(CollectionRecord):
    schema_version: Literal["aletheia-event-schema-v1"] = "aletheia-event-schema-v1"
    event_schema_id: str
    timestamp_field: str
    timezone_policy: str
    source_id_field: str
    event_type_field: str
    message_storage: str
    parser_name: str | None = None
    parser_version: str | None = None
    template_dictionary_hash: str | None = None
    missing_field_policy: str
    late_event_policy: str
    clock_skew_policy: str

    @field_validator("event_schema_id", "timestamp_field", "timezone_policy", "source_id_field", "event_type_field", "message_storage", "missing_field_policy", "late_event_policy", "clock_skew_policy")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _non_empty(value)


class TransformRecord(CollectionRecord):
    schema_version: Literal["aletheia-transform-v1"] = "aletheia-transform-v1"
    transform_id: str
    input_dataset_id: str
    ordered_steps: tuple[dict[str, object], ...]
    fit_scope: str
    code_commit: str | None = None
    config_path: str | None = None
    config_sha256: str | None = None
    output_manifest_sha256: str | None = None


class SplitRecord(CollectionRecord):
    schema_version: Literal["aletheia-split-v1"] = "aletheia-split-v1"
    split_id: str
    dataset_id: str
    strategy: str
    train_interval: tuple[str, str]
    validation_interval: tuple[str, str]
    development_test_interval: tuple[str, str]
    sealed_holdout_interval: tuple[str, str]
    group_exclusion_keys: tuple[str, ...] = ()
    parser_fit_scope: str
    normalization_fit_scope: str
    threshold_selection_scope: str
    leakage_audit_path: str
    frozen_before_holdout_access: bool


class RunBridgeRecord(CollectionRecord):
    schema_version: Literal["aletheia-run-bridge-v1"] = "aletheia-run-bridge-v1"
    run_alias: str
    projmem_run_id: str | None = None
    architecture_id: str
    variant_id: str
    dataset_id: str
    event_schema_id: str
    transform_id: str
    split_id: str
    seed: str
    run_intent: Literal["exploratory", "tuning", "validation", "locked_evaluation"]
    technical_status: str
    scientific_status: str
    git_commit: str
    git_dirty: bool
    config_path: str
    config_sha256: str
    metrics_path: str | None = None
    artifact_manifest_id: str | None = None
    recorded_late: bool = False
    partition: Literal["development", "sealed_holdout"] = "development"


class ArtifactItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    role: str
    path: str
    sha256: str
    size_bytes: int = Field(ge=0)
    content_archived: bool
    archive_class: Literal["restricted", "public_sanitized", "not_archived"]
    availability_status: Literal["included", "restricted_reference", "missing"]


class ArtifactManifestRecord(CollectionRecord):
    schema_version: Literal["aletheia-artifact-manifest-v1"] = "aletheia-artifact-manifest-v1"
    artifact_manifest_id: str
    projmem_run_id: str | None = None
    items: tuple[ArtifactItem, ...]
    availability_verified_at_utc: datetime
    verified_by: str


class IncidentRecord(CollectionRecord):
    schema_version: Literal["aletheia-incident-v1"] = "aletheia-incident-v1"
    incident_id: str
    time_interval: tuple[str, str]
    affected_sources: tuple[str, ...]
    reference_label: str | None = None
    ground_truth_tier: Literal["G0", "G1", "G2", "G3", "G4"]
    ground_truth_evidence: tuple[dict[str, object], ...] = ()
    adjudicators: tuple[str, ...] = ()
    adjudication_notes: str | None = None
    causal_tier: Literal["C0", "C1", "C2", "C3", "C4"]
    causal_claim: str | None = None
    linked_run_ids: tuple[str, ...] = ()
    privacy_class: str


class LineageEdgeRecord(CollectionRecord):
    schema_version: Literal["aletheia-lineage-edge-v1"] = "aletheia-lineage-edge-v1"
    edge_id: str
    subject_id: str
    predicate: str
    object_id: str
    evidence_paths: tuple[str, ...]
    evidence_hashes: tuple[str, ...] = ()
    direct_observation: bool = True


class ProtocolDeviationRecord(CollectionRecord):
    schema_version: Literal["aletheia-deviation-v1"] = "aletheia-deviation-v1"
    deviation_id: str
    detected_at_utc: datetime
    event_time_utc: datetime
    affected_run_ids: tuple[str, ...] = ()
    category: str
    description: str
    reason: str
    data_recoverable: bool
    recovery_action: str | None = None
    impact_on_analysis: str
    severity: Literal["low", "medium", "high", "critical"]
    approved_by: str | None = None


class SealRecord(CollectionRecord):
    schema_version: Literal["aletheia-seal-v1"] = "aletheia-seal-v1"
    seal_id: str
    partition: str
    split_id: str
    bundle_path: str
    bundle_sha256: str
    inventory_path: str
    inventory_sha256: str
    protocol_path: str
    protocol_sha256: str
    custodian: str
    authorized_openers: tuple[str, ...]
    opened: bool = False


class AccessLogRecord(CollectionRecord):
    schema_version: Literal["aletheia-access-v1"] = "aletheia-access-v1"
    access_id: str
    seal_id: str
    actor: str
    action: str
    purpose: str
    content_opened: bool
    authorized_by: str
    notes: str = ""


class ToolchainRecord(CollectionRecord):
    schema_version: Literal["aletheia-toolchain-v1"] = "aletheia-toolchain-v1"
    toolchain_id: str
    projmem_version: str | None = None
    projmem_install_kind: str | None = None
    projmem_executable: str | None = None
    projmem_source_commit: str | None = None
    python_version: str
    os: str
    runtime_packages_hash: str | None = None


RECORD_FILES: dict[str, tuple[str, type[CollectionRecord]]] = {
    "architecture": ("architectures.jsonl", ArchitectureRecord),
    "variant": ("variants.jsonl", VariantRecord),
    "dataset": ("datasets.jsonl", DatasetSnapshotRecord),
    "event_schema": ("event_schemas.jsonl", EventSchemaRecord),
    "transform": ("transforms.jsonl", TransformRecord),
    "split": ("splits.jsonl", SplitRecord),
    "run_bridge": ("run_bridge.jsonl", RunBridgeRecord),
    "artifact_manifest": ("artifact_manifests.jsonl", ArtifactManifestRecord),
    "incident": ("incidents.jsonl", IncidentRecord),
    "lineage_edge": ("lineage_edges.jsonl", LineageEdgeRecord),
    "protocol_deviation": ("protocol_deviations.jsonl", ProtocolDeviationRecord),
    "seal": ("seal_records.jsonl", SealRecord),
    "access": ("access_log.jsonl", AccessLogRecord),
    "toolchain": ("toolchain.jsonl", ToolchainRecord),
}
