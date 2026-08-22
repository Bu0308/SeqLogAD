# 00 — Master Plan Index

## Active source of truth

- [Master implementation plan v1.1](master-implementation-plan-v1.1.md)
- [ADR-025](06_DECISIONS.md#adr-025--scientific-redirect-scope-reduction-and-kill-criteria)
- [Scientific protocol v1.1](../docs/research-protocol-v1.1.md)
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
- Research Freeze v1.1 documentation/config/tests.
- EFFECT-001 statistical method contract prepared and tested; numerical HDFS/BGL margins still require human approval.

Not implemented/run:

- raw split manifest and physical TEST guard;
- scientific Drain3 fit/freeze and parsed events;
- real sequences and sequence-destruction artifacts;
- baselines, models, training, tuning, killer experiments, or final TEST.

## Active critical path

```text
LIT-001 + EFFECT-001 human margin approval
→ schema/protocol identity compatibility
→ raw metadata/group extraction
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
