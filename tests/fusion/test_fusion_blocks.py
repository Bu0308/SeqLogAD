"""Block-level evaluator on the real fresh HDFS block cohort with synthetic scores."""
import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("polars")

from seqlogad.fusion.block_eval import main  # noqa: E402
from seqlogad.fusion.evaluate import unit_table  # noqa: E402
from seqlogad.fusion.units import build_cohort  # noqa: E402

BLOCKS = Path("/Users/apple/study/seqlogad-fusion/00_inputs_blocks")


def test_unit_table_aggregators():
    rows = [{"unit_id": "u", "window_id": w, "target_rank": i, "anomaly": True, "time_chunk": "c",
             "crossfit_fold": 0} for i, w in enumerate("abc")]
    scores = {"s": {"a": 1.0, "b": 5.0, "c": np.nan}}
    assert unit_table(rows, scores, "max")[0]["s"][0] == 5.0
    assert unit_table(rows, scores, "mean")[0]["s"][0] == 3.0
    assert unit_table(rows, scores, "top3")[0]["s"][0] == 3.0


@pytest.mark.skipif(not BLOCKS.exists(), reason="block cohort absent")
def test_block_evaluator_planted_anomaly_line(tmp_path):
    """A single anomalous line per bad block: max must beat a random-line proxy."""
    cohort = build_cohort(BLOCKS / "phase2_sequence_blocks", BLOCKS / "source_dev_blocks",
                          "FOLD-TARGET-ARCH-HADOOP")
    rng = np.random.default_rng(0)
    first_bad = {}
    scores = (tmp_path / "run/scores")
    scores.mkdir(parents=True)
    rows = []
    for r in cohort:
        planted = r["anomaly"] and first_bad.setdefault(r["unit_id"], r["window_id"]) == r["window_id"]
        rows.append({"window_id": r["window_id"], "status": "VALID",
                     "nll_mean": float(rng.normal() + (6.0 if planted else 0.0))})
    for job in ("sequence_hadoop_best", "semantic_hadoop_best_mk42"):
        (scores / f"{job}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows))
    out = tmp_path / "blocks.json"
    main(["--run", str(tmp_path / "run"), "--block-inputs", str(BLOCKS), "--out", str(out), "--reps", "30"])
    report = json.loads(out.read_text())
    assert report["blocks"] == 3000 and report["anomalous_blocks"] == 65
    m = report["metrics"]
    assert m["sequence_hadoop_best@max"]["average_precision"] > m["sequence_hadoop_best@single"]["average_precision"]
    assert report["tests"]["H6_seq_max_vs_single"]["point"] > 0
