"""Orchestration of the GPU entry point with a tiny CPU model (no download, no CUDA)."""
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
peft = pytest.importorskip("peft")
pytest.importorskip("polars")

import yaml  # noqa: E402

from seqlogad.fusion import run_scoring  # noqa: E402
from test_fusion_scorer import WordTokenizer  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data/phase2-sequence"
SIDECAR = REPO / "data/phase2-source-dev-v13r1"
SEMANTIC = REPO / "data/phase2"
pytestmark = pytest.mark.skipif(not (DATA.exists() and SIDECAR.exists() and SEMANTIC.exists()),
                                reason="restricted data absent")
FOLD = "FOLD-TARGET-ARCH-HDFS"


def _setup(tmp_path, monkeypatch, tolerance):
    cfg = yaml.safe_load((REPO / "configs/fusion/fusion-e1.yaml").read_text())
    cfg["artifacts"] = {FOLD: cfg["artifacts"][FOLD]}
    cfg["parity"] = {"tolerance_metric": tolerance, "tolerance_rel": tolerance, "tolerance_abs": tolerance}
    cfg["scoring"]["keep_hidden"] = False
    config = tmp_path / "e1.yaml"
    config.write_text(yaml.safe_dump(cfg))
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for key, target in (("sequence_bundle", DATA), ("source_development", SIDECAR), ("semantic_bundle", SEMANTIC)):
        (inputs / cfg["data"][key]).symlink_to(target)
    log = tmp_path / "train.jsonl"
    log.write_text(json.dumps({"step": 100, "per_source_validation_next_log_nll": {"ARCH-BGL": 1.0},
                               "per_source_validation_reconstruction_nll": {
                                   "ARCH-BGL": 1.0, "ARCH-HADOOP": 1.0, "ARCH-OPENSTACK": 1.0}}) + "\n")
    common = {"cfg": {"seed": 42, "mask_fraction": 0.3, "context_length": 96, "model_id": "m",
                      "model_revision": "r", "tokenizer_id": "m", "tokenizer_revision": "r",
                      "validation_records_per_source": 16},
              "precision": "torch.float32", "fold_id": FOLD, "train_log": str(log),
              "target_zip_sha256": "t", "recovery_zip_sha256": "r",
              "checkpoints": {"best": {"step": 100}, "latest": {"step": 200}},
              "metrics": {"best": {"source_development": {"per_source": {
                  "ARCH-BGL": {"auroc": 0.5, "average_precision": 0.03}}}}}}
    monkeypatch.setattr(run_scoring, "prepare_expert",
                        lambda kind, *a, **k: dict(common, kind=kind, run_id=f"{kind}-run"))

    def fake_loader(repo, experts, checkpoints):
        config_ = transformers.LlamaConfig(vocab_size=96, hidden_size=32, intermediate_size=64,
                                           num_hidden_layers=2, num_attention_heads=4,
                                           num_key_value_heads=2, max_position_embeddings=128)
        torch.manual_seed(0)
        model = transformers.LlamaForCausalLM(config_).eval()
        names = {}
        for expert in experts:
            for checkpoint in checkpoints:
                name = f"{expert['kind']}_hdfs_{checkpoint}"
                lora = peft.LoraConfig(r=2, lora_alpha=4, target_modules=["q_proj", "v_proj"])
                if isinstance(model, peft.PeftModel):
                    model.add_adapter(name, lora)
                else:
                    model = peft.get_peft_model(model, lora, adapter_name=name)
                names[(expert["kind"], expert["fold_id"], checkpoint)] = name
        for p in model.parameters():
            p.requires_grad_(False)
        return model, WordTokenizer(), None, names

    monkeypatch.setattr(run_scoring, "load_scoring_model", fake_loader)
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    return ["--repo", str(REPO), "--inputs", str(inputs), "--artifacts", str(artifacts),
            "--out", str(tmp_path / "run"), "--config", str(config)]


def test_parity_failure_aborts_before_any_fusion(tmp_path, monkeypatch):
    argv = _setup(tmp_path, monkeypatch, tolerance=1e-9)
    with pytest.raises(SystemExit, match="PARITY_FAILED"):
        run_scoring.main(argv)
    assert not (tmp_path / "run/run_manifest.json").exists()


def test_complete_scoring_run_writes_all_jobs(tmp_path, monkeypatch):
    argv = _setup(tmp_path, monkeypatch, tolerance=1e9)
    run_scoring.main(argv)
    run = tmp_path / "run"
    jobs = {p.stem for p in (run / "scores").glob("*.jsonl")}
    assert jobs == {"sequence_hdfs_best", "sequence_hdfs_latest", "semantic_hdfs_best",
                    "semantic_hdfs_latest", "semantic_base", "sequence_base"}
    rows = [json.loads(l) for l in (run / "scores/sequence_base.jsonl").read_text().splitlines()]
    assert len(rows) == 2048 and all("anomaly" not in r for r in rows)
    manifest = json.loads((run / "run_manifest.json").read_text())
    assert manifest["parity_pass"] and manifest["target_records_read"] is False
