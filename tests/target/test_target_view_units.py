"""TV-001 unit, window, sampling and drift rules on synthetic label-free frames."""
import polars as pl
import pytest

from seqlogad.target.diagnostics import _jsd
from seqlogad.target.materialize import template_key
from seqlogad.target.units import _quotas, build_units, build_windows, hash_sample


def _records(groups, ts_step=1_000_000):
    n = len(groups)
    return pl.DataFrame({"rank": list(range(100, 100 + n)), "effective_ts": [i * ts_step for i in range(n)],
                         "gid": [-1 if g == "GLOBAL" else int(g[1:]) for g in groups], "group": groups,
                         "norm_h": [i % 3 for i in range(n)]})


def test_template_key_masks_identifier_words_only():
    assert template_key("Receiving block blk_123456 src: /10.250.19.102:54106", 3) == "Receiving block <V> src: <V>"
    assert template_key("instruction cache parity error corrected", 3) == "instruction cache parity error corrected"
    with pytest.raises(ValueError):
        template_key("x", 2)


def test_bgl_windows_use_at_most_context_previous_lines():
    frame = _records(["GLOBAL"] * 12)
    windows = build_windows(frame, "ARCH-BGL", "TARGET_EVALUATION", 8)
    assert windows.height == 11  # first line has no predecessor
    assert windows["context_record_count"].max() == 8
    last = windows.row(-1, named=True)
    assert last["context_ranks"] == list(range(103, 111)) and last["target_rank"] == 111


def test_hdfs_windows_stay_inside_block_and_skip_unblocked_lines():
    frame = _records(["G1", "G2", "G1", "GLOBAL", "G2", "G1"])
    windows = build_windows(frame, "ARCH-HDFS", "TARGET_EVALUATION", 8)
    assert windows["target_rank"].to_list() == [102, 104, 105]
    assert windows.filter(pl.col("target_rank") == 105)["context_ranks"].to_list() == [[100, 102]]
    units = build_units(frame, "ARCH-HDFS", "TARGET_EVALUATION", 2, 100, 0)
    assert sorted(units["n_lines"].to_list()) == [2, 3]


def test_identical_inputs_share_dedupe_key():
    frame = _records(["GLOBAL"] * 7).with_columns(pl.lit(5).alias("norm_h"))
    windows = build_windows(frame, "ARCH-BGL", "TARGET_EVALUATION", 2)
    keys = windows["dedupe_key"].to_list()
    assert keys[0] != keys[1] and len(set(keys[1:])) == 1  # context length 1 vs 2, then identical


def test_units_strata_are_equal_count_and_chronological():
    frame = _records(["GLOBAL"] * 40)
    units = build_units(frame, "ARCH-BGL", "TARGET_EVALUATION", 4, 10, 5_000_000)
    assert units.group_by("stratum").len().sort("stratum")["len"].to_list() == [10, 10, 10, 10]
    assert units["stratum"].to_list() == sorted(units["stratum"].to_list())
    assert units["embargo"].sum() == 5 and units["chunk"].max() == 3


def test_quotas_are_proportional_and_exact():
    quota = _quotas({0: 50, 1: 30, 2: 20}, 11)
    assert sum(quota.values()) == 11 and quota[0] >= quota[1] >= quota[2]
    assert _quotas({0: 5, 1: 5}, 0) == {0: 5, 1: 5}


def test_hash_sample_is_deterministic_salted_and_stratified():
    units = build_units(_records(["GLOBAL"] * 200), "ARCH-BGL", "TARGET_EVALUATION", 4, 100, 0)
    a, b = hash_sample(units, 40, "tag"), hash_sample(units, 40, "tag")
    assert a.to_list() == b.to_list() and a.sum() == 40
    assert units.filter(a).group_by("stratum").len()["len"].to_list() == [10, 10, 10, 10]
    assert hash_sample(units, 40, "other").to_list() != a.to_list()


def test_jsd_bounds():
    assert _jsd({"a": 3}, {"a": 7}) == 0
    assert _jsd({"a": 1}, {"b": 1}) == pytest.approx(1.0)
