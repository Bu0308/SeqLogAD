"""Confirmation evaluator smoke test on the real independent cohort with random scores."""
import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("polars")

from seqlogad.fusion.confirm_eval import holm, main  # noqa: E402
from seqlogad.fusion.units import build_cohort  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CONFIRM = Path("/Users/apple/study/seqlogad-fusion/00_inputs_confirm")
ORIGINAL = {"phase2_sequence": REPO / "data/phase2-sequence",
            "phase2_source_development_v13r1": REPO / "data/phase2-source-dev-v13r1"}


def test_holm_step_down():
    out = holm({"a": 0.001, "b": 0.03, "c": 0.04})
    assert out == {"a": True, "b": False, "c": False}
    assert holm({"a": 0.01, "b": 0.02})["b"] is True


@pytest.mark.skipif(not CONFIRM.exists() or not ORIGINAL["phase2_sequence"].exists(), reason="data absent")
def test_confirm_evaluator_runs_and_excludes_overlap(tmp_path):
    original = tmp_path / "orig"
    original.mkdir()
    for name, target in ORIGINAL.items():
        (original / name).symlink_to(target)
    scores = tmp_path / "run/scores"
    scores.mkdir(parents=True)
    rng = np.random.default_rng(0)
    for fold, tag in (("FOLD-TARGET-ARCH-HDFS", "hdfs"), ("FOLD-TARGET-ARCH-HADOOP", "hadoop"),
                      ("FOLD-TARGET-ARCH-BGL", "bgl")):
        windows = [r["window_id"] for r in build_cohort(CONFIRM / "phase2_sequence_confirm",
                                                        CONFIRM / "source_dev_confirm", fold)]
        jobs = [f"sequence_{tag}_best"] + ([f"semantic_{tag}_best_mkmean", f"semantic_{tag}_best_mk42"]
                                          if tag != "bgl" else [])
        for job in jobs:
            (scores / f"{job}.jsonl").write_text("".join(json.dumps(
                {"window_id": w, "status": "VALID", "nll_mean": float(rng.gamma(2))}) + "\n" for w in windows))
    out = tmp_path / "confirm.json"
    main(["--run", str(tmp_path / "run"), "--confirm-inputs", str(CONFIRM), "--original-inputs", str(original),
          "--out", str(out), "--reps", "20"])
    report = json.loads(out.read_text())
    hdfs = report["results"]["FOLD-TARGET-ARCH-HADOOP|ARCH-HDFS"]
    assert hdfs["excluded_overlapping_units"] == 57 and hdfs["positives"] == 18
    assert set(report["primary_family_holm"]["pvalues"]) == {
        "FOLD-TARGET-ARCH-HDFS|ARCH-BGL|H1_vw_seq_b0", "FOLD-TARGET-ARCH-HDFS|ARCH-BGL|H2_vw_sem_seq",
        "FOLD-TARGET-ARCH-HADOOP|ARCH-BGL|H1_vw_seq_b0", "FOLD-TARGET-ARCH-HADOOP|ARCH-BGL|H2_vw_sem_seq"}
