"""Regression guards for the forward v2 protocol and migration boundary."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str) -> dict:
    return yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))


def test_v2_protocol_is_forward_planning_contract() -> None:
    protocol = _load("configs/protocols/protocol-v2-domain-adaptive-fusion.yaml")
    meta = protocol["protocol"]
    assert meta["id"] == "DOMAIN-ADAPTIVE-FUSION-001"
    assert meta["version"] == "2.0"
    assert meta["status"] == "PLANNED_USER_APPROVED"
    assert meta["empirical_status"] == "NOT_RUN"
    assert meta["execution_ready"] is False
    assert meta["legacy_foundation"] == "configs/protocols/protocol-v1.1.yaml"


def test_v2_boundaries_and_fixed_model_stack_are_explicit() -> None:
    protocol = _load("configs/protocols/protocol-v2-domain-adaptive-fusion.yaml")
    data = protocol["data_and_folds"]
    assert data["minimum_source_architectures"] >= 3
    assert data["fold_strategy"] == "LEAVE_ONE_ARCHITECTURE_OUT"
    assert data["mixed_system_random_split_allowed"] is False
    assert data["target_labels_in_adaptation"] is False
    assert data["target_labels_in_calibration"] is False
    assert data["target_labels_in_final_evaluation_only"] is True

    experts = protocol["experts"]
    assert experts["semantic"]["adapter"] == "LoRA-Semantic"
    assert experts["sequence"]["adapter"] == "LoRA-Sequence"
    assert experts["semantic"]["checkpoint_independent"] is True
    assert experts["sequence"]["checkpoint_independent"] is True
    assert experts["structural_time"]["model"] == "Temporal_Graph_Transformer_GTAT"
    assert protocol["fusion"]["mandatory_comparator"] == "EQUAL_WEIGHT_FUSION"


def test_active_state_points_to_v2_without_rewriting_v1_1_foundation() -> None:
    state = _load("configs/active-state.yaml")["active_state"]
    contract = state["implementation_contract"]
    assert contract["protocol"] == "configs/protocols/protocol-v2-domain-adaptive-fusion.yaml"
    assert contract["relationship_to_plan"] == "AGREES_WITH_WORKBOOK_SUBORDINATE_TO_IT"
    assert state["scientific_results_status"] == "NOT_RUN"
    assert state["historical_foundation"]["status"] == "SUPERSEDED_HISTORICAL_PROVENANCE"


def test_collection_contract_cannot_change_scientific_inputs() -> None:
    collection = _load("configs/collection/v2.yaml")["collection"]
    assert collection["protocol"] == "configs/protocols/protocol-v2-domain-adaptive-fusion.yaml"
    assert collection["append_only"] is True
    assert collection["raw_events_included"] is False
    assert collection["target_labels_allowed"] == "FINAL_EVALUATION_ONLY"
    assert collection["validation"]["reject_orphan_references"] is True
