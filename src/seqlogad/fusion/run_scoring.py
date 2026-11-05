"""GPU entry point for FUSION-E1: verify, reproduce, then score every unit once.

Usage (inside ``pmem run`` on the GPU host):
    python -m seqlogad.fusion.run_scoring --repo . --inputs /workspace/fusion/inputs \
        --artifacts /workspace/fusion/artifacts --out /workspace/fusion/runs/E1 \
        --config configs/fusion/fusion-e1.yaml
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import yaml

from seqlogad.common.checksum import sha256_file
from seqlogad.sequence.implementation import implementation_digest

from .artifacts import assert_same_base, prepare_expert
from .loading import activate, assert_frozen, load_scoring_model
from .parity import all_pass, semantic_parity, sequence_parity
from .scorer import encode, score_examples
from .units import build_cohort, strip_labels


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps({k: v for k, v in row.items() if k != "hidden"}) + "\n")


def _write_hidden(path: Path, rows: list[dict]) -> None:
    kept = [r for r in rows if "hidden" in r]
    if kept:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path.with_suffix(".npy"), np.stack([r["hidden"] for r in kept]))
        path.with_suffix(".ids.json").write_text(json.dumps([r["window_id"] for r in kept]))


def _run_job(name, kind, cfg, rows, model, tokenizer, dtype, scoring, out, timings):
    started = time.time()
    examples = [encode(kind, tokenizer, cfg, row) for row in rows]
    result = score_examples(model, examples, tokenizer.pad_token_id, dtype,
                            token_budget=scoring["token_budget"], keep_hidden=scoring["keep_hidden"])
    _write_jsonl(out / "scores" / f"{name}.jsonl", result)
    _write_hidden(out / "hidden" / name, result)
    timings[name] = {"seconds": round(time.time() - started, 2), "units": len(rows)}
    print(f"[score] {name}: {len(rows)} units in {timings[name]['seconds']} s", flush=True)
    return {r["window_id"]: r for r in result}


def semantic_validation_nll(expert, data_root, model, tokenizer, dtype, scoring):
    from seqlogad.semantic.objective import select_records

    cfg = expert["cfg"]
    rows = select_records(data_root, expert["fold_id"], "val", cfg["validation_records_per_source"], cfg["seed"])
    shaped = [{"window_id": f"{r['architecture_id']}:{r['rank']}", "target_message": r["normalized_message"],
               "architecture_id": r["architecture_id"]} for r in rows]
    examples = [encode("semantic", tokenizer, cfg, row) for row in shaped]
    scores = {r["window_id"]: r for r in score_examples(model, examples, tokenizer.pad_token_id, dtype,
                                                        token_budget=scoring["token_budget"])}
    per_source = {}
    for arch in sorted({r["architecture_id"] for r in shaped}):
        values = [scores[r["window_id"]]["nll_mean"] for r in shaped
                  if r["architecture_id"] == arch and scores[r["window_id"]]["status"] != "ABSTAIN"]
        per_source[arch] = float(np.mean(values))
    return per_source


def _environment(torch, dtype) -> dict:
    cuda = torch.cuda.is_available()
    return {"gpu": torch.cuda.get_device_name(0) if cuda else "CPU", "torch": torch.__version__,
            "cuda": torch.version.cuda, "python": platform.python_version(),
            "peak_vram_allocated": torch.cuda.max_memory_allocated() if cuda else None,
            "peak_vram_reserved": torch.cuda.max_memory_reserved() if cuda else None,
            "dtype": str(dtype)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    for flag in ("--repo", "--inputs", "--artifacts", "--out", "--config"):
        parser.add_argument(flag, type=Path, required=True)
    args = parser.parse_args(argv)
    import torch

    cfg = yaml.safe_load(args.config.read_text())
    out = args.out
    if out.exists():
        raise SystemExit(f"output exists, preserve evidence: {out}")
    out.mkdir(parents=True)
    work = out / "work"
    data = args.inputs / cfg["data"]["sequence_bundle"]
    sidecar = args.inputs / cfg["data"]["source_development"]
    experts, cohorts = [], {}
    for fold_id, spec in cfg["artifacts"].items():
        cohorts[fold_id] = build_cohort(data, sidecar, fold_id)
        (out / "cohorts").mkdir(exist_ok=True)
        (out / "cohorts" / f"{fold_id}.unlabeled.json").write_text(json.dumps(strip_labels(cohorts[fold_id])))
        for kind, files in spec.items():
            experts.append(prepare_expert(kind, fold_id, args.artifacts / files["target"],
                                          args.artifacts / files["recovery"], work, args.repo))
    base_identity = assert_same_base(experts)
    model, tokenizer, dtype, names = load_scoring_model(args.repo, experts, tuple(cfg["scoring"]["checkpoints"]))
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    timings, scoring = {}, cfg["scoring"]

    parity, scores = {}, {}
    for expert in experts:
        for checkpoint in cfg["scoring"]["checkpoints"]:
            name = names[(expert["kind"], expert["fold_id"], checkpoint)]
            activate(model, name)
            scores[name] = _run_job(name, expert["kind"], expert["cfg"], strip_labels(cohorts[expert["fold_id"]]),
                                    model, tokenizer, dtype, scoring, out, timings)
        if expert["kind"] == "sequence":
            best = {k: v["nll_mean"] for k, v in scores[names[("sequence", expert["fold_id"], "best")]].items()}
            parity[expert["run_id"]] = sequence_parity(expert, cohorts[expert["fold_id"]], best,
                                                       cfg["parity"]["tolerance_metric"],
                                                       cfg["parity"]["tolerance_rel"], cfg["parity"]["tolerance_abs"])
        else:
            activate(model, names[("semantic", expert["fold_id"], "best")])
            per_source = semantic_validation_nll(expert, args.inputs / cfg["data"]["semantic_bundle"],
                                                 model, tokenizer, dtype, scoring)
            parity[expert["run_id"]] = semantic_parity(expert, per_source, cfg["parity"]["tolerance_rel"],
                                                       cfg["parity"]["tolerance_abs"])
        (out / "parity.json").write_text(json.dumps(parity, indent=2))
        if not all_pass({expert["run_id"]: parity[expert["run_id"]]}):
            raise SystemExit(f"PARITY_FAILED for {expert['run_id']}; see parity.json")

    if cfg["scoring"]["base_model_control"]:
        union = {r["window_id"]: r for rows in cohorts.values() for r in strip_labels(rows)}
        rows = sorted(union.values(), key=lambda r: (r["architecture_id"], r["target_rank"]))
        assert_frozen(model)
        with model.disable_adapter():
            for expert_kind in ("semantic", "sequence"):
                reference = next(e for e in experts if e["kind"] == expert_kind)
                _run_job(f"{expert_kind}_base", expert_kind, reference["cfg"], rows,
                         model, tokenizer, dtype, scoring, out, timings)

    manifest = {
        "schema": "SEQLOGAD-FUSION-SCORING-1", "experiment_id": cfg["experiment_id"],
        "config_sha256": sha256_file(args.config), "base": base_identity,
        "implementation_sha256": implementation_digest(args.repo),
        "inputs": {p.relative_to(args.artifacts).as_posix(): sha256_file(p)
                   for p in sorted(args.artifacts.rglob("*.zip"))},
        "bundle_sha256": sha256_file(data / "manifests/bundle.json"),
        "experts": [{k: e[k] for k in ("kind", "fold_id", "run_id", "checkpoints", "target_zip_sha256",
                                       "recovery_zip_sha256")} for e in experts],
        "adapters": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in names.items()},
        "parity_pass": all_pass(parity), "timings": timings,
        "environment": _environment(torch, dtype),
        "labels_on_gpu_host": "SOURCE_DEVELOPMENT_ONLY", "target_records_read": False,
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("FUSION_SCORING_COMPLETE=YES", flush=True)


if __name__ == "__main__":
    main()
