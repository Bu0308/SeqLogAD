# Tests

Tests are organized by behavior rather than implementation chronology.

- `unit/`: schemas, parser, sequences, scoring, retrieval and verifier contracts.
- `integration/`: pipeline boundaries.
- `api/`: HTTP contract tests.
- `agent/`: tool selection, workflow limits and tracing.
- `security/`: prompt injection, fabricated evidence and unsafe generated code.
- `performance/`: throughput and latency harness documentation.

The active suite covers environment, protocol v1.1/history/addenda, synthetic exact-split contract arithmetic/identity, canonical event/template/sequence/localization/mutation schemas, checksum, dataset config/acquisition/validation/manifest behavior, and the dataset-integrity integration flow. Test count is taken from the latest actual run, not hard-coded here. The real splitter/TEST guard, parser, baseline, and sequence-control implementations remain planned unless their tests contain real assertions. Requirements are listed in `Plan/04_TEST_PLAN.md`.
