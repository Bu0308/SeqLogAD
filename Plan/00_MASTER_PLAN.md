# 00 — Master Plan Index

## Active plan

The active research and implementation contract is [master-implementation-plan-v3.md](master-implementation-plan-v3.md).

Current direction:

> **Multi-Model Sequence Anomaly Localization with Structured Evidence Fusion and Evidence-Grounded Regression-Test Recommendation**

Central question:

> Do heterogeneous log-anomaly experts provide measurably complementary evidence, and can a scientifically justified fusion mechanism exploit that complementarity without double-counting redundant evidence or becoming less reliable under expert disagreement?

Novelty remains **UNVERIFIED / PRIOR-ART VALIDATION REQUIRED**.

## Current state

Implemented:

- HDFS/BGL acquisition contracts;
- canonical-source checksums;
- immutable raw-data policy;
- manifests and fingerprints;
- independent dataset verification;
- 27 foundation tests.

Planned/not implemented:

- canonical events and Drain3 parsing;
- sequences, splits, and mutations;
- baselines and experts A–D;
- calibration, complementarity, and fusion;
- retrieval/evidence/downstream agent/API/UI.

## Active expert set

1. SeqLogAD-T lightweight causal Transformer — long-range context/order.
2. Markov/N-gram — short transition probability.
3. Isolation Forest — quantitative/statistical behavior.
4. Normal-reference retriever — structural deviation from normal executions.

The set is provisional. Complementarity analysis may remove or demote an expert.

## Critical path

```text
LIT/ADR/ENV
→ SCHEMA
→ PARSE
→ SEQ/SPLIT
→ MUT
→ BASE/MODEL/RETR-D
→ CAL/COMP
→ FUSION BASELINES
→ STRUCTURED FUSION
→ HUMAN FINAL EVALUATION
→ DOWNSTREAM EVIDENCE/TEST STUDY
```

## Ownership boundary

AI/Codex prepares implementation, configs, tests, scripts, and commands. The human researcher executes training, tuning, checkpoint selection, ablations, fusion training, locked TEST evaluation, and empirical decisions. No metric may be fabricated.

## Historical plans

[master-implementation-plan.md](master-implementation-plan.md) is retained as the V1/V2 historical plan and is superseded for future work. Decisions remain preserved in [06_DECISIONS.md](06_DECISIONS.md).
