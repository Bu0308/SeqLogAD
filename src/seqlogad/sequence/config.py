"""Resolved immutable P2.2 seed-42 development configuration."""
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


def development_run_id(fold_id, seed=42):
    target = fold_id.removeprefix("FOLD-TARGET-ARCH-")
    if target not in TARGETS or seed != 42:
        raise ValueError("P2.2 development run is locked to seed 42 and three target folds")
    return f"P2.2-DEVELOPMENT-{target}-S42"


def load_config(repo_root, overrides=None, run_mode="development"):
    root = Path(repo_root)
    cfg = yaml.safe_load((root / "configs/models/sequence-reference-v1.yaml").read_text())["sequence_reference"]
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
    if cfg["adapter_name"] != "sequence" or cfg["expert_id"] != "SEQUENCE_LLAMA_REFERENCE":
        raise ValueError("P2.2 expert/adapter identity changed")
    if cfg["source_label_status"] != "UNRESOLVED_DENY" or cfg["clean_normal_claim"]:
        raise ValueError("P2.2 label/normality policy changed")
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
