"""SCHEMA-001 tests using synthetic records only."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from seqlogad.common.schemas import (
    AnomalyLabel,
    EventAttribute,
    EventObservation,
    EventProvenance,
    EventSupervision,
    EventTemplate,
    GroupKind,
    LabelAccess,
    LabelGranularity,
    LabelSourceKind,
    LogEvent,
    ScientificPartition,
    UNSEEN_EVENT_ID,
    build_event_id,
    build_record_id,
)


DATASET_FINGERPRINT = "1" * 64
SOURCE_LINE_SHA256 = hashlib.sha256(b"synthetic log line").hexdigest()
PARSER_STATE_SHA256 = "2" * 64
REGISTRY_SHA256 = "3" * 64
PARSER_CONFIG_SHA256 = "4" * 64
NORMALIZATION_CONFIG_SHA256 = "5" * 64
TEMPLATE = "Received block <*> from <*>"
EVENT_ID = build_event_id(
    parser_version="0.9.11",
    normalization_version="norm-v1",
    normalized_template=TEMPLATE,
)


def make_provenance(
    *,
    dataset_key: str = "hdfs",
    partition: ScientificPartition = ScientificPartition.BASE_TRAIN,
) -> EventProvenance:
    if dataset_key == "hdfs":
        dataset_id = "HDFS_v1"
        dataset_version = "zenodo-8196385:HDFS_v1"
        source_file = "data/raw/hdfs/HDFS_v1/HDFS.log"
        group_kind = GroupKind.HDFS_BLOCK
        group_ids = ("blk_-1",)
    else:
        dataset_id = "BGL"
        dataset_version = "zenodo-8196385:BGL"
        source_file = "data/raw/bgl/BGL/BGL.log"
        group_kind = GroupKind.NONE
        group_ids = ()
    return EventProvenance(
        dataset_key=dataset_key,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_fingerprint=DATASET_FINGERPRINT,
        source_file=source_file,
        source_line_number=7,
        chronological_index=6,
        source_line_sha256=SOURCE_LINE_SHA256,
        partition=partition,
        group_kind=group_kind,
        group_ids=group_ids,
    )


def make_supervision(
    *,
    dataset_key: str = "hdfs",
    partition: ScientificPartition = ScientificPartition.BASE_TRAIN,
    label: AnomalyLabel = AnomalyLabel.NORMAL,
) -> EventSupervision:
    validation = partition in {
        ScientificPartition.VAL_EXPERT,
        ScientificPartition.VAL_FUSION,
    }
    return EventSupervision(
        label=label,
        granularity=(
            LabelGranularity.BLOCK_SESSION
            if dataset_key == "hdfs"
            else LabelGranularity.EVENT
        ),
        access=(
            LabelAccess.VALIDATION_EVALUATION
            if validation
            else LabelAccess.NORMAL_POOL_FILTERING
        ),
        source_kind=(
            LabelSourceKind.EXTERNAL_FILE
            if dataset_key == "hdfs"
            else LabelSourceKind.INLINE_FIELD
        ),
        source_reference=(
            "preprocessed/anomaly_label.csv"
            if dataset_key == "hdfs"
            else "BGL.log:first_column"
        ),
    )


def make_event(
    *,
    dataset_key: str = "hdfs",
    partition: ScientificPartition = ScientificPartition.BASE_TRAIN,
    label: AnomalyLabel = AnomalyLabel.NORMAL,
    supervision: EventSupervision | None | object = ...,
    event_id: str = EVENT_ID,
) -> LogEvent:
    provenance = make_provenance(dataset_key=dataset_key, partition=partition)
    resolved_supervision = (
        make_supervision(dataset_key=dataset_key, partition=partition, label=label)
        if supervision is ... and partition is not ScientificPartition.TEST
        else None
        if supervision is ...
        else supervision
    )
    record_id = build_record_id(
        dataset_fingerprint=provenance.dataset_fingerprint,
        source_file=provenance.source_file,
        source_line_number=provenance.source_line_number,
        source_line_sha256=provenance.source_line_sha256,
    )
    return LogEvent(
        record_id=record_id,
        provenance=provenance,
        observation=EventObservation(
            message="Received block blk_-1 from node-1",
            source_timestamp="081109 203518 143",
            timestamp_utc=datetime(2008, 11, 9, 20, 35, 18, tzinfo=timezone.utc),
            attributes=(
                EventAttribute(name="severity", value="INFO"),
                EventAttribute(name="component", value="DataNode"),
            ),
        ),
        event_id=event_id,
        parameters=("blk_-1", "node-1"),
        parser_state_sha256=PARSER_STATE_SHA256,
        template_registry_sha256=REGISTRY_SHA256,
        supervision=resolved_supervision,
    )


def test_event_id_is_deterministic_and_context_bound() -> None:
    assert EVENT_ID == build_event_id(
        parser_version="0.9.11",
        normalization_version="norm-v1",
        normalized_template=TEMPLATE,
    )
    assert EVENT_ID != build_event_id(
        parser_version="0.9.11",
        normalization_version="norm-v2",
        normalized_template=TEMPLATE,
    )
    assert EVENT_ID != build_event_id(
        parser_version="0.9.11",
        normalization_version="norm-v1",
        normalized_template="Received packet <*> from <*>",
    )


def test_event_template_validates_all_frozen_identity_fields() -> None:
    template = EventTemplate(
        event_id=EVENT_ID,
        normalized_template=TEMPLATE,
        parser_version="0.9.11",
        parser_config_sha256=PARSER_CONFIG_SHA256,
        normalization_version="norm-v1",
        normalization_config_sha256=NORMALIZATION_CONFIG_SHA256,
        template_sha256=hashlib.sha256(TEMPLATE.encode("utf-8")).hexdigest(),
    )
    assert template.fit_partition is ScientificPartition.BASE_TRAIN
    assert EventTemplate.model_validate_json(template.canonical_json()) == template


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("event_id", f"EVT-{'0' * 64}", "event_id does not match"),
        ("template_sha256", "0" * 64, "template_sha256 does not match"),
        ("fit_partition", "VAL_EXPERT", "templates may only be fitted"),
    ],
)
def test_event_template_rejects_identity_drift(
    field: str, value: str, message: str
) -> None:
    payload = {
        "event_id": EVENT_ID,
        "normalized_template": TEMPLATE,
        "parser_version": "0.9.11",
        "parser_config_sha256": PARSER_CONFIG_SHA256,
        "normalization_version": "norm-v1",
        "normalization_config_sha256": NORMALIZATION_CONFIG_SHA256,
        "template_sha256": hashlib.sha256(TEMPLATE.encode("utf-8")).hexdigest(),
        "fit_partition": "BASE_TRAIN",
    }
    payload[field] = value
    with pytest.raises(ValidationError, match=message):
        EventTemplate.model_validate(payload)


def test_record_id_and_serialization_are_deterministic() -> None:
    event = make_event()
    restored = LogEvent.model_validate_json(event.canonical_json())
    assert restored == event
    assert restored.canonical_json() == event.canonical_json()
    assert restored.canonical_sha256() == event.canonical_sha256()
    assert event.record_id == build_record_id(
        dataset_fingerprint=DATASET_FINGERPRINT,
        source_file="data/raw/hdfs/HDFS_v1/HDFS.log",
        source_line_number=7,
        source_line_sha256=SOURCE_LINE_SHA256,
    )


def test_attributes_are_sorted_and_label_names_are_rejected() -> None:
    observation = EventObservation(
        message="synthetic",
        attributes=(
            EventAttribute(name="severity", value="INFO"),
            EventAttribute(name="component", value="DataNode"),
        ),
    )
    assert [item.name for item in observation.attributes] == ["component", "severity"]
    with pytest.raises(ValidationError, match="supervision/label fields"):
        EventAttribute(name="is_anomaly", value=True)
    with pytest.raises(ValidationError, match="supervision/label fields"):
        EventAttribute(name="source_label", value="-")


def test_duplicate_attributes_and_non_finite_values_are_rejected() -> None:
    with pytest.raises(ValidationError, match="attribute names must be unique"):
        EventObservation(
            message="synthetic",
            attributes=(
                EventAttribute(name="component", value="A"),
                EventAttribute(name="component", value="B"),
            ),
        )
    with pytest.raises(ValidationError, match="attribute floats must be finite"):
        EventAttribute(name="duration", value=float("nan"))


def test_bgl_supervision_is_structurally_absent_from_model_input() -> None:
    event = make_event(dataset_key="bgl")
    model_payload = event.to_model_input().model_dump(mode="json")
    serialized = str(model_payload).lower()
    assert set(model_payload) == {"record_id", "event_id", "timestamp_utc", "attributes"}
    assert "supervision" not in serialized
    assert "label" not in serialized
    assert "alert" not in serialized
    assert "message" not in model_payload
    assert event.observation.label_isolated is True


def test_test_partition_cannot_expose_supervision() -> None:
    event = make_event(partition=ScientificPartition.TEST)
    assert event.supervision is None
    with pytest.raises(ValidationError, match="TEST LogEvent records must not expose"):
        make_event(
            partition=ScientificPartition.TEST,
            supervision=make_supervision(partition=ScientificPartition.VAL_EXPERT),
        )


def test_training_partitions_reject_real_anomalies() -> None:
    with pytest.raises(ValidationError, match="training pools may contain normal records only"):
        make_event(label=AnomalyLabel.ANOMALY)


def test_validation_partitions_require_validation_access() -> None:
    wrong_access = make_supervision(partition=ScientificPartition.BASE_TRAIN)
    with pytest.raises(ValidationError, match="validation_evaluation access"):
        make_event(
            partition=ScientificPartition.VAL_EXPERT,
            supervision=wrong_access,
        )
    anomaly = make_event(
        partition=ScientificPartition.VAL_EXPERT,
        label=AnomalyLabel.ANOMALY,
    )
    assert anomaly.supervision is not None
    assert anomaly.supervision.label is AnomalyLabel.ANOMALY


def test_dataset_specific_group_and_label_granularity_are_enforced() -> None:
    hdfs_provenance = make_provenance().model_copy(
        update={"group_kind": GroupKind.NONE, "group_ids": ()}
    )
    record_id = build_record_id(
        dataset_fingerprint=hdfs_provenance.dataset_fingerprint,
        source_file=hdfs_provenance.source_file,
        source_line_number=hdfs_provenance.source_line_number,
        source_line_sha256=hdfs_provenance.source_line_sha256,
    )
    with pytest.raises(ValidationError, match="HDFS events require hdfs_block"):
        LogEvent(
            record_id=record_id,
            provenance=hdfs_provenance,
            observation=EventObservation(message="synthetic"),
            event_id=EVENT_ID,
            parser_state_sha256=PARSER_STATE_SHA256,
            template_registry_sha256=REGISTRY_SHA256,
            supervision=make_supervision(),
        )

    wrong_granularity = make_supervision(dataset_key="bgl").model_copy(
        update={"granularity": LabelGranularity.BLOCK_SESSION}
    )
    with pytest.raises(ValidationError, match="BGL source supervision must use event"):
        make_event(dataset_key="bgl", supervision=wrong_granularity)


def test_record_id_mismatch_and_unsafe_source_paths_are_rejected() -> None:
    event = make_event()
    with pytest.raises(ValidationError, match="record_id does not match"):
        LogEvent.model_validate({**event.model_dump(), "record_id": f"LOG-{'0' * 64}"})
    with pytest.raises(ValidationError, match="repository-relative POSIX path"):
        EventProvenance.model_validate(
            {**make_provenance().model_dump(), "source_file": "../HDFS.log"}
        )


def test_naive_normalized_timestamp_is_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        EventObservation(message="synthetic", timestamp_utc=datetime(2026, 1, 1))


def test_unseen_event_id_is_valid_without_fabricating_a_template() -> None:
    event = make_event(event_id=UNSEEN_EVENT_ID)
    assert event.event_id == UNSEEN_EVENT_ID


def test_schema_models_forbid_extra_fields_and_are_immutable() -> None:
    event = make_event()
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        LogEvent.model_validate({**event.model_dump(), "unexpected": True})
    with pytest.raises(ValidationError, match="Instance is frozen"):
        event.event_id = UNSEEN_EVENT_ID  # type: ignore[misc]
