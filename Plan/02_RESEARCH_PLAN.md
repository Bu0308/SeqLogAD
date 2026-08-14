# 02 — Research Plan V3

## Research direction

The project evaluates heterogeneous expert value, complementarity, scientifically controlled fusion, dependency/redundancy handling, and downstream evidence usefulness. It does not assume that multi-model complexity is beneficial.

## Research questions

| ID | Question | Hypothesis status | Priority |
|---|---|---|---|
| RQ1 | How well do independently optimized experts capture different anomaly mechanisms? | HYPOTHESIS — TO BE TESTED | P0 |
| RQ2 | Do experts exhibit complementary error/localization patterns? | HYPOTHESIS — TO BE TESTED | P0 |
| RQ3 | Can structured fusion beat strongest-single and standard fusion baselines? | HYPOTHESIS — TO BE TESTED | P0 |
| RQ4 | Does dependency/redundancy handling improve reliability/FPR control? | HYPOTHESIS — TO BE TESTED | P0 after RQ2 |
| RQ5 | Does structured evidence improve investigation/test recommendation over score-only context? | HYPOTHESIS — TO BE TESTED | P1 downstream |

Detailed objectives, metrics, requirements, and falsification criteria are in `docs/research-questions.md`.

## Expert rationale

| Expert | Intended unique signal | Removal condition |
|---|---|---|
| Transformer | Long-range context and ordering | No incremental error/localization value |
| Markov/N-gram | Short transition surprise | Duplicates Transformer without cost/accuracy advantage |
| Isolation Forest | Quantitative/statistical behavior | Feature-family evidence adds no marginal value |
| Normal-reference retriever | Historical normal deviation and expected behavior | Structural references do not improve detection/localization/evidence |

## Prior-art validation

`LIT-001` is P0 and must cover log ensembles/MoE, multi-pattern detectors, localization, synthetic mutation, retrieval-augmented detection, evidential/reliability fusion, redundancy/dependency, abstention, RCA, and log-derived test generation.

Each paper row records representation, supervision, experts, fusion level, localization coordinates, reliability/dependency/conflict treatment, calibration, abstention, datasets, split/leakage controls, downstream use, code availability, and exact difference from V3.

Allowed novelty outcomes: `KNOWN_COMPONENT`, `OUR_ADAPTATION`, `POTENTIAL_CONTRIBUTION`, `HIGH_PRIOR_ART_RISK`, `ALREADY_SOLVED`, or `NEEDS_REFRAMING`. No candidate is currently labeled novel.

## Candidate objectives

Expert A is evaluated in stages:

- A0: next-event loss only.
- A1: next-event plus ranking.
- A2: next-event plus coordinate-aware localization.
- A3: next-event plus ranking plus localization.

The combined loss is a candidate configuration, not a novelty claim.

Fusion starts with detection plus fused-localization loss. Calibration is infrastructure. A redundancy term is potential work after prior-art and complementarity gates. The rejected `confidence × conflict` term is not part of the official core due confidence-collapse risk.

## Fusion comparison requirement

F8 must be compared against F0–F7. A result against weak averaging baselines alone cannot support RQ3.

## Falsification criteria

- RQ1 weakens if experts have no family-specific strengths.
- RQ2 is unsupported if error/localization overlap is effectively complete and oracle gain is negligible.
- RQ3 is unsupported if F8 fails to beat the strongest appropriate baseline under paired analysis.
- RQ4 is rejected if dependency handling worsens calibration, FPR, or detection at matched coverage.
- RQ5 is unsupported if structured evidence fails to improve grounding or human-reviewed QA quality.

Negative findings remain valid research outputs.

## Scientific-integrity constraints

- Parser/split/window/mutation artifacts are frozen before model comparison.
- No TEST data participates in fitting, calibration, checkpoint selection, fusion, thresholding, or novelty decisions.
- Real anomaly labels are evaluation-only unless an experiment is explicitly reclassified.
- Every run records config, seed, dataset fingerprint, artifact IDs, Git state, package/hardware metadata, and failure status.
- Human researcher executes training, tuning, ablations, fusion training, and final TEST.
- Planned experiments remain `NOT_RUN`; AI never invents metrics.

## Current contribution status

| Candidate | Status |
|---|---|
| Heterogeneous experts | Engineering/research design |
| Transformer/Markov/Isolation Forest | Known components |
| Structural retrieval expert | Adaptation/known family |
| Synthetic mutations/ranking | Known/general techniques |
| Coordinate-aware localization | Adaptation |
| Structured claim representation | Potential contribution |
| Claim-level heterogeneous fusion | Potential contribution |
| Redundancy-aware fusion | High prior-art risk |
| Conflict-aware abstention | Known/general family |
| RCA/test recommendation integration | Potential integration contribution |
