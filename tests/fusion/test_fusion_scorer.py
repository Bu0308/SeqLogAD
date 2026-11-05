"""Batched scorer on a tiny random Llama with two LoRA adapters (CPU, no download)."""
import numpy as np
import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
peft = pytest.importorskip("peft")

from seqlogad.fusion.loading import activate, assert_frozen  # noqa: E402
from seqlogad.fusion.scorer import encode, make_batches, score_examples  # noqa: E402


class WordTokenizer:
    """Deterministic stand-in with the attributes the encoders use."""
    bos_token_id, eos_token_id, pad_token_id = 1, 2, 2

    def encode(self, text, add_special_tokens=False):
        return [3 + (sum(ord(c) for c in piece) % 90) for piece in text.replace("\n", " \n ").split(" ") if piece]


CFG = {"seed": 42, "mask_fraction": 0.3, "context_length": 64}
ROWS = [{"window_id": f"w{i}", "target_message": msg, "context_messages": ctx}
        for i, (msg, ctx) in enumerate([
            ("disk error on node 7", ["boot ok", "fan ok"]),
            ("fan ok", ["boot ok"]),
            ("kernel panic: unable to mount root fs on unknown block", ["a", "b", "c"]),
            ("x", ["only one predecessor"]),
            ("", ["empty target abstains"]),
        ])]


@pytest.fixture(scope="module")
def model():
    torch.manual_seed(0)
    config = transformers.LlamaConfig(vocab_size=96, hidden_size=32, intermediate_size=64,
                                      num_hidden_layers=2, num_attention_heads=4,
                                      num_key_value_heads=2, max_position_embeddings=128)
    base = transformers.LlamaForCausalLM(config).eval()
    lora = dict(r=2, lora_alpha=4, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                init_lora_weights=False)
    wrapped = peft.get_peft_model(base, peft.LoraConfig(**lora), adapter_name="semantic_x_best")
    wrapped.add_adapter("sequence_x_best", peft.LoraConfig(use_rslora=True, **lora))
    for parameter in wrapped.parameters():
        parameter.requires_grad_(False)
    return wrapped.eval()


@pytest.mark.parametrize("kind", ["semantic", "sequence"])
def test_batched_equals_single_example(model, kind):
    tok = WordTokenizer()
    examples = [encode(kind, tok, CFG, row) for row in ROWS]
    assert examples[-1]["status"] == "ABSTAIN"
    batched = {r["window_id"]: r for r in score_examples(model, examples, 2, None, token_budget=256)}
    single = {}
    for example in examples:
        for r in score_examples(model, [example], 2, None, token_budget=10_000):
            single[r["window_id"]] = r
    for key, row in batched.items():
        if row["status"] == "ABSTAIN":
            assert single[key]["status"] == "ABSTAIN"
            continue
        assert row["nll_mean"] == pytest.approx(single[key]["nll_mean"], abs=1e-5)
        assert row["n_tokens"] == len(row["token_nll"]) > 0


def test_adapter_switch_and_base_control_change_scores(model):
    tok = WordTokenizer()
    examples = [encode("sequence", tok, CFG, row) for row in ROWS[:3]]
    activate(model, "sequence_x_best")
    a = [r["nll_mean"] for r in score_examples(model, examples, 2, None)]
    activate(model, "semantic_x_best")
    b = [r["nll_mean"] for r in score_examples(model, examples, 2, None)]
    with model.disable_adapter():
        c = [r["nll_mean"] for r in score_examples(model, examples, 2, None)]
    base = model.get_base_model()
    assert not np.allclose(a, b) and not np.allclose(a, c)
    with model.disable_adapter():
        direct = [r["nll_mean"] for r in score_examples(base, examples, 2, None)]
    assert np.allclose(c, direct)


def test_hidden_state_shape_and_frozen_parameters(model):
    tok = WordTokenizer()
    examples = [encode("semantic", tok, CFG, row) for row in ROWS[:2]]
    rows = score_examples(model, examples, 2, None, keep_hidden=True)
    assert all(r["hidden"].shape == (32,) for r in rows)
    model.set_adapter("semantic_x_best")              # raw PEFT call re-enables gradients
    with pytest.raises(ValueError):
        assert_frozen(model)
    activate(model, "semantic_x_best")
    assert_frozen(model)
    with pytest.raises(ValueError):
        next(model.parameters()).requires_grad_(True)
        assert_frozen(model)
    next(model.parameters()).requires_grad_(False)


def test_batches_respect_token_budget():
    examples = [{"input_ids": [0] * n, "window_id": str(n), "status": "VALID"} for n in (5, 9, 3, 20, 7)]
    for batch in make_batches(examples, 20):
        assert max(len(e["input_ids"]) for e in batch) * len(batch) <= 20 or len(batch) == 1
