"""CANONICAL-NUL-DECISION-001 proposal and freeze-boundary tests.

These tests validate only the non-binding decision contract. They do not
implement the codec, read scientific TEST, or generate a canonical corpus.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/protocols/canonical-nul-decision-v1.yaml"


def _yaml(relative: str) -> dict:
    return yaml.safe_load((PROJECT_ROOT / relative).read_text(encoding="utf-8"))


def _contract() -> dict:
    return _yaml("configs/protocols/canonical-nul-decision-v1.yaml")[
        "canonical_nul_decision"
    ]


def test_proposal_identity_is_deterministic_and_not_human_approved() -> None:
    contract = _contract()
    payload = contract["identity_payload"]
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    assert payload["decision_status"] == "FROZEN_HUMAN_REVIEW_READY"
    assert payload["approval_status"] == "PENDING_HUMAN_APPROVAL"
    assert payload["approval_source"] is None
    assert payload["result_informed"] is False
    assert payload["authority_scope"]["implementation_authorized"] is False
    assert payload["authority_scope"]["real_corpus_generation_authorized"] is False
    assert hashlib.sha256(canonical).hexdigest() == contract["decision_identity"][
        "payload_sha256"
    ]


def test_verified_finding_is_narrow_non_test_and_exact() -> None:
    finding = _contract()["identity_payload"]["verified_non_test_finding"]

    assert finding["test_membership_loader_used"] is False
    assert finding["searched_partitions"] == [
        "BASE_TRAIN",
        "FUSION_TRAIN",
        "VAL_EXPERT",
        "VAL_FUSION",
    ]
    assert finding["affected_source_line_numbers"] == [
        4223248,
        4223278,
        4224013,
        4224014,
    ]
    assert finding["affected_partition"] == "VAL_FUSION"
    assert finding["affected_parent_count"] == 3
    assert finding["nul_bytes_per_affected_line"] == 1
    assert len(finding["affected_records"]) == 4
    assert all(record["partition"] == "VAL_FUSION" for record in finding["affected_records"])


def test_option_a_preserves_frozen_population_and_parser_contract() -> None:
    payload = _contract()["identity_payload"]
    option = payload["options"]["option_a"]
    selected = payload["selected_policy"]
    parser = payload["parser_contract"]
    population = payload["population_and_leakage"]

    assert selected["option_id"] == "OPTION_A"
    assert selected["policy_version"] == "seqlogad-nul-escape-v1"
    assert option["scientific_population_changed"] is False
    assert option["one_line_one_event"] is True
    assert option["parser_refit_required"] is False
    assert population["bgl_parent_cardinality"] == 100
    assert population["split_membership_changed"] is False
    assert population["test_identity_changed"] is False
    assert population["labels_used"] is False
    assert parser["version"] == "0.9.11"
    assert parser["mode"] == "RESTORE_ONLY"
    assert parser["update"] == "FORBIDDEN"
    assert parser["no_match_fallback"] == "EVT_UNSEEN"
    assert parser["parser_state_change"] is False
    assert parser["template_registry_change"] is False


def test_codec_contract_is_typed_collision_safe_and_content_only() -> None:
    selected = _contract()["identity_payload"]["selected_policy"]
    transform = selected["transform"]
    collision = selected["collision_contract"]

    assert selected["inputs_allowed"] == ["raw_message_bytes"]
    assert set(selected["inputs_forbidden"]) == {
        "anomaly_label",
        "partition_id",
        "parent_id",
        "test_outcome",
        "model_result",
    }
    assert transform["escape_introducer_hex"] == "5c"
    assert transform["nul_encoding_hex"] == "5c783030"
    assert transform["reversibility"] == (
        "decoder_is_selected_only_when_status_is_NUL_ESCAPED"
    )
    assert transform["malformed_escape_policy"] == "REJECT"
    assert collision["original_backslash_is_escaped_when_and_only_when_NUL_ESCAPED"] is True
    assert collision["literal_backslash_x00_is_not_equivalent_to_raw_NUL"] is True
    assert collision["identity_components"] == [
        "policy_version",
        "normalization_status",
        "canonical_message",
        "raw_message_sha256",
    ]


def test_versioning_boundary_does_not_change_event_or_parser_identity() -> None:
    versioning = _contract()["identity_payload"]["versioning"]

    assert versioning["protocol_v1_1"] == "UNCHANGED"
    assert versioning["event_template_schema"] == "1.0"
    assert versioning["event_template_schema_change"] is False
    assert versioning["log_event_schema"] == "1.0"
    assert versioning["log_event_schema_change"] is False
    assert versioning["parser_normalization_version"] == "seqlogad-message-v1"
    assert versioning["parser_normalization_version_change"] is False
    assert versioning["canonical_artifact_envelope_after_approval"] == "1.1"
    assert versioning["binding_status_before_human_approval"] == (
        "NON_BINDING_PROPOSAL"
    )


def test_all_twenty_future_tests_and_acceptance_contract_are_frozen() -> None:
    payload = _contract()["identity_payload"]
    required = payload["required_resume_tests"]
    acceptance = payload["acceptance_test"]

    assert list(required) == [f"T{index}" for index in range(1, 21)]
    assert acceptance["scope"] == "SYNTHETIC_NON_TEST_100_EVENT_BGL_PARENT"
    assert acceptance["input_events"] == 100
    assert acceptance["output_events"] == 100
    assert acceptance["silent_drop"] is False
    assert acceptance["parser_mutation"] is False


def test_active_state_records_the_nul_policy_as_a_reused_decision() -> None:
    """The workbook migration adopts Option A verbatim rather than reopening it."""

    state = _yaml("configs/active-state.yaml")["active_state"]
    reused = state["reused_decisions"]["CANONICAL-NUL-DECISION-001"]
    assert reused["classification"] == "REUSE_WITH_EXISTING_DECISION"
    assert reused["policy_version"] == "seqlogad-nul-escape-v1"
    assert state["phase_1_contracts"]["nul_policy"] == (
        "configs/protocols/canonical-nul-decision-v1.yaml"
    )

def test_test_integrity_and_frozen_bgl_identities_are_unchanged() -> None:
    payload = _contract()["identity_payload"]
    test_integrity = payload["test_integrity"]
    identities = payload["frozen_identities"]

    assert test_integrity == {
        "hdfs_status": "SEALED",
        "bgl_status": "SEALED",
        "never_opened": True,
        "open_count": 0,
        "unlock_records": 0,
        "test_search_performed": False,
        "test_artifact_generated": False,
    }
    assert identities["bgl_dataset_fingerprint"] == (
        "c9ee7a8db13d37c88f896e305ed12dc7a66b586cdae4e388db4949f78afbe861"
    )
    assert identities["bgl_split_payload_hash"] == (
        "0c1bb1b9b755aa2aa50238771cf5bf34649e1ca33c7964e061766b659aeebd05"
    )
    assert identities["bgl_test_partition_hash"] == (
        "7ecf43ab27d6519b7af4ae4e8f7be5cd9d5351c8c11d18b3bd11b4ff896a876d"
    )
    assert identities["bgl_parser_state_sha256"] == (
        "e44649d24afbd4bc335e2d38d54cea9338c211c600baef185cd7a0dee6aee4f6"
    )
    assert identities["bgl_template_registry_sha256"] == (
        "bc4ac9e2c6ea51e712ed06c0648372d6ed800f2788d135cd5cc89d7d1047d17f"
    )


def test_proposal_references_exist_and_have_no_private_path() -> None:
    contract = _contract()
    for field in ("human_readable_record", "citation_record"):
        assert (PROJECT_ROOT / contract[field]).is_file()

    scoped_paths = [
        CONTRACT_PATH,
        PROJECT_ROOT / contract["human_readable_record"],
        PROJECT_ROOT / contract["citation_record"],
    ]
    for path in scoped_paths:
        assert "/Users/" not in path.read_text(encoding="utf-8")
