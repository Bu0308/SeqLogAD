"""Raw corpus -> normalized target records for chosen segments, verified against the frozen stream.

Reuses the frozen Phase 2 helpers unchanged (they are inside the V13R1 implementation
digest). The raw adapters return message bytes only; no label column is produced.
"""
from __future__ import annotations

from pathlib import Path

import polars as pl

from seqlogad.common.checksum import sha256_file
from seqlogad.fusion.volatile import is_volatile
from seqlogad.protocol.architectures import ADAPTERS, ARCHITECTURES, resolve_files
from seqlogad.protocol.normalizer import load_normalizer
from seqlogad.protocol.nul import canonicalize_nul_message
from seqlogad.semantic.contracts import read
from seqlogad.semantic.prepare import hash64, locate_source_rows

SEGMENT_CODES = {"EARLY": 0, "GUARD": 1, "MID": 2, "LATE": 3}


def template_key(message: str, min_digits: int) -> str:
    """A-priori template rule (TV-D6): words with >= min_digits digits become <V>."""
    if min_digits != 3:
        raise ValueError("template rule is frozen to fusion.volatile (3 digits)")
    return " ".join("<V>" if is_volatile(w) else w for w in message.split(" "))


def load_stream(root: Path, architecture: str) -> tuple[pl.DataFrame, dict]:
    folder = root / "data/processed/protocol/streams" / architecture.lower()
    index = read(folder / "stream-index.json")
    if sha256_file(folder / "stream.parquet") != index["stream_parquet_sha256"]:
        raise ValueError(f"{architecture}: frozen stream checksum mismatch")
    return pl.read_parquet(folder / "stream.parquet"), index


def _positions(root: Path, architecture: str, stream: pl.DataFrame, index: dict, codes: set[int]) -> pl.DataFrame:
    # locate_source_rows verifies every raw line against the stream and keeps segments {0, 2};
    # mark the wanted rows 0 and the rest 1 so its frozen verification is reused unchanged.
    marked = stream.with_columns(
        pl.when(pl.col("segment").is_in(list(codes))).then(0).otherwise(1).cast(pl.UInt8).alias("segment"))
    located = locate_source_rows(root, architecture, marked, index).select("rank", "file_position")
    return located.join(stream, on="rank", how="inner", validate="1:1").sort("file_position")


def _normalize(root: Path, architecture: str, selected: pl.DataFrame, index: dict) -> list[str]:
    normalizer = load_normalizer(root)
    if normalizer.rule_file_sha256 != index["normalizer"]["rule_file_sha256"]:
        raise ValueError("normalizer changed since the frozen stream")
    spec = ARCHITECTURES[architecture]
    adapter = ADAPTERS[spec.adapter]
    wanted = iter(selected.select("file_position", "norm_h").iter_rows())
    current, position, texts = next(wanted, None), 0, []
    for path in resolve_files(root, spec):
        with path.open("rb") as handle:
            for number, line in enumerate(handle, 1):
                if current and position == current[0]:
                    record = adapter(line, path.relative_to(root).as_posix(), number)
                    text = normalizer.normalize(canonicalize_nul_message(record.raw_message_bytes).canonical_message)
                    if hash64(text.encode()) != current[1]:
                        raise ValueError(f"{architecture}: normalized text differs from frozen norm_h")
                    texts.append(text)
                    current = next(wanted, None)
                position += 1
    if current is not None or len(texts) != selected.height:
        raise ValueError(f"{architecture}: incomplete materialization")
    return texts


def materialize(root: Path, architecture: str, segments: list[str], min_digits: int) -> tuple[pl.DataFrame, dict]:
    """Return rank-ordered records of the requested segments with text and template key."""
    stream, index = load_stream(root, architecture)
    codes = {SEGMENT_CODES[s] for s in segments}
    selected = _positions(root, architecture, stream, index, codes)
    texts = _normalize(root, architecture, selected, index)
    frame = selected.with_columns(pl.Series("normalized_message", texts)).with_columns(
        pl.col("normalized_message").map_elements(lambda m: template_key(m, min_digits),
                                                  return_dtype=pl.String).alias("template_key"),
        pl.when(pl.col("gid") >= 0).then(pl.concat_str([pl.lit("G"), pl.col("gid")]))
        .otherwise(pl.lit("GLOBAL")).alias("group"))
    return frame.select("rank", "segment", "effective_ts", "gid", "group", "norm_h",
                        "normalized_message", "template_key").sort("rank"), index
