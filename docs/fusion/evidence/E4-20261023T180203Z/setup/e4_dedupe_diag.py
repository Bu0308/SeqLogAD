"""D-20 diagnostic: is the deduped-vs-direct NLL gap larger than plain batch-composition noise?

Scores a fixed sample of windows three ways with the frozen Hadoop-fold Sequence adapter:
A = direct, sample alone; B = direct, sample mixed with other windows (different batchmates);
D = the deduplicated score already written by run_confirm.  Reports |A-B| (noise floor) vs |A-D|.
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from seqlogad.fusion.artifacts import prepare_expert
from seqlogad.fusion.evaluate import load_scores
from seqlogad.fusion.loading import activate, load_scoring_model
from seqlogad.fusion.scorer import encode, score_examples
from seqlogad.fusion.units import build_cohort, strip_labels
import yaml

repo, art, cfgp, e4, rb, rh, out = map(Path, sys.argv[1:8])
cfg = yaml.safe_load(cfgp.read_text())
fold = "FOLD-TARGET-ARCH-HADOOP"
spec = cfg["artifacts"][fold]["sequence"]
expert = prepare_expert("sequence", fold, art / spec["target"], art / spec["recovery"], out.parent / "diag_work", repo)
model, tok, dtype, names = load_scoring_model(repo, [expert], ("best",))
activate(model, names[("sequence", fold, "best")])
budget = cfg["scoring"]["token_budget"]
report = {}
for name, inputs, bundle, side, run in [("BGL", e4 / "bgl", "phase2_sequence_confirm", "source_dev_confirm", rb),
                                        ("HDFS", e4 / "hdfs", "phase2_sequence_blocks", "source_dev_blocks", rh)]:
    rows = strip_labels(build_cohort(inputs / bundle, inputs / side, fold))
    rows = sorted(rows, key=lambda r: r["window_id"])
    rng = np.random.default_rng(20)
    idx = rng.choice(len(rows), 1024, replace=False)
    sample, others = [rows[i] for i in idx[:256]], [rows[i] for i in idx[256:]]
    enc = lambda rs: [encode("sequence", tok, expert["cfg"], r) for r in rs]
    a = {r["window_id"]: r["nll_mean"] for r in score_examples(model, enc(sample), tok.pad_token_id, dtype, token_budget=budget)}
    b = {r["window_id"]: r["nll_mean"] for r in score_examples(model, enc(sample + others), tok.pad_token_id, dtype, token_budget=budget)}
    d = load_scores(run, "sequence_hadoop_best")
    ids = [w for w in a if w in d and np.isfinite(d[w])]
    A, B, D = (np.array([m[w] for w in ids]) for m in (a, b, d))
    allv = np.array([v for v in d.values() if np.isfinite(v)])
    report[name] = {"n": len(ids), "noise_floor_A_vs_B": {"max": float(np.abs(A - B).max()), "mean": float(np.abs(A - B).mean())},
                    "dedupe_A_vs_D": {"max": float(np.abs(A - D).max()), "mean": float(np.abs(A - D).mean())},
                    "spearman_A_D": float(spearmanr(A, D)[0]), "cohort_score_sd": float(allv.std()),
                    "cohort_score_iqr": float(np.subtract(*np.percentile(allv, [75, 25])))}
    print(name, json.dumps(report[name]), flush=True)
out.write_text(json.dumps(report, indent=2))
print("DIAG_WRITTEN")
