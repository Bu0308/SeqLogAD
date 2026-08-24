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
    ]
    assert [item["path"] for item in protocol["binding_addenda"]] == expected
    assert default["protocol"]["binding_addenda"] == expected
    assert state["protocol_stack"]["binding_addenda"] == expected
    for path in [state["protocol_stack"]["base"], *expected]:
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
    state = _load_yaml("configs/active-state.yaml")["active_state"]
    default = _load_yaml("configs/default.yaml")

    assert state["pipeline"] == {
        "SPLIT-001": "COMPLETE",
        "PARSE-001": "COMPLETE_FROZEN",
        "PURGE-AUDIT-001": "COMPLETE",
        "PURGE-DECISION-001": "HUMAN_DECISION_REQUIRED",
        "CANONICAL-EVENT-001": "NOT_STARTED",
        "SEQ-001": "NOT_STARTED",
        "scientific_experiments": "NOT_RUN",
    }
    assert state["next_scientific_task"] == "PURGE-DECISION-001"
    assert default["pipeline"]["next_scientific_task"] == "PURGE-DECISION-001"
    assert state["repository_hygiene"]["license_status"] == (
        "OWNER_DECISION_REQUIRED"
    )
    assert default["repository_hygiene"]["license_status"] == (
        "OWNER_DECISION_REQUIRED"
    )
    for dataset in _load_yaml("configs/active-state.yaml")["datasets"].values():
        split = dataset["split"]
        assert split["test_status"] == "SEALED"
        assert split["never_opened"] is True
        assert split["open_count"] == 0
        assert split["unlock_records"] == 0


def test_purge_audit_status_is_bound_without_authorizing_split_change() -> None:
    active = _load_yaml("configs/active-state.yaml")
    risk = active["methodological_risks"]["hdfs_boundary_purge"]
    assert risk["status"] == "PURGE_REPRESENTATIVENESS_CONCERN"
    assert risk["interpretation"] == "PLAN_CONFLICT_DETECTED_HUMAN_REVIEW_REQUIRED"
    assert risk["may_change_split"] is False
    assert risk["partition_specific_outcomes_emitted"] is False
    assert risk["test_membership_opened"] is False
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
    assert state["pipeline"]["PARSE-001"] == "COMPLETE_FROZEN"


def test_artifact_pointers_are_portable_and_match_local_artifacts_when_present() -> None:
    active = _load_yaml("configs/active-state.yaml")
    for dataset_key, dataset in active["datasets"].items():
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
        "configs/experiments/detector_baselines.yaml",
        "configs/models/baselines.yaml",
        "Plan/00_MASTER_PLAN.md",
        "Plan/master-implementation-plan-v1.1.md",
        "data/README.md",
        "docs/metadata-extraction-contract.md",
        "src/seqlogad/models/README.md",
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
