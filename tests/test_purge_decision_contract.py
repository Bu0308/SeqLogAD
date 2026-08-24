"""PURGE-DECISION-001 frozen-contract regression tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _yaml(relative: str) -> dict:
    return yaml.safe_load((PROJECT_ROOT / relative).read_text(encoding="utf-8"))


def test_purge_decision_identity_is_canonical_and_frozen() -> None:
    decision = _yaml("configs/protocols/purge-decision-v1.yaml")["purge_decision"]
    payload = decision["identity_payload"]
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    assert payload["decision_status"] == "FROZEN_HUMAN_APPROVED"
    assert payload["approval_source"] == "HUMAN_RESEARCHER"
    assert payload["approval_timing"] == "PRE_SCIENTIFIC_EXPERIMENT"
    assert payload["result_informed"] is False
    assert hashlib.sha256(canonical).hexdigest() == decision["decision_identity"][
        "payload_sha256"
    ]


def test_primary_hdfs_identities_parser_and_effect_are_unchanged() -> None:
    payload = _yaml("configs/protocols/purge-decision-v1.yaml")["purge_decision"][
        "identity_payload"
    ]
    evidence = payload["evidence_identity"]
    primary = payload["primary_hdfs_protocol"]
    effect = _yaml("configs/protocols/effect-001.yaml")

    assert evidence["split_payload_hash"] == (
        "21ec061a7717cd03e7648e3d89200d486bce81eb7dd1bf4114272dd90fc4295c"
    )
    assert evidence["test_partition_hash"] == (
        "fa0c743619f8e2f7ef82a3cb2057eb99891515d56b0aa87f168c60bec093175d"
    )
    assert evidence["parser_state_sha256"] == (
        "7d9bd8041d00ee3a1ce6c32d8e19efd8764108d8695f559ec91b4381ecda8d91"
    )
    assert primary["status"] == "FROZEN_UNCHANGED"
    assert primary["split_regeneration_allowed"] is False
    assert primary["parser_refit_allowed"] is False
    assert primary["effect_001_change_allowed"] is False
    assert effect["practical_effect"]["hdfs"]["delta_ap"] == 0.01
    assert effect["practical_effect"]["bgl"]["delta_ap"] == 0.01


def test_secondary_sensitivity_is_preregistered_nonselection_and_not_run() -> None:
    payload = _yaml("configs/protocols/purge-decision-v1.yaml")["purge_decision"][
        "identity_payload"
    ]
    sensitivity = payload["secondary_purge_sensitivity"]
    assert sensitivity["status"] == "PRE_REGISTERED_SECONDARY_NOT_RUN"
    assert sensitivity["role"] == "ROBUSTNESS_ONLY"
    assert sensitivity["confirmatory"] is False
    assert sensitivity["selection_allowed"] is False
    assert sensitivity["tuning_allowed"] is False
    assert sensitivity["execution"]["status"] == "NOT_RUN"
    assert sensitivity["execution"]["use_to_rewrite_primary_result"] is False
    assert sensitivity["execution"]["scientific_test_membership_access_allowed"] is False
    assert sensitivity["artifact_policy"]["artifacts_created_by_this_task"] is False


def test_test_seals_remain_closed_and_canonical_event_is_next() -> None:
    contract = _yaml("configs/protocols/purge-decision-v1.yaml")["purge_decision"]
    payload = contract["identity_payload"]
    active = _yaml("configs/active-state.yaml")

    assert payload["test_integrity"] == {
        "status": "SEALED",
        "never_opened": True,
        "open_count": 0,
        "unlock_records": 0,
    }
    assert payload["next_authorized_task"] == "CANONICAL-EVENT-001"
    assert active["active_state"]["next_scientific_task"] == "CANONICAL-EVENT-001"
    for dataset in active["datasets"].values():
        split = dataset["split"]
        assert split["test_status"] == "SEALED"
        assert split["never_opened"] is True
        assert split["open_count"] == 0
        assert split["unlock_records"] == 0


def test_decision_references_exist_and_payload_has_no_private_path() -> None:
    decision = _yaml("configs/protocols/purge-decision-v1.yaml")["purge_decision"]
    for field in ("human_readable_record", "citation_note"):
        assert (PROJECT_ROOT / decision[field]).is_file()
    text = (PROJECT_ROOT / "configs/protocols/purge-decision-v1.yaml").read_text(
        encoding="utf-8"
    )
    assert "/Users/" not in text
