"""Append-only research-process collection for the v2 workflow."""

from seqlogad.collection.models import (
    RECORD_FILES,
    ArtifactManifestRecord,
    AccessLogRecord,
    ArchitectureRecord,
    DatasetSnapshotRecord,
    EventSchemaRecord,
    IncidentRecord,
    LineageEdgeRecord,
    ProtocolDeviationRecord,
    RunBridgeRecord,
    SealRecord,
    SplitRecord,
    ToolchainRecord,
    TransformRecord,
    VariantRecord,
)
from seqlogad.collection.store import (
    CollectionError,
    append_record,
    initialize_collection,
    validate_collection,
)

__all__ = [
    "RECORD_FILES",
    "ArchitectureRecord",
    "VariantRecord",
    "DatasetSnapshotRecord",
    "EventSchemaRecord",
    "TransformRecord",
    "SplitRecord",
    "RunBridgeRecord",
    "ArtifactManifestRecord",
    "AccessLogRecord",
    "IncidentRecord",
    "LineageEdgeRecord",
    "ProtocolDeviationRecord",
    "SealRecord",
    "ToolchainRecord",
    "CollectionError",
    "append_record",
    "initialize_collection",
    "validate_collection",
]
