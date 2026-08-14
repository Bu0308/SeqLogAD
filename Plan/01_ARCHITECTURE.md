# 01 — Architecture V3

Status legend: `IMPLEMENTED`, `PLANNED`, `P1`, `HUMAN_EXECUTES`.

## Component map

```text
Raw System Logs
      ↓
Dataset Integrity / Provenance                         IMPLEMENTED
      ↓
Canonical Event Representation                         PLANNED
      ↓
Drain3 Parsing / Templates                             PLANNED
      ↓
Event Sequence Construction                            PLANNED
      ↓
Five-Way Leakage-Safe Splits                           PLANNED
      ↓
┌───────────────────────────────────────────────────────────────┐
│ HETEROGENEOUS EXPERTS                                PLANNED │
│ A — SeqLogAD-T Transformer                                   │
│ B — Markov / N-gram transition expert                        │
│ C — Isolation Forest quantitative expert                     │
│ D — structural normal-reference retrieval expert             │
└──────────────────────────────┬────────────────────────────────┘
                               ↓
Complementarity / Retention Gate                       PLANNED
                               ↓
Standard Fusion Baselines F0–F7                       PLANNED
                               ↓
Structured Evidence Consensus Fusion F8               PLANNED
                               ↓
Anomaly + Token/Gap/Transition Localization
+ Reliability + Structured Claims                     PLANNED
                               ↓
Evidence-Grounded Investigation                        P1
                               ↓
Regression-Test Recommendation                         P1
```

## Data layer

| Artifact | Responsibility | Fit/access boundary |
|---|---|---|
| Raw bytes/manifest | Immutable source identity | Already verified |
| Canonical event | Stable parsed-field contract | Schema before parser |
| Parser state | Template mining and event-ID mapping | Fit on `BASE_TRAIN`, then freeze |
| Event sequence | Ordered event IDs and provenance | Dataset-specific grouping |
| Mutation record | Expected/observed pair and location labels | Training-derived normal sequences only |
| Split manifest | Stable group/sequence partition | Created before overlapping windows |

Candidate partitions are `BASE_TRAIN`, `FUSION_TRAIN`, `VAL_EXPERT`, `VAL_FUSION`, and `TEST`. Ratios are **TO BE FINALIZED**.

## Expert layer

| Expert | Input | Output | Constraint |
|---|---|---|---|
| A SeqLogAD-T | Event/time/context sequence | Sequence energy, token/gap/transition scores | Lightweight causal Transformer |
| B Markov/N-gram | Event transitions | Transition surprise and sequence score | Fit counts only |
| C Isolation Forest | Quantitative feature vector | Sequence/family score and feature evidence | No fabricated token location |
| D Normal reference | Observed sequence + normal index | Nearest IDs and structural diff | Structural P0; dense P1 |

## Localization contract

For observed sequence `E1 E2 E3`:

```text
G0 E1 G1 E2 G2 E3 G3
```

- Token coordinates: extra, replacement, repeated observed event.
- Gap coordinates: missing event.
- Transition coordinates: unexpected transition and reorder evidence.

All masks and metrics are coordinate-family aware.

## ExpertEvidence boundary

Every expert eventually returns a backend-independent structured record containing expert/model identity, fit partition, raw and calibrated sequence score, optional token/gap/transition scores, structured claims, evidence references, uncertainty, and latency. Unsupported localization fields remain absent rather than being fabricated.

## Complementarity gate

Before fusion training, analyze score correlation, disagreement, error overlap, oracle gain, family-conditional performance, localization overlap, and leave-one-expert-out marginal contribution. Remove or demote redundant experts.

## Fusion layer

The required ladder is F0 strongest single, F1 mean, F2 validation-weighted average, F3 voting/rank voting, F4 logistic stacking, F5 MLP stacking, F6 standard gating/MoE, F7 evidential/Dempster-Shafer if applicable, and F8 structured fusion.

F8 may consume calibrated scores, coordinate-aware localization, claims, evidence family, reliability, dependency estimates, and conflict indicators. It may output a score/decision, fused localization, reliability, structured evidence, and optional abstention.

The minimal candidate loss is detection plus fused localization. Redundancy-aware terms require `LIT-001` and ablation. Conflict is currently an input/verifier/abstention signal, not a `confidence × conflict` core loss.

## Downstream boundary

The LLM/agent is not a detector and cannot train, update, or override experts/fusion. It receives frozen versioned evidence artifacts, uses read-only tools, requires evidence IDs, and may return `INSUFFICIENT_EVIDENCE`.

## Elasticsearch boundary

Elasticsearch is an optional P1/P2 adapter for storage, filtering, BM25, and vector search. Core data, expert, fusion, and downstream contracts do not import a concrete Elasticsearch client. Elasticsearch is not a research contribution.

## Current implemented flow

Only this path works today:

```text
dataset config → path/source validation → acquisition/checksum policy
→ required-file validation → deterministic manifest → independent verification
```

Everything after dataset integrity is planned.
