# Parsing

PARSE-001 implements only the leakage-scoped parser lifecycle:

- `normal_pool.py`: selects and hashes permitted normal `BASE_TRAIN` source
  membership without persisting labels/messages;
- `normalization.py`: isolates HDFS/BGL free-text Content from structured fields
  and inline labels;
- `drain_parser.py`: freezes config, fits Drain3 once, persists/restores it,
  validates identities, exposes immutable `match`, and maps no match to
  `EVT_UNSEEN`;
- `seqlogad.cli.fit_parser`: gate/pool/fit/validate CLI.

Input: accepted raw bytes, ordinary BASE split membership, scoped normal labels,
and `configs/parsing/drain3-v1.yaml`.

Output: ignored reproducible parser-state/provenance directories under
`data/processed/parsers/`.

Dependencies: Drain3 0.9.11, PyYAML, ingestion verification, split/TEST guards,
checksums, and common schemas.

PARSE-002 remains unimplemented: this module does not yet emit the full
partition-scoped canonical `LogEvent` corpus or scientific sequences.
