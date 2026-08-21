# Tests

Tests are organized by behavior rather than implementation chronology.

- `unit/`: schemas, parser, sequences, scoring, retrieval and verifier contracts.
- `integration/`: pipeline boundaries.
- `api/`: HTTP contract tests.
- `agent/`: tool selection, workflow limits and tracing.
- `security/`: prompt injection, fabricated evidence and unsafe generated code.
- `performance/`: throughput and latency harness documentation.

The active 73-test suite covers environment, scientific-protocol freeze, canonical event/template/sequence/localization/mutation schemas, checksum, dataset config/acquisition/validation/manifest behavior, and the dataset-integrity integration flow. Most parser/model/retrieval/fusion/downstream test files remain explicit placeholders and do not count as coverage. Future V3 requirements are listed in `Plan/04_TEST_PLAN.md`.
