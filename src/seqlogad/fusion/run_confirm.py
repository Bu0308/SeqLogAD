"""FUSION-E2-CONFIRM GPU pass: score the independent cohort with the frozen experts.

Jobs: Sequence best per fold; Semantic best per fold under mask seeds 42..49
(mean aggregate, as fixed in E1.1).  Anchor check (fail-closed): the HDFS-fold
Sequence adapter must reproduce its recorded selection-cohort AUROC/AP (parity,
|delta| <= 0.01).  Pre-registration deviation D-18: the original anchor compared
against E1R score files that became unreachable when their pod could not restart.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml

from .artifacts import prepare_expert
from .evaluate import FOLD_TAG
from .loading import activate, load_scoring_model
from .parity import all_pass, sequence_parity
from .run_multimask import aggregate
from .run_scoring import _write_jsonl
from .scorer import encode, score_examples, score_unique
from .units import build_cohort, strip_labels

DEDUPE_CHECK_ROWS, DEDUPE_TOLERANCE = 256, 0.01


def _dedupe_check(model, tokenizer, cfg, rows, deduped, dtype, budget) -> dict:
    """Re-score a fixed sample without deduplication; recorded, flagged loudly beyond tolerance."""
    sample = sorted(rows, key=lambda r: r["window_id"])[::max(1, len(rows) // DEDUPE_CHECK_ROWS)][:DEDUPE_CHECK_ROWS]
    direct = score_examples(model, [encode("sequence", tokenizer, cfg, r) for r in sample],
                            tokenizer.pad_token_id, dtype, token_budget=budget)
    by_id = {r["window_id"]: r for r in deduped}
    diffs = [abs(r["nll_mean"] - by_id[r["window_id"]]["nll_mean"]) for r in direct if r["status"] != "ABSTAIN"]
    check = {"rows": len(diffs), "max_abs_diff": max(diffs), "tolerance": DEDUPE_TOLERANCE,
             "pass": max(diffs) <= DEDUPE_TOLERANCE}
    print(f"[dedupe] {'PASS' if check['pass'] else 'DEDUPE_CHECK_FAILED'} {check}", flush=True)
    return check


def _encoding_stats(encoded: list[dict]) -> dict:
    abstain = sum(e["status"] == "ABSTAIN" for e in encoded)
    volatile = [e.get("volatile_tokens", 0) for e in encoded if e["status"] != "ABSTAIN"]
    return {"rows": len(encoded), "abstain": abstain, "rows_with_volatile_tokens_removed": sum(v > 0 for v in volatile),
            "volatile_tokens_removed": int(sum(volatile))}


def main(argv=None):
    parser = argparse.ArgumentParser()
    for flag in ("--repo", "--inputs", "--confirm-inputs", "--artifacts", "--out", "--config"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--seeds", default="42,43,44,45,46,47,48,49")
    parser.add_argument("--folds", default="", help="comma-separated fold ids; default all in config")
    parser.add_argument("--bundle-name", default="phase2_sequence_confirm")
    parser.add_argument("--sidecar-name", default="source_dev_confirm")
    parser.add_argument("--dedupe", action="store_true",
                        help="score each distinct encoding once (E4); the anchor is never deduplicated")
    parser.add_argument("--semantic-kinds", default="semantic",
                        help="comma-separated: semantic, semantic_template (volatile tokens dropped, E5)")
    args = parser.parse_args(argv)
    score_cohort = score_unique if args.dedupe else score_examples
    semantic_kinds = args.semantic_kinds.split(",")
    seeds = [int(s) for s in args.seeds.split(",")]
    cfg = yaml.safe_load(args.config.read_text())
    if args.out.exists():
        raise SystemExit(f"output exists, preserve evidence: {args.out}")
    (args.out / "scores").mkdir(parents=True)
    bundle = args.confirm_inputs / args.bundle_name
    sidecar = args.confirm_inputs / args.sidecar_name
    wanted = set(filter(None, args.folds.split(",")))
    experts, cohorts = [], {}
    for fold_id, spec in cfg["artifacts"].items():
        if wanted and fold_id not in wanted:
            continue
        cohorts[fold_id] = strip_labels(build_cohort(bundle, sidecar, fold_id))
        for kind, files in spec.items():
            experts.append(prepare_expert(kind, fold_id, args.artifacts / files["target"],
                                          args.artifacts / files["recovery"], args.out / "work", args.repo))
    model, tokenizer, dtype, names = load_scoring_model(args.repo, experts, ("best",))
    budget = cfg["scoring"]["token_budget"]
    if "semantic_template" in semantic_kinds:  # fail fast on tokenizer/offset problems, before any GPU work
        semantic_expert = next(e for e in experts if e["kind"] == "semantic")
        probe = [r for rows in cohorts.values() for r in rows][:512]
        preflight = _encoding_stats([encode("semantic_template", tokenizer, semantic_expert["cfg"], r) for r in probe])
        print(f"[preflight] semantic_template {preflight}", flush=True)
        if preflight["abstain"] > 0.05 * preflight["rows"]:
            raise SystemExit(f"TEMPLATE_PREFLIGHT_FAILED {preflight}")
    report = {"seeds": seeds, "timings": {}, "anchor": None, "dedupe": args.dedupe}

    anchor_expert = next(e for e in experts if e["kind"] == "sequence")
    activate(model, names[("sequence", anchor_expert["fold_id"], "best")])
    original = build_cohort(args.inputs / cfg["data"]["sequence_bundle"],
                            args.inputs / cfg["data"]["source_development"], anchor_expert["fold_id"])
    selection = [r for r in original if r["selection_cohort"]]
    rows = score_examples(model, [encode("sequence", tokenizer, anchor_expert["cfg"], r) for r in strip_labels(selection)],
                          tokenizer.pad_token_id, dtype, token_budget=budget)
    parity = {anchor_expert["run_id"]: sequence_parity(
        anchor_expert, selection, {r["window_id"]: r["nll_mean"] for r in rows},
        cfg["parity"]["tolerance_metric"], cfg["parity"]["tolerance_rel"], cfg["parity"]["tolerance_abs"])}
    report["anchor"] = parity
    (args.out / "confirm_manifest.json").write_text(json.dumps(report, indent=2))
    if not all_pass(parity):
        raise SystemExit("ANCHOR_FAILED (parity); see confirm_manifest.json")
    print(f"[anchor] parity PASS on {len(rows)} selection windows", flush=True)

    for expert in experts:
        tag = FOLD_TAG[expert["fold_id"]]
        activate(model, names[(expert["kind"], expert["fold_id"], "best")])
        rows_in = cohorts[expert["fold_id"]]
        if expert["kind"] == "sequence":
            started = time.time()
            result = score_cohort(model, [encode("sequence", tokenizer, expert["cfg"], r) for r in rows_in],
                                  tokenizer.pad_token_id, dtype, token_budget=budget)
            _write_jsonl(args.out / "scores" / f"sequence_{tag}_best.jsonl", result)
            report["timings"][f"sequence_{tag}"] = round(time.time() - started, 2)
            if args.dedupe:
                report[f"dedupe_check_{tag}"] = _dedupe_check(model, tokenizer, expert["cfg"], rows_in, result,
                                                              dtype, budget)
            print(f"[confirm] sequence {tag}: {len(result)} units", flush=True)
            continue
        for kind in semantic_kinds:
            per_seed = {}
            for seed in seeds:
                started = time.time()
                cfg_seed = dict(expert["cfg"], seed=seed)
                encoded = [encode(kind, tokenizer, cfg_seed, r) for r in rows_in]
                if seed == seeds[0]:
                    report[f"encoding_{kind}_{tag}"] = _encoding_stats(encoded)
                    print(f"[confirm] {kind} {tag} encoding {report[f'encoding_{kind}_{tag}']}", flush=True)
                result = score_cohort(model, encoded, tokenizer.pad_token_id, dtype, token_budget=budget)
                _write_jsonl(args.out / "scores" / f"{kind}_{tag}_best_mk{seed}.jsonl", result)
                per_seed[seed] = {r["window_id"]: r for r in result}
                report["timings"][f"{kind}_{tag}_mk{seed}"] = round(time.time() - started, 2)
            for name, rows_out in aggregate(per_seed).items():
                _write_jsonl(args.out / "scores" / f"{kind}_{tag}_best_{name}.jsonl", rows_out)
            print(f"[confirm] {kind} {tag}: {len(seeds)} seeds", flush=True)
            (args.out / "confirm_manifest.json").write_text(json.dumps(report, indent=2))
    (args.out / "confirm_manifest.json").write_text(json.dumps(report, indent=2))
    print("CONFIRM_SCORING_COMPLETE=YES", flush=True)


if __name__ == "__main__":
    main()
