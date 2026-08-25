# Escalation

Stop normal work and return the narrowest applicable code:

| Code | Use when |
|---|---|
| `FROZEN_CONTRACT_CONFLICT` | Assignment contradicts a frozen scientific rule |
| `PLAN_CONFLICT_DETECTED` | Active plan/task/dependency instructions conflict |
| `TEST_BOUNDARY_CONFLICT` | TEST access, exposure, use, or seal policy is threatened |
| `STATE_MISMATCH_DETECTED` | Repository state/status differs from the active registry |
| `IDENTITY_MISMATCH` | Dataset/split/parser/artifact identity or hash differs |
| `LABEL_LEAKAGE_DETECTED` | Labels enter an unauthorized scope or reveal forbidden information |
| `NONDETERMINISTIC_ARTIFACT` | Required deterministic reproduction differs |
| `SCHEMA_GAP` | Frozen behavior cannot be represented without a schema decision |
| `SCIENTIFIC_GATE_REQUIRED` | Work requires an unopened human-owned conditional gate |

Report the code in `SCIENTIFIC_DECISIONS_CHANGED` or `BLOCKERS`, never as `STATUS`:

```text
<CODE>
RULE: <precise rule and authoritative path/section>
EVIDENCE: <repository evidence and verified external citations if methodological>
CONSEQUENCE: <what cannot proceed and why>
MINIMUM_AMENDMENT: <smallest human-owned pre-result amendment required>
VERIFIED_CITATIONS: <authoritative repository paths and source links>
```

Do not repair the plan. Methodological claims require verified sources newest-first (2026→2025→2024→seminal) and classification as `LITERATURE_SUPPORTED`, `LITERATURE_INFORMED_SEQLOGAD_DECISION`, `SEQLOGAD_PROTOCOL_DECISION`, or `ENGINEERING_DECISION`.
