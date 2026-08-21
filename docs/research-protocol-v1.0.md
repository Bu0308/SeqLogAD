# PROTOCOL-001 v1.0 — Historical Frozen Scientific Protocol

> **SUPERSEDED FOR FUTURE EXPERIMENTS BY [`research-protocol-v1.1.md`](research-protocol-v1.1.md).** This version is preserved as the human-approved 2026-08-20 contract. No experiment was run under v1.0, and no result is invalidated by the v1.1 redirect.

| Field | Frozen value |
|---|---|
| Protocol ID | `PROTOCOL-001` |
| Version | `1.0` |
| Status | **FROZEN — HUMAN APPROVED** |
| Approval date | 2026-08-20 |
| Machine-readable contract | `configs/protocols/protocol-v1.yaml` |
| Method provenance | `docs/references/PROTOCOL-001-citations.md` |
| Empirical status | `NOT_RUN` |

This document freezes supervision, raw pre-partitioning, sequence construction, parser fit scope, synthetic localization, model/fusion development ownership, leakage controls, and evaluation policy. It is a research contract, not an implementation or an experimental result.

Changing a frozen rule requires a new protocol version and an explicit decision-log entry made **before** affected artifacts or results are inspected. Old protocol versions remain preserved.

## 1. Scientific framing

The precise project description is:

> **Normal-only self-supervised sequential anomaly detection with synthetic supervision for anomaly localization and fusion.**

The system is not described as entirely label-free or purely unsupervised because labels and synthetic targets have controlled roles:

- normal-only data fits the parser, normal behavior experts, and normal-reference corpus;
- self-supervised objectives learn sequence behavior without using the anomaly label as model input;
- synthetic mutations provide training targets for localization, ranking, and fusion;
- real anomaly labels may filter authorized normal pools and support validation/evaluation decisions;
- labels are never model-input features and are never part of a base self-supervised loss;
- final `TEST` labels remain sealed until the one authorized final evaluation.

Synthetic-anomaly performance and real-anomaly performance are separate result families. Synthetic success must not be presented as proof of real-anomaly detection quality.

## 2. Frozen pipeline order

```text
Verified immutable raw bytes
→ minimal metadata and grouping-key extraction
→ raw chronological pre-partition
→ controlled label isolation / normal-pool filtering
→ fit Drain3 on BASE_TRAIN normal messages only
→ freeze parser state, normalization, and template registry
→ transform all partitions without parser updates
→ build dataset-specific sequences inside each partition
→ create deterministic synthetic mutations in authorized pools
→ fit experts on their assigned partitions
→ freeze experts and generate out-of-sample evidence
→ calibrate and measure complementarity
→ KEEP / DEMOTE / REMOVE expert decision
→ fit and select fusion without TEST
→ lock artifacts and protocol
→ human executes TEST once
→ downstream RAG/Agent consumes frozen evidence only
```

Raw pre-partitioning occurs before any train-fitted parser or transformation. No overlapping sequence/window may cross a partition boundary.

## 3. Five-way chronological split

The official top-level split is chronological and fixed:

| Partition | Share | Authorized purpose |
|---|---:|---|
| `BASE_TRAIN` | 60% | Fit Drain3, vocabulary/statistics, base experts, and normal-reference corpus |
| `FUSION_TRAIN` | 10% | Generate separate synthetic fusion-training cases and fit learned fusion |
| `VAL_EXPERT` | 10% | Expert hyperparameter, checkpoint, score aggregation, and expert-threshold selection |
| `VAL_FUSION` | 10% | Calibration, fusion selection, fusion threshold, and optional abstention selection |
| `TEST` | 10% | One locked final evaluation by the human researcher |

Rules:

1. Ratios are assigned by chronological raw units after dataset-specific atomicity rules are applied, not by randomly shuffling generated samples.
2. No stratification may reorder chronology.
3. Exact boundaries and any purged units must be recorded in a split manifest.
4. `VAL_FUSION` is internally ordered into two non-overlapping regions: the first half of the partition for calibration and the second half for fusion/threshold/abstention selection. Each region therefore represents 5% of the full chronological stream before boundary purging.
5. An implementation may deviate from an exact row count to preserve HDFS group atomicity; it must report target and realized ratios.
6. Boundaries are fixed before model results are inspected.

## 4. Label-access contract

| Stage | Normal/anomaly labels | Allowed use | Forbidden use |
|---|---|---|---|
| Raw pre-partition | Visible only to the controlled partitioning/label-isolation component | Attach evaluation identity and identify normal pools | Model features, parser message text, learned representation |
| `BASE_TRAIN` | Available to controlled data preparation | Retain normal records for parser/expert/reference fitting; audit contamination | Model input or base self-supervised target |
| `FUSION_TRAIN` | Available to controlled data preparation | Retain normal parents for synthetic fusion cases | Train on real anomaly labels in the frozen core protocol |
| `VAL_EXPERT` | Available to evaluator | Expert selection, aggregation, thresholding, and validation metrics | Base/expert weight updates outside registered training procedures; TEST inference |
| `VAL_FUSION` | Available to calibrator/evaluator | Calibration, fusion selection, thresholding, optional abstention | Expert refitting; TEST inference |
| `TEST` | **Sealed** | One final human-authorized evaluation after artifact freeze | Any training, tuning, calibration, thresholding, architecture/fusion/claim selection |

For BGL, the inline alert marker must be physically separated from the message and excluded from parser/model input. For HDFS, `anomaly_label.csv` is an external controlled label source, not a log-message feature.

## 5. TEST seal

Before final evaluation, code and routine commands must not expose TEST labels, TEST metrics, class counts, anomaly-family summaries, previews, or model comparisons. Only structural facts required to build and hash the sealed partition may be recorded.

The final TEST command is run exactly once by the human researcher after all of the following are frozen:

- dataset fingerprints and split manifest;
- parser state and event-ID mapping;
- sequence and mutation contracts;
- expert checkpoints/counts/reference indexes;
- calibrators, retained expert set, fusion model, thresholds, and abstention rule;
- metric implementation and report schema;
- selected seeds/configs and Git revision.

A genuine implementation bug discovered during final TEST does not authorize silent tuning. The run is marked invalid, the defect and affected artifacts are documented, a new protocol/run version is approved, and the full final evaluation is rerun without selecting fixes by favorable TEST results.

## 6. HDFS construction contract

### 6.1 Scientific input

- Primary raw scientific input: `HDFS.log` from the verified HDFS archive.
- Controlled label source: `anomaly_label.csv`.
- Canonical Loghub preprocessed templates, structured CSV, and event traces may be used only for external sanity comparison; they are forbidden as scientific parser/template/sequence input.

### 6.2 Atomic unit and chronology

- The scientific evaluation/grouping unit is an HDFS block/session.
- Minimal pre-parser extraction may identify block IDs and raw line order solely to preserve session atomicity.
- A block's chronological key is its earliest source line index, with deterministic block ID as a tie-breaker.
- All events belonging to one block must remain in one partition.
- If one raw line contains multiple block IDs, those blocks form one atomic connected component for partition assignment.
- A block/component that spans a nominal partition boundary is not split. It is recorded and removed as `PURGED_BOUNDARY` rather than moved opportunistically to improve ratios.
- Lines with no usable block ID are retained in a separately audited pool and are not silently assigned to a scientific block sequence.

### 6.3 HDFS labels and localization

- Block labels filter authorized normal fitting pools and support real sequence-level validation/evaluation.
- Real HDFS labels do not establish token, gap, or transition ground truth; real localization metrics are therefore `N/A` unless an independently verified localization annotation is introduced in a later protocol.
- Synthetic HDFS mutations may be evaluated for localization, but their results must remain in a synthetic-localization report.

### 6.4 HDFS sequence shape

- One block produces one variable-length parent sequence.
- Causal training contexts may be derived only inside that parent sequence and its partition.
- The model context cap is computed from the `BASE_TRAIN` normal sequence-length distribution as `min(P99, 256)` and then frozen.
- Truncation policy, truncated counts, and masks must be reported; padding never contributes to losses or anomaly scores.

## 7. BGL construction contract

### 7.1 Raw chronology and label isolation

- Preserve source line order.
- Separate the inline alert/normal marker from the raw message before parser/model input construction.
- Split the raw chronological stream first; create windows only inside one partition.

### 7.2 Parent windows

- The primary BGL evaluation unit is a non-overlapping parent window of 100 consecutive events.
- A final residual window is retained with masking when it contains at least 20 events; a shorter residual is recorded as `DROPPED_SHORT_WINDOW`.
- A parent window is anomalous when at least one contained event carries the source alert label.
- Causal subcontexts may be generated inside a parent for expert training, but predictions and evaluation are aggregated back to the parent-window ID.
- No parent or subcontext crosses a top-level split boundary.

### 7.3 BGL localization

- Source inline alert positions may support a clearly labeled secondary real token-alert analysis.
- They do not automatically prove missing-event or root-cause localization.
- Synthetic token/gap/transition localization remains a separate evaluation track.

## 8. Drain3 fit/freeze contract

1. Fit Drain3 only on `BASE_TRAIN` messages belonging to the authorized normal pool.
2. Any normalization/regex decision is fitted or finalized from `BASE_TRAIN` only.
3. Persist and hash parser version, Drain3 version/configuration, normalization version, state artifact, and frozen template registry.
4. Transform `FUSION_TRAIN`, `VAL_EXPERT`, `VAL_FUSION`, and `TEST` in read-only mode. No later event may update parser state or existing template assignments.
5. Map an unseen frozen-template result to reserved event ID `EVT_UNSEEN`; do not expand the vocabulary after freeze.
6. Derive deterministic event IDs from a versioned digest of parser version, normalization version, and normalized template text; do not use discovery-order numbering as scientific identity.
7. Report unseen-template/OOV rates by partition without using TEST observations to revise the parser.

## 9. Synthetic mutation contract

Synthetic mutations are created after immutable raw data, partition assignment, frozen parsing, and parent-sequence construction. Raw logs are never mutated.

| Source pool | Synthetic use |
|---|---|
| Normal `BASE_TRAIN` parents | Expert A ranking/localization training and development fixtures |
| Normal `FUSION_TRAIN` parents | Fusion-training cases only |
| `VAL_EXPERT` parents | Expert validation/evaluation only; no expert training |
| `VAL_FUSION` parents | Calibration/fusion validation only; no fusion-training examples |
| `TEST` parents | No mutation before final command; final synthetic stress tests, if enabled, are reported separately |

Frozen mutation families:

- missing event → gap target;
- extra event → token target;
- repeated event → token target;
- replacement → token target and affected transitions;
- reorder → token and transition evidence according to the registered operation.

`Unexpected transition` is derived evidence/analysis, not a Markov-selected mutation generator in v1. This prevents the Markov expert from defining the benchmark it is later scored on.

Every mutation records deterministic mutation ID, source parent/partition, seed, operation, parameters, expected and observed sequence hashes, token/gap/transition coordinates, and no-op rejection. Sampling is frequency-bucket aware so trivial rare-template insertion does not dominate. Padding cannot be selected or scored as a mutation.

## 10. Expert ownership and staged fitting

| Component | Fit data | Validation/selection data | TEST rule |
|---|---|---|---|
| Frequency baseline | Normal `BASE_TRAIN` | `VAL_EXPERT` | Frozen before TEST |
| Markov/N-gram | Normal `BASE_TRAIN` counts | `VAL_EXPERT` | Frozen before TEST |
| Isolation Forest | Normal `BASE_TRAIN` features | `VAL_EXPERT` | Frozen before TEST |
| LSTM baseline | Normal `BASE_TRAIN`; authorized synthetic objectives if explicitly configured | `VAL_EXPERT` | Human-selected checkpoint frozen |
| SeqLogAD-T | Normal `BASE_TRAIN`; synthetic ranking/localization from `BASE_TRAIN` | `VAL_EXPERT` | Human-selected A0–A3 variant frozen |
| Normal-reference expert | Normal `BASE_TRAIN` reference corpus | `VAL_EXPERT` retrieval/scoring choices | Index frozen before TEST |
| Calibrators | First half of `VAL_FUSION` | Checked without expert refit | Frozen before fusion selection |
| Learned fusion | `FUSION_TRAIN` frozen expert evidence | Second half of `VAL_FUSION` | Human-selected fusion frozen |

Staged training is mandatory by default: fit experts independently, freeze them, generate versioned expert evidence, calibrate, measure complementarity, decide expert retention, then fit fusion. End-to-end joint training and partial unfreezing require a separate P1 protocol amendment.

SeqLogAD-T candidates are A0 next-event, A1 next-event plus ranking, A2 next-event plus coordinate-aware localization, and A3 next-event plus ranking and localization. The combined loss is not claimed novel.

Isolation Forest P0 features are sequence length, event-frequency summaries, unique-template ratio, repetition, transition rarity, and entropy. Temporal features are P1 until timestamp quality is validated. Expert D uses structural edit distance, LCS, event n-gram overlap, and transition overlap in P0; dense semantic retrieval is P1.

## 11. Seed and selection budget

- Seed `42` is the development/default reproducibility seed and has no special scientific meaning.
- Report stochastic core methods with seeds `42`, `43`, and `44`.
- Use at most 12 candidate configurations per stochastic core method in the initial controlled search, evaluated with seed 42.
- Re-evaluate the top two validation candidates across all three seeds.
- Select using mean `VAL_EXPERT` PR-AUC; tie-break by lower FPR, then lower latency.
- Seed/config selection never uses TEST.

Deterministic experts still record a seed/config identity where libraries require it, but repeated identical deterministic fits are not presented as independent stochastic runs.

## 12. Scoring, aggregation, and thresholds

Required sequence aggregations are mean, max, and top-r, where:

```text
r = max(1, ceil(0.10 × valid_sequence_length))
```

Padding is excluded. Expert aggregation is selected on `VAL_EXPERT`; fusion aggregation is selected on the selection half of `VAL_FUSION`.

Primary threshold report uses the threshold maximizing validation F1. A secondary operational report uses a validation FPR target of 1%. Both thresholds are frozen before TEST. PR-AUC is the primary threshold-free detection metric.

## 13. Complementarity gate

Before learned structured fusion, measure at minimum:

- Pearson and Spearman score correlation;
- prediction disagreement;
- pairwise error overlap/double-fault behavior;
- oracle ensemble gain;
- anomaly-family conditional performance;
- token/gap/transition localization overlap where supported;
- leave-one-expert-out and add-one-expert marginal contribution.

Each expert receives a human-recorded decision:

- `KEEP`: paired-bootstrap marginal PR-AUC improvement is positive with its 95% interval above zero, or absolute PR-AUC gain is at least 0.005, or a family-specific recall/localization gain is at least 0.02, or it contributes a verified evidence family unavailable elsewhere;
- `DEMOTE`: detection contribution is insufficient but unique structured evidence remains useful downstream;
- `REMOVE`: absolute Spearman correlation is at least 0.95, error overlap is at least 0.90, leave-one-out degradation is below 0.005 with a confidence interval containing zero, and no unique evidence family is demonstrated.

These are frozen practical decision thresholds, not prior-work findings or proof of optimality. If results are ambiguous, default to the simpler retained set and document uncertainty.

## 14. Fusion ladder and ownership

Required comparators:

- F0 strongest single frozen expert;
- F1 normalized mean;
- F2 validation-weighted average;
- F3 voting/rank voting;
- F4 logistic stacking;
- F5 MLP stacking;
- F6 standard gating/MoE;
- F7 evidential/Dempster-Shafer only if `LIT-001` and technical checks justify applicability;
- F8 proposed Structured Evidence Consensus Fusion.

F8 may fail. It must be compared against F0 and appropriate learned fusion baselines, not only weak averaging. It is `PROPOSED / TO BE TESTED`, not novel.

Fusion consumes only frozen/versioned expert evidence. `FUSION_TRAIN` fits learned fusion; the first half of `VAL_FUSION` fits calibration; the second half selects fusion, thresholds, and optional abstention. TEST is excluded from every fusion choice.

The v1 minimal candidate fusion loss is detection plus fused-localization loss. A redundancy term is not core until `LIT-001` and RQ2 demonstrate both prior-art position and measurable need. Conflict is a fusion input, verifier signal, abstention signal, and evaluation variable; the collapse-prone `confidence × conflict` penalty is excluded.

## 15. Evaluation contract

### 15.1 Real anomaly detection

Report per dataset and do not pool HDFS/BGL into one headline result:

- **primary:** PR-AUC;
- Precision, Recall, F1, and FPR at frozen thresholds;
- median and P95 inference latency;
- throughput and peak memory;
- per-anomaly-family results where ground truth supports them.

### 15.2 Localization

- Report token, gap, and transition localization separately.
- Use appropriate precision/recall/F1 or ranking metrics per coordinate family.
- HDFS real localization is `N/A` under current labels.
- BGL source alert-token localization is secondary and explicitly distinguished from synthetic localization.
- Never merge synthetic and real localization scores into one value.

### 15.3 Calibration and abstention

- Calibration: Brier score, negative log likelihood, and ECE with 15 equal-mass bins.
- Abstention: risk-coverage curve, AURC, coverage, and error at matched coverage.
- Calibration/abstention policies are selected without TEST.

### 15.4 Statistical analysis

- Report 95% paired bootstrap confidence intervals with 5,000 resamples for primary paired comparisons.
- HDFS resampling unit is the block/session.
- BGL uses temporal block resampling over parent windows to preserve local dependence.
- Use McNemar's test for paired binary error differences where assumptions apply.
- Apply Holm correction within each declared family of multiple comparisons.
- Report effect sizes and confidence intervals, not p-values alone.

## 16. Mandatory leakage audit

The final protocol gate must check and record at least:

1. raw chronological order preservation;
2. HDFS block/component atomicity;
3. HDFS boundary purge records;
4. BGL window containment inside one partition;
5. duplicate raw/parent sequences across partitions;
6. overlapping-context leakage across partitions;
7. parser fit scope;
8. frozen parser state and registry hash;
9. normalization fit scope;
10. label-field exclusion from parser/model text/features;
11. synthetic-parent partition ownership;
12. no raw-data mutation;
13. no padding contribution to losses/scores;
14. no no-op synthetic mutations;
15. no TEST reference in expert/reference indexes;
16. no TEST fit in calibration/fusion/thresholds;
17. out-of-sample expert evidence for learned fusion;
18. checkpoint and config selection scope;
19. TEST command lock and access log;
20. deterministic artifact IDs, seeds, and hashes.

Any failed critical leakage check blocks scientific evaluation.

## 17. Downstream RAG/Agent boundary

RAG and the investigation agent are downstream consumers only. They:

- consume frozen expert/fusion outputs and versioned evidence IDs;
- cannot change scores, thresholds, checkpoints, partitions, or expert-retention decisions;
- cannot access hidden TEST labels;
- cannot train/update the detector or fusion;
- cannot treat log text as instructions;
- must cite evidence IDs and may return `INSUFFICIENT_EVIDENCE`;
- remain read-only and cannot execute production remediation.

RQ5/downstream experiments are P1 and cannot substitute for RQ1–RQ4 core evaluation.

## 18. Required future artifacts

Implementation must eventually produce versioned, non-overwriting artifacts for:

- raw pre-partition/split manifest and purge report;
- frozen parser state, registry, normalization config, and hashes;
- canonical event and sequence datasets;
- mutation manifests by source partition;
- expert configs/checkpoints/counts/reference indexes;
- out-of-sample ExpertEvidence records;
- calibration and complementarity reports;
- expert `KEEP/DEMOTE/REMOVE` decision record;
- fusion configs/artifacts and selection report;
- TEST unlock record and immutable final result bundle.

Artifact schemas and commands are not implemented by PROTOCOL-001.

## 19. Change control

The human-approved values in this historical snapshot and `configs/protocols/protocol-v1.yaml` were the v1.0 source of truth. Active future work now uses protocol v1.1. A proposed change under v1.0 required:

1. reason and affected scientific claims;
2. new protocol version;
3. decision-log entry and citation/provenance update;
4. invalidated artifacts/runs;
5. confirmation that the change was not selected after viewing TEST results.

Editorial corrections that do not alter scientific behavior may keep version 1.0 but must be logged. Any behavioral change increments the protocol version.

## 20. Freeze declaration

The human researcher approved the protocol decisions on 2026-08-20. No experiment result supports them yet. `PROTOCOL-001` is complete at the contract level; implementation begins only with a separately authorized downstream task.
