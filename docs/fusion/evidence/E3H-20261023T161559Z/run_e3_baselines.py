"""Same-protocol paper baselines on the E3-HDFS block cohort (CPU, no DeepLog)."""
import json, sys, time
from pathlib import Path
import numpy as np
from seqlogad.fusion.baselines import B0, score_rows, train_messages
from seqlogad.fusion.baselines_eval import train_windows
from seqlogad.fusion.evaluate import single_metrics, unit_table
from seqlogad.fusion.paper_baselines import Vocab, count_matrix, pca_scores, iforest_scores, knn_tfidf_scores
from seqlogad.fusion.units import build_cohort

FOLD, ARCH = "FOLD-TARGET-ARCH-HADOOP", "ARCH-HDFS"
blocks, orig, out = map(Path, sys.argv[1:4])
bundle = blocks / "phase2_sequence_blocks"
rows = [r for r in build_cohort(bundle, blocks / "source_dev_blocks", FOLD) if r["architecture_id"] == ARCH]
train = train_windows(orig, FOLD, ARCH)
test = [(r["context_messages"], r["target_message"]) for r in rows]
print("rows", len(rows), "train", len(train), flush=True)
vocab = Vocab([m for c, t in train for m in [*c, t]])
tr, te = count_matrix(train, vocab), count_matrix(test, vocab)
raw, timing = {}, {}
for name, fn in [("pca_xu2009", lambda: pca_scores(tr, te)),
                 ("iforest_liu2008", lambda: iforest_scores(tr, te)),
                 ("knn_tfidf_k4", lambda: knn_tfidf_scores([t for _, t in train], [t for _, t in test]))]:
    t0 = time.time(); raw[name] = fn(); timing[name] = time.time() - t0
    print(name, f"{timing[name]:.1f}s", flush=True)
b0 = score_rows(B0(train_messages(bundle, FOLD, ARCH)), rows)
window = {n: {r["window_id"]: float(v) for r, v in zip(rows, vals)} for n, vals in raw.items()}
window["b0_frequency"] = {k: v["b0_frequency"] for k, v in b0.items()}
window["b0_markov"] = {k: v["b0_markov"] for k, v in b0.items()}
report = {"experiment": "FUSION-E3-HDFS paper baselines (unpaired)", "windows": len(rows),
          "train_windows": len(train), "vocab": len(vocab), "seconds": timing, "metrics": {}}
for agg in ("max", "top3", "mean"):
    table, _ = unit_table(rows, window, agg)
    y = table["anomaly"]
    report["blocks"], report["positives"] = int(y.size), int(y.sum())
    for n in window:
        report["metrics"][f"{n}@{agg}"] = single_metrics(y, table[n], [0.01, 0.05])
(out / "e3_paper_baselines.json").write_text(json.dumps(report, indent=2, default=float))
(out / "e3_paper_baselines_window_scores.json").write_text(json.dumps(window))
print("DONE")
