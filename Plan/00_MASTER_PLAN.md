# 00 — Master Plan Index

## Active source of truth

- [Master implementation plan v1.1](master-implementation-plan-v1.1.md)
- [ADR-025](06_DECISIONS.md#adr-025--scientific-redirect-scope-reduction-and-kill-criteria)
- [Scientific protocol v1.1](../docs/research-protocol-v1.1.md)
- [Exact split-semantics addendum](../docs/split-clarification-contract.md)
- [EFFECT-001 statistical decision contract](../docs/statistical-decision-contract.md)
- [Active post-PARSE execution state](../configs/active-state.yaml)
- [Post-PARSE canonical context](../docs/audits/PROJECT-CONTEXT-POST-PARSE-001.md)

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
- exact split allocation/purge/residual/hash contract and real deterministic split artifacts;
- physical HDFS/BGL TEST seals, both `SEALED / NEVER_OPENED`;
- PARSE-001 normal-only `BASE_TRAIN` Drain3 fit/freeze, persistence, restore, and immutable matching;
- EFFECT-001 frozen and human-approved with `delta_HDFS = delta_BGL = 0.01 AP`; empirical status remains `NOT_RUN`.

Not implemented/run:

- canonical event corpus generated from the frozen parser;
- real sequences and sequence-destruction artifacts;
- baselines, models, training, tuning, killer experiments, or final TEST.

Current next scientific task after `ALIGN-FIX-001`:

`CANONICAL-EVENT-001` — generate partition-scoped canonical event artifacts by
read-only matching against the frozen HDFS/BGL Drain3 states.

## Active critical path

```text
[COMPLETE] LIT-001 + EFFECT-001 + SCHEMA-COMPAT-001
→ [COMPLETE] raw metadata + exact split clarification
→ [COMPLETE] chronological split + physical TEST guard
→ [COMPLETE] normal BASE_TRAIN Drain3 fit/freeze
→ [NEXT] CANONICAL-EVENT-001
→ partition-contained sequences
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
