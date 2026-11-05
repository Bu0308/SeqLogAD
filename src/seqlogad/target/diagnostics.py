"""Label-free drift diagnostics between the burn-in buffer and evaluation strata (TV-001 section 6)."""
from __future__ import annotations

import math

import polars as pl


def memory(buffer: pl.DataFrame) -> pl.DataFrame:
    """B0 target memory: counts of every template key and normalized message in the buffer."""
    keys = buffer.group_by("template_key").len("count").with_columns(pl.lit("template_key").alias("field"))
    msgs = buffer.group_by("norm_h").len("count").with_columns(pl.lit("norm_h").alias("field"))
    return pl.concat([keys.rename({"template_key": "value"}),
                      msgs.with_columns(pl.col("norm_h").cast(pl.String)).rename({"norm_h": "value"})]
                     ).select("field", "value", "count")


def _jsd(p: dict[str, int], q: dict[str, int]) -> float:
    """Jensen-Shannon divergence in bits between two count tables (0 = identical, 1 = disjoint)."""
    sp, sq = sum(p.values()), sum(q.values())
    total = 0.0
    for key in set(p) | set(q):
        a, b = p.get(key, 0) / sp, q.get(key, 0) / sq
        m = (a + b) / 2
        total += (a * math.log2(a / m) if a else 0.0) + (b * math.log2(b / m) if b else 0.0)
    return total / 2


def drift_report(buffer: pl.DataFrame, evaluation: pl.DataFrame, line_strata: pl.Series) -> list[dict]:
    """Per evaluation stratum: unseen-template rate, unseen-message rate, template JSD to the buffer."""
    seen_keys = set(buffer["template_key"].unique().to_list())
    seen_msgs = set(buffer["norm_h"].unique().to_list())
    base = dict(buffer.group_by("template_key").len().iter_rows())
    frame = evaluation.with_columns(line_strata.alias("stratum"))
    report = []
    for (stratum,), part in sorted(frame.group_by("stratum"), key=lambda kv: kv[0][0]):
        counts = dict(part.group_by("template_key").len().iter_rows())
        report.append({
            "stratum": int(stratum), "lines": part.height,
            "unseen_template_line_rate": float((~part["template_key"].is_in(list(seen_keys))).mean()),
            "unseen_message_line_rate": float((~part["norm_h"].is_in(list(seen_msgs))).mean()),
            "template_jsd_bits": round(_jsd(base, counts), 6)})
    return report
