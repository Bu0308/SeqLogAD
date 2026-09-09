"""ALIGN-FIX-001 active-state and configuration consistency tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_STATE_PATH = PROJECT_ROOT / "configs" / "active-state.yaml"


def _load_yaml(relative: str) -> dict:
    return yaml.safe_load((PROJECT_ROOT / relative).read_text(encoding="utf-8"))


def _portable(relative: str) -> bool:
    path = PurePosixPath(relative)
    return not path.is_absolute() and ".." not in path.parts


def test_active_protocol_stack_is_explicit_and_resolvable() -> None:
    protocol = _load_yaml("configs/protocols/protocol-v1.1.yaml")
    default = _load_yaml("configs/default.yaml")
    state = _load_yaml("configs/active-state.yaml")["active_state"]

    expected = [
        "configs/protocols/effect-001.yaml",
        "configs/protocols/split-clarification-v1.yaml",
        "configs/protocols/purge-decision-v1.yaml",
    ]
    assert [item["path"] for item in protocol["binding_addenda"]] == expected
    # default.yaml no longer binds the v1.1 addenda: under the workbook they are
    # historical provenance, and the registry is where that is recorded.
    assert "binding_addenda" not in default["protocol"]
    historical = state["historical_foundation"]
    assert historical["status"] == "SUPERSEDED_HISTORICAL_PROVENANCE"
    assert historical["may_control_routing"] is False
    assert historical["addenda"] == expected
    for path in [historical["protocol"], *expected]:
        assert (PROJECT_ROOT / path).is_file()


def test_active_method_and_seed_contract_matches_effect_001() -> None:
    model = _load_yaml("configs/models/baselines.yaml")
    experiment = _load_yaml("configs/experiments/detector_baselines.yaml")
    effect = _load_yaml("configs/protocols/effect-001.yaml")

    isolation_forest = "isolation_forest_order_insensitive"
    assert isolation_forest in model["must"]
    assert isolation_forest in model["required_primary_orderless_candidates"]
    assert isolation_forest not in model["should"]
    assert model["seed_policy"]["stochastic_methods"][isolation_forest] == [
        42,
        43,
        44,
    ]
    assert experiment["seed_policy"]["stochastic_methods"]["isolation_forest"] == [
        42,
        43,
        44,
    ]
    assert effect["seed_policy"]["stochastic_core_seeds"] == [42, 43, 44]
    assert set(model["seed_policy"]["deterministic_methods"].values()) == {
        "NOT_APPLICABLE_DETERMINISTIC"
    }
    assert set(experiment["seed_policy"]["deterministic_methods"].values()) == {
        "NOT_APPLICABLE_DETERMINISTIC"
    }


def test_active_status_next_task_test_state_and_license_are_exact() -> None:
    """The registry routes the workbook and retires the old pointers, without
    disturbing the frozen HDFS/BGL identities it still has to keep verifiable."""

    state = _load_yaml("configs/active-state.yaml")["active_state"]
    default = _load_yaml("configs/default.yaml")

    plan = state["authoritative_plan"]
    assert plan["path"] == "Bang_ke_hoach_SeqLogAD.xlsx"
    assert plan["conflict_rule"] == "THE_WORKBOOK_WINS_OVER_EVERY_OTHER_DOCUMENT"
    assert default["plan"]["authoritative"] == "Bang_ke_hoach_SeqLogAD.xlsx"

    assert state["next_authorized_task"] == "P2.PRE"
    assert default["protocol"]["next_authorized_task"] == "P2.PRE"
    assert default["pipeline"]["next_authorized_task"] == "P2.PRE"
    assert state["scientific_results_status"] == "NOT_RUN"
    assert state["representation_training_status"] == "NOT_STARTED"
    assert state["target_adaptation_status"] == "NOT_STARTED"

    historical = state["historical_foundation"]
    assert historical["status"] == "SUPERSEDED_HISTORICAL_PROVENANCE"
    assert historical["may_control_routing"] is False
    assert historical["retired_artifacts_retained"] is True
    for retired in ("SEQ-001", "THEORY-COMPLETE-001", "KT-1", "EFFECT-001"):
        assert retired in historical["retired_pointers"]

    reused = state["reused_decisions"]["CANONICAL-NUL-DECISION-001"]
    assert reused["classification"] == "REUSE_WITH_EXISTING_DECISION"
    assert reused["policy_version"] == "seqlogad-nul-escape-v1"

    assert state["repository_hygiene"]["license_status"] == "OWNER_DECISION_REQUIRED"
    assert default["repository_hygiene"]["license_status"] == "OWNER_DECISION_REQUIRED"

    # The retired split artifacts are provenance and must stay sealed and untouched.
    for dataset in _load_yaml("configs/active-state.yaml")["historical_datasets"].values():
        split = dataset["split"]
        assert split["test_status"] == "SEALED"
        assert split["never_opened"] is True
        assert split["open_count"] == 0
        assert split["unlock_records"] == 0

def test_purge_decision_resolves_gate_without_authorizing_split_change() -> None:
    active = _load_yaml("configs/active-state.yaml")
    risk = active["historical_methodological_risks"]["hdfs_boundary_purge"]
    assert risk["status"] == "PURGE_REPRESENTATIVENESS_CONCERN"
    assert risk["interpretation"] == (
        "RESOLVED_BY_OPTION_B_PRIMARY_UNCHANGED_SECONDARY_PREREGISTERED"
    )
    assert risk["may_change_split"] is False
    assert risk["partition_specific_outcomes_emitted"] is False
    assert risk["test_membership_opened"] is False
    assert risk["human_disposition"] == (
        "KEEP_FROZEN_PRIMARY_AND_PREREGISTER_SECONDARY_PURGE_SENSITIVITY"
    )
    assert risk["primary_split_status"] == "FROZEN_UNCHANGED"
    assert risk["sensitivity_status"] == "PRE_REGISTERED_SECONDARY_NOT_RUN"
    assert risk["canonical_event_authorized"] is True
    assert risk["current_effective_canonical_event_authorization"] is False
    assert risk["superseding_gate"] == (
        "CANONICAL-NUL-DECISION-001_PENDING_HUMAN_APPROVAL"
    )
    assert risk["decision_payload_sha256"] == (
        "5af8505364c793b2fbd42885ebcdea1eba03b75c808415214af7311aa4ecd177"
    )
    assert risk["audit_payload_sha256"] == (
        "274b62f3a7a6b072aec9e142b3e7e97c1548c08984ebe5240f4dc753ed27eabb"
    )
    artifact_path = PROJECT_ROOT / risk["audit_artifact"]
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["audit_payload_sha256"] == risk["audit_payload_sha256"]
    assert artifact["scientific_payload"]["final_classification"] == risk["status"]


def test_split_snapshot_is_explicitly_historical_after_parse_completion() -> None:
    clarification = _load_yaml("configs/protocols/split-clarification-v1.yaml")[
        "split_clarification"
    ]
    state = _load_yaml("configs/active-state.yaml")["active_state"]

    assert clarification["status"] == "FROZEN_HUMAN_APPROVED"
    assert clarification["status_snapshot_scope"] == (
        "SPLIT_001_AUTHORIZATION_AND_COMPLETION"
    )
    assert clarification["parser_fitted"] is False
    assert clarification["next_authorized_task"] == "PARSE-001"
    assert clarification["current_execution_state"] == "configs/active-state.yaml"
    assert state["historical_foundation"]["status"] == "SUPERSEDED_HISTORICAL_PROVENANCE"


def test_artifact_pointers_are_portable_and_match_local_artifacts_when_present() -> None:
    active = _load_yaml("configs/active-state.yaml")
    for dataset_key, dataset in active["historical_datasets"].items():
        split = dataset["split"]
        parser = dataset["parser"]
        for key in ("directory", "manifest", "test_seal"):
            assert _portable(split[key])
        for key in ("manifest", "state"):
            assert _portable(parser[key])

        split_manifest_path = PROJECT_ROOT / split["manifest"]
        parser_manifest_path = PROJECT_ROOT / parser["manifest"]
        seal_path = PROJECT_ROOT / split["test_seal"]
        if not all(path.is_file() for path in (split_manifest_path, parser_manifest_path, seal_path)):
            # Generated artifacts are intentionally absent from clean CI checkouts.
            continue

        split_manifest = json.loads(split_manifest_path.read_text(encoding="utf-8"))
        parser_manifest = json.loads(parser_manifest_path.read_text(encoding="utf-8"))
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
        assert split_manifest["dataset"]["key"] == dataset_key
        assert split_manifest["dataset"]["dataset_fingerprint"] == dataset[
            "dataset_fingerprint"
        ]
        assert split_manifest["identity"]["split_payload_hash"] == split[
            "split_payload_hash"
        ]
        assert split_manifest["identity"]["partition_hashes"]["BASE_TRAIN"] == split[
            "base_train_partition_hash"
        ]
        assert split_manifest["identity"]["partition_hashes"]["TEST"] == split[
            "test_partition_hash"
        ]
        assert parser_manifest["identity"]["parser_state_sha256"] == parser[
            "parser_state_sha256"
        ]
        assert hashlib.sha256(parser_manifest_path.read_bytes()).hexdigest() == parser[
            "manifest_sha256"
        ]
        assert seal["status"] == "SEALED"
        assert seal["never_opened"] is True
        assert seal["open_count"] == 0
        assert seal["unlock_records"] == 0


def test_active_configs_have_no_private_paths_or_stale_execution_todos() -> None:
    config_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((PROJECT_ROOT / "configs").rglob("*.yaml"))
    )
    assert "/Users/" not in config_text

    active_files = [
        "configs/default.yaml",
        "configs/parsing/normalizer-cs-v1.yaml",
        "configs/protocols/cross-system-split-v1.yaml",
        "configs/protocols/target-buffer-v1.yaml",
        "configs/protocols/leak-cs-001-exceptions.yaml",
        "configs/plan/excel-roadmap-v1.yaml",
        "Plan/00_MASTER_PLAN.md",
        "Plan/master-implementation-plan-v1.1.md",
        "data/README.md",
        "docs/metadata-extraction-contract.md",
        "docs/protocol/PHASE-1-RECORD.md",
    ]
    active_text = "\n".join(
        (PROJECT_ROOT / path).read_text(encoding="utf-8") for path in active_files
    )
    for stale in (
        "TODO_FIVE_WAY_SPLIT",
        "seed: TODO",
        "No parser run",
        "split guard not implemented",
        "Isolation Forest | SHOULD",
    ):
        assert stale not in active_text
