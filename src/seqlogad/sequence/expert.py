"""Standalone Sequence-LoRA scorer independent from Semantic and fusion state."""
from __future__ import annotations

from pathlib import Path

from seqlogad.common.checksum import sha256_file
from seqlogad.semantic.checkpoint import verify_checkpoint
from seqlogad.semantic.contracts import read

from .config import load_config
from .model import load_model
from .scoring import score_next_log
from .implementation import implementation_digest


def assert_encoding_compatible(checkpoint_config, reference_config):
    for key in (
        "version", "context_policy", "context_length", "objective",
        "use_rslora", "training_context_views", "rank", "alpha",
    ):
        if checkpoint_config[key] != reference_config[key]:
            raise ValueError("Sequence checkpoint encoding variant mismatch")
    for key in ("checkpoint_selection", "source_development", "source_label_status"):
        if checkpoint_config.get(key) != reference_config.get(key):
            raise ValueError("Sequence checkpoint development policy mismatch")


class SequenceExpert:
    @classmethod
    def from_checkpoint(cls, repo_root, run_directory, checkpoint_name=None):
        run = Path(run_directory)
        cfg = read(run / "config.yaml")
        candidate = {"1.2": "v12", "1.3": "v13", "1.3.1": "v13r1"}.get(cfg.get("version"))
        if candidate is None:
            raise ValueError("unknown Sequence checkpoint version")
        defaults, base = load_config(repo_root, candidate=candidate)
        assert_encoding_compatible(cfg, defaults)
        for key in [
            "model_id", "model_revision", "tokenizer_id", "tokenizer_revision",
            "base_config_sha256", "expert_id", "adapter_name",
        ]:
            if cfg[key] != defaults[key]:
                raise ValueError("Sequence expert incompatible with frozen base/config")
        manifest = read(run / "manifest.json")
        if candidate == "v13r1" and manifest["identity"].get("implementation_sha256") != implementation_digest(repo_root):
            raise ValueError("Sequence inference implementation differs from trained code")
        if manifest.get("semantic_adapter_used") is not False:
            raise ValueError("Sequence checkpoint does not prove adapter isolation")
        checkpoint = run / "checkpoints" / (checkpoint_name or manifest["best_checkpoint"])
        if not checkpoint.resolve().is_relative_to((run / "checkpoints").resolve()):
            raise ValueError("checkpoint path outside Sequence run")
        # The run identity is frozen before training starts.  ``config.yaml`` is
        # subsequently annotated with ``real_training_completed`` for the final
        # export, so recomputing its digest here would reject a valid checkpoint.
        verify_checkpoint(checkpoint, manifest["identity"])
        model, tokenizer, dtype = load_model(cfg, base, checkpoint / "adapter")
        if str(dtype) != manifest["precision"]:
            raise ValueError("Sequence inference precision differs from trained run")
        model.eval()
        instance = cls()
        instance.model, instance.tokenizer, instance.cfg = model, tokenizer, cfg
        instance.metadata = {
            "fold_id": manifest["fold_id"],
            "checkpoint_sha256": sha256_file(checkpoint / "adapter/adapter_model.safetensors"),
            "input_manifest_sha256": manifest["data_manifest_sha256"],
            "context_config_sha256": manifest["identity"]["config_sha256"],
        }
        return instance

    def score(self, context_messages, target_message, architecture_id, window_id, record_ids):
        metadata = dict(
            self.metadata,
            architecture_id=architecture_id,
            unit_id=window_id,
            record_ids=list(record_ids),
        )
        return score_next_log(
            self.model, self.tokenizer, self.cfg, context_messages, target_message, metadata
        )
