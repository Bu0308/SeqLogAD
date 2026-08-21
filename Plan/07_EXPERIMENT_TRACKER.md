# 07 — Experiment Tracker v1.1

No scientific experiment has run. Every empirical row is `NOT_RUN`; empty metrics mean unmeasured, never zero.

## Run record contract

Every run records experiment ID, owner, status, exact dataset fingerprint, split/parser/sequence artifact IDs, protocol `1.1`, config snapshot, Git dirty state/commit, method/version, seed, hardware/packages, pipeline-generated metrics, output path, and failure/invalidation reason.

## Core order-insensitive and sequential conditions

| ID | Method/question | Scope | Status | Metrics |
|---|---|---|---|---|
| OI-0 | Unseen event-type detector | MUST | NOT_RUN | — |
| OI-1 | Sequence length only | MUST | NOT_RUN | — |
| OI-2 | Total/event count-vector baseline | MUST | NOT_RUN | — |
| OI-3 | Isolation Forest order-insensitive features | SHOULD | NOT_RUN | — |
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
| GATE-SEQ | Sequence/order-sensitivity claim state | NOT_RUN |
| GATE-TRANSFORMER | Open/remove Transformer | NOT_RUN |
| GATE-LOCALIZATION | Open/remove localization | NOT_RUN |
| GATE-FUSION | Open/remove simple fusion | NOT_RUN |

## Rules

- Human executes all empirical runs and final TEST.
- AI cannot fabricate or manually promote metrics.
- TEST is never used to choose method, threshold, dataset, architecture, gate, novelty, or claim.
- Negative/failed runs remain traceable.
- Practical-effect thresholds are frozen before the first empirical run.
