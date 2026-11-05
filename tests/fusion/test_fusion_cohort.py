"""Real-bundle cohort contract (skipped when the restricted data is not present)."""
from collections import Counter
from pathlib import Path

import pytest

pytest.importorskip("polars")

from seqlogad.fusion.baselines import B0, score_rows, train_messages  # noqa: E402
from seqlogad.fusion.units import build_cohort, strip_labels  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data/phase2-sequence"
SIDECAR = REPO / "data/phase2-source-dev-v13r1"
pytestmark = pytest.mark.skipif(not (DATA.exists() and SIDECAR.exists()), reason="restricted data absent")


def test_cohort_counts_match_recorded_selection():
    cohort = build_cohort(DATA, SIDECAR, "FOLD-TARGET-ARCH-HDFS")
    counts = Counter((r["selection_cohort"], r["anomaly"]) for r in cohort)
    assert counts[(True, True)] == 16 and counts[(True, False)] == 496   # recorded V13R1 cohort
    assert counts[(False, True)] == 67 and len(cohort) == 2048
    assert {r["architecture_id"] for r in cohort} == {"ARCH-BGL"}        # target never present


def test_unlabeled_copy_and_b0_are_label_free():
    cohort = build_cohort(DATA, SIDECAR, "FOLD-TARGET-ARCH-BGL")
    assert all("anomaly" not in r for r in strip_labels(cohort))
    b0 = B0(train_messages(DATA, "FOLD-TARGET-ARCH-BGL", "ARCH-HDFS"))
    scores = score_rows(b0, cohort[:50])
    assert all(v["b0_frequency"] > 0 and v["b0_markov"] > 0 for v in scores.values())


def test_evaluator_end_to_end_on_real_cohorts_with_synthetic_scores(tmp_path):
    """Pipeline smoke test only: the scores are random, so no metric is meaningful."""
    import json

    import numpy as np
    import yaml

    from seqlogad.fusion.evaluate import main

    cfg = yaml.safe_load((REPO / "configs/fusion/fusion-e1.yaml").read_text())
    cfg["evaluation"]["bootstrap"]["reps"] = 20
    config = tmp_path / "e1.yaml"
    config.write_text(yaml.safe_dump(cfg))
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / cfg["data"]["sequence_bundle"]).symlink_to(DATA)
    (inputs / cfg["data"]["source_development"]).symlink_to(SIDECAR)
    run = tmp_path / "run/scores"
    run.mkdir(parents=True)
    rng = np.random.default_rng(0)
    windows = {r["window_id"] for fold in cfg["artifacts"] for r in build_cohort(DATA, SIDECAR, fold)}
    jobs = ["semantic_base", "sequence_base"] + [f"{k}_{f}_{c}" for f in ("hdfs", "hadoop", "bgl")
                                                 for k in ("semantic", "sequence") for c in ("best", "latest")]
    for job in jobs:
        with (run / f"{job}.jsonl").open("w") as handle:
            for w in sorted(windows):
                handle.write(json.dumps({"window_id": w, "status": "VALID", "nll_mean": float(rng.gamma(2.0))}) + "\n")
    out = tmp_path / "results.json"
    main(["--run", str(tmp_path / "run"), "--inputs", str(inputs), "--config", str(config), "--out", str(out)])
    report = json.loads(out.read_text())
    hdfs = report["folds"]["FOLD-TARGET-ARCH-HDFS"]["sources"]["ARCH-BGL"]
    assert hdfs["units"] == 1536 and hdfs["positives"] == 67               # fresh units only
    assert report["folds"]["FOLD-TARGET-ARCH-BGL"]["semantic_expert"] == "BASE_MODEL_ONLY_EXPLORATORY"
    assert "cauchy" in hdfs["fusion_gain"]
