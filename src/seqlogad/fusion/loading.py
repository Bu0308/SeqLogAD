"""One frozen NF4 base with every expert adapter attached under its own name.

The base is prepared exactly as during training validation
(``prepare_model_for_kbit_training`` and float32 LoRA weights), so scores match
the selection-time numerics.  All parameters are frozen; nothing is trained.
"""
from __future__ import annotations

from pathlib import Path


def adapter_name(expert: dict, checkpoint: str) -> str:
    fold = expert["fold_id"].removeprefix("FOLD-TARGET-ARCH-").lower()
    return f"{expert['kind']}_{fold}_{checkpoint}"


def load_scoring_model(repo_root: Path, experts: list[dict], checkpoints=("best", "latest")):
    import torch
    from peft import PeftModel, prepare_model_for_kbit_training

    from seqlogad.sequence.config import load_config
    from seqlogad.sequence.model import load_model

    sequence = next((e for e in experts if e["kind"] == "sequence"), experts[0])
    _, base = load_config(repo_root, candidate="v13r1")
    model, tokenizer, dtype = load_model(sequence["cfg"], base, base_only=True)
    if str(dtype) != sequence["precision"]:
        raise ValueError(f"scoring precision {dtype} differs from training {sequence['precision']}")
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    names = {}
    for expert in experts:
        for checkpoint in checkpoints:
            name = adapter_name(expert, checkpoint)
            path = str(Path(expert["checkpoints"][checkpoint]["path"]) / "adapter")
            if not isinstance(model, PeftModel):
                model = PeftModel.from_pretrained(model, path, adapter_name=name, is_trainable=False)
            else:
                model.load_adapter(path, adapter_name=name, is_trainable=False)
            names[(expert["kind"], expert["fold_id"], checkpoint)] = name
    for parameter_name, parameter in model.named_parameters():
        if "lora_" in parameter_name:
            parameter.data = parameter.data.float()
        parameter.requires_grad_(False)
    model.eval()
    assert_frozen(model)
    return model, tokenizer, dtype, names


def activate(model, name: str) -> None:
    """Switch adapter; PEFT's ``set_adapter`` re-enables gradients, so refreeze."""
    model.set_adapter(name)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    assert_frozen(model)


def assert_frozen(model) -> None:
    trainable = [name for name, p in model.named_parameters() if p.requires_grad]
    if trainable:
        raise ValueError(f"scoring model has trainable parameters: {trainable[:3]}")
