"""Exercise the loader's actual call path without torch/weights/network."""
import sys
from types import SimpleNamespace as NS
from pathlib import Path
import pytest
from seqlogad.semantic.config import load_config
from seqlogad.semantic import model as module


def test_loader_pins_base_tokenizer_quantizer_and_independent_adapter(monkeypatch):
    cfg, base = load_config(Path(__file__).resolve().parents[1])
    calls = {}
    class Param:
        requires_grad = True
        def __init__(self): self.data = self
        def float(self): return self
    instance = NS(config=NS(use_cache=True), peft_config={'semantic': {}},
                  named_parameters=lambda: [('x.lora_A.semantic.weight', Param())])
    class Tokenizer:
        is_fast = True
        bos_token_id, eos_token_id = 128000, 128001
        eos_token = '<|end_of_text|>'
    Tokenizer.__name__ = 'PreTrainedTokenizerFast'
    def tokenizer(*args, **kw): calls['tokenizer'] = (args, kw); return Tokenizer()
    def model(*args, **kw): calls['model'] = (args, kw); return instance
    def quant(**kw): calls['quant'] = kw; return kw
    def adapter(model, config, adapter_name): calls['adapter'] = adapter_name; return model
    def prepare(model, **kw): calls['prepare'] = kw; return model
    cuda = NS(is_available=lambda: True, get_device_capability=lambda: (8,0),
              is_bf16_supported=lambda **kw: True, current_device=lambda: 0)
    torch = NS(cuda=cuda, bfloat16='bf16', float16='fp16', uint8='uint8',
               backends=NS(cuda=NS(matmul=NS(allow_tf32=True))))
    monkeypatch.setitem(sys.modules, 'torch', torch)
    monkeypatch.setitem(sys.modules, 'transformers', NS(AutoModelForCausalLM=NS(from_pretrained=model),
        AutoTokenizer=NS(from_pretrained=tokenizer), BitsAndBytesConfig=quant))
    monkeypatch.setitem(sys.modules, 'peft', NS(LoraConfig=lambda **kw: kw, get_peft_model=adapter,
        prepare_model_for_kbit_training=prepare, PeftModel=NS()))
    monkeypatch.setattr(module, 'verify_access', lambda b: {'metadata':'PASS'})
    result, tok, dtype = module.load_model(cfg, base)
    for key in ('model', 'tokenizer'):
        assert calls[key][0][0] == cfg['model_id']
        assert calls[key][1]['revision'] == cfg['model_revision']
        assert calls[key][1]['trust_remote_code'] is False
    assert calls['model'][1]['device_map'] == {'': 0}
    assert calls['quant']['load_in_4bit'] is True
    assert calls['quant']['bnb_4bit_use_double_quant'] is True
    assert calls['quant']['bnb_4bit_quant_type'] == 'nf4'
    assert calls['adapter'] == 'semantic'
    assert result.config.use_cache is False and tok.pad_token == tok.eos_token


def test_authenticated_hash_mismatch_rejected(monkeypatch, tmp_path):
    cfg, base = load_config(Path(__file__).resolve().parents[1])
    wrong = tmp_path / 'wrong.json'; wrong.write_text('{}')
    monkeypatch.setitem(sys.modules, 'huggingface_hub', NS(
        HfApi=lambda **kw: NS(whoami=lambda: {}, model_info=lambda *a, **kw: NS(sha=cfg['model_revision'])),
        hf_hub_download=lambda *a, **kw: str(wrong)))
    with pytest.raises(ValueError, match='hash mismatch'): module.verify_access(base)
