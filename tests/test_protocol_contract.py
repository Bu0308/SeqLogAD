"""Regression guard for the human-approved PROTOCOL-001 contract."""

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = PROJECT_ROOT / "configs" / "protocols" / "protocol-v1.yaml"


def test_protocol_001_frozen_decisions() -> None:
    """Critical scientific decisions must not drift through incidental edits."""

    protocol = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))

    assert protocol["protocol"]["id"] == "PROTOCOL-001"
    assert protocol["protocol"]["version"] == "1.0"
    assert protocol["protocol"]["status"] == "FROZEN_HUMAN_APPROVED"
    assert protocol["protocol"]["empirical_status"] == "NOT_RUN"

    ratios = protocol["partitions"]["ratios"]
    assert ratios == {
        "BASE_TRAIN": 0.60,
        "FUSION_TRAIN": 0.10,
        "VAL_EXPERT": 0.10,
        "VAL_FUSION": 0.10,
        "TEST": 0.10,
    }
    assert sum(ratios.values()) == 1.0
    assert protocol["partitions"]["strategy"] == "raw_chronological"

    assert protocol["labels"]["test_sealed_until_final_command"] is True
    assert protocol["labels"]["test_execution_owner"] == "HUMAN"
    assert protocol["labels"]["test_execution_count"] == 1
    assert protocol["framing"]["anomaly_labels_as_model_input"] is False
    assert protocol["framing"]["anomaly_labels_in_base_loss"] is False

    assert protocol["hdfs"]["grouping_unit"] == "block_session"
    assert protocol["hdfs"]["boundary_policy"] == "PURGED_BOUNDARY"
    assert protocol["bgl"]["parent_window_events"] == 100
    assert protocol["bgl"]["overlap"] == 0
    assert protocol["parser"]["fit_partition"] == "BASE_TRAIN"
    assert protocol["parser"]["fit_normal_only"] is True
    assert protocol["parser"]["freeze_after_fit"] is True

    assert protocol["training"]["stochastic_report_seeds"] == [42, 43, 44]
    assert protocol["evaluation"]["detection"]["primary_metric"] == "PR_AUC"
    assert protocol["fusion"]["f8_may_fail"] is True
    assert "F0_strongest_single" in protocol["fusion"]["required_comparators"]
    assert protocol["downstream"]["rag_agent_role"] == "frozen_evidence_consumer_only"
