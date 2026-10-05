"""Finalize terminal recovery without crossing the recorded stopping boundary."""
import json


def terminal_metrics(run, completed_steps, cfg, early_state):
    if completed_steps > cfg["max_steps"]:
        raise ValueError("checkpoint exceeds configured training budget")
    terminal = (completed_steps == cfg["max_steps"]
                or early_state.get("stale_evaluations", 0) >= cfg["early_stopping_patience"])
    if not terminal:
        return None
    if completed_steps <= 0:
        raise ValueError("invalid terminal checkpoint step")
    rows = [json.loads(line) for line in (run / "logs/train.jsonl").read_text().splitlines() if line]
    if not rows or rows[-1].get("step") != completed_steps:
        raise ValueError("terminal recovery lacks matching persisted metrics")
    return dict(rows[-1], recovered_terminal_checkpoint=True)
