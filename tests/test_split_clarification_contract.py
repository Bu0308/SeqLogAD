"""Synthetic-only guards for PROTOCOL-SPLIT-CLARIFY-001.

These tests prove the frozen arithmetic and identity contract. They do not
read accepted HDFS/BGL raw data, create a real partition manifest, or assign
scientific TEST membership.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    PROJECT_ROOT / "configs" / "protocols" / "split-clarification-v1.yaml"
)
PARTITIONS = (
    "BASE_TRAIN",
    "FUSION_TRAIN",
    "VAL_EXPERT",
    "VAL_FUSION",
    "TEST",
)


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def _boundaries(n: int) -> tuple[int, ...]:
    return (
        0,
        (60 * n) // 100,
        (70 * n) // 100,
        (80 * n) // 100,
        (90 * n) // 100,
        n,
    )


def _nominal_partition(rank: int, boundaries: tuple[int, ...]) -> str:
    if not 0 <= rank < boundaries[-1]:
        raise ValueError("rank is outside the allocation universe")
    for index, name in enumerate(PARTITIONS):
        if boundaries[index] <= rank < boundaries[index + 1]:
            return name
    raise AssertionError("valid rank did not map to a partition")


def _assign_hdfs_components(
    components: dict[str, tuple[int, ...]], n_eligible: int
) -> tuple[dict[str, str], dict[str, int]]:
    boundaries = _boundaries(n_eligible)
    decisions: dict[str, str] = {}
    counts = {name: 0 for name in PARTITIONS}
    counts["PURGED_BOUNDARY"] = 0

    seen_ranks: set[int] = set()
    for component_id, ranks in sorted(components.items()):
        if not ranks or len(ranks) != len(set(ranks)):
            raise ValueError("component ranks must be non-empty and unique")
        if seen_ranks.intersection(ranks):
            raise ValueError("eligible rank cannot belong to two components")
        seen_ranks.update(ranks)
        occupied = {_nominal_partition(rank, boundaries) for rank in ranks}
        if len(occupied) == 1:
            decision = next(iter(occupied))
        else:
            decision = "PURGED_BOUNDARY"
        decisions[component_id] = decision
        counts[decision] += len(ranks)

    if seen_ranks != set(range(n_eligible)):
        raise ValueError("synthetic eligible universe must reconcile exactly")
    return decisions, counts


def _bgl_partition_summary(n: int) -> tuple[list[int], list[int], list[int]]:
    boundaries = _boundaries(n)
    sizes = [boundaries[index + 1] - boundaries[index] for index in range(5)]
    windows = [size // 100 for size in sizes]
    residuals = [size % 100 for size in sizes]
    return sizes, windows, residuals


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _sha256_canonical(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def test_clarification_preserves_its_split_stage_snapshot_and_active_pointer() -> None:
    contract = _load_contract()
    metadata = contract["split_clarification"]

    assert metadata == {
        "id": "PROTOCOL-SPLIT-CLARIFY-001",
        "version": "1.0",
        "status": "FROZEN_HUMAN_APPROVED",
        "approved_on": "2026-08-22",
        "parent_protocol_id": "PROTOCOL-001",
        "parent_protocol_version": "1.1",
        "empirical_status": "NOT_RUN",
        "status_snapshot_scope": "SPLIT_001_AUTHORIZATION_AND_COMPLETION",
        "current_execution_state": "configs/active-state.yaml",
        "execution_ready": True,
        "split_execution_authorized": True,
        "authorization_source": "HUMAN_RESEARCHER",
        "authorized_on": "2026-08-23",
        "real_split_created": True,
        "scientific_test_created": True,
        "scientific_test_accessed": False,
        "parser_fitted": False,
        "human_readable_contract": "docs/split-clarification-contract.md",
        "evidence_matrix": "docs/literature/split-protocol-evidence-matrix.md",
        "citation_note": (
            "docs/references/PROTOCOL-SPLIT-CLARIFY-001-citations.md"
        ),
        "implementation_status": "COMPLETE",
        "test_state": "SEALED_NEVER_OPENED",
        "next_authorized_task": "PARSE-001",
        "real_artifacts": {
            "hdfs": {
                "path": "data/processed/splits/hdfs",
                "split_payload_hash": "21ec061a7717cd03e7648e3d89200d486bce81eb7dd1bf4114272dd90fc4295c",
                "test_partition_hash": "fa0c743619f8e2f7ef82a3cb2057eb99891515d56b0aa87f168c60bec093175d",
            },
            "bgl": {
                "path": "data/processed/splits/bgl",
                "split_payload_hash": "0c1bb1b9b755aa2aa50238771cf5bf34649e1ca33c7964e061766b659aeebd05",
                "test_partition_hash": "7ecf43ab27d6519b7af4ae4e8f7be5cd9d5351c8c11d18b3bd11b4ff896a876d",
            },
        },
    }
    assert (PROJECT_ROOT / metadata["human_readable_contract"]).is_file()
    assert (PROJECT_ROOT / metadata["evidence_matrix"]).is_file()
    assert (PROJECT_ROOT / metadata["citation_note"]).is_file()
    assert (PROJECT_ROOT / metadata["current_execution_state"]).is_file()


def test_shared_boundaries_and_label_independence_are_exact() -> None:
    contract = _load_contract()
    shared = contract["shared"]

    assert shared["partition_order"] == list(PARTITIONS)
    assert shared["target_ratios"] == {
        "BASE_TRAIN": 0.60,
        "FUSION_TRAIN": 0.10,
        "VAL_EXPERT": 0.10,
        "VAL_FUSION": 0.10,
        "TEST": 0.10,
    }
    assert shared["boundary_algorithm"] == "cumulative_floor"
    assert shared["boundary_integer_denominator"] == 100
    assert shared["boundary_integer_numerators"] == [0, 60, 70, 80, 90, 100]
    assert shared["label_independent"] is True
    assert shared["anomaly_labels_read_for_assignment"] is False
    assert shared["parser_or_template_state_used_for_assignment"] is False
    assert shared["randomization"] is False
    assert shared["ratio_repair"] is False
    assert "label" not in inspect.signature(_assign_hdfs_components).parameters

    assert _boundaries(20) == (0, 12, 14, 16, 18, 20)
    assert _boundaries(0) == (0, 0, 0, 0, 0, 0)
    assert _boundaries(3) == (0, 1, 2, 2, 2, 3)


def test_current_entry_point_and_default_config_require_the_split_addendum() -> None:
    entry_point = (PROJECT_ROOT / "docs" / "research-protocol.md").read_text(
        encoding="utf-8"
    )
    default = yaml.safe_load(
        (PROJECT_ROOT / "configs" / "default.yaml").read_text(encoding="utf-8")
    )

    assert "split-clarification-contract.md" in entry_point
    assert "split-clarification-v1.yaml" in entry_point
    assert default["protocol"]["split_addendum"] == (
        "configs/protocols/split-clarification-v1.yaml"
    )
    assert default["protocol"]["split_addendum_status"] == (
        "FROZEN_HUMAN_APPROVED"
    )
    assert default["protocol"]["execution_ready"] is False


def test_hdfs_synthetic_fixture_proves_atomic_purge_and_reconciliation() -> None:
    # CY models a non-contiguous/transitively connected META-001 component.
    components = {
        "C0": (0, 1, 2, 3),
        "C1": (4, 5, 6, 7, 8, 9, 10),
        "CX": (11, 12),
        "C2": (13,),
        "CY": (14, 16),
        "C3": (15,),
        "C4": (17,),
        "C5": (18, 19),
    }

    decisions, counts = _assign_hdfs_components(components, n_eligible=20)

    assert decisions == {
        "C0": "BASE_TRAIN",
        "C1": "BASE_TRAIN",
        "C2": "FUSION_TRAIN",
        "C3": "VAL_EXPERT",
        "C4": "VAL_FUSION",
        "C5": "TEST",
        "CX": "PURGED_BOUNDARY",
        "CY": "PURGED_BOUNDARY",
    }
    assert [counts[name] for name in PARTITIONS] == [11, 1, 1, 1, 2]
    assert counts["PURGED_BOUNDARY"] == 4
    assigned = sum(counts[name] for name in PARTITIONS)
    structurally_ineligible = 2
    total_raw = 22
    assert assigned == 16
    assert total_raw == structurally_ineligible + assigned + 4
    assert [counts[name] / assigned for name in PARTITIONS] == [
        0.6875,
        0.0625,
        0.0625,
        0.0625,
        0.125,
    ]
    assert counts["PURGED_BOUNDARY"] / 20 == 0.20

    hdfs = _load_contract()["hdfs"]
    assert hdfs["structural_line_disposition"] == "STRUCTURAL_EXCLUSION"
    assert hdfs["boundary_component_disposition"] == "PURGED_BOUNDARY"


@pytest.mark.parametrize(
    ("ranks", "expected"),
    [
        ((0, 12), "PURGED_BOUNDARY"),
        ((0, 14, 18), "PURGED_BOUNDARY"),
        (tuple(range(20)), "PURGED_BOUNDARY"),
    ],
)
def test_hdfs_components_crossing_two_three_or_all_partitions_are_purged(
    ranks: tuple[int, ...], expected: str
) -> None:
    remaining = tuple(rank for rank in range(20) if rank not in ranks)
    components = {"CROSSING": ranks}
    if remaining:
        components["REMAINDER"] = remaining

    decisions, _ = _assign_hdfs_components(components, n_eligible=20)

    assert decisions["CROSSING"] == expected


def test_hdfs_duplicate_structural_membership_is_rejected() -> None:
    with pytest.raises(ValueError, match="two components"):
        _assign_hdfs_components({"A": (0,), "B": (0, 1)}, n_eligible=2)


def test_empty_hdfs_universe_is_reconciled_but_not_execution_ready() -> None:
    decisions, counts = _assign_hdfs_components({}, n_eligible=0)
    contract = _load_contract()

    assert decisions == {}
    assert all(count == 0 for count in counts.values())
    assert contract["shared"]["empty_input_policy"] == (
        "VALID_STRUCTURAL_MANIFEST_NOT_EXECUTION_READY"
    )
    assert contract["hdfs"]["zero_eligible_policy"] == (
        "VALID_RECONCILED_NOT_EXECUTION_READY"
    )
    assert contract["shared"]["duplicate_structural_identity_policy"] == "REJECT"
    assert contract["shared"]["unsupported_protocol_version_policy"] == "REJECT"


def test_bgl_synthetic_fixture_proves_windows_residuals_and_reconciliation() -> None:
    sizes, windows, residuals = _bgl_partition_summary(1037)

    assert _boundaries(1037) == (0, 622, 725, 829, 933, 1037)
    assert sizes == [622, 103, 104, 104, 104]
    assert windows == [6, 1, 1, 1, 1]
    assert residuals == [22, 3, 4, 4, 4]
    assert sum(100 * count for count in windows) == 1000
    assert sum(residuals) == 37
    assert sum(sizes) == 1037 == 1000 + 37


@pytest.mark.parametrize(
    ("n", "expected_sizes", "expected_windows", "expected_residuals"),
    [
        (0, [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]),
        (99, [59, 10, 10, 10, 10], [0, 0, 0, 0, 0], [59, 10, 10, 10, 10]),
        (100, [60, 10, 10, 10, 10], [0, 0, 0, 0, 0], [60, 10, 10, 10, 10]),
        (1000, [600, 100, 100, 100, 100], [6, 1, 1, 1, 1], [0, 0, 0, 0, 0]),
    ],
)
def test_bgl_small_exact_and_multiple_window_edge_cases(
    n: int,
    expected_sizes: list[int],
    expected_windows: list[int],
    expected_residuals: list[int],
) -> None:
    sizes, windows, residuals = _bgl_partition_summary(n)

    assert sizes == expected_sizes
    assert windows == expected_windows
    assert residuals == expected_residuals
    assert sum(100 * value for value in windows) + sum(residuals) == n


def test_split_payload_hash_excludes_volatile_and_recursively_derived_fields() -> None:
    scientific_payload = {
        "dataset_fingerprint": "a" * 64,
        "protocol": {"id": "PROTOCOL-001", "version": "1.1"},
        "split_contract": {
            "id": "PROTOCOL-SPLIT-CLARIFY-001",
            "version": "1.0",
        },
        "ratios": [0.60, 0.10, 0.10, 0.10, 0.10],
        "ordered_assignments": [
            {
                "structural_unit": "SYNTHETIC-1",
                "partition": "BASE_TRAIN",
                "disposition": "assigned",
            }
        ],
        "ordered_exclusions": [],
    }
    first_hash = _sha256_canonical(scientific_payload)
    volatile_manifest_a = {
        "canonical_split_payload": scientific_payload,
        "generated_at": "2026-08-22T00:00:00Z",
        "assignment_ids": ["PART-" + "1" * 64],
        "partition_hashes": {"BASE_TRAIN": "2" * 64},
    }
    volatile_manifest_b = {
        "canonical_split_payload": scientific_payload,
        "generated_at": "2027-01-01T00:00:00Z",
        "assignment_ids": ["PART-" + "3" * 64],
        "partition_hashes": {"BASE_TRAIN": "4" * 64},
    }

    assert first_hash == _sha256_canonical(
        volatile_manifest_a["canonical_split_payload"]
    )
    assert first_hash == _sha256_canonical(
        volatile_manifest_b["canonical_split_payload"]
    )
    assert _sha256_canonical(volatile_manifest_a) != _sha256_canonical(
        volatile_manifest_b
    )


def test_identity_and_future_test_seal_contract_are_non_circular_and_closed() -> None:
    contract = _load_contract()
    identity = contract["identity"]

    assert identity["split_payload_hash"] == (
        "SHA256_CANONICAL_SPLIT_PAYLOAD_BYTES"
    )
    assert identity["digest_encoding"] == "lowercase_hex_64"
    assert identity["split_payload"]["top_level_keys"] == [
        "schema_version",
        "dataset_fingerprint",
        "protocol",
        "split_contract",
        "partition_order",
        "target_ratios",
        "boundary_contract",
        "dataset_semantics",
        "assignments",
        "exclusions",
    ]
    assert identity["split_payload"]["assignment_sort_key"] == [
        "partition_order_index",
        "chronological_start",
        "structural_unit_id",
    ]
    assert identity["split_payload"]["exclusion_sort_key"] == [
        "chronological_start",
        "unit_kind",
        "structural_unit_id",
    ]
    assert identity["assignment_id"]["calculated_after_split_payload_hash"] is True
    assert identity["assignment_id"]["excluded_from_split_payload"] is True
    assert "assignment_ids" in identity["partition_hash"]["excludes"]
    assert identity["partition_hash"]["membership_sort_key"] == [
        "chronological_start",
        "structural_unit_id",
    ]
    assert identity["manifest_file_hash"]["embedded_in_manifest"] is False
    assert identity["manifest_file_hash"]["scientific_identity"] is False

    seal = contract["future_test_seal"]
    assert seal["implemented_in_this_task"] is True
    assert seal["opened_in_this_task"] is False
    assert seal["default_access"] == "DENIED"
    assert seal["status"] == "SEALED"
    assert seal["never_opened"] is True
    assert seal["open_count"] == 0
    assert seal["unlock_records"] == 0
    assert seal["must_bind"] == [
        "dataset_fingerprint",
        "protocol_id_and_version",
        "split_payload_hash",
        "TEST_partition_hash",
    ]


def test_evidence_classification_uses_only_frozen_values() -> None:
    contract = _load_contract()
    evidence = contract["evidence_classification"]
    allowed = set(evidence.pop("allowed_values"))

    assert allowed == {
        "LITERATURE_SUPPORTED",
        "LITERATURE_INFORMED_SEQLOGAD_DECISION",
        "SEQLOGAD_PROTOCOL_DECISION",
        "INSUFFICIENT_EVIDENCE",
    }
    assert set(evidence.values()) <= allowed
    assert evidence["five_way_60_10_10_10_10"] == "SEQLOGAD_PROTOCOL_DECISION"
    assert evidence["cumulative_floor_rounding"] == "SEQLOGAD_PROTOCOL_DECISION"
    assert evidence["bgl_raw_split_before_windows"] == "LITERATURE_SUPPORTED"
    assert evidence["hdfs_connected_component_boundary_purge"] == (
        "SEQLOGAD_PROTOCOL_DECISION"
    )
