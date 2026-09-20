"""Pinned single-device QLoRA loader for the isolated Sequence adapter."""
from __future__ import annotations

from seqlogad.semantic.model import precision, verify_access


def assert_isolated(model):
    trainable = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    if not trainable or any("lora_" not in name or ".sequence." not in name for name in trainable):
        raise ValueError("trainable base/shared/Semantic adapter detected")
    if set(model.peft_config) != {"sequence"}:
        raise ValueError("unexpected P2.2 adapter namespace")
    return trainable


def load_model(cfg, base, adapter_path=None, base_only=False):
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    verify_access(base)
    dtype = precision(torch)
    torch.backends.cuda.matmul.allow_tf32 = False
    tokenizer = AutoTokenizer.from_pretrained(
        cfg["tokenizer_id"], revision=cfg["tokenizer_revision"], use_fast=True,
        trust_remote_code=False, token=True,
    )
    if tokenizer.__class__.__name__ != "PreTrainedTokenizerFast" or not tokenizer.is_fast:
        raise ValueError("tokenizer class mismatch")
    if tokenizer.bos_token_id != 128000 or tokenizer.eos_token_id != 128001:
        raise ValueError("special token mismatch")
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=dtype,
        bnb_4bit_quant_storage=torch.uint8,
    )
    model = AutoModelForCausalLM.from_pretrained(
        cfg["model_id"], revision=cfg["model_revision"], token=True,
        trust_remote_code=False, use_safetensors=True, quantization_config=quant,
        torch_dtype=dtype, device_map={"": torch.cuda.current_device()},
        attn_implementation="sdpa",
    )
    model.config.use_cache = False
    if base_only:
        model.eval()
        return model, tokenizer, dtype
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    if adapter_path:
        model = PeftModel.from_pretrained(
            model, str(adapter_path), adapter_name="sequence", is_trainable=True
        )
    else:
        lora = LoraConfig(
            task_type="CAUSAL_LM", r=cfg["rank"], lora_alpha=cfg["alpha"],
            lora_dropout=cfg["dropout"], target_modules=cfg["target_modules"],
            bias="none", modules_to_save=None,
        )
        model = get_peft_model(model, lora, adapter_name="sequence")
    for _, parameter in model.named_parameters():
        if parameter.requires_grad:
            parameter.data = parameter.data.float()
    assert_isolated(model)
    return model, tokenizer, dtype
