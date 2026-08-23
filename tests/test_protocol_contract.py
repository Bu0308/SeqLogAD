"""Regression guards for the active and historical scientific protocols."""

from pathlib import Path

import yaml

from seqlogad.common.schemas import (
    ACTIVE_PROTOCOL_VERSION,
    ScientificPartition,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_PATH = PROJECT_ROOT / "configs" / "protocols" / "protocol-v1.1.yaml"
HISTORICAL_PATH = PROJECT_ROOT / "configs" / "protocols" / "protocol-v1.yaml"
EFFECT_PATH = PROJECT_ROOT / "configs" / "protocols" / "effect-001.yaml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_protocol_v1_1_frozen_data_and_test_contract() -> None:
    protocol = _load(ACTIVE_PATH)

    assert protocol["protocol"]["id"] == "PROTOCOL-001"
    assert protocol["protocol"]["version"] == "1.1"
    assert protocol["protocol"]["status"] == "FROZEN_HUMAN_APPROVED"
    assert protocol["protocol"]["empirical_status"] == "NOT_RUN"
    assert protocol["protocol"]["direction"] == "HYBRID_B_PLUS_C"

    assert protocol["partitions"]["ratios"] == {
        "BASE_TRAIN": 0.60,
        "FUSION_TRAIN": 0.10,
        "VAL_EXPERT": 0.10,
        "VAL_FUSION": 0.10,
        "TEST": 0.10,
    }
    assert protocol["partitions"]["split_before_train_fitted_transform"] is True
    assert protocol["partitions"]["split_before_window_generation"] is True
    assert protocol["partitions"]["reserved_partitions_are_not_repurposed"] is True

    labels = protocol["labels"]
    assert labels["model_input_allowed"] is False
    assert labels["base_loss_allowed"] is False
    assert labels["test_contractually_sealed"] is True
    assert labels["test_physically_sealed"] is True
    assert labels["test_physical_state"] == "SEALED_NEVER_OPENED"
    assert labels["test_execution_owner"] == "HUMAN"
    assert labels["test_execution_count"] == 1

    assert protocol["datasets"]["hdfs"]["grouping_unit"] == "block_session"
    assert protocol["datasets"]["hdfs"]["boundary_policy"] == "PURGED_BOUNDARY"
    assert protocol["datasets"]["bgl"]["parent_window_events"] == 100
    assert protocol["datasets"]["bgl"]["overlap"] == 0
    assert protocol["parser"]["fit_partition"] == "BASE_TRAIN"
    assert protocol["parser"]["fit_normal_only"] is True
    assert protocol["parser"]["freeze_after_fit"] is True


def test_active_schema_identity_matches_protocol_v1_1_machine_contract() -> None:
    protocol = _load(ACTIVE_PATH)

    assert ACTIVE_PROTOCOL_VERSION == protocol["protocol"]["version"]
    assert {item.value for item in ScientificPartition} == set(
        protocol["partitions"]["ratios"]
    )


def test_protocol_v1_1_core_and_conditional_scope() -> None:
    protocol = _load(ACTIVE_PATH)
    methods = protocol["methods"]

    assert methods["must"] == [
        "unseen_event_type",
        "sequence_length",
        "event_count_and_count_vector",
        "markov_or_ngram",
        "sequence_destruction_control",
    ]
    assert "isolation_forest_order_insensitive" in methods["should"]
    assert methods["conditional"]["transformer"] == "SEQUENCE_SIGNAL_GATE"
    assert methods["conditional"]["localization"] == "SEQUENCE_AND_FAITHFULNESS_GATE"
    assert "lstm" in methods["removed_from_core"]
    assert "trainable_fusion_f2_through_f8" in methods["removed_from_core"]


def test_protocol_v1_1_killer_experiments_and_kill_criteria_are_preregistered() -> None:
    protocol = _load(ACTIVE_PATH)

    assert set(protocol["killer_experiments"]) == {
        "KT-1",
        "KT-2",
        "KT-3",
        "KT-4",
        "KT-5",
        "KT-6",
    }
    assert all(
        item["status"] == "NOT_RUN"
        for item in protocol["killer_experiments"].values()
    )
    assert set(protocol["kill_criteria"]) >= {
        "minimum_practical_effect",
        "KC-1",
        "KC-2",
        "KC-3",
        "KC-4",
        "KC-5",
        "KC-6",
    }
    assert (
        protocol["kill_criteria"]["minimum_practical_effect"]["value"]
        == "TO_BE_FROZEN_BEFORE_RUN"
    )
    assert protocol["evaluation"]["primary_detection_metric"] == "PR_AUC"
    assert protocol["evaluation"]["stochastic_core_seeds"] == [42, 43, 44]


def test_historical_protocol_v1_0_is_preserved() -> None:
    historical = _load(HISTORICAL_PATH)

    assert historical["protocol"]["version"] == "1.0"
    assert historical["protocol"]["status"] == "FROZEN_HUMAN_APPROVED"
    assert historical["protocol"]["empirical_status"] == "NOT_RUN"
    assert (PROJECT_ROOT / "docs" / "research-protocol-v1.0.md").is_file()


def test_effect_001_records_pre_experiment_human_margin_approval() -> None:
    contract = _load(EFFECT_PATH)
    metadata = contract["effect_contract"]

    assert metadata["id"] == "EFFECT-001"
    assert metadata["parent_protocol_id"] == "PROTOCOL-001"
    assert metadata["parent_protocol_version"] == "1.1"
    assert metadata["status"] == "FROZEN_HUMAN_APPROVED"
    assert metadata["empirical_status"] == "NOT_RUN"
    assert metadata["execution_ready"] is True
    assert metadata["scientific_pipeline_execution_authorized"] is False
    assert metadata["scientific_test_accessed"] is False
    assert metadata["blocked_by"] == []
    assert metadata["approval"] == {
        "source": "HUMAN_RESEARCHER",
        "timing": "PRE_EXPERIMENT",
        "result_informed": False,
        "framework": "RESOURCE_FEASIBILITY_MARGIN",
        "same_margin_for_both_datasets": True,
        "dataset_conclusions_remain_independent": True,
        "observed_before_approval": {
            "scientific_baseline": False,
            "KT-1": False,
            "KT-2": False,
            "KT-3": False,
            "parser_derived_experiment": False,
            "TEST_result": False,
        },
    }

    practical = contract["practical_effect"]
    assert practical["hdfs"] == {
        "delta_ap": 0.01,
        "status": "FROZEN_HUMAN_APPROVED",
    }
    assert practical["bgl"] == {
        "delta_ap": 0.01,
        "status": "FROZEN_HUMAN_APPROVED",
    }
    assert practical["selected_framework"] == "RESOURCE_FEASIBILITY_MARGIN"
    assert practical["test_derived_margin_allowed"] is False
    assert practical["outcome_derived_margin_allowed"] is False


def test_effect_001_freezes_primary_comparison_and_bootstrap_contract() -> None:
    contract = _load(EFFECT_PATH)

    estimand = contract["primary_estimand"]
    assert estimand["formula"] == (
        "AP_sequence_d_minus_AP_strongest_orderless_d"
    )
    assert estimand["metric"]["canonical_name"] == "average_precision"
    assert estimand["metric"]["computation"] == (
        "non_interpolated_average_precision"
    )
    assert estimand["datasets"] == ["hdfs", "bgl"]
    assert estimand["pooled_hdfs_bgl_claim_allowed"] is False
    assert estimand["development_gate_partition"] == "VAL_EXPERT"
    assert estimand["final_confirmatory_partition"] == "TEST"
    assert estimand["final_confirmatory_execution_owner"] == "HUMAN"

    uncertainty = contract["uncertainty"]
    assert uncertainty["method"] == "paired_cluster_percentile_bootstrap"
    assert uncertainty["confidence_level"] == 0.95
    assert uncertainty["valid_replicates"] == 10_000
    assert uncertainty["resampling_seed"] == 42
    assert uncertainty["hdfs"]["resampling_unit"] == "block_session"
    assert uncertainty["bgl"]["resampling_unit"] == (
        "non_overlapping_100_event_parent_window"
    )
    assert uncertainty["bgl"]["residual_adjacent_window_dependence_modeled"] is (
        False
    )
    assert uncertainty["bgl"]["limitation_must_be_reported"] is True
    assert uncertainty["degenerate_replicate"]["action"] == (
        "reject_and_redraw"
    )
    assert uncertainty["degenerate_replicate"]["maximum_total_attempts"] == (
        100_000
    )

    selection = contract["orderless_baseline_selection"]
    assert selection["selection_partition"] == "VAL_EXPERT"
    assert selection["required_primary_candidates"] == [
        "unseen_event_type",
        "sequence_length",
        "total_event_count",
        "event_count_vector",
        "isolation_forest_order_insensitive",
    ]
    assert selection["isolation_forest_role"] == "REQUIRED_PRIMARY_CANDIDATE"
    assert selection["test_selection_allowed"] is False
    assert contract["equal_budget"][
        "maximum_complete_configurations_per_family_per_dataset"
    ] == 12


def test_effect_001_freezes_decision_multiplicity_seed_and_kt3_rules() -> None:
    contract = _load(EFFECT_PATH)

    assert set(contract["decision_regions"]) == {
        "meaningful_sequence_gain",
        "practical_equivalence",
        "meaningful_harm",
        "inconclusive",
        "inconclusive_is_no_difference",
    }
    assert contract["decision_regions"]["inconclusive_is_no_difference"] is False

    primary_family = contract["multiple_comparisons"]["primary_family"]
    assert primary_family["hdfs_contrasts"] == 1
    assert primary_family["bgl_contrasts"] == 1
    assert primary_family["correction"] == "NONE"
    assert contract["multiple_comparisons"][
        "disjunctive_at_least_one_dataset_claim_allowed"
    ] is False

    seeds = contract["seed_policy"]
    assert seeds["stochastic_core_seeds"] == [42, 43, 44]
    assert seeds["select_best_seed_allowed"] is False
    assert seeds["bootstrap_resamples_seeds"] is False
    assert seeds["bootstrap_and_seed_variability_reported_separately"] is True

    kt3 = contract["kt3_sequence_destruction"]
    assert kt3["practical_margin"] == "reuse_dataset_specific_delta"
    assert kt3["transformation_seeds"] == [42, 43, 44]
    assert kt3["no_op_units_retained_in_primary_population"] is True

    test_policy = contract["test_policy"]
    assert test_policy == {
        "physical_test_generation_or_opening_before_human_margin_approval": False,
        "human_margin_approval_completed": True,
        "scientific_test_accessed_at_approval": False,
        "test_used_for_delta": False,
        "test_used_for_baseline_selection": False,
        "test_used_for_hyperparameters": False,
        "test_used_for_bootstrap_design": False,
        "test_used_for_comparison_family": False,
        "test_used_for_decision_boundary": False,
    }
    assert (PROJECT_ROOT / "docs" / "statistical-decision-contract.md").is_file()
    assert (PROJECT_ROOT / "docs" / "references" / "EFFECT-001-citations.md").is_file()
