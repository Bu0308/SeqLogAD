"""SCHEMA-002 contract tests using synthetic identities only."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from seqlogad.common.schemas import (
    ACTIVE_PROTOCOL_VERSION,
    AnomalyLabel,
    EventSequence,
    LabelAccess,
    LabelAggregationRule,
    LabelSourceKind,
    LocalizationCoordinates,
    LocalizationSource,
    MutationOperation,
    MutationParameter,
    MutationRecord,
    ProtocolVersion,
    PartitionAssignment,
    PartitionDisposition,
    PartitionIdentity,
    PartitionUnitKind,
    ScientificPartition,
    SequenceDestructionRecord,
    SequenceDestructionStatus,
    SequenceModelInput,
    SequenceStrategy,
    SequenceSupervision,
    build_active_partition_identity,
    build_mutation_id,
    build_partition_assignment_id,
    build_sequence_id,
    build_sequence_destruction_id,
    build_split_manifest_id,
    hash_event_ids,
    hash_event_multiset,
)


DATASET_FINGERPRINT = "1" * 64
SPLIT_MANIFEST_SHA256 = "2" * 64
SPLIT_MANIFEST_ID = build_split_manifest_id(SPLIT_MANIFEST_SHA256)
PARSER_STATE_SHA256 = "3" * 64
REGISTRY_SHA256 = "4" * 64
TARGET_RATIOS = {
    ScientificPartition.BASE_TRAIN: 0.60,
    ScientificPartition.FUSION_TRAIN: 0.10,
    ScientificPartition.VAL_EXPERT: 0.10,
    ScientificPartition.VAL_FUSION: 0.10,
    ScientificPartition.TEST: 0.10,
}


def record_ids(length: int) -> tuple[str, ...]:
    return tuple(f"LOG-{index + 1:064x}" for index in range(length))


def event_ids(length: int, *, offset: int = 0) -> tuple[str, ...]:
    return tuple(f"EVT-{offset + index + 1:064x}" for index in range(length))


def make_assignment(
    *,
    dataset_key: str = "hdfs",
    partition: ScientificPartition | None = ScientificPartition.BASE_TRAIN,
    disposition: PartitionDisposition = PartitionDisposition.ASSIGNED,
    event_count: int = 3,
) -> PartitionAssignment:
    hdfs = dataset_key == "hdfs"
    unit_kind = (
        PartitionUnitKind.HDFS_BLOCK_COMPONENT
        if hdfs
        else PartitionUnitKind.BGL_RAW_RANGE
    )
    unit_key = (
        "component:blk_-1"
        if hdfs
        else f"raw-lines:1-{event_count}"
    )
    member_group_ids = ("blk_-1",) if hdfs else ()
    reason = None if disposition is PartitionDisposition.ASSIGNED else "protocol exclusion"
    assignment_id = build_partition_assignment_id(
        dataset_fingerprint=DATASET_FINGERPRINT,
        split_manifest_id=SPLIT_MANIFEST_ID,
        unit_kind=unit_kind,
        unit_key=unit_key,
        chronological_start=0,
        chronological_end=max(0, event_count - 1),
        disposition=disposition,
        partition=partition,
        member_group_ids=member_group_ids,
        reason=reason,
    )
    return PartitionAssignment(
        assignment_id=assignment_id,
        dataset_fingerprint=DATASET_FINGERPRINT,
        split_manifest_id=SPLIT_MANIFEST_ID,
        unit_kind=unit_kind,
        unit_key=unit_key,
        chronological_start=0,
        chronological_end=max(0, event_count - 1),
        source_line_start=1,
        source_line_end=max(1, event_count),
        event_count=event_count,
        disposition=disposition,
        partition=partition,
        member_group_ids=member_group_ids,
        reason=reason,
    )


def make_partition_identity(
    assignment: PartitionAssignment,
    partition: ScientificPartition,
    *,
    protocol_version: ProtocolVersion = ACTIVE_PROTOCOL_VERSION,
) -> PartitionIdentity:
    if protocol_version == ACTIVE_PROTOCOL_VERSION:
        return build_active_partition_identity(
            split_manifest_sha256=SPLIT_MANIFEST_SHA256,
            assignment_id=assignment.assignment_id,
            partition=partition,
        )
    return PartitionIdentity(
        protocol_version=protocol_version,
        split_manifest_id=SPLIT_MANIFEST_ID,
        split_manifest_sha256=SPLIT_MANIFEST_SHA256,
        assignment_id=assignment.assignment_id,
        partition=partition,
        target_ratio=TARGET_RATIOS[partition],
    )


def make_supervision(
    *,
    dataset_key: str,
    partition: ScientificPartition,
    label: AnomalyLabel = AnomalyLabel.NORMAL,
    real_localization: LocalizationCoordinates | None = None,
) -> SequenceSupervision:
    validation = partition in {
        ScientificPartition.VAL_EXPERT,
        ScientificPartition.VAL_FUSION,
    }
    return SequenceSupervision(
        label=label,
        access=(
            LabelAccess.VALIDATION_EVALUATION
            if validation
            else LabelAccess.NORMAL_POOL_FILTERING
        ),
        aggregation_rule=(
            LabelAggregationRule.HDFS_BLOCK_SOURCE_LABEL
            if dataset_key == "hdfs"
            else LabelAggregationRule.BGL_ANY_SOURCE_ALERT
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
        real_localization=real_localization,
    )


def make_sequence(
    *,
    dataset_key: str = "hdfs",
    partition: ScientificPartition = ScientificPartition.BASE_TRAIN,
    length: int | None = None,
    label: AnomalyLabel = AnomalyLabel.NORMAL,
    supervision: SequenceSupervision | None | object = ...,
    protocol_version: ProtocolVersion = ACTIVE_PROTOCOL_VERSION,
) -> EventSequence:
    resolved_length = length if length is not None else (3 if dataset_key == "hdfs" else 100)
    assignment = make_assignment(
        dataset_key=dataset_key,
        partition=partition,
        event_count=resolved_length,
    )
    identities = event_ids(resolved_length)
    records = record_ids(resolved_length)
    strategy = (
        SequenceStrategy.HDFS_BLOCK_SESSION
        if dataset_key == "hdfs"
        else SequenceStrategy.BGL_FIXED_PARENT_WINDOW
    )
    source_key = (
        "hdfs:block:blk_-1"
        if dataset_key == "hdfs"
        else f"bgl:raw-lines:1-{resolved_length}"
    )
    resolved_supervision = (
        make_supervision(
            dataset_key=dataset_key,
            partition=partition,
            label=label,
        )
        if supervision is ... and partition is not ScientificPartition.TEST
        else None
        if supervision is ...
        else supervision
    )
    sequence_id = build_sequence_id(
        dataset_fingerprint=DATASET_FINGERPRINT,
        partition_assignment_id=assignment.assignment_id,
        strategy=strategy,
        source_key=source_key,
        record_ids=records,
    )
    return EventSequence(
        sequence_id=sequence_id,
        dataset_key=dataset_key,
        dataset_id="HDFS_v1" if dataset_key == "hdfs" else "BGL",
        dataset_version=f"zenodo-8196385:{'HDFS_v1' if dataset_key == 'hdfs' else 'BGL'}",
        dataset_fingerprint=DATASET_FINGERPRINT,
        partition_identity=make_partition_identity(
            assignment,
            partition,
            protocol_version=protocol_version,
        ),
        strategy=strategy,
        source_key=source_key,
        record_ids=records,
        event_ids=identities,
        source_line_numbers=tuple(range(1, resolved_length + 1)),
        chronological_indices=tuple(range(resolved_length)),
        content_sha256=hash_event_ids(identities),
        parser_state_sha256=PARSER_STATE_SHA256,
        template_registry_sha256=REGISTRY_SHA256,
        target_window_size=100 if dataset_key == "bgl" else None,
        is_residual_window=dataset_key == "bgl" and resolved_length < 100,
        supervision=resolved_supervision,
    )


def make_mutation(
    operation: MutationOperation,
    *,
    source_partition: ScientificPartition = ScientificPartition.BASE_TRAIN,
    localization: LocalizationCoordinates | None = None,
) -> MutationRecord:
    source = make_sequence(partition=source_partition)
    expected = event_ids(3)
    if operation is MutationOperation.MISSING:
        observed = (expected[0], expected[2])
        coordinates = LocalizationCoordinates(
            source=LocalizationSource.SYNTHETIC_MUTATION,
            sequence_level=True,
            token_positions=(),
            gap_positions=(1,),
            transition_positions=(),
        )
    elif operation in {MutationOperation.EXTRA, MutationOperation.REPEATED}:
        inserted = expected[0] if operation is MutationOperation.REPEATED else event_ids(1, offset=10)[0]
        observed = (expected[0], inserted, expected[1], expected[2])
        coordinates = LocalizationCoordinates(
            source=LocalizationSource.SYNTHETIC_MUTATION,
            sequence_level=True,
            token_positions=(1,),
            gap_positions=(),
            transition_positions=(0, 1),
        )
    elif operation is MutationOperation.REPLACEMENT:
        observed = (expected[0], event_ids(1, offset=10)[0], expected[2])
        coordinates = LocalizationCoordinates(
            source=LocalizationSource.SYNTHETIC_MUTATION,
            sequence_level=True,
            token_positions=(1,),
            gap_positions=(),
            transition_positions=(0, 1),
        )
    else:
        observed = (expected[1], expected[0], expected[2])
        coordinates = LocalizationCoordinates(
            source=LocalizationSource.SYNTHETIC_MUTATION,
            sequence_level=True,
            token_positions=(0, 1),
            gap_positions=(),
            transition_positions=(0, 1),
        )
    parameters = (
        MutationParameter(name="position", value=1),
        MutationParameter(name="policy", value="synthetic-fixture"),
    )
    expected_sha256 = hash_event_ids(expected)
    observed_sha256 = hash_event_ids(observed)
    mutation_id = build_mutation_id(
        source_sequence_id=source.sequence_id,
        generator_version="mut-v1",
        seed=42,
        operation=operation,
        ordinal=0,
        parameters=parameters,
        expected_event_ids_sha256=expected_sha256,
        observed_event_ids_sha256=observed_sha256,
        expected_length=len(expected),
        observed_length=len(observed),
        localization=localization or coordinates,
    )
    return MutationRecord(
        mutation_id=mutation_id,
        source_sequence_id=source.sequence_id,
        source_partition=source_partition,
        dataset_fingerprint=DATASET_FINGERPRINT,
        split_manifest_id=SPLIT_MANIFEST_ID,
        generator_version="mut-v1",
        seed=42,
        operation=operation,
        ordinal=0,
        parameters=parameters,
        expected_event_ids_sha256=expected_sha256,
        observed_event_ids_sha256=observed_sha256,
        expected_length=len(expected),
        observed_length=len(observed),
        localization=localization or coordinates,
    )


def make_sequence_destruction(
    *,
    partition: ScientificPartition = ScientificPartition.VAL_EXPERT,
    no_op: bool = False,
) -> SequenceDestructionRecord:
    source = make_sequence(
        partition=partition,
        length=1 if no_op else None,
        label=AnomalyLabel.ANOMALY,
    )
    original = source.event_ids
    destroyed = original if no_op else (original[1], original[0], *original[2:])
    status = (
        SequenceDestructionStatus.NOOP_UNPERTURBABLE
        if no_op
        else SequenceDestructionStatus.APPLIED
    )
    no_op_reason = "single-event sequence" if no_op else None
    original_sha256 = hash_event_ids(original)
    destroyed_sha256 = hash_event_ids(destroyed)
    multiset_sha256 = hash_event_multiset(original)
    control_id = build_sequence_destruction_id(
        source_sequence_id=source.sequence_id,
        source_parent_key=source.source_key,
        source_partition_identity=source.partition_identity,
        dataset_fingerprint=source.dataset_fingerprint,
        generator_version="kt3-shuffle-v1",
        seed=42,
        original_event_ids_sha256=original_sha256,
        destroyed_event_ids_sha256=destroyed_sha256,
        original_event_multiset_sha256=multiset_sha256,
        destroyed_event_multiset_sha256=hash_event_multiset(destroyed),
        original_length=len(original),
        destroyed_length=len(destroyed),
        status=status,
        no_op_reason=no_op_reason,
    )
    return SequenceDestructionRecord(
        control_id=control_id,
        source_sequence_id=source.sequence_id,
        source_parent_key=source.source_key,
        source_partition_identity=source.partition_identity,
        dataset_fingerprint=source.dataset_fingerprint,
        generator_version="kt3-shuffle-v1",
        seed=42,
        original_event_ids_sha256=original_sha256,
        destroyed_event_ids_sha256=destroyed_sha256,
        original_event_multiset_sha256=multiset_sha256,
        destroyed_event_multiset_sha256=hash_event_multiset(destroyed),
        original_length=len(original),
        destroyed_length=len(destroyed),
        status=status,
        no_op_reason=no_op_reason,
        source_label=(
            None if partition is ScientificPartition.TEST else AnomalyLabel.ANOMALY
        ),
        label_access=(
            None
            if partition is ScientificPartition.TEST
            else LabelAccess.VALIDATION_EVALUATION
        ),
    )


def test_split_identity_locks_protocol_id_hash_and_target_ratio() -> None:
    assignment = make_assignment()
    identity = make_partition_identity(assignment, ScientificPartition.BASE_TRAIN)
    assert identity.protocol_id == "PROTOCOL-001"
    assert identity.protocol_version == "1.1"
    assert identity.split_manifest_id == f"SPLIT-{SPLIT_MANIFEST_SHA256}"

    payload = identity.model_dump()
    payload["target_ratio"] = 0.59
    with pytest.raises(ValidationError, match="target_ratio"):
        PartitionIdentity.model_validate(payload)


def test_partition_identity_preserves_historical_v1_0_explicitly() -> None:
    assignment = make_assignment()
    historical = make_partition_identity(
        assignment,
        ScientificPartition.BASE_TRAIN,
        protocol_version="1.0",
    )
    restored = PartitionIdentity.model_validate_json(historical.canonical_json())
    assert restored.protocol_version == "1.0"
    assert restored == historical


def test_partition_identity_rejects_unsupported_or_missing_version() -> None:
    identity = make_partition_identity(
        make_assignment(),
        ScientificPartition.BASE_TRAIN,
    )
    payload = identity.model_dump()
    payload["protocol_version"] = "2.0"
    with pytest.raises(ValidationError, match="protocol_version"):
        PartitionIdentity.model_validate(payload)

    del payload["protocol_version"]
    with pytest.raises(ValidationError, match="Field required"):
        PartitionIdentity.model_validate(payload)


@pytest.mark.parametrize(("partition", "ratio"), TARGET_RATIOS.items())
def test_active_partition_contract_matches_protocol_v1_1(
    partition: ScientificPartition,
    ratio: float,
) -> None:
    identity = make_partition_identity(make_assignment(partition=partition), partition)
    assert identity.protocol_version == ACTIVE_PROTOCOL_VERSION
    assert identity.partition is partition
    assert identity.target_ratio == ratio


def test_partition_assignment_identity_is_deterministic() -> None:
    assignment = make_assignment()
    assert assignment == make_assignment()
    assert assignment.unit_kind is PartitionUnitKind.HDFS_BLOCK_COMPONENT
    assert assignment.member_group_ids == ("blk_-1",)
    assert assignment.unit_key == "component:blk_-1"
    assert assignment.assignment_id == build_partition_assignment_id(
        dataset_fingerprint=DATASET_FINGERPRINT,
        split_manifest_id=SPLIT_MANIFEST_ID,
        unit_kind=PartitionUnitKind.HDFS_BLOCK_COMPONENT,
        unit_key="component:blk_-1",
        chronological_start=0,
        chronological_end=2,
        disposition=PartitionDisposition.ASSIGNED,
        partition=ScientificPartition.BASE_TRAIN,
        member_group_ids=("blk_-1",),
        reason=None,
    )


def test_partition_assignment_represents_hdfs_purge_and_bgl_short_drop() -> None:
    purged = make_assignment(
        disposition=PartitionDisposition.PURGED_BOUNDARY,
        partition=None,
    )
    dropped = make_assignment(
        dataset_key="bgl",
        disposition=PartitionDisposition.DROPPED_SHORT_WINDOW,
        partition=None,
        event_count=19,
    )
    active_residual = make_assignment(
        dataset_key="bgl",
        disposition=PartitionDisposition.DROPPED_RESIDUAL_WINDOW,
        partition=None,
        event_count=99,
    )
    assert purged.partition is None
    assert dropped.event_count == 19
    assert active_residual.event_count == 99
    assert active_residual.partition is None


@pytest.mark.parametrize(
    ("dataset_key", "disposition", "event_count", "message"),
    [
        (
            "hdfs",
            PartitionDisposition.DROPPED_SHORT_WINDOW,
            3,
            "HDFS components",
        ),
        (
            "hdfs",
            PartitionDisposition.DROPPED_RESIDUAL_WINDOW,
            3,
            "HDFS components",
        ),
        ("bgl", PartitionDisposition.PURGED_BOUNDARY, 3, "BGL raw ranges"),
        ("bgl", PartitionDisposition.DROPPED_SHORT_WINDOW, 20, "shorter than 20"),
        (
            "bgl",
            PartitionDisposition.DROPPED_RESIDUAL_WINDOW,
            100,
            "1 to 99",
        ),
    ],
)
def test_partition_assignment_rejects_invalid_exclusion_semantics(
    dataset_key: str,
    disposition: PartitionDisposition,
    event_count: int,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        make_assignment(
            dataset_key=dataset_key,
            disposition=disposition,
            partition=None,
            event_count=event_count,
        )


def test_localization_distinguishes_unsupported_from_supported_empty() -> None:
    sequence_only = LocalizationCoordinates(
        source=LocalizationSource.REAL_SOURCE_ALERT,
        sequence_level=True,
    )
    synthetic = LocalizationCoordinates(
        source=LocalizationSource.SYNTHETIC_MUTATION,
        sequence_level=True,
        token_positions=(),
        gap_positions=(3, 1),
        transition_positions=(),
    )
    assert sequence_only.token_positions is None
    assert synthetic.token_positions == ()
    assert synthetic.gap_positions == (1, 3)


def test_localization_uses_token_gap_and_transition_bounds() -> None:
    valid = LocalizationCoordinates(
        source=LocalizationSource.SYNTHETIC_MUTATION,
        sequence_level=True,
        token_positions=(2,),
        gap_positions=(3,),
        transition_positions=(1,),
    )
    valid.validate_for_observed_length(3)

    with pytest.raises(ValueError, match="transition position"):
        LocalizationCoordinates(
            source=LocalizationSource.SYNTHETIC_MUTATION,
            sequence_level=True,
            transition_positions=(2,),
        ).validate_for_observed_length(3)


def test_real_source_localization_is_token_only() -> None:
    valid = make_supervision(
        dataset_key="bgl",
        partition=ScientificPartition.VAL_EXPERT,
        label=AnomalyLabel.ANOMALY,
        real_localization=LocalizationCoordinates(
            source=LocalizationSource.REAL_SOURCE_ALERT,
            sequence_level=True,
            token_positions=(7,),
        ),
    )
    assert valid.real_localization is not None

    with pytest.raises(ValidationError, match="gap localization"):
        make_supervision(
            dataset_key="bgl",
            partition=ScientificPartition.VAL_EXPERT,
            label=AnomalyLabel.ANOMALY,
            real_localization=LocalizationCoordinates(
                source=LocalizationSource.REAL_SOURCE_ALERT,
                sequence_level=True,
                token_positions=(7,),
                gap_positions=(),
            ),
        )


def test_hdfs_sequence_is_deterministic_and_round_trips() -> None:
    sequence = make_sequence()
    restored = EventSequence.model_validate_json(sequence.canonical_json())
    assert restored == sequence
    assert restored.partition_identity.protocol_version == "1.1"
    assert restored.partition_identity.split_manifest_id == SPLIT_MANIFEST_ID
    assert (
        restored.partition_identity.assignment_id
        == sequence.partition_identity.assignment_id
    )
    assert sequence.sequence_id == build_sequence_id(
        dataset_fingerprint=DATASET_FINGERPRINT,
        partition_assignment_id=sequence.partition_identity.assignment_id,
        strategy=SequenceStrategy.HDFS_BLOCK_SESSION,
        source_key="hdfs:block:blk_-1",
        record_ids=sequence.record_ids,
    )


def test_sequence_rejects_alignment_content_and_identity_drift() -> None:
    sequence = make_sequence()
    for field, value, message in (
        ("event_ids", sequence.event_ids[:-1], "equal lengths"),
        ("content_sha256", "9" * 64, "content_sha256"),
        ("sequence_id", f"SEQ-{'9' * 64}", "sequence_id"),
    ):
        payload = sequence.model_dump()
        payload[field] = value
        with pytest.raises(ValidationError, match=message):
            EventSequence.model_validate(payload)


def test_bgl_parent_window_contract_is_version_aware() -> None:
    assignment = make_assignment(dataset_key="bgl", event_count=100)
    assert assignment.unit_kind is PartitionUnitKind.BGL_RAW_RANGE
    assert assignment.unit_key == "raw-lines:1-100"
    assert assignment.member_group_ids == ()
    assert assignment.chronological_start == 0
    assert assignment.chronological_end == 99

    active = make_sequence(dataset_key="bgl")
    assert len(active.event_ids) == 100
    assert active.partition_identity.protocol_version == "1.1"
    assert active.source_key == "bgl:raw-lines:1-100"

    historical_residual = make_sequence(
        dataset_key="bgl",
        length=20,
        protocol_version="1.0",
    )
    assert historical_residual.is_residual_window

    with pytest.raises(ValidationError, match="Protocol v1.1"):
        make_sequence(dataset_key="bgl", length=20)
    with pytest.raises(ValidationError, match="20 to 99"):
        make_sequence(dataset_key="bgl", length=19, protocol_version="1.0")


def test_sequence_destruction_record_round_trips_full_kt3_provenance() -> None:
    control = make_sequence_destruction()
    restored = SequenceDestructionRecord.model_validate_json(
        control.canonical_json()
    )

    assert restored == control
    assert restored.source_partition_identity.protocol_version == "1.1"
    assert restored.source_partition_identity.partition is ScientificPartition.VAL_EXPERT
    assert restored.source_partition_identity.split_manifest_id == SPLIT_MANIFEST_ID
    assert restored.source_label is AnomalyLabel.ANOMALY
    assert restored.label_access is LabelAccess.VALIDATION_EVALUATION
    assert restored.original_length == restored.destroyed_length
    assert (
        restored.original_event_multiset_sha256
        == restored.destroyed_event_multiset_sha256
    )
    assert restored.raw_data_mutated is False


def test_sequence_destruction_record_supports_registered_noop_and_rejects_drift() -> None:
    no_op = make_sequence_destruction(no_op=True)
    assert no_op.status is SequenceDestructionStatus.NOOP_UNPERTURBABLE
    assert no_op.no_op_reason == "single-event sequence"

    payload = no_op.model_dump()
    payload["destroyed_event_multiset_sha256"] = "9" * 64
    with pytest.raises(ValidationError, match="event multiset"):
        SequenceDestructionRecord.model_validate(payload)

    payload = no_op.model_dump()
    payload["status"] = SequenceDestructionStatus.APPLIED
    payload["no_op_reason"] = None
    with pytest.raises(ValidationError, match="changed order"):
        SequenceDestructionRecord.model_validate(payload)


def test_sequence_destruction_record_preserves_test_seal() -> None:
    sealed = make_sequence_destruction(partition=ScientificPartition.TEST)
    assert sealed.source_label is None
    assert sealed.label_access is None

    payload = sealed.model_dump()
    payload["source_label"] = AnomalyLabel.ANOMALY
    with pytest.raises(ValidationError, match="must not expose supervision"):
        SequenceDestructionRecord.model_validate(payload)


def test_test_sequence_cannot_expose_supervision() -> None:
    sealed = make_sequence(partition=ScientificPartition.TEST)
    assert sealed.supervision is None

    with pytest.raises(ValidationError, match="TEST EventSequence"):
        make_sequence(
            partition=ScientificPartition.TEST,
            supervision=make_supervision(
                dataset_key="hdfs",
                partition=ScientificPartition.BASE_TRAIN,
            ),
        )


def test_train_and_validation_label_access_is_enforced() -> None:
    with pytest.raises(ValidationError, match="normal-pool-filtering"):
        make_sequence(label=AnomalyLabel.ANOMALY)

    valid = make_sequence(
        partition=ScientificPartition.VAL_EXPERT,
        label=AnomalyLabel.ANOMALY,
    )
    assert valid.supervision is not None
    assert valid.supervision.access is LabelAccess.VALIDATION_EVALUATION


def test_dataset_specific_label_source_is_enforced() -> None:
    invalid = SequenceSupervision(
        label=AnomalyLabel.NORMAL,
        access=LabelAccess.NORMAL_POOL_FILTERING,
        aggregation_rule=LabelAggregationRule.HDFS_BLOCK_SOURCE_LABEL,
        source_kind=LabelSourceKind.INLINE_FIELD,
        source_reference="synthetic:inline",
    )
    with pytest.raises(ValidationError, match="external-file"):
        make_sequence(supervision=invalid)


def test_model_input_is_label_free_and_length_checked() -> None:
    model_input = make_sequence().to_model_input()
    assert set(model_input.model_dump()) == {"sequence_id", "event_ids", "valid_length"}
    assert model_input.valid_length == len(model_input.event_ids)

    with pytest.raises(ValidationError, match="valid_length"):
        SequenceModelInput(
            sequence_id=model_input.sequence_id,
            event_ids=model_input.event_ids,
            valid_length=1,
        )


@pytest.mark.parametrize("operation", list(MutationOperation))
def test_each_frozen_mutation_family_has_valid_coordinates(
    operation: MutationOperation,
) -> None:
    mutation = make_mutation(operation)
    restored = MutationRecord.model_validate_json(mutation.canonical_json())
    assert restored == mutation
    assert mutation.source_label is AnomalyLabel.NORMAL
    assert mutation.localization.sequence_level


def test_mutation_id_is_independent_of_parameter_order() -> None:
    source = make_sequence()
    parameters = (
        MutationParameter(name="zeta", value=2),
        MutationParameter(name="alpha", value=1),
    )
    localization = LocalizationCoordinates(
        source=LocalizationSource.SYNTHETIC_MUTATION,
        sequence_level=True,
        token_positions=(),
        gap_positions=(1,),
        transition_positions=(),
    )
    expected_sha256 = hash_event_ids(event_ids(3))
    observed_sha256 = hash_event_ids((event_ids(3)[0], event_ids(3)[2]))
    forward = build_mutation_id(
        source_sequence_id=source.sequence_id,
        generator_version="mut-v1",
        seed=42,
        operation=MutationOperation.MISSING,
        ordinal=0,
        parameters=parameters,
        expected_event_ids_sha256=expected_sha256,
        observed_event_ids_sha256=observed_sha256,
        expected_length=3,
        observed_length=2,
        localization=localization,
    )
    reverse = build_mutation_id(
        source_sequence_id=source.sequence_id,
        generator_version="mut-v1",
        seed=42,
        operation=MutationOperation.MISSING,
        ordinal=0,
        parameters=tuple(reversed(parameters)),
        expected_event_ids_sha256=expected_sha256,
        observed_event_ids_sha256=observed_sha256,
        expected_length=3,
        observed_length=2,
        localization=localization,
    )
    assert forward == reverse
    changed_output = build_mutation_id(
        source_sequence_id=source.sequence_id,
        generator_version="mut-v1",
        seed=42,
        operation=MutationOperation.MISSING,
        ordinal=0,
        parameters=parameters,
        expected_event_ids_sha256=expected_sha256,
        observed_event_ids_sha256="8" * 64,
        expected_length=3,
        observed_length=2,
        localization=localization,
    )
    assert changed_output != forward


def test_mutation_rejects_test_no_op_and_wrong_coordinate_family() -> None:
    with pytest.raises(ValidationError, match="TEST mutations"):
        make_mutation(MutationOperation.MISSING, source_partition=ScientificPartition.TEST)

    mutation = make_mutation(MutationOperation.MISSING)
    payload = mutation.model_dump()
    payload["observed_event_ids_sha256"] = mutation.expected_event_ids_sha256
    with pytest.raises(ValidationError, match="no-op"):
        MutationRecord.model_validate(payload)

    wrong = LocalizationCoordinates(
        source=LocalizationSource.SYNTHETIC_MUTATION,
        sequence_level=True,
        token_positions=(0,),
        gap_positions=(),
        transition_positions=(),
    )
    with pytest.raises(ValidationError, match="gap-only"):
        make_mutation(MutationOperation.MISSING, localization=wrong)


def test_mutation_rejects_out_of_bounds_and_non_finite_parameters() -> None:
    out_of_bounds = LocalizationCoordinates(
        source=LocalizationSource.SYNTHETIC_MUTATION,
        sequence_level=True,
        token_positions=(),
        gap_positions=(3,),
        transition_positions=(),
    )
    with pytest.raises(ValidationError, match="gap position"):
        make_mutation(MutationOperation.MISSING, localization=out_of_bounds)

    with pytest.raises(ValidationError, match="must be finite"):
        MutationParameter(name="temperature", value=math.inf)


def test_schema_models_are_strict_and_immutable() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        LocalizationCoordinates(
            source=LocalizationSource.SYNTHETIC_MUTATION,
            sequence_level=True,
            token_positions=(0,),
            unknown=True,
        )
    sequence = make_sequence()
    with pytest.raises(ValidationError, match="frozen"):
        sequence.sequence_id = f"SEQ-{'0' * 64}"  # type: ignore[misc]
