# Research Questions — V3

All questions and hypotheses below are **HYPOTHESIS — TO BE TESTED**. No experimental conclusion or novelty claim is implied.

All RQs use the same frozen data-access, split, leakage, fitting, and evaluation contract in [`research-protocol.md`](research-protocol.md). PR-AUC is the primary real-anomaly detection metric; synthetic localization and real-anomaly evaluation remain separate.

## RQ1 — Expert value

**Question:** How well do individually optimized heterogeneous experts capture different behavioral anomaly mechanisms?

- **Priority:** CORE / P0
- **Objective:** Establish strong, independently optimized experts with different inductive biases.
- **Hypothesis:** Transformer, Markov/N-gram, Isolation Forest, and normal-reference retrieval may perform differently across anomaly families; no expert is assumed to dominate globally.
- **Experiment concept:** Evaluate each expert on identical frozen artifacts, partitions, anomaly families, thresholds, and compute budgets. Include statistical and LSTM baselines.
- **Primary metrics:** Precision, Recall, F1, PR-AUC, FPR, detection latency, throughput, memory; token/gap/transition localization metrics where supported.
- **Required components:** Canonical events, sequences, five-way split, mutation labels, experts A–D, evaluator.
- **Falsification:** If experts produce effectively identical rankings/errors or a simple baseline dominates consistently, the heterogeneous-expert premise is weakened.

## RQ2 — Complementarity

**Question:** Do heterogeneous experts exhibit measurable complementary error and localization patterns?

- **Priority:** CORE / P0
- **Objective:** Determine whether combining experts is scientifically justified.
- **Hypothesis:** Different inductive biases may produce lower error overlap and family-specific strengths.
- **Experiment concept:** Measure score correlation, disagreement, error overlap, oracle gain, anomaly-family conditional performance, localization overlap, and marginal contribution.
- **Primary metrics:** Pearson/Spearman correlation, disagreement rate, double-fault/error-overlap measures, oracle PR-AUC/F1 gain, family-specific recall, leave-one-expert-out delta.
- **Required components:** Frozen out-of-sample expert predictions and stable sequence IDs.
- **Falsification:** An expert is redundant if it adds no meaningful oracle or realized gain and its errors/localizations substantially duplicate another expert.

## RQ3 — Fusion

**Question:** Can structured evidence fusion outperform the strongest individual expert and standard fusion baselines?

- **Priority:** CORE / P0
- **Objective:** Test whether claim-level structured evidence adds value beyond score aggregation.
- **Hypothesis:** Structured fusion may improve detection/localization and reliability when evidence is genuinely complementary.
- **Experiment concept:** Compare F0 strongest single, F1 normalized mean, F2 validation-weighted average, F3 voting/rank voting, F4 logistic stacking, F5 MLP stacking, F6 gating/MoE, F7 evidential baseline when applicable, and F8 structured fusion.
- **Primary metrics:** PR-AUC, F1, FPR, token/gap/transition localization, ECE, Brier score, latency, memory.
- **Required components:** Calibrated ExpertEvidence records, claim alignment, fusion baselines, proposed fusion, locked evaluation protocol.
- **Falsification:** If F8 does not reliably outperform the strongest appropriate baseline under paired analysis, the structured-fusion hypothesis is unsupported.

## RQ4 — Reliability and redundancy

**Question:** Does explicit handling of expert dependency/redundancy improve reliability and false-positive control without sacrificing detection performance?

- **Priority:** CORE / P0 after RQ2 gate
- **Objective:** Avoid double-counting correlated evidence and characterize disagreement safely.
- **Hypothesis:** Dependency-aware weighting or abstention may improve calibration/risk control, but a redundancy penalty may also suppress useful consensus.
- **Experiment concept:** Compare no redundancy handling, candidate redundancy-aware variants, and conflict-aware abstention at matched coverage.
- **Primary metrics:** ECE, Brier score, FPR, PR-AUC, risk-coverage, abstention rate, conditional error under conflict, false-positive reduction.
- **Required components:** Reliability estimates, dependency matrix computed without TEST, conflict variables, abstention protocol.
- **Falsification:** Reject a mechanism if it reduces detection materially, collapses confidence, or provides no calibrated reliability gain.

## RQ5 — Downstream value

**Question:** Does fused structured evidence improve evidence-grounded investigation and regression-test recommendation compared with score-only context?

- **Priority:** P1 downstream research after frozen fusion artifacts
- **Objective:** Measure whether localization and structured claims improve QA usefulness rather than merely detector scores.
- **Hypothesis:** Evidence IDs, expected/observed differences, and reliability/conflict context may reduce unsupported conclusions and improve test relevance.
- **Experiment concept:** Compare score-only, strongest-expert evidence, and fused structured evidence under the same downstream model/provider and curated cases.
- **Primary metrics:** Citation correctness, unsupported conclusion rate, evidence precision/recall, investigation completeness, test relevance, step completeness, expected-result correctness, human acceptance.
- **Required components:** Frozen expert/fusion outputs, evidence schema/verifier, read-only investigation workflow, human rubric.
- **Falsification:** If structured evidence does not improve grounding or QA acceptance, downstream contribution is unsupported.

## Claim-state policy

Allowed states are `PROPOSED`, `HYPOTHESIS`, `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, and `REJECTED`.

Novelty uses a separate literature decision: `UNVERIFIED`, `KNOWN_COMPONENT`, `OUR_ADAPTATION`, `POTENTIAL_CONTRIBUTION`, `HIGH_PRIOR_ART_RISK`, or a later evidence-backed classification. `LIT-001` owns that decision.
