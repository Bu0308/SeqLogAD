"""E1.1-C: rescore the Semantic expert under K deterministic mask seeds.

The trained objective masks 30 % of the words with a seed derived from the
text, so an anomalous token is only scored when it happens to be masked.
Averaging (or maxing) the reconstruction NLL over several seeds removes that
lottery without retraining.  Seed 42 is the training/E1 seed and must
reproduce the E1 scores (consistency check, fail-closed).

Usage (GPU host, inside ``pmem run``):
    python -m seqlogad.fusion.run_multimask --repo . --inputs <inputs> \
        --artifacts <artifacts> --e1-run runs/E1-... --out runs/E11-... \
        --config configs/fusion/fusion-e1.yaml --seeds 42,43,44,45,46,47,48,49
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import yaml

from .artifacts import prepare_expert
from .evaluate import FOLD_TAG, load_scores
from .loading import activate, load_scoring_model
from .run_scoring import _write_jsonl
from .scorer import encode, score_examples
from .units import build_cohort, strip_labels

CONSISTENCY_TOLERANCE = 2e-3


def aggregate(per_seed: dict[int, dict[str, dict]]) -> dict[str, list[dict]]:
    """Per-window mean and max of nll_mean across seeds (abstentions excluded)."""
    windows = sorted(set().union(*[set(rows) for rows in per_seed.values()]))
    out = {"mkmean": [], "mkmax": []}
    for window in windows:
        values = [rows[window]["nll_mean"] for rows in per_seed.values()
                  if window in rows and rows[window]["status"] != "ABSTAIN"]
        for name, fn in (("mkmean", np.mean), ("mkmax", np.max)):
            if values:
                out[name].append({"window_id": window, "status": "VALID", "nll_mean": float(fn(values)),
                                  "seeds_scored": len(values)})
            else:
                out[name].append({"window_id": window, "status": "ABSTAIN", "reason": "all seeds abstained"})
    return out


def check_consistency(seed42: dict[str, dict], e1: dict[str, float]) -> float:
    diffs = [abs(seed42[w]["nll_mean"] - v) for w, v in e1.items()
             if w in seed42 and seed42[w]["status"] != "ABSTAIN" and np.isfinite(v)]
    if not diffs:
        raise ValueError("no overlapping windows to check seed-42 consistency")
    return float(max(diffs))


def main(argv=None):
    parser = argparse.ArgumentParser()
    for flag in ("--repo", "--inputs", "--artifacts", "--e1-run", "--out", "--config"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--seeds", default="42,43,44,45,46,47,48,49")
    args = parser.parse_args(argv)
    seeds = [int(s) for s in args.seeds.split(",")]
    if 42 not in seeds:
        raise SystemExit("seed 42 is required for the E1 consistency check")
    cfg = yaml.safe_load(args.config.read_text())
    if args.out.exists():
        raise SystemExit(f"output exists, preserve evidence: {args.out}")
    (args.out / "scores").mkdir(parents=True)
    data = args.inputs / cfg["data"]["sequence_bundle"]
    sidecar = args.inputs / cfg["data"]["source_development"]
    experts, cohorts = [], {}
    for fold_id, spec in cfg["artifacts"].items():
        if "semantic" not in spec:
            continue
        cohorts[fold_id] = strip_labels(build_cohort(data, sidecar, fold_id))
        files = spec["semantic"]
        experts.append(prepare_expert("semantic", fold_id, args.artifacts / files["target"],
                                      args.artifacts / files["recovery"], args.out / "work", args.repo))
    model, tokenizer, dtype, names = load_scoring_model(args.repo, experts, ("best",))
    report = {"seeds": seeds, "consistency_max_abs_diff": {}, "timings": {}}
    for expert in experts:
        tag = FOLD_TAG[expert["fold_id"]]
        activate(model, names[("semantic", expert["fold_id"], "best")])
        per_seed = {}
        for seed in seeds:
            started = time.time()
            cfg_seed = dict(expert["cfg"], seed=seed)
            examples = [encode("semantic", tokenizer, cfg_seed, row) for row in cohorts[expert["fold_id"]]]
            rows = score_examples(model, examples, tokenizer.pad_token_id, dtype,
                                  token_budget=cfg["scoring"]["token_budget"])
            _write_jsonl(args.out / "scores" / f"semantic_{tag}_best_mk{seed}.jsonl", rows)
            per_seed[seed] = {r["window_id"]: r for r in rows}
            report["timings"][f"{tag}_mk{seed}"] = round(time.time() - started, 2)
            print(f"[multimask] {tag} seed {seed}: {len(rows)} units", flush=True)
        diff = check_consistency(per_seed[42], load_scores(args.e1_run, f"semantic_{tag}_best"))
        report["consistency_max_abs_diff"][tag] = diff
        if diff > CONSISTENCY_TOLERANCE:
            (args.out / "multimask_manifest.json").write_text(json.dumps(report, indent=2))
            raise SystemExit(f"SEED42_INCONSISTENT for {tag}: max |diff| {diff}")
        for name, rows in aggregate(per_seed).items():
            _write_jsonl(args.out / "scores" / f"semantic_{tag}_best_{name}.jsonl", rows)
    (args.out / "multimask_manifest.json").write_text(json.dumps(report, indent=2))
    print("MULTIMASK_COMPLETE=YES", flush=True)


if __name__ == "__main__":
    main()
