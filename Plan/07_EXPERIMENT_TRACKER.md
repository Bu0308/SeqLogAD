# 07 — Experiment Tracker v1.1

No scientific experiment has run. Every empirical row is `NOT_RUN`; empty metrics mean unmeasured, never zero.

## Run record contract

Every run records experiment ID, owner, status, exact dataset fingerprint, split/parser/sequence artifact IDs, protocol `1.1`, EFFECT-001 version/approval/hash, config snapshot, Git dirty state/commit, method/version, seed, hardware/packages, pipeline-generated metrics, output path, and failure/invalidation reason.

## Statistical execution gate

| Contract | Frozen fields | Human-owned fields | Status |
|---|---|---|---|
| EFFECT-001 | Estimand, AP semantics, orderless family, selection/tie rule, equal budget, 95% paired bootstrap, multiplicity, seeds, KT-3, negative outcomes | `delta_HDFS = delta_BGL = 0.01 AP`; pre-experiment `RESOURCE_FEASIBILITY_MARGIN` | `DONE / FROZEN_HUMAN_APPROVED` |

No empirical row changed during EFFECT-001 approval; every condition below remains `NOT_RUN`.

PURGE-AUDIT-001 is a dataset/split validity audit, not a scientific method run.
It produced no AP/F1/model result and did not access partition-specific
outcomes. PURGE-DECISION-001 froze Option B before scientific outcomes; it
also created no empirical result.

## Pre-registered secondary robustness condition

| ID | Purpose | Role | Execution boundary | Status | Metrics |
|---|---|---|---|---|---|
| HDFS-PURGE-SENSITIVITY-001 | Assess whether the qualitative HDFS sequence-order conclusion depends on boundary-purge construction | SECONDARY / ROBUSTNESS_ONLY / NON-SELECTION | Human-only after immutable primary HDFS result; reuse frozen artifacts | PRE_REGISTERED_SECONDARY_NOT_RUN | — |

## Core order-insensitive and sequential conditions

| ID | Method/question | Scope | Status | Metrics |
|---|---|---|---|---|
| OI-0 | Unseen event-type detector | MUST | NOT_RUN | — |
| OI-1 | Sequence length only | MUST | NOT_RUN | — |
| OI-2A | Total event-count baseline | MUST | NOT_RUN | — |
| OI-2B | Event count-vector baseline | MUST | NOT_RUN | — |
| OI-3 | Isolation Forest order-insensitive features | MUST | NOT_RUN | — |
| SQ-0 | Markov/N-gram transition surprise | MUST | NOT_RUN | — |

## Killer experiments

| ID | Purpose | Scope | Status | Decision artifact |
|---|---|---|---|---|
| KT-1 | Trivial/strong baseline ceiling and equal-budget comparison | MUST | NOT_RUN | — |
| KT-2 | HDFS count-label dependence/collisions/out-of-sample prediction | MUST | NOT_RUN | — |
| KT-3 | Original versus order-destroyed paired comparison | MUST | NOT_RUN | — |
| KT-4 | Localization target randomization | CONDITIONAL | NOT_RUN | — |
| KT-5 | Counterfactual repair/deletion faithfulness | CONDITIONAL | NOT_RUN | — |
| KT-6 | Random/corrupted expert fusion control | CONDITIONAL | NOT_RUN | — |

## Conditional methods

| ID | Method | Opening gate | Status | Metrics |
|---|---|---|---|---|
| T-0 | Lightweight Transformer | Sequence signal + residual long-range question | NOT_RUN / CONDITIONAL | — |
| LOC-0 | Coordinate-aware synthetic localization | Sequence + target-validity gate | NOT_RUN / CONDITIONAL | — |
| F0 | Strongest eligible single expert | At least two complementary experts | NOT_RUN / CONDITIONAL | — |
| F1 | Simple normalized mean | Same complementarity gate | NOT_RUN / CONDITIONAL | — |

LSTM, normal-reference Expert D, and F2–F8 are removed from the v1.1 core. Historical experiment IDs remain in V3 history only.

## Gate decision records

| ID | Decision | Status |
|---|---|---|
| GATE-DATA | Per-dataset suitability/ceiling interpretation | NOT_RUN |
| GATE-PURGE | Keep frozen primary + pre-register secondary purge sensitivity | FROZEN_HUMAN_APPROVED |
| GATE-SEQ | Sequence/order-sensitivity claim state | NOT_RUN |
| GATE-TRANSFORMER | Open/remove Transformer | NOT_RUN |
| GATE-LOCALIZATION | Open/remove localization | NOT_RUN |
| GATE-FUSION | Open/remove simple fusion | NOT_RUN |

## Rules

- Human executes all empirical runs and final TEST.
- AI cannot fabricate or manually promote metrics.
- TEST is never used to choose method, threshold, dataset, architecture, gate, novelty, or claim.
- Negative/failed runs remain traceable.
- Numerical practical-effect margins are human-approved before the first empirical run; all statistical method fields follow EFFECT-001.
- HDFS and BGL receive separate primary conclusions; no pooled/disjunctive claim is registered.
- Secondary method/metric comparisons remain descriptive and cannot replace the one primary contrast per dataset.
