# Handoff template

Primary summary must be at most 12 lines. Keep detail compact and pointer-based.

```text
TASK_ID: <id>
STATUS: <COMPLETE|BLOCKED|FAILED>
FROZEN_VERSION: PROTOCOL-001 v1.1 + binding addenda
INPUTS/HASHES: <paths and SHA-256>
OBJECTIVE/IMPLEMENTATION: <one line>
SCIENTIFIC_DECISIONS_CHANGED: NONE | <conflict code; no change applied>
FILES: <repository-relative paths>
OUTPUTS/HASHES: <paths and SHA-256>
TESTS/DETERMINISM: <commands; result; deterministic status>
TEST_STATUS: SEALED / NEVER_OPENED; no access
LABEL/LEAKAGE_STATUS: <label use; leakage result>
BLOCKERS/NEXT_AUTHORIZED_TASK: <blocker/conflict code or NONE>; <task without starting it>
```
