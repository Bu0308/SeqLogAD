# 07 — Experiment Tracker V3

No model, calibration, complementarity, fusion, or downstream experiment has been run. Every row below is `NOT_RUN`; metric cells remain empty until a human-executed run produces traceable artifacts.

## Run record contract

| Field | Required value |
|---|---|
| Experiment ID | Stable ID below or approved extension |
| Owner | `HUMAN` for empirical execution |
| Status | `NOT_RUN`, `RUNNING`, `COMPLETE`, `FAILED`, `INVALIDATED` |
| Dataset identity | Dataset ID/version/fingerprint |
| Split artifact | Five-way split-manifest ID |
| Parser/sequence/mutation artifacts | Version/hash IDs |
| Config snapshot | Immutable copied config |
| Code state | Git commit and dirty state |
| Model/expert/fusion identity | Name, version, checkpoint IDs |
| Seed/group | Explicit seed and multi-seed group |
| Hardware/packages | Runtime metadata and lock |
| Metrics | Pipeline-generated only |
| Output path | Experiment-specific non-overwriting directory |
| Notes/failure | Deviations, failures, invalidation reason |

## Baseline and Expert A experiments

| ID | Purpose | Status | Metrics |
|---|---|---|---|
| B0 | Frequency/statistical reference | NOT_RUN | — |
| B1 | Markov/N-gram transition expert | NOT_RUN | — |
| B2 | Isolation Forest quantitative expert | NOT_RUN | — |
| B3 | LSTM neural baseline | NOT_RUN | — |
| A0 | SeqLogAD-T next-event loss only | NOT_RUN | — |
| A1 | A0 plus ranking loss | NOT_RUN | — |
| A2 | A0 plus token/gap/transition localization | NOT_RUN | — |
| A3 | Next-event plus ranking plus localization | NOT_RUN | — |
| D0 | Structural normal-reference retrieval expert | NOT_RUN | — |
| D1 | Optional dense retrieval extension | NOT_RUN | — |

## Complementarity/calibration experiments

| ID | Purpose | Status | Metrics |
|---|---|---|---|
| CAL0 | Raw-score calibration baseline | NOT_RUN | — |
| CAL1 | Validation-fitted calibration comparison | NOT_RUN | — |
| COMP0 | Pairwise score/error/localization analysis | NOT_RUN | — |
| COMP1 | Oracle gain and leave-one-expert-out marginal value | NOT_RUN | — |
| COMP2 | Human keep/remove/demote decision | NOT_RUN | — |

## Fusion experiments

| ID | Method | Status | Metrics |
|---|---|---|---|
| F0 | Strongest single expert | NOT_RUN | — |
| F1 | Normalized mean | NOT_RUN | — |
| F2 | Validation-weighted average | NOT_RUN | — |
| F3 | Voting/rank voting | NOT_RUN | — |
| F4 | Logistic stacking | NOT_RUN | — |
| F5 | MLP stacking | NOT_RUN | — |
| F6 | Standard gating/MoE | NOT_RUN | — |
| F7 | Evidential/Dempster-Shafer if applicable | NOT_RUN | — |
| F8 | Structured Evidence Consensus Fusion | NOT_RUN | — |
| F8-R | F8 plus candidate redundancy handling | NOT_RUN | — |
| F8-A | F8 plus conflict-aware abstention | NOT_RUN | — |

## Downstream experiments

| ID | Condition | Status | Metrics |
|---|---|---|---|
| DS0 | Score-only investigation context | NOT_RUN | — |
| DS1 | Strongest-expert structured evidence | NOT_RUN | — |
| DS2 | Fused structured evidence | NOT_RUN | — |
| DS3 | Regression-test recommendation human review | NOT_RUN | — |

## Rules

- Human researcher executes all empirical runs and final TEST.
- AI/Codex prepares commands and scripts but cannot promote a planned row to completed without real artifacts.
- TEST is never used to tune parser, models, calibrators, fusion, thresholds, or abstention.
- Failed/negative runs are retained with reasons.
- Empty metrics mean not measured, never zero.
