# SCHEMA-COMPAT-001 — Contract and Citation Provenance

| Field | Value |
|---|---|
| Task | `SCHEMA-COMPAT-001` |
| Date | 2026-08-22 |
| Status | `COMPLETE` |
| Empirical status | `NOT_RUN` |
| Scientific TEST accessed | `false` |

## Sources actually consulted

This compatibility decision is derived from version-controlled SeqLogAD contracts, not from an external algorithm or reported paper result:

1. `docs/research-protocol-v1.1.md` and `configs/protocols/protocol-v1.1.yaml` — active protocol identity, five partitions, HDFS grouping, BGL 100-event parents, label isolation, and TEST boundary.
2. `docs/statistical-decision-contract.md` and `configs/protocols/effect-001.yaml` — KT-3 paired-control invariants, registered shuffle seeds, retained no-op policy, dataset-specific AP decisions, and TEST ownership.
3. `docs/research-protocol-v1.0.md` and `configs/protocols/protocol-v1.yaml` — preserved historical identity and former BGL residual-window semantics.
4. `docs/schemas/canonical-events.md`, `docs/schemas/event-sequences-and-localization.md`, and `src/seqlogad/common/schemas/` — implemented record boundaries and the incompatibilities audited here.
5. `docs/references/SCHEMA-001-citations.md`, `docs/references/SCHEMA-002-citations.md`, and `docs/references/EFFECT-001-citations.md` — provenance of the parent contracts; no finding is reinterpreted as a SeqLogAD result.

## External citation status

No new external paper, code, metric, or method was copied or relied upon to choose the compatibility mechanism. Therefore this task adds no new bibliographic citation. Existing papers remain cited in the parent contract notes above.

## SeqLogAD decisions

- Support explicit historical Protocol `1.0` and active Protocol `1.1`; reject omission and unsupported values.
- Require the active factory for new identities; do not silently relabel history.
- Keep record-format `schema_version=1.0` distinct from scientific `protocol_version`.
- Interpret active-v1.1 BGL parents as exactly 100 events while retaining explicit-v1.0 residual parsing.
- Preserve future active-v1.1 trailing BGL residual provenance as an excluded raw range rather than a scientific parent sequence.
- Keep synthetic anomaly `MutationRecord` separate from KT-3 `SequenceDestructionRecord`.
- Record retained unperturbable no-ops and forbid TEST-label exposure.

These are repository contract decisions. They are not novelty claims and do not constitute an experiment.

## Scope assurance

Only synthetic unit fixtures were created. No raw byte, dataset manifest, real split, parsed event, real sequence, shuffle artifact, model, metric, or scientific TEST partition was read or generated.
