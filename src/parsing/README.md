# Parsing

Converts raw log lines into canonical events, templates, event IDs and parameters.

Input: raw HDFS/BGL log lines.

Output: parsed events, template records and parser metadata in Parquet-compatible schemas.

Dependencies: Drain3, Polars, PyArrow and common schemas.

Planned files: `drain_parser.py`, `normalization.py`, `bgl_adapter.py`.

Implementation status: no parser implementation exists yet.
