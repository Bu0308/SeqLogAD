"""Pinned, single-device QLoRA loader with explicit adapter isolation."""
import hashlib
from pathlib import Path


def verify_access(base):
    from huggingface_hub import HfApi, hf_hub_download
    info = base['required_metadata']; model = info['base_model_identifier']; rev = info['model_revision_commit']
    api = HfApi(token=True)
    api.whoami()  # Never print account or token.
    if api.model_info(model, revision=rev).sha != rev:
        raise ValueError('HF revision mismatch')
    for name, key in [('config.json', 'model_config_sha256'), ('tokenizer_config.json', 'tokenizer_config_sha256')]:
        path = hf_hub_download(model, name, revision=rev, token=True)
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != base['revision_policy'][key]:
            raise ValueError('pinned metadata hash mismatch')
    return {'authentication': 'PASS', 'revision': rev, 'metadata': 'PASS'}


def precision(torch):
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA required; CPU/MPS training is not permitted')
    major, minor = torch.cuda.get_device_capability()
    if (major, minor) < (7, 5):
        raise RuntimeError('GPU below frozen conditional capability')
    native = torch.cuda.is_bf16_supported(including_emulation=False)
    return torch.bfloat16 if native else torch.float16


def assert_isolated(model):
    trainable = [name for name, param in model.named_parameters() if param.requires_grad]
    if not trainable or any('lora_' not in name or '.semantic.' not in name for name in trainable):
        raise ValueError('trainable base/shared adapter detected')
    if set(model.peft_config) != {'semantic'}:
        raise ValueError('unexpected adapter namespace')
    return trainable


def load_model(cfg, base, adapter_path=None, base_only=False):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
    verify_access(base)
    dtype = precision(torch)
    torch.backends.cuda.matmul.allow_tf32 = False
    tokenizer = AutoTokenizer.from_pretrained(cfg['tokenizer_id'], revision=cfg['tokenizer_revision'],
                                               use_fast=True, trust_remote_code=False, token=True)
    if tokenizer.__class__.__name__ != 'PreTrainedTokenizerFast' or not tokenizer.is_fast:
        raise ValueError('tokenizer class mismatch')
    if tokenizer.bos_token_id != 128000 or tokenizer.eos_token_id != 128001:
        raise ValueError('special token mismatch')
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'right'
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=dtype, bnb_4bit_quant_storage=torch.uint8)
    model = AutoModelForCausalLM.from_pretrained(cfg['model_id'], revision=cfg['model_revision'],
        token=True, trust_remote_code=False, use_safetensors=True, quantization_config=quant,
        torch_dtype=dtype, device_map={'': torch.cuda.current_device()}, attn_implementation='sdpa')
    model.config.use_cache = False
    if base_only:
        model.eval()
        return model, tokenizer, dtype
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    if adapter_path:
        model = PeftModel.from_pretrained(model, str(adapter_path), adapter_name='semantic', is_trainable=True)
    else:
        lora = LoraConfig(task_type='CAUSAL_LM', r=cfg['rank'], lora_alpha=cfg['alpha'],
            lora_dropout=cfg['dropout'], target_modules=cfg['target_modules'], bias='none', modules_to_save=None)
        model = get_peft_model(model, lora, adapter_name='semantic')
    for name, param in model.named_parameters():
        if param.requires_grad:
            param.data = param.data.float()
    assert_isolated(model)
    return model, tokenizer, dtype
