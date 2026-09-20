"""Single-GPU P2.2 Sequence-QLoRA execution; importing never loads weights."""
from __future__ import annotations

import json
import math
import os
import random
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from seqlogad.common.checksum import sha256_file
from seqlogad.semantic.checkpoint import save_checkpoint, seal, verify_checkpoint, verify_seal
from seqlogad.semantic.contracts import dump
from seqlogad.semantic.prepare import git_state
from seqlogad.semantic.runtime import export_environment, seed_all
from .config import development_run_id, identity, load_config
from .contracts import validate_bundle
from .model import assert_isolated, load_model, precision
from .objective import _prompt, collate, encode_window, literal_text, select_windows

RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*")


def validate_run_id(run_id):
    if not isinstance(run_id, str) or RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise ValueError("unsafe P2.2 run_id")
    return run_id


def _cached_batch_encode(tokenizer, texts, cache):
    missing = list(dict.fromkeys(text for text in texts if text not in cache))
    if missing:
        encoded = tokenizer(
            missing, add_special_tokens=False, padding=False, truncation=False,
        )["input_ids"]
        cache.update((text, tuple(ids)) for text, ids in zip(missing, encoded, strict=True))
    return [cache[text] for text in texts]


def _overflow_example(tokenizer, state, prompt_tokens, target_tokens, context_length):
    complete = state["keep"] == len(state["target_words"])
    suffix = list(target_tokens) + ([tokenizer.eos_token_id] if complete else [])
    prefix = [tokenizer.bos_token_id] + list(prompt_tokens)
    ids = prefix + suffix
    if len(ids) > context_length:
        return None, len(ids) - context_length
    return {
        "input_ids": ids,
        "attention_mask": [1] * len(ids),
        "labels": [-100] * len(prefix) + suffix,
        "coverage": state["keep"] / len(state["target_words"]),
        "retained_target_words": state["keep"],
        "original_target_words": len(state["target_words"]),
        "retained_context_records": len(state["contexts"]),
        "original_context_records": state["original_context"],
        "complete": complete and len(state["contexts"]) == state["original_context"],
    }, 0


def _encode_overflow_batch(tokenizer, pending, cfg, label, prompt_cache, target_cache):
    states = [{
        "position": position,
        "contexts": list(contexts),
        "original_context": len(contexts),
        "target_words": list(target_words),
        "keep": len(target_words),
    } for position, contexts, target_words in pending]
    resolved, failures, round_index = {}, {}, 0
    while states:
        round_index += 1
        prompt_texts = [_prompt(state["contexts"]) for state in states]
        target_texts = [" ".join(state["target_words"][:state["keep"]]) for state in states]
        prompts = _cached_batch_encode(tokenizer, prompt_texts, prompt_cache)
        targets = _cached_batch_encode(tokenizer, target_texts, target_cache)
        remaining = []
        for state, prompt_tokens, target_tokens in zip(states, prompts, targets, strict=True):
            example, overflow = _overflow_example(
                tokenizer, state, prompt_tokens, target_tokens, cfg["context_length"]
            )
            if example is not None:
                resolved[state["position"]] = example
                continue
            state["keep"] -= max(1, overflow // 4)
            if state["keep"] > 0:
                remaining.append(state)
            elif len(state["contexts"]) > 1:
                state["contexts"] = state["contexts"][1:]
                state["keep"] = len(state["target_words"])
                remaining.append(state)
            else:
                failures[state["position"]] = "no causal context plus target content fits token horizon"
        states = remaining
        if round_index == 1 or round_index % 8 == 0:
            print(json.dumps({
                "encoding": label, "phase": "overflow_crop", "round": round_index,
                "active": len(states), "resolved": len(resolved), "rejected": len(failures),
            }), flush=True)
    return resolved, failures


def encoded_windows(rows, tokenizer, cfg, label="windows", batch_size=512):
    encoded, rejected = [], []
    fast_path = callable(tokenizer)
    prepared = []
    for row in rows:
        contexts = [message for message in row["context_messages"]
                    if message and message.strip()]
        target_words = literal_text(row["target_message"]).split()
        if not contexts or not target_words:
            reason = ("sequence window has no usable predecessor" if not contexts
                      else "sequence target is empty")
            rejected.append({"architecture_id": row["architecture_id"],
                             "window_id": row["window_id"], "reason": reason})
            continue
        prepared.append((row, contexts, " ".join(target_words)))

    for start in range(0, len(prepared), batch_size):
        chunk = prepared[start:start + batch_size]
        prompt_cache, target_cache = {}, {}
        if fast_path:
            prompt_texts = [_prompt(contexts) for _, contexts, _ in chunk]
            target_texts = [target for _, _, target in chunk]
            prompt_ids = _cached_batch_encode(tokenizer, prompt_texts, prompt_cache)
            target_ids = _cached_batch_encode(tokenizer, target_texts, target_cache)
        else:
            prompt_ids = [tokenizer.encode(_prompt(contexts), add_special_tokens=False)
                          for _, contexts, _ in chunk]
            target_ids = [tokenizer.encode(target, add_special_tokens=False)
                          for _, _, target in chunk]
        results, pending = [None] * len(chunk), []
        for position, ((row, contexts, target), prompt_tokens, target_tokens) in enumerate(zip(
                chunk, prompt_ids, target_ids, strict=True)):
            ids = [tokenizer.bos_token_id] + list(prompt_tokens) + list(target_tokens) + [tokenizer.eos_token_id]
            if len(ids) <= cfg["context_length"]:
                results[position] = {
                    "input_ids": ids,
                    "attention_mask": [1] * len(ids),
                    "labels": [-100] * (1 + len(prompt_tokens))
                              + list(target_tokens) + [tokenizer.eos_token_id],
                    "coverage": 1.0,
                    "retained_target_words": len(target.split()),
                    "original_target_words": len(target.split()),
                    "retained_context_records": len(contexts),
                    "original_context_records": len(contexts),
                    "complete": True,
                }
            elif fast_path:
                pending.append((position, contexts, target.split()))
            else:
                try:
                    results[position] = encode_window(
                        tokenizer, row["context_messages"], row["target_message"], cfg
                    )
                except ValueError as exc:
                    results[position] = str(exc)
        failures = {}
        if pending:
            resolved, failures = _encode_overflow_batch(
                tokenizer, pending, cfg, label, prompt_cache, target_cache
            )
            for position, example in resolved.items():
                results[position] = example
        for position, ((row, _, _), example) in enumerate(zip(chunk, results, strict=True)):
            if position in failures or isinstance(example, str):
                rejected.append({
                    "architecture_id": row["architecture_id"], "window_id": row["window_id"],
                    "reason": failures.get(position, example),
                })
                continue
            if example is None:
                raise RuntimeError("P2.2 batch encoder left an unresolved window")
            example.update(
                architecture_id=row["architecture_id"], window_id=row["window_id"],
                context_ranks=list(row["context_ranks"]), target_rank=row["target_rank"],
            )
            encoded.append(example)
        print(json.dumps({"encoding": label, "completed": min(start + len(chunk), len(prepared)),
                          "total": len(prepared), "rejected": len(rejected)}), flush=True)
    if not encoded:
        raise ValueError("all P2.2 windows abstained")
    return encoded, rejected


def evaluate(model, tokenizer, examples, dtype):
    import torch

    model.eval()
    scores = []
    with torch.no_grad():
        for example in examples:
            batch = {key: value.to(model.device)
                     for key, value in collate([example], tokenizer.pad_token_id).items()}
            with torch.autocast("cuda", dtype=dtype):
                loss = model(**batch).loss
            value = float(loss)
            if not math.isfinite(value):
                raise ValueError("nonfinite source validation next-log loss")
            scores.append(value)
    model.train()
    return sum(scores) / len(scores)


def evaluate_by_source(model, tokenizer, examples, dtype):
    sources = sorted({row["architecture_id"] for row in examples})
    per_source = {
        source: evaluate(model, tokenizer,
                         [row for row in examples if row["architecture_id"] == source], dtype)
        for source in sources
    }
    return {
        "aggregate_nll": sum(per_source.values()) / len(per_source),
        "per_source_nll": per_source,
        "aggregation": "MEAN_OF_EQUAL_WEIGHT_SOURCE_MEAN_TARGET_TOKEN_NLL",
    }


def preflight(model, tokenizer, examples, dtype):
    import torch

    example = max(examples, key=lambda row: len(row["input_ids"]))
    model.train()
    model.zero_grad(set_to_none=True)
    batch = {key: value.to(model.device)
             for key, value in collate([example], tokenizer.pad_token_id).items()}
    with torch.autocast("cuda", dtype=dtype):
        loss = model(**batch).loss
    if not torch.isfinite(loss):
        raise ValueError("P2.2 preflight loss nonfinite; native BF16 A40 required")
    loss.backward()
    if any(parameter.grad is not None and not torch.isfinite(parameter.grad).all()
           for parameter in model.parameters()):
        raise ValueError("P2.2 preflight gradients nonfinite")
    model.zero_grad(set_to_none=True)
    return {"loss": float(loss), "tokens": len(example["input_ids"]), "finite": True}


def optimize(model, tokenizer, dtype, train, val, cfg, optimizer, scaler, run,
             run_identity, first, best, early_state=None, checkpoint_callback=None):
    import torch

    model.train()
    early_state = dict(early_state or {})
    stale = early_state.get("stale_evaluations", 0)
    monitor_best = early_state.get("monitor_best")
    history = list(early_state.get("validation_history", []))
    train_by_source = {
        source: [row for row in train if row["architecture_id"] == source]
        for source in sorted({row["architecture_id"] for row in train})
    }
    source_ids = sorted(train_by_source)
    for step in range(first, cfg["max_steps"]):
        optimizer.zero_grad(set_to_none=True)
        losses = []
        warmup = max(1, cfg["warmup_steps"])
        factor = ((step + 1) / warmup if step < cfg["warmup_steps"]
                  else (cfg["max_steps"] - step) / max(1, cfg["max_steps"] - cfg["warmup_steps"]))
        for group in optimizer.param_groups:
            group["lr"] = cfg["learning_rate"] * min(1.0, factor)
        for _ in range(cfg["gradient_accumulation_steps"]):
            source = source_ids[random.randrange(len(source_ids))]
            pool = train_by_source[source]
            example = pool[random.randrange(len(pool))]
            batch = {key: value.to(model.device)
                     for key, value in collate([example], tokenizer.pad_token_id).items()}
            with torch.autocast("cuda", dtype=dtype):
                loss = model(**batch).loss
            if not torch.isfinite(loss):
                dump(run / "numerical-failure.json", {
                    "step_attempt": step + 1, "completed_steps": step,
                    "phase": "forward", "precision": str(dtype),
                    "loss_scale": scaler.get_scale(), "optimizer_update_applied": False,
                })
                raise ValueError("nonfinite P2.2 training loss; update not applied")
            losses.append(float(loss.detach()))
            scaler.scale(loss / cfg["gradient_accumulation_steps"]).backward()
        scaler.unscale_(optimizer)
        norm = torch.nn.utils.clip_grad_norm_(
            [parameter for parameter in model.parameters() if parameter.requires_grad],
            cfg["max_grad_norm"],
        )
        if not torch.isfinite(norm):
            dump(run / "numerical-failure.json", {
                "step_attempt": step + 1, "completed_steps": step,
                "phase": "backward", "precision": str(dtype),
                "loss_scale": scaler.get_scale(), "optimizer_update_applied": False,
            })
            raise ValueError("nonfinite P2.2 gradients; update not applied")
        scaler.step(optimizer)
        scaler.update()
        assert_isolated(model)
        metrics = {
            "step": step + 1,
            "train_next_log_nll": sum(losses) / len(losses),
            "loss_scale": scaler.get_scale(),
            "gradient_norm": float(norm),
            "optimizer_update_applied": True,
        }
        should_stop = False
        if (step + 1) % cfg["validation_steps"] == 0 or step + 1 == cfg["max_steps"]:
            validation = evaluate_by_source(model, tokenizer, val, dtype)
            value = validation["aggregate_nll"]
            metrics["source_validation_next_log_nll"] = value
            metrics["per_source_validation_next_log_nll"] = validation["per_source_nll"]
            checkpoint = run / "checkpoints" / f"step-{step + 1}"
            selection_improved = best["loss"] is None or value < best["loss"]
            if selection_improved:
                best = {"loss": value, "checkpoint": checkpoint.name}
            patience_improved = monitor_best is None or value < monitor_best - cfg["early_stopping_min_delta"]
            if patience_improved:
                monitor_best, stale = value, 0
            else:
                stale += 1
            history.append({
                "step": step + 1, "aggregate_nll": value,
                "per_source_nll": validation["per_source_nll"],
                "selection_improved": selection_improved,
                "patience_improved": patience_improved,
            })
            should_stop = stale >= cfg["early_stopping_patience"]
            metrics["early_stopping"] = {
                "stale_evaluations": stale,
                "patience": cfg["early_stopping_patience"],
                "minimum_delta": cfg["early_stopping_min_delta"],
                "triggered": should_stop,
            }
            current_early = {
                "stale_evaluations": stale,
                "monitor_best": monitor_best,
                "validation_history": history,
            }
            scheduler = {
                "kind": "LINEAR_WARMUP_THEN_LINEAR_DECAY",
                "last_completed_step": step + 1,
                "learning_rate_factor": min(1.0, factor),
            }
            save_checkpoint(
                model, optimizer, scaler, checkpoint, step + 1, run_identity, best,
                current_early, scheduler, adapter_name="sequence",
            )
            if checkpoint_callback:
                checkpoint_callback(run, checkpoint, best["checkpoint"])
        with (run / "logs/train.jsonl").open("a") as handle:
            handle.write(json.dumps(metrics) + "\n")
        print(json.dumps(metrics), flush=True)
        if should_stop:
            break
    return best, metrics


def run_training(repo_root, data_root, output_root, fold_id, run_id, overrides=None,
                 resume_from=None, expected_bundle_sha256=None, run_mode="development",
                 checkpoint_callback=None):
    import torch

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "true")

    cfg, base = load_config(repo_root, overrides, run_mode=run_mode)
    validation = validate_bundle(data_root, fold_id, expected_bundle_sha256)
    if not expected_bundle_sha256:
        raise ValueError("trusted P2.2 bundle SHA-256 is required")
    validate_run_id(run_id)
    if fold_id not in cfg["target_folds"] or run_id != development_run_id(fold_id, cfg["seed"]):
        raise ValueError("P2.2 run identity differs from frozen seed-42 matrix")
    run = Path(output_root) / fold_id / cfg["expert_id"] / run_id
    resume_path = Path(resume_from).resolve() if resume_from else None
    resume_in_place = bool(resume_path and run.exists() and resume_path.is_relative_to(run.resolve()))
    if run.exists() and not resume_in_place:
        raise ValueError("P2.2 run directory exists without verified in-place resume")
    run.mkdir(parents=True, exist_ok=resume_in_place)
    (run / "logs").mkdir(exist_ok=resume_in_place)
    (run / "checkpoints").mkdir(exist_ok=resume_in_place)
    if resume_in_place:
        (run / "checksums.sha256").unlink(missing_ok=True)
    run_identity = {
        "config_sha256": identity(cfg),
        "bundle_sha256": validation["bundle_sha256"],
        "fold_id": fold_id,
        "precision": str(precision(torch)),
        "adapter": "sequence",
    }
    resume = verify_checkpoint(resume_from, run_identity) if resume_from else None
    dump(run / "config.yaml", cfg)
    export_environment(run)
    selected = {
        "train": select_windows(data_root, fold_id, "train", cfg["train_windows_per_source"],
                                cfg["seed"], replacement=True),
        "val": select_windows(data_root, fold_id, "val", cfg["validation_windows_per_source"],
                              cfg["seed"], replacement=False),
    }
    dump(run / "selection.json", {
        partition: [{"architecture_id": row["architecture_id"], "window_id": row["window_id"]}
                    for row in rows]
        for partition, rows in selected.items()
    })
    seed_all(cfg["seed"])
    torch.cuda.reset_peak_memory_stats()
    start = time.monotonic()
    model, tokenizer, dtype = load_model(
        cfg, base, Path(resume_from) / "adapter" if resume_from else None
    )
    train, rejected_train = encoded_windows(selected["train"], tokenizer, cfg, "train")
    val, rejected_val = encoded_windows(selected["val"], tokenizer, cfg, "validation")
    dump(run / "coverage.json", {
        "train_rejected": rejected_train,
        "validation_rejected": rejected_val,
        "train_mean_target_coverage": sum(row["coverage"] for row in train) / len(train),
        "validation_mean_target_coverage": sum(row["coverage"] for row in val) / len(val),
        "train_mean_retained_context_records": sum(row["retained_context_records"] for row in train) / len(train),
        "validation_mean_retained_context_records": sum(row["retained_context_records"] for row in val) / len(val),
    })
    dump(run / "preflight.json", preflight(model, tokenizer, train, dtype))
    seed_all(cfg["seed"])
    optimizer = torch.optim.AdamW(
        [parameter for parameter in model.parameters() if parameter.requires_grad],
        lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"],
    )
    scaler = torch.amp.GradScaler(
        "cuda", enabled=(dtype == torch.float16), init_scale=cfg["fp16_initial_scale"],
        growth_interval=cfg["fp16_growth_interval"],
    )
    first, best = 0, {"loss": None, "checkpoint": None}
    early = {"stale_evaluations": 0, "monitor_best": None, "validation_history": []}
    if resume:
        state = torch.load(Path(resume_from) / "state.pt", map_location="cpu", weights_only=True)
        optimizer.load_state_dict(state["optimizer"])
        scaler.load_state_dict(state["scaler"])
        torch.set_rng_state(state["torch_rng"])
        torch.cuda.set_rng_state_all(state["cuda_rng"])
        random.setstate(state["python_rng"])
        first, best = state["step"], state["best"]
        early = state.get("early_stopping", early)
        if not {"stale_evaluations", "monitor_best", "validation_history"} <= set(early):
            raise ValueError("P2.2 resume lacks complete early-stopping state")
        if state.get("scheduler", {}).get("last_completed_step") != first:
            raise ValueError("P2.2 resume lacks matching scheduler state")
        if first >= cfg["max_steps"]:
            raise ValueError("P2.2 checkpoint already completed configured budget")
        previous_best = Path(resume_from).parent / best["checkpoint"]
        if not previous_best.exists():
            raise ValueError("P2.2 resume best checkpoint missing")
        if not previous_best.resolve().is_relative_to(run.resolve()):
            shutil.copytree(previous_best, run / "checkpoints/resume-best")
            best["checkpoint"] = "resume-best"
    try:
        best, metrics = optimize(
            model, tokenizer, dtype, train, val, cfg, optimizer, scaler, run,
            run_identity, first, best, early, checkpoint_callback,
        )
        selected_checkpoint = run / "checkpoints" / best["checkpoint"]
        from peft import set_peft_model_state_dict
        from safetensors.torch import load_file
        set_peft_model_state_dict(
            model, load_file(str(selected_checkpoint / "adapter/adapter_model.safetensors")),
            adapter_name="sequence",
        )
        from .scoring import score_next_log
        sample = selected["val"][0]
        checkpoint_hash = sha256_file(selected_checkpoint / "adapter/adapter_model.safetensors")
        metadata = {
            "fold_id": fold_id,
            "architecture_id": sample["architecture_id"],
            "unit_id": sample["window_id"],
            "record_ids": [f"{sample['architecture_id']}:{rank}" for rank in
                           list(sample["context_ranks"]) + [sample["target_rank"]]],
            "checkpoint_sha256": checkpoint_hash,
            "input_manifest_sha256": validation["bundle_sha256"],
            "context_config_sha256": identity(cfg),
        }
        evidence = score_next_log(
            model, tokenizer, cfg, sample["context_messages"], sample["target_message"], metadata
        )
        dump(run / "sanity-evidence.json", evidence)
        from .diagnostics import run_probes
        probe_meta = {key: value for key, value in metadata.items()
                      if key in {"fold_id", "checkpoint_sha256", "input_manifest_sha256", "context_config_sha256"}}
        probe_meta.update(architecture_id="SYNTHETIC", unit_id="probe", record_ids=[])
        dump(run / "sequence-probes.json", run_probes(
            lambda context, target: score_next_log(model, tokenizer, cfg, context, target, probe_meta)
        ))
        torch.cuda.synchronize()
        metrics.update(
            runtime_seconds=time.monotonic() - start,
            best=best,
            peak_vram_allocated=torch.cuda.max_memory_allocated(),
            peak_vram_reserved=torch.cuda.max_memory_reserved(),
        )
        dump(run / "metrics.json", metrics)
        cfg["real_training_completed"] = True
        dump(run / "config.yaml", cfg)
        manifest = {
            "run_id": run_id,
            "fold_id": fold_id,
            "expert_id": cfg["expert_id"],
            "identity": run_identity,
            "base_model_id": cfg["model_id"],
            "base_model_revision": cfg["model_revision"],
            "tokenizer_id": cfg["tokenizer_id"],
            "tokenizer_revision": cfg["tokenizer_revision"],
            "adapter_name": "sequence",
            "semantic_adapter_used": False,
            "seed": cfg["seed"],
            "training_mode": cfg["training_mode"],
            "precision": str(dtype),
            "adapter_config": cfg,
            "resume_parent": str(resume_from) if resume_from else None,
            "data_manifest_sha256": validation["bundle_sha256"],
            "data_manifest_path": "manifests/bundle.json",
            "git": git_state(repo_root),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "completion_status": "TRAINING_COMPLETED_REQUIRES_REVIEW",
            "scientific_results": "NOT_EVALUATED",
            "real_training_completed": True,
            "environment": "environment.json",
            "metrics": "metrics.json",
            "dependency_lock": "dependency-lock.txt",
            "checkpoint": str(selected_checkpoint.relative_to(run)),
            "best_checkpoint": best["checkpoint"],
            "checkpoint_sha256": checkpoint_hash,
            "metadata_file_sha256": {
                key: base["revision_policy"][key]
                for key in ["model_config_sha256", "tokenizer_config_sha256"]
            },
        }
        dump(run / "manifest.json", manifest)
        seal(run)
        verify_seal(run, require_nested_ledgers=True)
        return {"run_directory": str(run), "metrics": metrics}
    except Exception as exc:
        dump(run / "failure.json", {
            "type": type(exc).__name__, "message": str(exc), "training_completed": False,
        })
        raise
