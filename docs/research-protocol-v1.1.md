# PROTOCOL-001 v1.1 — Sequence-Value Research Freeze

| Field | Frozen value |
|---|---|
| Protocol ID | `PROTOCOL-001` |
| Version | `1.1` |
| Status | **FROZEN — HUMAN APPROVED** |
| Approval date | 2026-08-21 |
| Direction | `HYBRID_B_PLUS_C` with Option B as core |
| Machine contract | `configs/protocols/protocol-v1.1.yaml` |
| Citation note | `docs/references/RESEARCH-FREEZE-v1.1-citations.md` |
| Empirical status | `NOT_RUN` |

This protocol is a pre-registered research contract. It contains no experimental result and makes no claim that HDFS/BGL are trivial, that sequence order is useful, or that any model is superior.

## 1. Research framing

Project topic:

> **Sequence-Based Unsupervised Anomaly Detection for Large-Scale Event Logs**

Precise supervision description:

> **Normal-only self-supervised sequential anomaly detection with synthetic supervision for conditional anomaly localization.**

Core question:

> How much additional anomaly-detection value does sequence order provide beyond strong order-insensitive baselines under a leakage-controlled, chronological, and equal-budget protocol?

The approved direction is `HYBRID_B_PLUS_C`:

- **Option B is core:** retain HDFS/BGL and directly test dataset suitability, trivial-baseline ceiling, and sequence added value.
- **Option C is conditional:** open localization-faithfulness work only if sequence signal and synthetic-label validity pass their gates.
- Dataset expansion/replacement is a fallback, not an active change.

## 2. Frozen pipeline order

```text
verified immutable raw logs
→ metadata/group-key extraction without a fitted parser
→ raw chronological partition assignment
→ controlled label isolation and BASE_TRAIN normal pool
→ fit Drain3 only on permitted normal BASE_TRAIN messages
→ freeze parser, normalization, template registry, and event mapping
→ transform permitted partitions read-only
→ canonical events and sequences built inside partition boundaries
→ order-insensitive baselines and dataset-suitability diagnostics
→ Markov/N-gram sequential baseline
→ sequence-destruction negative control
→ scientific gate decision
→ conditional Transformer/localization/fusion only when their gates pass
→ human-only locked final TEST
```

Raw partitioning precedes every fitted transform and every overlapping/derived context. No generated window, sequence context, parser update, vocabulary update, normal-reference index, calibrator, threshold, or model choice may cross or use a forbidden partition boundary.

## 3. Dataset role and suitability status

HDFS and BGL remain the verified core datasets. Their bytes, manifests, and fingerprints are unchanged.

| Dataset | Construction contract | Scientific status |
|---|---|---|
| HDFS | Block/session atomicity; boundary-spanning connected components are purged | Candidate evidence source; sequence informativeness is `TO_BE_TESTED` |
| BGL | Source chronology; non-overlapping 100-event parent windows after partitioning | Candidate evidence source; trivial-baseline ceiling is `TO_BE_TESTED` |

Prior work raises dataset-suitability risks, but its exact dataset variants, preprocessing, split, and evaluation may differ from SeqLogAD. Therefore no external number is treated as a SeqLogAD result and neither dataset is declared suitable or unsuitable before KT-1 through KT-3.

HDFS Loghub preprocessed templates, structured CSV, event traces, and `.npz` artifacts are not scientific inputs. Only verified `HDFS.log` plus the controlled label file may enter the future pipeline.

## 4. Five-way chronological partition contract

The top-level raw split remains:

| Partition | Share | Frozen role in v1.1 |
|---|---:|---|
| `BASE_TRAIN` | 60% | Fit parser and normal-only detector/reference statistics |
| `FUSION_TRAIN` | 10% | Reserved for conditional learned fusion; unused otherwise |
| `VAL_EXPERT` | 10% | Select baseline/sequential configurations and thresholds |
| `VAL_FUSION` | 10% | Reserved for conditional calibration/fusion selection; unused otherwise |
| `TEST` | 10% | One final evaluation by the human researcher |

Rules:

1. Assignment is chronological over raw dataset-specific atomic units; no random stratification reorders time.
2. HDFS groups/components remain atomic. A component crossing a nominal boundary is recorded and purged, not split or moved for class balance.
3. BGL windows are generated only after raw partition assignment and never overlap.
4. Reserved fusion partitions are not silently merged into other partitions after results are observed.
5. Target and realized ratios, purge records, file hashes, and deterministic partition IDs must be written to a future split manifest.
6. SPLIT-001 has created deterministic partition artifacts and hash-bound physical TEST guards. Both TEST partitions remain **SEALED / NEVER_OPENED**, with open count and unlock-record count equal to zero.
7. `PURGE-AUDIT-001` is a post-split data-validity audit only. It fixes aggregate `PURGED`/`RETAINED` component identities before label lookup, emits no partition-specific outcome statistic, and cannot change membership. Its result is `PURGE_REPRESENTATIVENESS_CONCERN`.
8. Binding addendum `PURGE-DECISION-001` resolves the stop gate with human-approved Option B: the frozen retained-component HDFS split remains the sole primary analysis, and a whole-component purge sensitivity is pre-registered as secondary, robustness-only, non-selection, non-tuning, and `NOT_RUN`. See [`../configs/protocols/purge-decision-v1.yaml`](../configs/protocols/purge-decision-v1.yaml).

## 5. Label and supervision contract

- Labels may be used by controlled data preparation to form authorized normal pools.
- Labels may support validation and final evaluation in their authorized partitions.
- Labels are never parser/model input features and never enter the base self-supervised loss.
- Real anomaly labels do not train the frozen core detector.
- Synthetic localization labels, if the localization gate opens, come only from deterministic mutations of authorized normal training parents.
- Synthetic localization and real-anomaly detection are reported separately.
- TEST labels are unavailable to training, fitting, normalization, parsing, vocabulary construction, thresholding, calibration, architecture selection, research-direction selection, or novelty selection.

## 6. Parser fit/freeze contract

1. Extract only minimum metadata/group keys needed for pre-partitioning before parser fit.
2. Fit Drain3 only on authorized normal `BASE_TRAIN` messages.
3. Freeze Drain3 state, normalization, template registry, event identity mapping, package/config versions, and hashes.
4. Transform later permitted partitions read-only; unseen templates map to the reserved `EVT_UNSEEN` contract without expanding the frozen vocabulary.
5. Report OOV/unseen-template behavior without using TEST to change parser decisions.

## 7. Minimal scientific methods

### MUST — order-insensitive controls

- unseen event-type detector;
- sequence-length-only score/classifier;
- total event count and per-event count-vector baseline.

### SHOULD — stronger order-insensitive control

- Isolation Forest over validation-frozen count/summary features.

### MUST — sequential comparator

- Markov/N-gram next-event or transition-surprise detector fitted from normal `BASE_TRAIN` counts.

### CONDITIONAL

- lightweight Transformer only after the sequence-signal gate;
- synthetic localization only after sequence signal and target-validity gates;
- F0 strongest-single and F1 simple score fusion only after at least two justified complementary experts exist;
- trainable fusion, retrieval expert, LSTM, RAG/Agent, API/UI, and Elasticsearch are outside the frozen core.

All methods receive the same legal data scope and comparable selection budget. Three seeds (`42`, `43`, `44`) are required for stochastic core methods. Deterministic methods record one deterministic run identity rather than pretending repeated identical fits are independent runs.

## 8. Pre-registered killer experiments

Every row is `NOT_RUN`.

| ID | Purpose | Required design | Decision use |
|---|---|---|---|
| `KT-1` | Trivial-baseline ceiling | Compare unseen-event, length, count/count-vector, EFFECT-001-required Isolation Forest, and Markov under the same frozen split | Establish room for sequence claims |
| `KT-2` | HDFS count-label dependence | Count-vector collision analysis, label purity/conditional entropy or justified equivalent, and out-of-sample order-insensitive prediction | Test whether orderless features largely explain labels |
| `KT-3` | Sequence destruction | Shuffle/destroy order while preserving each sample's event multiset, count vector, length, label, partition, and ID linkage | Directly test order sensitivity |
| `KT-4` | Localization randomization | Conditional: randomize target positions and compare with registered localization | Sanity-check localization signal |
| `KT-5` | Counterfactual repair/deletion | Conditional: repair/delete predicted causes and measure score change against controls | Test localization faithfulness |
| `KT-6` | Corrupted expert control | Conditional: inject random/corrupted evidence without changing legal partitions | Test whether fusion ignores useless experts |

KT-1 through KT-3 precede any Transformer, localization, or fusion implementation. KT-4 through KT-6 are implemented/run only if their parent gate opens.

## 9. Negative-control invariants

For KT-3, order destruction must preserve:

- parent sample identity linkage and partition;
- event multiset and count vector;
- valid sequence length;
- label and evaluation unit;
- padding mask semantics.

The transformation seed, permutation, input/output hash, and no-op status must be logged. A no-op shuffle is rejected or explicitly counted. No raw log is mutated.

Conditional localization controls must compare against random positions and registered counterfactual operations. Conditional fusion controls must include at least one random or corrupted expert and must not reward confidence merely because an additional expert exists.

## 10. Pre-registered kill criteria

`minimum_practical_effect` remains `TO_BE_FROZEN_BEFORE_RUN`. Its owner is the human researcher, supported by LIT-001 and a validation-only power/feasibility analysis. No numerical threshold is invented in this freeze.

| ID | Trigger | Required response |
|---|---|---|
| `KC-1` | Strong order-insensitive baseline reaches the dataset ceiling within the pre-frozen practical margin | Do not claim sequence advantage; reframe result around measured added value/negative evidence |
| `KC-2` | HDFS orderless representation nearly determines labels under out-of-sample analysis | Do not use HDFS alone as primary evidence of sequence benefit |
| `KC-3` | KT-3 causes no practically meaningful sequential-detector degradation | Do not claim order sensitivity on that dataset/protocol |
| `KC-4` | Markov/N-gram shows no meaningful sequence value or long-range residual need | Do not implement Transformer in the core |
| `KC-5` | Localization fails randomization/counterfactual sanity controls | Do not claim localization faithfulness; remove it from the evaluated contribution |
| `KC-6` | Experts show negligible disagreement/oracle gain/marginal value | Do not build trainable fusion; retain strongest single or simple comparator only |

Negative or null findings are valid outcomes. No architecture is retained merely because it appeared in an earlier plan.

## 11. Metrics and selection

- Primary real-anomaly detection metric: **PR-AUC** per dataset.
- Secondary: Precision, Recall, F1, FPR, median/P95 latency, throughput, and memory.
- Report target and realized partition ratios and class prevalence only through authorized validation/final-evaluation commands.
- Select configurations and thresholds on the designated validation partition only.
- Any claimed sequence added value requires paired comparisons and uncertainty intervals over the correct evaluation unit.
- Exact statistical tests, resampling counts, and minimum practical effect are frozen before the first run; values are not selected after seeing outcomes.

## 12. Conditional gates

### Transformer gate

Open only if KT-1 through KT-3 show remaining sequence signal and a scientifically relevant question that Markov/N-gram cannot answer. Otherwise status is `REMOVE_FROM_CORE`.

### Localization gate

Open only if sequence signal exists, deterministic synthetic targets are valid, and KT-4/KT-5 designs can test faithfulness rather than only agreement with synthetic labels.

### Fusion gate

Open only if at least two eligible experts demonstrate different inductive signals and measurable complementarity through score correlation, disagreement, error overlap, oracle gain, and marginal contribution. If opened, compare strongest single (`F0`) before simple mean (`F1`); trainable F2–F8 are not part of v1.1 core and require a new approved amendment.

## 13. TEST policy

TEST may be run once by the human researcher only after the following are frozen and hashed:

- split manifest and physical access guard;
- parser/template/event mapping;
- sequence construction and negative-control transformations;
- selected baseline/sequential method, seeds, thresholds, and metric code;
- claim and kill-criterion decision record;
- Git revision and environment snapshot.

Routine commands must not expose TEST labels, counts, previews, metrics, or model comparisons. A genuine implementation failure follows a documented invalidation and protocol-amendment process; it does not authorize result-driven tuning.

## 14. Human/AI ownership

AI/Codex may prepare source, tests, configs, deterministic artifact builders, and commands. The human researcher approves protocol changes, freezes practical-effect thresholds, executes empirical runs/training/tuning, selects checkpoints/configs from authorized validation only, opens final TEST, and owns scientific conclusions. AI must never fabricate a metric or promote `NOT_RUN` to a result.

## 15. Scope boundaries

- No raw-data mutation or manifest regeneration is authorized by this protocol freeze.
- No parser/model/baseline/split/negative-control implementation is performed by the freeze task.
- RAG/Agent can only be a future downstream consumer of frozen evidence and cannot change detection outcomes or access hidden TEST labels.
- Elasticsearch is an optional future backend, not a contribution.
- Project source license remains an owner decision; data availability does not grant redistribution rights.

## 16. Required future artifacts

Before any scientific result, future tasks must create and validate:

1. targeted LIT-001 matrix completion and frozen practical-effect policy;
2. raw partition/split manifest, purge report, hashes, and TEST access guard;
3. parser state/config/registry hashes;
4. canonical event and sequence artifacts inside partitions;
5. baseline configs, predictions, and negative-control manifests;
6. registered gate decisions and claim states;
7. immutable final result bundle after human TEST unlock.

SCHEMA-COMPAT-001 froze explicit historical-v1.0/active-v1.1 partition identity support and KT-3 control provenance. This compatibility result does not create a split, sequence, shuffle, TEST guard, or scientific artifact.

## 17. Change control

Any behavioral change requires a new protocol version, decision-log entry, citation/provenance update, affected-artifact inventory, and confirmation that TEST was not consulted. Historical protocol files remain immutable. Editorial changes may update the current entry point but cannot silently alter the machine contract.

## 18. Freeze declaration

The human researcher approved the v1.1 redirect on 2026-08-21. No killer experiment, parser run, model fit, training, tuning, or scientific TEST evaluation has occurred. The next task must be separately authorized.
