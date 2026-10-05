"""Sequence optimization, checkpoint selection and terminal recovery boundary."""
import json
import os
import random
from seqlogad.semantic.checkpoint import save_checkpoint
from seqlogad.semantic.contracts import dump
from .augmentation import sample_training_view
from .model import assert_isolated
from .objective import collate
from .recovery_state import terminal_metrics
from .source_validation import score_validation, summarize_validation


def evaluate_by_source(model, tokenizer, examples, dtype, development_labels=None):
    return summarize_validation(score_validation(model, tokenizer, examples, dtype), development_labels)


def optimize(model, tokenizer, dtype, train, val, cfg, optimizer, scaler, run,
             run_identity, first, best, early_state=None, checkpoint_callback=None,
             raw_train_windows=None, development_labels=None):
    import torch

    early_state = dict(early_state or {})
    terminal = terminal_metrics(run, first, cfg, early_state)
    if terminal is not None:
        return best, terminal
    model.train()
    stale = early_state.get("stale_evaluations", 0)
    monitor_best = early_state.get("monitor_best")
    history = list(early_state.get("validation_history", []))
    train_by_source = {
        source: [row for row in train if row["architecture_id"] == source]
        for source in sorted({row["architecture_id"] for row in train})
    }
    source_ids = sorted(train_by_source)
    if raw_train_windows is None:
        raise ValueError("V12 multiscale training requires the source-only raw windows")
    for step in range(first, cfg["max_steps"]):
        optimizer.zero_grad(set_to_none=True)
        losses = []
        context_view_counts = {"full": 0, "short": 0}
        requested_context_counts = {}
        warmup = max(1, cfg["warmup_steps"])
        factor = ((step + 1) / warmup if step < cfg["warmup_steps"]
                  else (cfg["max_steps"] - step) / max(1, cfg["max_steps"] - cfg["warmup_steps"]))
        for group in optimizer.param_groups:
            group["lr"] = cfg["learning_rate"] * min(1.0, factor)
        for _ in range(cfg["gradient_accumulation_steps"]):
            source = source_ids[random.randrange(len(source_ids))]
            pool = train_by_source[source]
            example = pool[random.randrange(len(pool))]
            key = (example["architecture_id"], example["window_id"])
            if key not in raw_train_windows:
                raise ValueError("V12 selected window missing from source-only raw window map")
            example, view_info = sample_training_view(
                example, raw_train_windows[key], tokenizer, cfg
            )
            context_view_counts[view_info["view"]] += 1
            requested = str(view_info["requested_context_records"])
            requested_context_counts[requested] = requested_context_counts.get(requested, 0) + 1
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
            "training_context_view_counts": context_view_counts,
            "training_requested_context_records": requested_context_counts,
        }
        should_stop = False
        if (step + 1) % cfg["validation_steps"] == 0 or step + 1 == cfg["max_steps"]:
            validation = evaluate_by_source(model, tokenizer, val, dtype, development_labels)
            value = validation["aggregate_nll"]
            metrics["source_validation_next_log_nll"] = value
            metrics["per_source_validation_next_log_nll"] = validation["per_source_nll"]
            metrics["per_source_validation_perplexity"] = validation["per_source_perplexity"]
            checkpoint = run / "checkpoints" / f"step-{step + 1}"
            if development_labels is None:
                selection_value, key, direction = value, "loss", "min"
            else:
                development = validation["source_development"]
                metrics["source_development"] = development
                metrics["source_development_macro_f1"] = development["macro_f1"]
                selection_value, key, direction = development["macro_f1"], "f1", "max"
            selection_improved = best[key] is None or (
                selection_value < best[key] if direction == "min"
                else selection_value > best[key]
            )
            if selection_improved:
                best = {key: selection_value, "checkpoint": checkpoint.name}
                if development_labels is not None:
                    best["source_development"] = development
            patience_improved = monitor_best is None or (
                selection_value < monitor_best - cfg["early_stopping_min_delta"]
                if direction == "min" else
                selection_value > monitor_best + cfg["early_stopping_min_delta"]
            )
            if patience_improved:
                monitor_best, stale = selection_value, 0
            else:
                stale += 1
            history.append({
                "step": step + 1, "aggregate_nll": value,
                "per_source_nll": validation["per_source_nll"],
                "selection_metric": key, "selection_value": selection_value,
                "selection_improved": selection_improved,
                "patience_improved": patience_improved,
            })
            should_stop = stale >= cfg["early_stopping_patience"]
            metrics["early_stopping"] = {
                "stale_evaluations": stale,
                "patience": cfg["early_stopping_patience"],
                "minimum_delta": cfg["early_stopping_min_delta"],
                "metric": key, "direction": direction,
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
        with (run / "logs/train.jsonl").open("a") as handle:
            handle.write(json.dumps(metrics) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        if "early_stopping" in metrics and checkpoint_callback:
            checkpoint_callback(run, checkpoint, best["checkpoint"])
        print(json.dumps(metrics), flush=True)
        if should_stop:
            break
    return best, metrics


