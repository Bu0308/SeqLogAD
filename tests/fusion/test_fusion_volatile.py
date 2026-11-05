import numpy as np
import pytest

from seqlogad.fusion import rules
from seqlogad.fusion.volatile import encode_template, is_volatile, volatile_spans
from seqlogad.semantic.objective import encode_message

CFG = {"seed": 42, "mask_fraction": 0.15, "context_length": 512}


class CharTokenizer:
    """One token per character; offsets are exact, like a fast HF tokenizer."""
    bos_token_id, eos_token_id = 1, 2

    def encode(self, text, add_special_tokens=False):
        return [ord(c) + 10 for c in text]

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        return {"input_ids": self.encode(text), "offset_mapping": [(i, i + 1) for i in range(len(text))]}


def test_volatile_rule_ignores_placeholders_and_keeps_identifiers_out():
    assert is_volatile("/user/root/rand/_temporary/_task_200811092030_0003_m_000793_0/part-<NUM>.")
    assert is_volatile("R02-M1-N0-C:J12-U11")
    assert not is_volatile("<NUM>") and not is_volatile("block") and not is_volatile("x86")
    assert volatile_spans("a /p_123 b") == [(2, 8)]


def test_template_encoding_only_drops_volatile_target_tokens():
    tok = CharTokenizer()
    text = "allocateBlock: /user/_task_2008_0003/part-<NUM>. <BLK>"
    base, template = encode_message(tok, text, CFG), encode_template(tok, text, CFG)
    assert template["input_ids"] == base["input_ids"]  # prompt and target unchanged
    dropped = [i for i, (a, b) in enumerate(zip(base["labels"], template["labels"])) if a != b]
    target_start = next(i for i, v in enumerate(base["labels"]) if v != -100)
    clean_word = "/user/_task_2008_0003/part-<NUM>."
    first = target_start + text.index(clean_word)
    assert dropped == list(range(first, first + len(clean_word)))
    assert template["volatile_tokens"] == len(clean_word)
    assert template["labels"][-1] == tok.eos_token_id


def test_message_without_identifiers_is_scored_exactly_as_before():
    tok = CharTokenizer()
    text = "instruction cache parity error corrected"
    assert encode_template(tok, text, CFG)["labels"] == encode_message(tok, text, CFG)["labels"]


def test_generalized_mean_spans_vovk_wang_to_minimum():
    a, b = np.array([0.01, 0.2, 0.5]), np.array([0.3, 0.02, 0.5])
    assert np.allclose(rules.generalized_mean_score(a, b, 1.0), rules.vovk_wang_score(a, b))
    assert np.allclose(rules.generalized_mean_score(a, b, -np.inf), -np.log(np.minimum(a, b)))
    assert np.allclose(rules.generalized_mean_score(a, b, -60.0), -np.log(np.minimum(a, b)), atol=0.02)
    assert np.allclose(rules.generalized_mean_score(a, b, -1.0), -np.log(2 / (1 / a + 1 / b)))
    assert np.allclose(rules.generalized_mean_score(a, b, 0.0, 0.5), -0.5 * np.log(a * b))
    assert np.allclose(rules.generalized_mean_score(a, b, -1.0, 1.0), -np.log(a))
    with pytest.raises(ValueError):
        rules.generalized_mean_score(a, b, 1.0, 1.5)
