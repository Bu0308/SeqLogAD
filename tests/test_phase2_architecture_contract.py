"""P2.0 declarative guards; not evidence of model or GPU-runtime correctness."""

from pathlib import Path, PurePosixPath

import pytest
import yaml

from seqlogad.protocol.labels import LabelAccessDeniedError, open_labels

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs/protocols/phase2-architecture-v1.yaml"
P2 = yaml.safe_load(CONTRACT.read_text())["phase2"]


def test_roles_and_sequence_candidates_cannot_collapse() -> None:
    experts = P2["experts"]
    ids = [e["id"] for e in experts]
    assert len(ids) == len(set(ids)) == 4
    roles = {e["id"]: e["role"] for e in experts}
    assert roles == {
        "SEMANTIC_LLAMA": "SEMANTIC",
        "SEQUENCE_LLAMA_REFERENCE": "SEQUENCE",
        "SEQUENCE_LIGHTWEIGHT": "SEQUENCE",
        "GTAT_STRUCTURAL_TEMPORAL": "STRUCTURAL_TEMPORAL",
    }
    by_id = {e["id"]: e for e in experts}
    assert by_id["SEQUENCE_LLAMA_REFERENCE"]["status"] == "REFERENCE_CANDIDATE"
    assert by_id["SEQUENCE_LLAMA_REFERENCE"]["adapter"] == "LoRA-Sequence"
    assert by_id["SEQUENCE_LIGHTWEIGHT"]["status"] == "REQUIRED_CANDIDATE_SLOT"
    assert P2["sequence_winner"] == "UNDECIDED"
    assert P2["gtat_satisfies_sequence_role"] is False
    assert all(e["primary_objective"] for e in experts)
    assert P2["adapter_policy"]["share_adapter_weights"] is False
    assert P2["adapter_policy"]["share_adaptation_checkpoints"] is False


@pytest.mark.parametrize("expert", P2["experts"], ids=lambda e: e["id"])
def test_each_expert_has_fail_closed_access(expert: dict) -> None:
    access = P2["access_profiles"][expert["access_profile"]]
    assert access["anomaly_labels"] is False
    assert access["representation_training"] == ["SOURCE_TRAIN"]
    assert access["reference_fit"] == ["SOURCE_TRAIN"]
    assert access["learned_feature_fit"] == ["SOURCE_TRAIN"]
    assert access["checkpoint_selection"] == ["SOURCE_VALIDATION"]
    assert access["hyperparameter_search"] == ["SOURCE_VALIDATION"]
    assert access["threshold_selection"] == access["calibration"] == []
    for operation in ("sequence_construction", "graph_construction", "normalization_apply"):
        assert access[operation] == ["SOURCE_TRAIN", "SOURCE_VALIDATION"]
    assert {"TARGET_BURN_IN", "TARGET_EVALUATION", "GUARD", "EXCLUDED", "SOURCE_LATE"} == set(access["forbidden_partitions"])
    assert access["synthetic_controls_for_training_or_selection"] is False


@pytest.mark.parametrize("scope", ["TRAINING", "MODEL_SELECTION", "SOURCE_VALIDATION", "SOURCE_EVALUATION"])
def test_existing_label_boundary_is_not_bypassed(scope: str, tmp_path: Path) -> None:
    with pytest.raises(LabelAccessDeniedError):
        list(open_labels(tmp_path, "ARCH-HDFS", scope=scope, reason="P2.0 negative contract test"))
    assert not (tmp_path / "data/processed/protocol/label-access-audit.jsonl").exists()


def test_future_phases_and_scientific_claims_are_not_activated() -> None:
    assert P2["execution_ready"] is P2["training_authorized"] is P2["phase3_enabled"] is False
    assert P2["scientific_results"] == "NOT_RUN"
    evaluation = P2["evaluation"]
    assert evaluation["target_inputs"] == []
    assert evaluation["anomaly_label_access"] is False
    assert evaluation["adaptive_fusion"] is evaluation["g2_auto_pass"] is False
    assert evaluation["synthetic_results_are_natural_anomaly_results"] is False
    assert evaluation["supervised_metrics_status"] == "BLOCKED_PENDING_SOURCE_EVALUATION_SCOPE"
    assert P2["source_label_scope"] == "UNRESOLVED_DENY"


def test_data_paths_and_dependency_closure_conventions() -> None:
    data = P2["portability"]
    assert data["data_root"] == "data/phase2"
    assert data["train_partition"] == data["reference_partition"] == "SOURCE_TRAIN"
    assert data["val_partition"] == "SOURCE_VALIDATION"
    for field in ("evaluation_in_training_bundle", "labels_in_training_bundle", "raw_data_required_on_gpu_host", "external_symlinks_allowed", "absolute_manifest_paths_allowed"):
        assert data[field] is False
    paths = [data["data_root"], data["fold_root"], data["evaluator_root"]]
    paths += data["required_bundle_files"] + data["required_fold_files"]
    for view in data["views"].values():
        paths += view["required"] + view["optional"]
        assert set(view["required"]).isdisjoint(view["optional"])
        assert "metadata/view.json" in view["required"]
    for path in paths:
        parsed = PurePosixPath(path)
        assert not parsed.is_absolute() and ".." not in parsed.parts
        assert "\\" not in path and "~" not in path
    assert not PurePosixPath(data["evaluator_root"]).is_relative_to(data["data_root"])
    assert data["views"]["sequence"]["shared_by"] == P2["evaluation"]["comparison_candidates"]
    assert {"dataset_id", "architecture_id", "partition", "sample_count", "record_count", "schema_version", "sha256", "membership_sha256", "stream_index_sha256", "target_labels_read", "label_columns", "provenance"} <= set(data["manifest_required_fields"])


def test_notebooks_are_mandatory_future_deliverables() -> None:
    spec = P2["notebooks"]
    assert spec["mandatory_for_every_real_training_task"] is True
    assert spec["implementation_owner"] == "PYTHON_MODULES"
    assert {"DATA_ROOT", "OUTPUT_ROOT", "SEED", "FOLD_ID", "RESUME_FROM", "MODEL_REVISION", "TOKENIZER_REVISION"} <= set(spec["required_config_keys"])
    paths = [expert["notebook"] for expert in P2["experts"]]
    assert len(paths) == len(set(paths))
    for expert in P2["experts"]:
        path = PurePosixPath(expert["notebook"])
        assert path.parent == PurePosixPath("notebooks") and path.suffix == ".ipynb"
        assert path.name.startswith(expert["training_task"] + "_")
    assert {"checkpoints", "config.yaml", "metrics.json", "logs", "manifest.json", "environment.json"} <= set(spec["required_run_artifacts"])


def test_task_namespace_is_explicit_until_migration() -> None:
    assert P2["task_namespace"] == "P2_ARCH_V1"
    assert P2["routing_migration"] == "COMPLETE"
    assert list(P2["tasks"]) == ["P2.PRE"] + [f"P2.{i}" for i in range(1, 8)]
    visited = {"P1.8"}
    for task_id, task in P2["tasks"].items():
        assert set(task["depends_on"]) <= visited
        visited.add(task_id)
    assert (ROOT / P2["document"]).is_file()


def test_controls_and_evidence_do_not_promise_calibration() -> None:
    assert set(P2["sequence_controls"]) == {"event_permutation", "missing_event", "duplicate_event", "unexpected_next_event", "long_range_dependency_violation", "locally_plausible_globally_invalid"}
    evidence = P2["evidence"]
    assert evidence["score_calibrated_in_phase2"] is None
    assert evidence["unknown_uncertainty"] is None
    assert evidence["calibration_status_in_phase2"] == "NOT_CALIBRATED"
    assert evidence["evidence_is_causal_proof"] is False
    assert {"expert_id", "expert_role", "record_ids", "input_manifest_sha256", "checkpoint_sha256", "context_config_sha256", "coverage", "status", "reason"} <= set(evidence["required_fields"])


def test_task_execution_and_future_preflight_cannot_be_skipped() -> None:
    for task_id, task in P2["tasks"].items():
        assert task["execution_authorized"] is (task_id in {"P2.PRE", "P2.1"})
        assert "ROUTING_MIGRATION" not in task["blockers"]
    assert P2["tasks"]["P2.PRE"]["status"] == "PASS"
    assert P2["tasks"]["P2.1"]["blockers"] == []
    assert "GTAT_SPECIFICATION_BEFORE_TRAINING" in P2["tasks"]["P2.4"]["blockers"]
    preflight = P2["implementation_preflight"]
    assert preflight["required_before_materialization_or_training"] is True
    assert preflight["forbid_label_inventory_as_model_input"] is True
    assert preflight["provenance_is_predictive_feature"] is False
    assert {"file_allowlist", "column_allowlist", "fold_membership", "source_role_only", "checksum_and_counts", "reference_closure", "no_cross_fold_cache"} <= set(preflight["verify"])
    assert set(preflight["feature_allowlists"]) == {"semantic", "sequence", "graph"}
    freeze = P2["final_freeze"]
    assert freeze["retain_reference_checkpoint_and_evidence"] is True
    assert freeze["gtat_can_fill_sequence_slot"] is False
    assert freeze["requires_executed_manifest_preflight"] is True
    assert freeze["sequence_candidate_ids"] == P2["portability"]["views"]["sequence"]["shared_by"]
