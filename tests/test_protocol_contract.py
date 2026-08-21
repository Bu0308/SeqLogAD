"""Regression guards for the active and historical scientific protocols."""

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_PATH = PROJECT_ROOT / "configs" / "protocols" / "protocol-v1.1.yaml"
HISTORICAL_PATH = PROJECT_ROOT / "configs" / "protocols" / "protocol-v1.yaml"


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
    assert labels["test_physically_sealed"] is False
    assert labels["test_execution_owner"] == "HUMAN"
    assert labels["test_execution_count"] == 1

    assert protocol["datasets"]["hdfs"]["grouping_unit"] == "block_session"
    assert protocol["datasets"]["hdfs"]["boundary_policy"] == "PURGED_BOUNDARY"
    assert protocol["datasets"]["bgl"]["parent_window_events"] == 100
    assert protocol["datasets"]["bgl"]["overlap"] == 0
    assert protocol["parser"]["fit_partition"] == "BASE_TRAIN"
    assert protocol["parser"]["fit_normal_only"] is True
    assert protocol["parser"]["freeze_after_fit"] is True


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
