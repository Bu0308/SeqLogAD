# Tests

Tests are organized by behavior rather than implementation chronology.

- `unit/`: schemas, parser, sequences, scoring, retrieval and verifier contracts.
- `integration/`: pipeline boundaries.
- `api/`: HTTP contract tests.
- `agent/`: tool selection, workflow limits and tracing.
- `security/`: prompt injection, fabricated evidence and unsafe generated code.
- `performance/`: throughput and latency harness documentation.

The active suite covers environment, protocol v1.1/history/addenda, exact split arithmetic/identity, deterministic HDFS/BGL synthetic split workflows, TEST-seal and human-unlock fixtures, canonical event/template/sequence/localization/mutation schemas, checksum, dataset config/acquisition/validation/manifest behavior, and the dataset-integrity integration flow. Test count is taken from the latest actual run, not hard-coded here. Parser, baseline, and sequence-control implementations remain planned. Requirements are listed in `Plan/04_TEST_PLAN.md`.
