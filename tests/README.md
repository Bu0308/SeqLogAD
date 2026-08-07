# Tests

Test placeholders are organized by behavior rather than implementation chronology.

- `unit/`: schemas, parser, sequences, scoring, retrieval and verifier contracts.
- `integration/`: pipeline boundaries.
- `api/`: HTTP contract tests.
- `agent/`: tool selection, workflow limits and tracing.
- `security/`: prompt injection, fabricated evidence and unsafe generated code.
- `performance/`: throughput and latency harness documentation.

No test logic is implemented in the repository skeleton phase.
