"""Evaluation units, Sequence windows, time strata and label-blind hash sampling (TV-D4/5/8/9)."""
from __future__ import annotations

import hashlib
from collections import deque

import polars as pl

from seqlogad.sequence.prepare import _sequence_id, _window_id

LINE_UNIT_ARCHITECTURES = {"ARCH-BGL"}  # label granularity: one line; others: one grouping unit


def _hash_int(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def unit_ids(records: pl.DataFrame, architecture: str, partition: str) -> pl.Series:
    if architecture in LINE_UNIT_ARCHITECTURES:
        return ("L" + records["rank"].cast(pl.String)).alias("unit_id")
    return records["group"].map_elements(lambda g: _sequence_id(architecture, partition, g),
                                         return_dtype=pl.String).alias("unit_id")


def build_units(records: pl.DataFrame, architecture: str, partition: str, strata: int,
                chunk_lines: int, embargo_us: int) -> pl.DataFrame:
    """One row per unit, ordered by its last record; HDFS lines without a block are not units."""
    frame = records.with_columns(unit_ids(records, architecture, partition))
    if architecture not in LINE_UNIT_ARCHITECTURES:
        frame = frame.filter(pl.col("gid") >= 0)
    units = frame.group_by("unit_id").agg(
        pl.col("rank").min().alias("first_rank"), pl.col("rank").max().alias("last_rank"),
        pl.col("effective_ts").min().alias("first_ts"), pl.col("effective_ts").max().alias("last_ts"),
        pl.len().alias("n_lines")).sort("last_rank")
    n = units.height
    start_ts = int(records["effective_ts"].min())
    return units.with_row_index("order").with_columns(
        (pl.col("order") * strata // n).cast(pl.Int32).alias("stratum"),
        (pl.col("order") // chunk_lines).cast(pl.Int64).alias("chunk"),
        (pl.col("first_ts") < start_ts + embargo_us).alias("embargo"),
    ).drop("order")


def _quotas(sizes: dict[int, int], total: int) -> dict[int, int]:
    """Proportional allocation with largest remainders (Cochran-style self-weighting)."""
    population = sum(sizes.values())
    if total <= 0 or total >= population:
        return dict(sizes)
    raw = {s: total * size / population for s, size in sizes.items()}
    quota = {s: int(v) for s, v in raw.items()}
    for s in sorted(raw, key=lambda s: (quota[s] - raw[s], s))[: total - sum(quota.values())]:
        quota[s] += 1
    return quota


def hash_sample(units: pl.DataFrame, total: int, tag: str, key: str = "unit_id") -> pl.Series:
    """Boolean mask: within each stratum keep the `quota` units with the smallest salted hash."""
    sizes = dict(units.group_by("stratum").len().iter_rows())
    quota = _quotas(sizes, total)
    ranked = units.select(key, "stratum").with_columns(
        pl.col(key).map_elements(lambda u: _hash_int(f"{tag}|{u}"), return_dtype=pl.UInt64).alias("_h")
    ).with_columns(pl.col("_h").rank("ordinal").over("stratum").alias("_r"))
    limits = pl.Series([quota[s] for s in ranked["stratum"]])
    return (ranked["_r"] <= limits).alias("selected")


def build_windows(records: pl.DataFrame, architecture: str, partition: str, context: int,
                  keep: set[str] | None = None) -> pl.DataFrame:
    """Sequence windows: target record + <= `context` earlier records of its group in this segment."""
    ids = unit_ids(records, architecture, partition)
    cols = {k: [] for k in ("window_id", "sequence_id", "unit_id", "target_rank", "context_ranks",
                            "context_record_count", "target_effective_ts", "context_last_effective_ts",
                            "dedupe_key")}
    histories: dict[str, deque] = {}
    grouped_units = architecture not in LINE_UNIT_ARCHITECTURES
    rows = records.select("rank", "effective_ts", "group", "norm_h").iter_rows()
    for (rank, ts, group, norm_h), unit in zip(rows, ids):
        if grouped_units and group == "GLOBAL":
            continue  # no grouping unit, hence no label unit (same rule as build_units)
        history = histories.setdefault(group, deque(maxlen=context))
        if history and (keep is None or unit in keep):
            signature = ",".join(str(h[2]) for h in history) + f"|{norm_h}"
            for name, value in (("window_id", _window_id(architecture, partition, rank)),
                                ("sequence_id", _sequence_id(architecture, partition, group)),
                                ("unit_id", unit), ("target_rank", rank),
                                ("context_ranks", [h[0] for h in history]),
                                ("context_record_count", len(history)), ("target_effective_ts", ts),
                                ("context_last_effective_ts", history[-1][1]),
                                ("dedupe_key", hashlib.sha256(signature.encode()).hexdigest()[:32])):
                cols[name].append(value)
        history.append((rank, ts, norm_h))
    return pl.DataFrame(cols, schema_overrides={"context_ranks": pl.List(pl.Int64)})
