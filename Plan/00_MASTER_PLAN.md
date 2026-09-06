# 00 — Master Plan Index

## Authoritative plan

**[`../Bang_ke_hoach_SeqLogAD.xlsx`](../Bang_ke_hoach_SeqLogAD.xlsx)** — the
researcher's workbook. It defines the phases, the 32 micro-tasks, the gates and the
definitions of done. Machine-readable projection:
[`../configs/plan/excel-roadmap-v1.yaml`](../configs/plan/excel-roadmap-v1.yaml).
Where any plan document in this directory disagrees with the workbook, the workbook
wins. See [`../docs/migration/EXCEL-PLAN-MIGRATION-001.md`](../docs/migration/EXCEL-PLAN-MIGRATION-001.md).

Phase 1 is complete; G0 is `PROTOCOL_READY_PENDING_RESEARCHER_SIGNATURE`;
`NEXT_AUTHORIZED_TASK = P2.1`.

## Supporting implementation plan

- [Master implementation plan v2 — Domain-Adaptive Fusion](master-implementation-plan-v2-domain-adaptive-fusion.md)
  — narrative companion to the workbook, subordinate to it.

The user approved a strategic redirect on 2026-08-28, and on 2026-09-06 declared the
workbook above the authoritative roadmap. The v2 plan describes the same research
direction and now serves as its narrative companion, not as an independent authority.
The former v1.1 protocol, its HDFS/BGL artifacts, TEST seals and decisions are
retained as historical provenance; they are not deleted, and they are not
reinterpreted as results for the cross-system goal.

Current topic:

> **Domain-Adaptive Fusion for Zero-Label Cross-System Log Anomaly Detection**

Current question:

> Can a fusion model transfer knowledge across heterogeneous source systems,
> then adapt to an unseen target architecture using only its unlabeled normal-log
> buffer and detect anomalies with calibrated, explainable evidence?

## Current state

Historical assets that remain available for reuse as source-domain material:

- HDFS/BGL acquisition, checksums, manifests, fingerprints, and verification;
- Python 3.12 environment/package contract;
- canonical event/template and sequence/localization/mutation schema contracts;
- Protocol-v1.1 schema compatibility and KT-3 control-provenance contract;
- parser-independent HDFS component/BGL chronology metadata extraction;
- Research Freeze v1.1 documentation/config/tests;
- exact split allocation/purge/residual/hash contract and real deterministic split artifacts;
- physical HDFS/BGL TEST seals, both `SEALED / NEVER_OPENED`;
- PARSE-001 normal-only `BASE_TRAIN` Drain3 fit/freeze, persistence, restore, and immutable matching;
- PURGE-AUDIT-001 aggregate HDFS representativeness audit with deterministic payload and TEST-safe label boundary; result `PURGE_REPRESENTATIVENESS_CONCERN`;
- PURGE-DECISION-001 human-approved Option B: primary HDFS split unchanged and secondary purge sensitivity pre-registered / `NOT_RUN`;
- EFFECT-001 frozen and human-approved with `delta_HDFS = delta_BGL = 0.01 AP`; empirical status remains `NOT_RUN`.

Not implemented/run:

- canonical event corpus generated from the frozen parser;
- real sequences and sequence-destruction artifacts;
- baselines, models, training, tuning, killer experiments, or final TEST.

No Domain-Adaptive Fusion artifact, target adaptation, model run or new TEST
result exists. The planning critical path is defined in v2; implementation is
not authorized by this document alone.

## Historical v1.1 critical path

```text
[COMPLETE] LIT-001 + EFFECT-001 + SCHEMA-COMPAT-001
→ [COMPLETE] raw metadata + exact split clarification
→ [COMPLETE] chronological split + physical TEST guard
→ [COMPLETE] normal BASE_TRAIN Drain3 fit/freeze
→ [COMPLETE] PURGE-AUDIT-001
→ [COMPLETE / HUMAN APPROVED] PURGE-DECISION-001
→ [AUTHORIZED NEXT] CANONICAL-EVENT-001
→ partition-contained sequences
→ post-sequence leakage/integrity audit
→ order-insensitive baselines
→ Markov/N-gram
→ KT-1
→ KT-2
→ KT-3
→ human gate decision
→ conditional branch only if justified
→ one human final TEST
```

## Historical plans

- [V1.1 plan](master-implementation-plan-v1.1.md): former HDFS/BGL sequence-value protocol; replaced as the active forward plan by the user-directed v2 plan.
- [V3 plan](master-implementation-plan-v3.md): historical four-expert/fusion plan.
- [V1/V2 plan](master-implementation-plan.md): historical product/RAG/agent plan.

History is retained for provenance but cannot override ADR-025.
