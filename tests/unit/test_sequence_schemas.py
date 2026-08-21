"""SCHEMA-002 contract tests using synthetic identities only."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from seqlogad.common.schemas import (
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
    PartitionAssignment,
    PartitionDisposition,
    PartitionIdentity,
    PartitionUnitKind,
    ScientificPartition,
    SequenceModelInput,
    SequenceStrategy,
    SequenceSupervision,
    build_mutation_id,
    build_partition_assignment_id,
    build_sequence_id,
    build_split_manifest_id,
    hash_event_ids,
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
    unit_key = "component:blk_-1" if hdfs else "raw-lines:1-100"
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
) -> PartitionIdentity:
    return PartitionIdentity(
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
    source_key = "hdfs:block:blk_-1" if dataset_key == "hdfs" else "bgl:raw-lines:1-100"
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
        partition_identity=make_partition_identity(assignment, partition),
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


def test_split_identity_locks_protocol_id_hash_and_target_ratio() -> None:
    assignment = make_assignment()
    identity = make_partition_identity(assignment, ScientificPartition.BASE_TRAIN)
    assert identity.protocol_id == "PROTOCOL-001"
    assert identity.protocol_version == "1.0"
    assert identity.split_manifest_id == f"SPLIT-{SPLIT_MANIFEST_SHA256}"

    payload = identity.model_dump()
    payload["target_ratio"] = 0.59
    with pytest.raises(ValidationError, match="target_ratio"):
        PartitionIdentity.model_validate(payload)


def test_partition_assignment_identity_is_deterministic() -> None:
    assignment = make_assignment()
    assert assignment == make_assignment()
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
    assert purged.partition is None
    assert dropped.event_count == 19


@pytest.mark.parametrize(
    ("dataset_key", "disposition", "event_count", "message"),
    [
        ("hdfs", PartitionDisposition.DROPPED_SHORT_WINDOW, 3, "HDFS components"),
        ("bgl", PartitionDisposition.PURGED_BOUNDARY, 3, "BGL raw ranges"),
        ("bgl", PartitionDisposition.DROPPED_SHORT_WINDOW, 20, "shorter than 20"),
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


def test_bgl_parent_and_residual_window_contract() -> None:
    assert len(make_sequence(dataset_key="bgl").event_ids) == 100
    assert make_sequence(dataset_key="bgl", length=20).is_residual_window
    with pytest.raises(ValidationError, match="20 to 99"):
        make_sequence(dataset_key="bgl", length=19)


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
