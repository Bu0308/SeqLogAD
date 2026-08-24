# META-001 — Raw Group and Chronology Metadata Contract

| Field | Frozen implementation state |
|---|---|
| Task | META-001 |
| Schema version | 1.0 |
| Status | COMPLETE |
| Scientific result status | NOT_RUN |
| Scientific split created | false |
| Scientific TEST assigned/accessed | false |
| Parser/template state used | false |
| Labels used for grouping/chronology | false |
| Source module | src/seqlogad/ingestion/raw_metadata.py |
| Method/source note | docs/references/META-001-citations.md |

META-001 implements only the parser-independent metadata layer required before
SPLIT-001. It does not create a five-way partition, parse templates, build
scientific events/sequences, or expose TEST.

## 1. Verified raw-format findings

Read-only structural inspection of the accepted manifest-bound bytes found:

- HDFS is ASCII/UTF-8-compatible text with CRLF terminators. The accepted log
  contains both positive and negative identifiers, such as
  blk_7503483334202473044 and blk_-1608999687919862906.
- The HDFS source can repeat the same block identifier within one line, for
  example in both message text and a path. The extractor records raw
  occurrences and canonical unique IDs separately.
- A full read-only matcher scan of accepted HDFS found no line without a valid
  blk_-?[0-9]+ token and no line with more than one distinct valid block ID.
  These are observations, not assumptions: tests and implementation still
  support no-ID, malformed, duplicate, and multi-distinct-ID cases.
- BGL is ASCII/UTF-8-compatible, line-oriented text. Its structural prefix is
  label, epoch, date, node, detailed timestamp; the detailed timestamp uses
  YYYY-MM-DD-HH.MM.SS.microseconds.
- A full read-only structural scan found accepted BGL detailed timestamps
  parseable and non-decreasing in source order. Source order remains canonical
  even if a future malformed/regressing record is encountered.

No label distribution, anomaly score, AP/F1, parser output, or scientific
partition was computed during this inspection.

## 2. HDFS extraction contract

For every exact raw line, the extractor records:

- manifest-bound source identity and raw-line LOG-SHA256 identity;
- one-based source line and zero-based chronology;
- exact-line SHA-256 and line-ending/UTF-8 status;
- all valid raw block-token occurrences;
- normalized unique block IDs (blk_0007 becomes blk_7);
- duplicate IDs, malformed block candidates, and explicit issues;
- final connected-component identity or an explicit unassigned reason.

A block ID is a source session identity. A component ID is the atomic grouping
identity used by the future splitter. Multiple distinct block IDs on one line
are unioned, including transitive co-occurrence. Component members are sorted
numerically and identified by a full SHA-256 of canonical member JSON.

The component chronology key is its earliest source line index; component ID is
independent of labels and chronology. Lines with no usable block are retained
as UNASSIGNED with NO_BLOCK_ID, MALFORMED_BLOCK_TOKEN, or DECODE_ERROR.

Implementation complexity:

- first pass: union-find over block co-occurrence;
- second pass: emit every line with final component ID;
- time: O(N alpha(B)), where N is lines and B is unique block IDs;
- memory: O(B) plus output buffers; raw message text is not retained.

## 3. BGL chronology contract

The authoritative rank is zero-based source-line order:

    original_line_index = chronological_rank = source_line_number - 1

The detailed timestamp is parsed and normalized without inventing a timezone.
It audits ties/regressions but does not reorder the immutable source. Ties use
source-line rank. Malformed timestamps and decode failures remain explicit.

The chronology ID hashes repository-relative source path, source-line index,
and normalized timestamp (or null). It does not include or parse the first BGL
anomaly-label value. The exact line-level record ID still hashes every raw byte
for provenance, so changing any source byte changes raw occurrence identity
while structural chronology identity remains stable.

META-001 does not create 100-event BGL parents. Consecutive ranks are the
minimal input needed by SPLIT-001 and later partition-contained windows.

Implementation complexity is O(N) time and O(1) streaming state.

## 4. Label and parser boundary

The extractor resolves only the configured required file whose role is log.
It never opens HDFS anomaly_label.csv, does not retain the BGL first-field
label, and exposes no label field. Synthetic invariants prove:

- changing HDFS label-like text does not change block/component identity;
- changing the BGL first-field label does not change chronology ID/rank;
- metadata schemas contain no label or partition fields;
- summaries state labels_used=false, parser_used=false,
  scientific_split_created=false, and test_partition_assigned=false.

Drain3 and seqlogad.parsing are not dependencies of this module.

## 5. Determinism and artifact policy

Persisted records use canonical sorted-key JSONL and full SHA-256 digests.
Python process-dependent hash() is never used. HDFS lines/components and BGL
lines have deterministic ordering.

Complete artifacts, when explicitly requested, use:

    data/processed/metadata/<dataset>/
    ├── lines.jsonl
    ├── components.jsonl   # HDFS only
    └── summary.json

The writer uses a temporary sibling, refuses overwrite, records content
hashes/counts, then atomically renames it. data/processed is ignored because
full metadata is large and regenerable. META-001 generated no full real
metadata artifact during validation.

## 6. CLI

Safe bounded validation:

    seqlogad-extract-raw-metadata --project-root . --dataset hdfs --dry-run --max-lines 1000 --json
    seqlogad-extract-raw-metadata --project-root . --dataset bgl --dry-run --max-lines 1000 --json

Explicit complete metadata generation for a later approved workflow:

    seqlogad-extract-raw-metadata --project-root . --dataset hdfs --output-dir data/processed/metadata/hdfs

There is deliberately no split, TEST, parser, template, window, baseline, or
experiment option in this CLI.

## 7. Downstream boundary

SPLIT-001 has consumed this contract to create deterministic raw partition
artifacts and unopened physical TEST seals. See
[`split-artifacts-and-test-seal.md`](split-artifacts-and-test-seal.md). The next
dependency, PARSE-001, subsequently consumed ordinary `BASE_TRAIN` membership and
is now complete with frozen parser states. META-001 itself remains unchanged.

PURGE-AUDIT-001 subsequently returned a representativeness concern.
PURGE-DECISION-001 resolved it with human-approved Option B: the primary split
remains unchanged and a separate purge sensitivity is pre-registered but not
run. `CANONICAL-EVENT-001` is now authorized next. META-001, Drain3, split
membership, and TEST remain unchanged.
