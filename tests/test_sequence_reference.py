import json
from pathlib import Path

import polars as pl
import pytest

from seqlogad.sequence.config import development_run_id, load_config
from seqlogad.sequence.augmentation import sample_training_view
from seqlogad.sequence.contracts import validate_bundle
from seqlogad.sequence.diagnostics import run_probes
from seqlogad.sequence.expert import assert_encoding_compatible
from seqlogad.sequence.objective import encode_window, select_windows
from seqlogad.sequence.train import encoded_windows
from seqlogad.sequence.prepare import _bounded_windows


ROOT = Path(__file__).parents[1]


class Tokenizer:
    bos_token_id = 1
    eos_token_id = 2
    pad_token_id = 2

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        return [100 + index for index, _ in enumerate(text.split())]

    def __call__(self, texts, add_special_tokens=False, padding=False, truncation=False):
        assert padding is truncation is False
        return {"input_ids": [self.encode(text, add_special_tokens) for text in texts]}


def test_sequence_config_freezes_seed_objective_budget_and_adapter_isolation():
    cfg, base = load_config(ROOT)
    assert cfg["seed"] == 42
    assert cfg["objective"] == "CAUSAL_NEXT_LOG_TARGET_TOKEN_NLL"
    assert cfg["adapter_name"] == "sequence"
    assert cfg["expert_id"] == "SEQUENCE_LLAMA_REFERENCE"
    assert cfg["context_policy"]["max_predecessor_records"] == 8
    assert cfg["train_windows_per_source"] == 8192
    assert base["peft"]["share_adapter_weights"] is False
    assert cfg["version"] == "1.2"
    assert cfg["use_rslora"] is True
    assert cfg["training_context_views"]["short_lengths"] == [1, 2, 4]
    assert development_run_id("FOLD-TARGET-ARCH-BGL") == "P2.2-DEVELOPMENT-BGL-S42-V12"


def test_old_checkpoint_encoding_cannot_be_loaded_as_v12():
    cfg, _ = load_config(ROOT)
    previous = dict(cfg, version="1.0")
    with pytest.raises(ValueError, match="encoding variant mismatch"):
        assert_encoding_compatible(previous, cfg)
    previous = dict(cfg, use_rslora=False)
    with pytest.raises(ValueError, match="encoding variant mismatch"):
        assert_encoding_compatible(previous, cfg)


def test_multiscale_training_view_keeps_target_and_causal_suffix():
    cfg, _ = load_config(ROOT)
    tokenizer = Tokenizer()
    raw = {
        "context_messages": ["old one", "old two", "recent three", "recent four"],
        "target_message": "next event",
    }
    full = encode_window(tokenizer, raw["context_messages"], raw["target_message"], cfg)

    class ShortRng:
        def random(self):
            return 0.9

        def choice(self, lengths):
            assert lengths == [1, 2]
            return 2

    short, info = sample_training_view(full, raw, tokenizer, cfg, ShortRng())
    assert info == {"requested_context_records": 2, "view": "short"}
    assert short["retained_context_records"] == 2
    assert short["labels"][-3:] == full["labels"][-3:]
    assert short["original_context_records"] == 2

    class FullRng:
        def random(self):
            return 0.1

    original, info = sample_training_view(full, raw, tokenizer, cfg, FullRng())
    assert original is full
    assert info["view"] == "full"


def test_v12_runpod_notebook_captures_attempts_with_persistent_projmem():
    path = ROOT / "notebooks/P2.2_run_all_sequence_lora_s42_v12.ipynb"
    notebook = json.loads(path.read_text())
    code = "\n".join("".join(cell["source"]) for cell in notebook["cells"]
                     if cell["cell_type"] == "code")
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"v12-cell-{index}", "exec")
    assert 'PERSISTENT_ROOT = STATE_ROOT / "sequence-v12"' in code
    assert '[pmem_cli, "run"' in code
    assert '"export-bundle"' in code
    assert '"track", "P2.2/seqlogad_outputs_P2.2_S42_FINAL.zip"' in code
    assert 'assert pmem_success' in code


@pytest.mark.parametrize("status", ["success", "failed"])
def test_v12_notebook_does_not_treat_failed_pmem_run_as_training_success(tmp_path, status):
    notebook = json.loads((ROOT / "notebooks/P2.2_run_all_sequence_lora_s42_v12.ipynb").read_text())
    execute = next("".join(cell["source"]) for cell in notebook["cells"]
                   if cell["cell_type"] == "code"
                   and '"P2.2 Sequence V12 RunPod attempt"' in "".join(cell["source"]))
    calls = []

    def fake_run_live(args, **kwargs):
        calls.append(args)
        if len(args) > 1 and args[1] == "run":
            return 0, f"Run run_{'a' * 32} {status}\nexit_code: {0 if status == 'success' else 1}\n"
        return 0

    namespace = {
        "VENV": tmp_path / "venv", "PERSISTENT_ROOT": tmp_path / "persistent",
        "SESSION_ROOT": tmp_path / "session-unique", "PYTHON": "python",
        "TASK_ID": "P2.2", "REPO_ROOT": "repo", "DATA_ROOT": "data",
        "OUTPUT_ROOT": "output", "EXPECTED_BUNDLE_SHA256": "bundle",
        "run_live": fake_run_live,
    }
    namespace["PERSISTENT_ROOT"].mkdir()
    if status == "failed":
        with pytest.raises(AssertionError, match="Projmem recorded a failed"):
            exec(execute, namespace)
    else:
        exec(execute, namespace)
    assert any("export-bundle" in args for args in calls)
    assert any("track" in args for args in calls) is (status == "success")


def test_target_only_causal_encoding_preserves_context_and_eos():
    cfg, _ = load_config(ROOT)
    encoded = encode_window(Tokenizer(), ["first event", "second event"], "third event", cfg)
    target_positions = [index for index, value in enumerate(encoded["labels"]) if value != -100]
    assert target_positions[0] > 0
    assert encoded["labels"][-1] == Tokenizer.eos_token_id
    assert encoded["coverage"] == 1.0
    assert encoded["retained_context_records"] == 2
    assert encoded["complete"] is True


def test_batched_encoding_matches_single_window_fast_path():
    cfg, _ = load_config(ROOT)
    row = {
        "architecture_id": "ARCH-X", "window_id": "w1",
        "context_ranks": [1, 2], "target_rank": 3,
        "context_messages": ["first event", "second event"],
        "target_message": "third event",
    }
    expected = encode_window(Tokenizer(), row["context_messages"], row["target_message"], cfg)
    actual, rejected = encoded_windows([row], Tokenizer(), cfg, batch_size=1)
    assert rejected == []
    for key in ("input_ids", "attention_mask", "labels", "coverage", "complete"):
        assert actual[0][key] == expected[key]


def test_batched_encoding_matches_single_window_overflow_crop_path():
    cfg, _ = load_config(ROOT)
    cfg = dict(cfg, context_length=18)
    rows = [{
        "architecture_id": "ARCH-X", "window_id": f"w{index}",
        "context_ranks": [1, 2], "target_rank": 3,
        "context_messages": ["first context has many words", "second context has many words"],
        "target_message": "target also has many words that need cropping",
    } for index in range(3)]
    expected = [encode_window(
        Tokenizer(), row["context_messages"], row["target_message"], cfg
    ) for row in rows]
    actual, rejected = encoded_windows(rows, Tokenizer(), cfg, batch_size=3)
    assert rejected == []
    for batch_item, single_item in zip(actual, expected, strict=True):
        for key in (
            "input_ids", "attention_mask", "labels", "coverage", "complete",
            "retained_target_words", "retained_context_records",
        ):
            assert batch_item[key] == single_item[key]


def test_overflow_keeps_full_target_by_dropping_oldest_context_first():
    cfg, _ = load_config(ROOT)
    cfg = dict(cfg, context_length=24)
    contexts = ["old context has several words", "recent context has several words"]
    target = "target message has several words"
    single = encode_window(Tokenizer(), contexts, target, cfg)
    assert single["retained_context_records"] == 1
    assert single["retained_target_words"] == len(target.split())
    assert single["coverage"] == 1.0
    assert single["labels"][-1] == Tokenizer.eos_token_id
    assert single["complete"] is False
    row = {
        "architecture_id": "ARCH-X", "window_id": "w-crop",
        "context_ranks": [1, 2], "target_rank": 3,
        "context_messages": contexts, "target_message": target,
    }
    batched, rejected = encoded_windows([row], Tokenizer(), cfg, batch_size=1)
    assert rejected == []
    for key in ("input_ids", "labels", "coverage", "retained_target_words",
                "retained_context_records", "complete"):
        assert batched[0][key] == single[key]


def test_bounded_windows_never_cross_group_and_preserve_multiplicity():
    stream = pl.DataFrame({
        "rank": [1, 2, 3, 4, 5, 6],
        "effective_ts": [10, 20, 30, 40, 50, 60],
        "gid": [7, 8, 7, 7, 8, 7],
    })
    windows, eligible = _bounded_windows(stream, "ARCH-X", "SOURCE_TRAIN", 20, 3)
    assert eligible == 4
    rows = {row["target_rank"]: row for row in windows.to_dicts()}
    assert rows[3]["context_ranks"] == [1]
    assert rows[4]["context_ranks"] == [1, 3]
    assert rows[5]["context_ranks"] == [2]
    assert rows[6]["context_ranks"] == [1, 3, 4]


def test_all_six_sequence_controls_are_diagnostic_only():
    report = run_probes(lambda context, target: {"score_raw": float(len(context) + len(target))})
    assert report["used_for_training_or_selection"] is False
    assert report["natural_anomaly_performance"] is None
    assert {item["kind"] for item in report["results"]} == {
        "event_permutation", "missing_event", "duplicate_event", "unexpected_next_event",
        "long_range_dependency_violation", "locally_plausible_globally_invalid",
    }


def test_real_sequence_bundle_validates_and_hydrates_without_labels():
    data_root = ROOT / "data/phase2-sequence"
    if not data_root.is_dir():
        return
    bundle = json.loads((data_root / "manifests/bundle.json").read_text())
    digest = __import__("hashlib").sha256((data_root / "manifests/bundle.json").read_bytes()).hexdigest()
    for fold in bundle["folds"]:
        report = validate_bundle(data_root, fold, digest)
        assert report["status"] == "PASS"
        assert report["view"]["label_columns"] == []
    rows = select_windows(
        data_root, "FOLD-TARGET-ARCH-BGL", "val", 2, 42, replacement=False
    )
    assert len(rows) == 6
    assert all(row["context_messages"] and row["target_message"] for row in rows)
    assert all("label" not in key.lower() for row in rows for key in row)
