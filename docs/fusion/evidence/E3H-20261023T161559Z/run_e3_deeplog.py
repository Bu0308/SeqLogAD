"""DeepLog (Du et al., CCS 2017) on the E3-HDFS block cohort, same protocol as the other baselines."""
import json, sys, time
from pathlib import Path
import torch
from seqlogad.fusion.baselines_eval import train_windows
from seqlogad.fusion.evaluate import single_metrics, unit_table
from seqlogad.fusion.paper_baselines import Vocab, deeplog_scores
from seqlogad.fusion.units import build_cohort

FOLD, ARCH = "FOLD-TARGET-ARCH-HADOOP", "ARCH-HDFS"
blocks, orig, out = map(Path, sys.argv[1:4])
rows = [r for r in build_cohort(blocks / "phase2_sequence_blocks", blocks / "source_dev_blocks", FOLD)
        if r["architecture_id"] == ARCH]
train = train_windows(orig, FOLD, ARCH)
test = [(r["context_messages"], r["target_message"]) for r in rows]
vocab = Vocab([m for c, t in train for m in [*c, t]])
t0 = time.time()
scores = deeplog_scores(train, test, vocab, seed=42)
seconds = time.time() - t0
window = {"deeplog_du2017": {r["window_id"]: float(v) for r, v in zip(rows, scores)}}
report = {"experiment": "FUSION-E3-HDFS DeepLog (unpaired)", "windows": len(rows), "train_windows": len(train),
          "vocab": len(vocab), "seconds": seconds, "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
          "torch": torch.__version__, "metrics": {}}
for agg in ("max", "top3", "mean"):
    table, _ = unit_table(rows, window, agg)
    report["blocks"], report["positives"] = int(table["anomaly"].size), int(table["anomaly"].sum())
    report["metrics"][f"deeplog_du2017@{agg}"] = single_metrics(table["anomaly"], table["deeplog_du2017"], [0.01, 0.05])
(out / "e3_deeplog.json").write_text(json.dumps(report, indent=2, default=float))
(out / "e3_deeplog_window_scores.json").write_text(json.dumps(window))
print("DEEPLOG_DONE", f"{seconds:.1f}s")
