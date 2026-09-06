"""Label-blind chronological stream index for one architecture (Excel P1.3/P1.5).

One deterministic pass over an architecture's raw files produces:

* the canonical chronological order of its records,
* a per-record segment code used by every fold,
* content hashes for the duplicate checks in LEAK-CS-001,
* field-coverage and parse diagnostics for the buffer readiness checks.

Nothing in this module reads a ground-truth label, a fold role or a model result.
Segment boundaries are fixed fractions of the record count, declared in
``configs/protocols/cross-system-split-v1.yaml`` before any label was inspected.
"""

from __future__ import annotations

import hashlib
import json
from array import array
from bisect import bisect_left
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import pyarrow as pa

from seqlogad.common.checksum import sha256_file
from seqlogad.protocol.architectures import (
    ARCHITECTURES,
    ArchitectureSpec,
    ParseStatus,
    TimestampStatus,
    iter_raw_records,
    resolve_files,
)
from seqlogad.protocol.normalizer import Normalizer
from seqlogad.protocol.nul import NormalizationStatus, canonicalize_nul_message


STREAM_INDEX_SCHEMA_VERSION = "1.0"
STREAM_ROOT = "data/processed/protocol/streams"


# Segment codes. GUARD is never assigned to any partition: it is a temporal buffer
# that keeps SOURCE_TRAIN / TARGET_BURN_IN from being adjacent to the later windows.
SEG_EARLY = 0
SEG_GUARD = 1
SEG_MID = 2
SEG_LATE = 3
SEG_EXCLUDED = 255
SEGMENT_NAMES = {SEG_EARLY: "EARLY", SEG_GUARD: "GUARD", SEG_MID: "MID", SEG_LATE: "LATE"}
ALL_SEGMENT_NAMES = {**SEGMENT_NAMES, SEG_EXCLUDED: "EXCLUDED"}

_TS_STATUS_CODES = {
    TimestampStatus.PARSED: 0,
    TimestampStatus.CONTINUATION: 1,
    TimestampStatus.UNPARSEABLE: 2,
}
_PARSE_STATUS_CODES = {
    ParseStatus.OK: 0,
    ParseStatus.CONTINUATION: 1,
    ParseStatus.MALFORMED: 2,
}


class ChronologyError(RuntimeError):
    """Raised when a stream cannot be indexed without losing a record."""


@dataclass(frozen=True, slots=True)
class SegmentFractions:
    """Cumulative fractions marking the EARLY/GUARD/MID/LATE boundaries."""

    early_end: float
    guard_end: float
    mid_end: float

    def validate(self) -> None:
        if not 0.0 < self.early_end < self.guard_end < self.mid_end < 1.0:
            raise ChronologyError("segment fractions must be strictly increasing in (0,1)")

    def boundaries(self, total: int) -> tuple[int, int, int]:
        """Deterministic floor boundaries; identical inputs give identical cuts."""

        return (
            int(total * self.early_end),
            int(total * self.guard_end),
            int(total * self.mid_end),
        )


def _hash64(payload: bytes) -> int:
    """Stable 64-bit content fingerprint used only for overlap analytics."""

    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big", signed=True)


def _iso(timestamp_us: int | None) -> str | None:
    if timestamp_us is None:
        return None
    return datetime.fromtimestamp(timestamp_us / 1_000_000, tz=timezone.utc).isoformat()


def _spanning_units(cut: int, first_sorted: list[int], last_sorted: list[int]) -> int:
    """How many grouping units are alive across ``cut`` (first < cut <= last)."""

    return bisect_left(first_sorted, cut) - bisect_left(last_sorted, cut)


def _spanning_records(
    cut: int, spans: list[tuple[int, int, int]]
) -> int:
    """Records belonging to units alive across ``cut``; these would be excluded."""

    return sum(size for first, last, size in spans if first < cut <= last)


def quiet_instants(spans: list[tuple[int, int, int]]) -> list[int]:
    """Times at which no grouping unit is alive: the ends of merged unit intervals."""

    if not spans:
        return []
    ordered = sorted((first, last) for first, last, _ in spans)
    instants: list[int] = []
    current_end = ordered[0][1]
    for first, last in ordered[1:]:
        if first > current_end:
            instants.append(current_end + 1)
            current_end = last
        else:
            current_end = max(current_end, last)
    instants.append(current_end + 1)
    return instants


def choose_cut_time(
    nominal_cut: int,
    nominal_rank: int,
    candidates: list[int],
    rank_at,
    spans: list[tuple[int, int, int]],
    minimum_cut: int,
) -> dict:
    """Pick a cut time by minimising the number of records displaced from the plan.

    Two ways to obtain a boundary that no grouping unit straddles:

    * keep the nominal cut and *exclude* every unit alive across it, or
    * *snap* the boundary to a quiet instant, moving records between segments.

    Both are label-blind, and both have an honest cost measured in records. The rule
    is simply to take the cheaper one, so a stream with a natural idle gap keeps all
    of its data while a stream with no idle gap pays a small exclusion instead of a
    large distortion.  Deterministic: candidates are sorted and ties go to the
    earliest.
    """

    nominal_cost = _spanning_records(nominal_cut, spans)
    best = {
        "chosen_time": nominal_cut,
        "strategy": "NOMINAL_CUT_WITH_UNIT_EXCLUSION",
        "displaced_records": nominal_cost,
    }
    for candidate in candidates:
        if candidate <= minimum_cut:
            continue
        cost = abs(rank_at(candidate) - nominal_rank)
        if cost < best["displaced_records"]:
            best = {
                "chosen_time": candidate,
                "strategy": "SNAPPED_TO_QUIET_INSTANT",
                "displaced_records": cost,
            }
    if best["chosen_time"] <= minimum_cut:
        best = {
            "chosen_time": minimum_cut + 1,
            "strategy": "FORCED_MONOTONIC",
            "displaced_records": nominal_cost,
        }
    return best


FLAG_PARSE_OK = 1 << 0
FLAG_LEVEL = 1 << 1
FLAG_SERVICE = 1 << 2
FLAG_COMPONENT = 1 << 3
FLAG_NODE = 1 << 4
FLAG_SESSION = 1 << 5
FLAG_TRACE = 1 << 6

FLAG_NAMES = {
    "parse_ok": FLAG_PARSE_OK,
    "level": FLAG_LEVEL,
    "service": FLAG_SERVICE,
    "component": FLAG_COMPONENT,
    "node_id": FLAG_NODE,
    "session_id": FLAG_SESSION,
    "trace_id": FLAG_TRACE,
}


def segment_field_coverage(part) -> dict:
    """Field presence and parse quality for one materialised segment."""

    total = part.height
    if total == 0:
        return {name: {"present": 0, "ratio": None} for name in FLAG_NAMES}
    coverage = {}
    for name, bit in FLAG_NAMES.items():
        present = int(part.select((pl.col("flags") & bit) != 0).to_series().sum())
        coverage[name] = {"present": present, "ratio": round(present / total, 6)}
    return coverage


def _arrow(values, arrow_type):
    """Zero-copy Arrow array over a compact ``array.array`` buffer."""

    buffer = pa.py_buffer(memoryview(values))
    return pa.Array.from_buffers(arrow_type, len(values), [None, buffer])


def scan_architecture(
    project_root: str | Path,
    spec: ArchitectureSpec,
    normalizer: Normalizer,
    fractions: SegmentFractions,
    *,
    max_records: int | None = None,
) -> tuple[pl.DataFrame, dict]:
    """Index one architecture and return ``(stream_frame, diagnostics)``.

    Columns are accumulated in ``array.array`` buffers rather than Python lists: at
    eleven million records the boxed-integer overhead of a list is the difference
    between a few hundred megabytes and several gigabytes.

    Records are produced in file order, so a *stable* sort on the effective
    timestamp alone reproduces the declared (timestamp, file rank, line number)
    ordering without materialising the last two keys.
    """

    fractions.validate()
    root = Path(project_root).resolve()

    effective_ts = array("q")
    raw_hashes = array("q")
    norm_hashes = array("q")
    group_ids = array("i")
    # Per-record presence bits, so field coverage and parse quality can be reported
    # *per segment* rather than only for the architecture as a whole. A readiness
    # check that measured the whole stream would say nothing about the buffer.
    flags = array("B")

    group_index: dict[str, int] = {}
    parse_counts: Counter[str] = Counter()
    ts_counts: Counter[str] = Counter()
    field_present: Counter[str] = Counter()
    nul_escaped = 0
    empty_normalized = 0
    inversions = 0
    previous_ts: int | None = None

    files = resolve_files(root, spec)
    file_index = {path.relative_to(root).as_posix(): rank for rank, path in enumerate(files)}
    last_ts_by_file: dict[int, int] = {}

    canonicalize = canonicalize_nul_message
    normalize = normalizer.normalize

    for record in iter_raw_records(root, spec, max_records=max_records):
        file_rank = file_index[record.source_file]
        parse_counts[str(record.parse_status)] += 1
        ts_counts[str(record.timestamp_status)] += 1

        if record.timestamp_us is not None:
            stamp = record.timestamp_us
            last_ts_by_file[file_rank] = stamp
        else:
            # Continuation / unparseable lines inherit the previous timestamp *inside
            # the same file* so they stay adjacent to the record they belong to. The
            # honest status is preserved separately in ``timestamp_status``.
            stamp = last_ts_by_file.get(file_rank, 0)

        if previous_ts is not None and stamp < previous_ts:
            inversions += 1
        previous_ts = stamp

        canonical = canonicalize(record.raw_message_bytes)
        if canonical.normalization_status is NormalizationStatus.NUL_ESCAPED:
            nul_escaped += 1
        normalized = normalize(canonical.canonical_message)
        if not normalized:
            empty_normalized += 1

        effective_ts.append(stamp)
        raw_hashes.append(_hash64(record.raw_message_bytes))
        norm_hashes.append(_hash64(normalized.encode("utf-8")))
        if record.session_id is None:
            group_ids.append(-1)
        else:
            gid = group_index.get(record.session_id)
            if gid is None:
                gid = len(group_index)
                group_index[record.session_id] = gid
            group_ids.append(gid)

        bits = 0
        if record.parse_status is ParseStatus.OK:
            bits |= FLAG_PARSE_OK
            field_present["parse_ok"] += 1
        if record.level is not None:
            bits |= FLAG_LEVEL
            field_present["level"] += 1
        if record.service is not None:
            bits |= FLAG_SERVICE
            field_present["service"] += 1
        if record.component is not None:
            bits |= FLAG_COMPONENT
            field_present["component"] += 1
        if record.node_id is not None:
            bits |= FLAG_NODE
            field_present["node_id"] += 1
        if record.session_id is not None:
            bits |= FLAG_SESSION
            field_present["session_id"] += 1
        if record.trace_id is not None:
            bits |= FLAG_TRACE
            field_present["trace_id"] += 1
        flags.append(bits)

    total = len(effective_ts)
    if total == 0:
        raise ChronologyError(f"{spec.architecture_id}: no records scanned")
    declared_groups = len(group_index)
    group_index.clear()

    table = pa.table(
        {
            "effective_ts": _arrow(effective_ts, pa.int64()),
            "raw_h": _arrow(raw_hashes, pa.int64()),
            "norm_h": _arrow(norm_hashes, pa.int64()),
            "gid": _arrow(group_ids, pa.int32()),
            "flags": _arrow(flags, pa.uint8()),
        }
    )
    frame = pl.from_arrow(table)
    del effective_ts, raw_hashes, norm_hashes, group_ids, flags, table

    frame = frame.with_row_index("file_position").sort(
        "effective_ts", maintain_order=True
    )
    frame = frame.drop("file_position").with_row_index("rank").with_columns(
        pl.col("rank").cast(pl.Int64)
    )

    b1, b2, b3 = fractions.boundaries(total)


    # Cut *times*, read off the chronological stream at the rank boundaries. Every
    # partition boundary is ultimately a time boundary, so these are what the
    # ordering invariants are stated against. Each nominal cut is then snapped back
    # to the latest quiet instant inside a declared search window, which keeps
    # boundary exclusions small wherever the stream actually has a quiet point.
    unit_spans = (
        frame.filter(pl.col("gid") >= 0)
        .group_by("gid")
        .agg(
            pl.col("effective_ts").min().alias("first_ts"),
            pl.col("effective_ts").max().alias("last_ts"),
            pl.len().alias("records"),
        )
    )
    spans = [
        (int(row["first_ts"]), int(row["last_ts"]), int(row["records"]))
        for row in unit_spans.iter_rows(named=True)
    ]
    del unit_spans
    first_sorted = sorted(span[0] for span in spans)
    last_sorted = sorted(span[1] for span in spans)
    candidates = quiet_instants(spans)

    sorted_ts = frame["effective_ts"].to_list()

    def rank_at(moment: int) -> int:
        return bisect_left(sorted_ts, moment)

    cut_times: list[int] = []
    cut_details: list[dict] = []
    minimum_cut = -1
    for name, index in (("early_end", b1), ("guard_end", b2), ("mid_end", b3)):
        if index >= total:
            continue
        nominal = int(sorted_ts[index])
        decision = choose_cut_time(nominal, index, candidates, rank_at, spans, minimum_cut)
        chosen = decision["chosen_time"]
        minimum_cut = chosen
        cut_times.append(chosen)
        cut_details.append(
            {
                "boundary": name,
                "nominal_rank": index,
                "nominal_time_utc": _iso(nominal),
                "chosen_time_utc": _iso(chosen),
                "chosen_rank": rank_at(chosen),
                "strategy": decision["strategy"],
                "displaced_records": decision["displaced_records"],
                "units_alive_at_chosen_cut": _spanning_units(chosen, first_sorted, last_sorted),
                "quiet_instant_candidates": len(candidates),
            }
        )
    del sorted_ts

    def _segment_expression(column: str) -> pl.Expr:
        codes = (SEG_EARLY, SEG_GUARD, SEG_MID, SEG_LATE)
        expression = pl.when(pl.col(column) < cut_times[0]).then(
            pl.lit(codes[0], dtype=pl.UInt8)
        )
        for position, cut in enumerate(cut_times[1:], start=1):
            expression = expression.when(pl.col(column) < cut).then(
                pl.lit(codes[position], dtype=pl.UInt8)
            )
        return expression.otherwise(pl.lit(codes[len(cut_times)], dtype=pl.UInt8))

    frame = frame.with_columns(_segment_expression("effective_ts").alias("rank_segment"))

    # Grouping-unit handling, in two label-blind steps.
    #
    # (a) Integrity: a unit (HDFS block, Hadoop application, OpenStack instance)
    #     follows the segment of its *last* record, so it is never split.
    # (b) Boundary exclusion: a unit whose lifetime *crosses* a cut time is removed
    #     from every partition. Without this, concurrent long-lived units (Hadoop
    #     applications overlap heavily) would put burn-in records after evaluation
    #     records in wall-clock time and quietly break chronological separation.
    #     Exclusions are counted and hashed, never silent.
    straddling_groups = 0
    excluded_groups = 0
    total_groups = 0
    grouped = frame.filter(pl.col("gid") >= 0)
    if grouped.height:
        group_stats = grouped.group_by("gid").agg(
            pl.col("rank_segment").n_unique().alias("distinct_segments"),
            pl.col("effective_ts").min().alias("group_first_ts"),
            pl.col("effective_ts").max().alias("group_last_ts"),
        )
        total_groups = group_stats.height
        straddling_groups = int(group_stats.filter(pl.col("distinct_segments") > 1).height)

        crosses = pl.lit(False)
        for cut in cut_times:
            crosses = crosses | (
                (pl.col("group_first_ts") < cut) & (pl.col("group_last_ts") >= cut)
            )
        group_stats = group_stats.with_columns(crosses.alias("crosses_cut"))
        excluded_groups = int(group_stats.filter(pl.col("crosses_cut")).height)
        group_stats = group_stats.with_columns(
            pl.when(pl.col("crosses_cut"))
            .then(pl.lit(SEG_EXCLUDED, dtype=pl.UInt8))
            .otherwise(_segment_expression("group_last_ts"))
            .alias("group_segment")
        ).select("gid", "group_segment")
        del grouped
        frame = frame.join(group_stats, on="gid", how="left")
        del group_stats
    else:
        frame = frame.with_columns(pl.lit(None, dtype=pl.UInt8).alias("group_segment"))

    frame = (
        frame.with_columns(
            pl.coalesce([pl.col("group_segment"), pl.col("rank_segment")]).alias("segment")
        )
        .sort("rank")
        .select("rank", "effective_ts", "raw_h", "norm_h", "gid", "flags", "segment")
    )

    segment_counts = {}
    segment_bounds = {}
    for code, name in ALL_SEGMENT_NAMES.items():
        part = frame.filter(pl.col("segment") == code)
        segment_counts[name] = int(part.height)
        segment_bounds[name] = {
            "records": int(part.height),
            "field_coverage": segment_field_coverage(part),
            "distinct_normalized_messages": int(part["norm_h"].n_unique()) if part.height else 0,
            "first_rank": int(part["rank"].min()) if part.height else None,
            "last_rank": int(part["rank"].max()) if part.height else None,
            "first_timestamp_utc": _iso(int(part["effective_ts"].min())) if part.height else None,
            "last_timestamp_utc": _iso(int(part["effective_ts"].max())) if part.height else None,
        }

    parsed = frame.filter(pl.col("effective_ts") > 0)
    diagnostics = {
        "schema_version": STREAM_INDEX_SCHEMA_VERSION,
        "architecture_id": spec.architecture_id,
        "dataset_id": spec.dataset_id,
        "domain": spec.domain,
        "adapter": spec.adapter,
        "evaluation_grouping": spec.evaluation_grouping,
        "target_eligibility": str(spec.target_eligibility),
        "record_count": total,
        "source_files": [
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
        "source_file_count": len(files),
        "stream_order": "TIMESTAMP_THEN_FILE_RANK_THEN_LINE_NUMBER",
        "stream_order_implementation": "STABLE_SORT_ON_EFFECTIVE_TIMESTAMP_OVER_FILE_ORDER",
        "file_append_order_inversions": inversions,
        "file_append_order_monotonic": inversions == 0,
        "timestamp_status_counts": dict(ts_counts),
        "parse_status_counts": dict(parse_counts),
        "records_dropped": 0,
        "records_excluded_from_partitions": int(
            frame.filter(pl.col("segment") == SEG_EXCLUDED).height
        ),
        "field_coverage": {
            name: {"present": int(field_present.get(name, 0)),
                   "ratio": round(field_present.get(name, 0) / total, 6)}
            for name in FLAG_NAMES
        },
        "first_timestamp_utc": _iso(int(parsed["effective_ts"].min())) if parsed.height else None,
        "last_timestamp_utc": _iso(int(parsed["effective_ts"].max())) if parsed.height else None,
        "nul_escaped_records": nul_escaped,
        "empty_normalized_records": empty_normalized,
        "distinct_raw_messages": int(frame["raw_h"].n_unique()),
        "distinct_normalized_messages": int(frame["norm_h"].n_unique()),
        "grouping_units": total_groups,
        "grouping_units_declared": declared_groups,
        "grouping_units_straddling_rank_segments": straddling_groups,
        "grouping_units_excluded_at_cut_times": excluded_groups,
        "excluded_records": int(frame.filter(pl.col("segment") == SEG_EXCLUDED).height),
        "excluded_record_ratio": round(
            frame.filter(pl.col("segment") == SEG_EXCLUDED).height / total, 6
        ),
        "grouping_integrity_rule": "UNIT_ASSIGNED_TO_SEGMENT_OF_ITS_LAST_RECORD",
        "boundary_exclusion_rule": "UNIT_LIFETIME_CROSSING_A_CUT_TIME_IS_EXCLUDED_FROM_ALL_PARTITIONS",
        "cut_times_utc": [_iso(cut) for cut in cut_times],
        "cut_selection_rule": "MINIMISE_DISPLACED_RECORDS_OVER_SNAP_OR_EXCLUDE",
        "segment_fractions": {
            "early_end": fractions.early_end,
            "guard_end": fractions.guard_end,
            "mid_end": fractions.mid_end,
        },
        "segment_nominal_rank_boundaries": {"early_end": b1, "guard_end": b2, "mid_end": b3},
        "cut_selection": cut_details,
        "segment_counts": segment_counts,
        "segments": segment_bounds,
        "labels_read": False,
        "fold_role_read": False,
    }
    return frame, diagnostics


def stream_directory(project_root: str | Path, architecture_id: str) -> Path:
    return Path(project_root).resolve() / STREAM_ROOT / architecture_id.lower()


def write_stream_index(
    project_root: str | Path,
    architecture_id: str,
    frame: pl.DataFrame,
    diagnostics: dict,
) -> dict:
    """Persist the stream index and bind its SHA-256 into the diagnostics."""

    directory = stream_directory(project_root, architecture_id)
    directory.mkdir(parents=True, exist_ok=True)
    stream_path = directory / "stream.parquet"
    frame.write_parquet(stream_path, compression="zstd")
    diagnostics = dict(diagnostics)
    diagnostics["stream_parquet"] = stream_path.relative_to(
        Path(project_root).resolve()
    ).as_posix()
    diagnostics["stream_parquet_sha256"] = sha256_file(stream_path)
    index_path = directory / "stream-index.json"
    index_path.write_text(
        json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return dict(diagnostics, stream_index_sha256=sha256_file(index_path))


def load_stream_index(project_root: str | Path, architecture_id: str) -> dict:
    """Load a stream index and attach its own digest.

    The digest is computed at read time rather than stored: a file cannot contain
    its own SHA-256, and downstream manifests need to bind the index they used.
    """

    path = stream_directory(project_root, architecture_id) / "stream-index.json"
    if not path.is_file():
        raise ChronologyError(f"missing stream index for {architecture_id}: {path}")
    index = json.loads(path.read_text(encoding="utf-8"))
    index["stream_index_sha256"] = sha256_file(path)
    return index


def load_stream_frame(project_root: str | Path, architecture_id: str) -> pl.DataFrame:
    path = stream_directory(project_root, architecture_id) / "stream.parquet"
    if not path.is_file():
        raise ChronologyError(f"missing stream parquet for {architecture_id}: {path}")
    return pl.read_parquet(path)


__all__ = [
    "ALL_SEGMENT_NAMES",
    "FLAG_NAMES",
    "segment_field_coverage",
    "quiet_instants",
    "choose_cut_time",
    "SEGMENT_NAMES",
    "SEG_EXCLUDED",
    "SEG_EARLY",
    "SEG_GUARD",
    "SEG_LATE",
    "SEG_MID",
    "STREAM_ROOT",
    "ChronologyError",
    "SegmentFractions",
    "load_stream_frame",
    "load_stream_index",
    "scan_architecture",
    "stream_directory",
    "write_stream_index",
]
