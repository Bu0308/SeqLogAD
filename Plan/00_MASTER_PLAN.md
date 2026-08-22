# 00 — Master Plan Index

## Active source of truth

- [Master implementation plan v1.1](master-implementation-plan-v1.1.md)
- [ADR-025](06_DECISIONS.md#adr-025--scientific-redirect-scope-reduction-and-kill-criteria)
- [Scientific protocol v1.1](../docs/research-protocol-v1.1.md)
- [Exact split-semantics addendum](../docs/split-clarification-contract.md)
- [EFFECT-001 statistical decision contract](../docs/statistical-decision-contract.md)

Current topic:

> **Sequence-Based Unsupervised Anomaly Detection for Large-Scale Event Logs**

Current question:

> How much additional anomaly-detection value does sequence order provide beyond strong order-insensitive baselines under a leakage-controlled, chronological, and equal-budget protocol?

## Current state

Implemented/verified:

- HDFS/BGL acquisition, checksums, manifests, fingerprints, and verification;
- Python 3.12 environment/package contract;
- canonical event/template and sequence/localization/mutation schema contracts;
- Protocol-v1.1 schema compatibility and KT-3 control-provenance contract;
- parser-independent HDFS component/BGL chronology metadata extraction;
- Research Freeze v1.1 documentation/config/tests;
- exact split allocation/purge/residual/hash contract and synthetic proof tests.
- EFFECT-001 frozen and human-approved with `delta_HDFS = delta_BGL = 0.01 AP`; empirical status remains `NOT_RUN`.

Not implemented/run:

- raw split manifest and physical TEST guard;
- scientific Drain3 fit/freeze and parsed events;
- real sequences and sequence-destruction artifacts;
- baselines, models, training, tuning, killer experiments, or final TEST.

## Active critical path

```text
LIT-001 + approved EFFECT-001 + SCHEMA-COMPAT-001
→ raw metadata/group extraction
→ PROTOCOL-SPLIT-CLARIFY-001 exact semantics
→ chronological split + TEST guard
→ normal BASE_TRAIN Drain3 fit/freeze
→ canonical events/sequences
→ KT-1 + KT-2
→ Markov/N-gram + KT-3
→ human gate decision
→ conditional branch only if justified
→ one human final TEST
```

## Historical plans

- [V3 plan](master-implementation-plan-v3.md): historical four-expert/fusion plan, superseded by v1.1.
- [V1/V2 plan](master-implementation-plan.md): historical product/RAG/agent plan, superseded by v1.1.

History is retained for provenance but cannot override ADR-025.
