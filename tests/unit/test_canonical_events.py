"""Synthetic-only CANONICAL-EVENT-001 identity and boundary tests."""

from __future__ import annotations

import hashlib

from seqlogad.common.schemas.events import (
    AnomalyLabel,
    EventObservation,
    EventProvenance,
    EventSupervision,
    GroupKind,
    LabelAccess,
    LabelGranularity,
    LabelSourceKind,
    LogEvent,
    ScientificPartition,
    build_event_id,
    build_record_id,
)
from seqlogad.parsing.canonical_events import canonical_event_sha256


def _bgl_record(*, marker: str) -> dict:
    raw_line = (
        f"{marker} 1117838570 2005.06.03 node 2005-06-03 node RAS KERNEL "
        "INFO instruction cache parity error corrected\n"
    ).encode()
    source_hash = hashlib.sha256(raw_line).hexdigest()
    provenance = EventProvenance(
        dataset_key="bgl",
        dataset_id="BGL",
        dataset_version="zenodo-8196385:BGL",
        dataset_fingerprint="a" * 64,
        source_file="data/raw/bgl/BGL/BGL.log",
        source_line_number=11,
        chronological_index=10,
        source_line_sha256=source_hash,
        partition=ScientificPartition.VAL_EXPERT,
        group_kind=GroupKind.NONE,
    )
    event_id = build_event_id(
        parser_version="0.9.11",
        normalization_version="seqlogad-message-v1",
        normalized_template="instruction cache parity error corrected",
    )
    event = LogEvent(
        record_id=build_record_id(
            dataset_fingerprint=provenance.dataset_fingerprint,
            source_file=provenance.source_file,
            source_line_number=provenance.source_line_number,
            source_line_sha256=provenance.source_line_sha256,
        ),
        provenance=provenance,
        observation=EventObservation(message="instruction cache parity error corrected"),
        event_id=event_id,
        parser_state_sha256="b" * 64,
        template_registry_sha256="c" * 64,
        supervision=EventSupervision(
            label=(AnomalyLabel.NORMAL if marker == "-" else AnomalyLabel.ANOMALY),
            granularity=LabelGranularity.EVENT,
            access=LabelAccess.VALIDATION_EVALUATION,
            source_kind=LabelSourceKind.INLINE_FIELD,
            source_reference="data/raw/bgl/BGL/BGL.log:11:first-field",
            category=None if marker == "-" else marker,
        ),
    )
    return {
        "schema_version": "1.0",
        "protocol_version": "1.1",
        "split_payload_hash": "d" * 64,
        "partition_hash": "e" * 64,
        "assignment_id": f"PART-{'f' * 64}",
        "structural_unit_id": f"BGL-PARENT-{'1' * 64}",
        "unit_kind": "BGL_PARENT_WINDOW",
        "position_within_unit": 10,
        "parser_implementation_version": "seqlogad-parse-001-v1",
        "parser_config_sha256": "2" * 64,
        "event": event.model_dump(mode="json"),
    }


def test_inline_label_does_not_change_canonical_transform_identity() -> None:
    normal = _bgl_record(marker="-")
    anomalous = _bgl_record(marker="KERNDTLB")

    assert normal["event"]["record_id"] != anomalous["event"]["record_id"]
    assert normal["event"]["provenance"]["source_line_sha256"] != anomalous["event"][
        "provenance"
    ]["source_line_sha256"]
    assert normal["event"]["event_id"] == anomalous["event"]["event_id"]
    assert canonical_event_sha256(normal) == canonical_event_sha256(anomalous)


def test_template_or_order_change_changes_canonical_identity() -> None:
    original = _bgl_record(marker="-")
    changed_event = _bgl_record(marker="-")
    changed_event["event"]["event_id"] = build_event_id(
        parser_version="0.9.11",
        normalization_version="seqlogad-message-v1",
        normalized_template="different <*> template",
    )
    changed_order = _bgl_record(marker="-")
    changed_order["position_within_unit"] = 11

    assert canonical_event_sha256(original) != canonical_event_sha256(changed_event)
    assert canonical_event_sha256(original) != canonical_event_sha256(changed_order)
