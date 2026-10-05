"""Resolved versioned P2.2 seed-42 Sequence candidate configuration."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import yaml


MODEL = "meta-llama/Llama-3.1-8B"
REVISION = "d04e592bb4f6aa9cfee91e2e20afa771667e1d4b"
TARGETS = {"HDFS", "BGL", "HADOOP"}


def identity(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def development_run_id(fold_id, seed=42, candidate="v12"):
    target = fold_id.removeprefix("FOLD-TARGET-ARCH-")
    if target not in TARGETS or seed != 42 or candidate not in {"v12", "v13", "v13r1"}:
        raise ValueError("P2.2 development run is locked to seed 42 and three target folds")
    return f"P2.2-DEVELOPMENT-{target}-S42-{candidate.upper()}"


def load_config(repo_root, overrides=None, run_mode="development", candidate="v12"):
    root = Path(repo_root)
    if candidate not in {"v12", "v13", "v13r1"}:
        raise ValueError("unknown Sequence candidate")
    cfg = yaml.safe_load((root / f"configs/models/sequence-reference-{candidate}.yaml").read_text())["sequence_reference"]
    base = yaml.safe_load((root / cfg["base_contract"]).read_text())["base_freeze"]
    if run_mode != "development" or cfg.get("run_mode") != "development":
        raise ValueError("P2.2 S42 supports only the frozen development mode")
    if base["status"] != "PASS" or not base["model"]["base_weights_immutable"]:
        raise ValueError("base freeze not ready")
    if not base["peft"]["adapter_isolation"] or base["peft"]["share_adapter_weights"]:
        raise ValueError("adapter isolation contract changed")
    fields = base["required_metadata"]
    expected = {
        "base_model_identifier": MODEL,
        "tokenizer_identifier": MODEL,
        "model_revision_commit": REVISION,
        "tokenizer_revision_commit": REVISION,
    }
    if any(fields[key] != value for key, value in expected.items()):
        raise ValueError("frozen base identity changed")
    cfg = deepcopy(cfg)
    allowed = {"seed", "training_mode"}
    if set(overrides or {}) - allowed:
        raise ValueError("P2.2 development accepts only seed/training-mode overrides")
    cfg.update(overrides or {})
    if cfg["seed"] != 42:
        raise ValueError("P2.2 development seed is locked to 42")
    modes = [base["quantization"]["default_training_mode"], base["quantization"]["low_memory_mode"]]
    if cfg["training_mode"] not in modes:
        raise ValueError("unfrozen P2.2 training mode")
    limit = 1024 if cfg["training_mode"] == modes[1] else 2048
    if not 64 <= cfg["context_length"] <= limit:
        raise ValueError("invalid sequence context length")
    integers = [
        "rank", "alpha", "gradient_accumulation_steps", "max_steps", "warmup_steps",
        "save_steps", "validation_steps", "train_windows_per_source",
        "validation_windows_per_source", "early_stopping_patience",
    ]
    if any(not isinstance(cfg[key], int) or cfg[key] <= 0 for key in integers):
        raise ValueError("invalid positive integer in P2.2 config")
    if cfg["save_steps"] != cfg["validation_steps"]:
        raise ValueError("P2.2 checkpoint and validation cadence must coincide")
    if cfg["objective"] != "CAUSAL_NEXT_LOG_TARGET_TOKEN_NLL":
        raise ValueError("unexpected P2.2 objective")
    if cfg["version"] != {"v12": "1.2", "v13": "1.3", "v13r1": "1.3.1"}[candidate] or cfg["context_policy"]["crop_policy"] != (
        "DROP_OLDEST_WHOLE_CONTEXT_RECORD_THEN_DECREASE_TARGET_WORD_PREFIX"
    ):
        raise ValueError("unexpected P2.2 encoding variant")
    views = cfg.get("training_context_views", {})
    if views != {
        "policy": "CAUSAL_SUFFIX_MULTI_SCALE",
        "short_lengths": [1, 2, 4],
        "full_context_probability": 0.5,
        "validation_and_inference": "FULL_AVAILABLE_CONTEXT_ONLY",
    } or cfg.get("use_rslora") is not True:
        raise ValueError("unexpected P2.2 V12 adaptation variant")
    if cfg["adapter_name"] != "sequence" or cfg["expert_id"] != "SEQUENCE_LLAMA_REFERENCE":
        raise ValueError("P2.2 expert/adapter identity changed")
    expected_label_status = ("UNRESOLVED_DENY" if candidate == "v12"
                             else "SOURCE_VALIDATION_MODEL_SELECTION_ONLY")
    if cfg["source_label_status"] != expected_label_status or cfg["clean_normal_claim"]:
        raise ValueError("P2.2 label/normality policy changed")
    if candidate in {"v13", "v13r1"}:
        if cfg["checkpoint_selection"] != "MAX_MACRO_SOURCE_DEVELOPMENT_F1":
            raise ValueError("V13 must select checkpoints by labeled source-development F1")
        development = cfg.get("source_development", {})
        if (development.get("permitted_architectures") != ["ARCH-BGL", "ARCH-HDFS"]
                or development.get("partition") != "SOURCE_VALIDATION"
                or development.get("training_labels_allowed") is not False
                or development.get("held_out_target_labels_allowed") is not False
                or development.get("bgl_unit") != "TARGET_LOG_LINE"
                or development.get("hdfs_unit") != "BLOCK_TRACE"
                or development.get("unit_score_aggregation") != "MEAN_OF_SELECTED_WINDOW_NLL"
                or development.get("threshold_selection") != "MAX_F1_HIGHEST_THRESHOLD_ON_TIE_PER_SOURCE"
                or development.get("macro_aggregation") != "EQUAL_WEIGHT_PER_AVAILABLE_LABELED_SOURCE"
                or development.get("metrics") != ["accuracy", "precision", "recall", "f1", "auroc", "average_precision"]):
            raise ValueError("V13 source-development boundary changed")
    if cfg["numerical_failure_policy"] != "ABORT_NO_SKIPPED_UPDATES":
        raise ValueError("P2.2 numerical guard must remain enabled")
    cfg.update(
        model_id=MODEL,
        model_revision=REVISION,
        tokenizer_id=MODEL,
        tokenizer_revision=REVISION,
        base_config_sha256=hashlib.sha256(
            (root / "configs/models/base-freeze-v1.yaml").read_bytes()
        ).hexdigest(),
    )
    return cfg, base
