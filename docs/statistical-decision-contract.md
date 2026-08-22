# EFFECT-001 — Statistical Decision Contract

| Field | Value |
|---|---|
| Contract ID | `EFFECT-001` |
| Parent protocol | `PROTOCOL-001` v1.1 |
| Contract version | `1.0` |
| Prepared | 2026-08-22 |
| Approved | 2026-08-22 |
| Status | **FROZEN — HUMAN APPROVED** |
| Machine contract | `configs/protocols/effect-001.yaml` |
| Citation note | `docs/references/EFFECT-001-citations.md` |
| Empirical status | `NOT_RUN` |
| Statistical contract ready | **YES** |
| Scientific pipeline authorized by this task | **NO** |

EFFECT-001 is a binding statistical addendum anticipated by Protocol v1.1. It does not rewrite the approved v1.1 data/supervision contract. The estimands, comparison family, baseline-selection rule, equal-budget rule, bootstrap design, confidence level, seed aggregation, decision regions, negative-result policy, and numerical practical-effect margins are frozen below. Human approval completes this statistical gate but does not authorize split/parser/baseline/KT/TEST execution by itself.

## 1. Freeze status

### Frozen now

- dataset-specific estimands and Average Precision semantics;
- four mutually exclusive conclusion regions;
- 95% paired cluster-percentile bootstrap with 10,000 valid replicates;
- HDFS block/session and BGL non-overlapping 100-event parent-window resampling units;
- strongest-orderless candidate family, validation-only selection, tie handling, and selection limitation;
- equal family-level tuning budget;
- seed aggregation and separation from bootstrap uncertainty;
- primary and secondary multiple-comparison families;
- KT-3 estimand and decision rule;
- negative/null/inconclusive outcomes as valid results;
- complete prohibition on TEST-informed design decisions.

### Human-approved fields

- `delta_HDFS = 0.01` absolute AP;
- `delta_BGL = 0.01` absolute AP;
- framework: `RESOURCE_FEASIBILITY_MARGIN`;
- approval source: `HUMAN_RESEARCHER`;
- approval timing: `PRE_EXPERIMENT`;
- result-informed: `false`.

The same margin keeps the primary rule simple, while HDFS and BGL estimates and conclusions remain independent. These values cannot be retroactively changed after observing scientific outcomes.

## 2. Primary estimand and metric

For each dataset `d` in `{HDFS, BGL}`:

```text
Delta_AP_d = AP_sequence,d - AP_strongest_orderless,d
```

`AP_sequence,d` is the Average Precision of the validation-selected Markov/N-gram comparator. `AP_strongest_orderless,d` is the Average Precision of the order-insensitive candidate selected entirely on `VAL_EXPERT`. A different orderless candidate may be selected for HDFS and BGL.

Average Precision is the threshold-free, non-interpolated area summary:

```text
AP = sum_n (Recall_n - Recall_(n-1)) * Precision_n
```

The anomaly class is positive. In this repository, `PR-AUC` in the primary contract means this Average Precision definition, not trapezoidal interpolation. The original evaluation set must contain both classes, unique unit IDs, and one finite scalar score per method/unit; otherwise the analysis is invalid rather than silently repaired.

HDFS and BGL produce separate estimates, intervals, decisions, and limitations. No pooled estimate and no “works on at least one dataset” claim is permitted under this contract. A cross-dataset paragraph may only synthesize the two registered dataset-specific conclusions.

`VAL_EXPERT` supports method selection and a selection-conditioned development gate only; such an interval cannot be described as the final confirmatory result. The registered final dataset-specific conclusion is computed on the once-opened human TEST after every method/config/claim is frozen.

## 3. Minimum practical effect — approved human decision

The targeted literature review found no transferable universal numerical AP margin. The values below are supplied and approved by the human researcher, not inferred or selected by Codex.

| Dataset | Required field | Current value | Status |
|---|---|---:|---|
| HDFS | `delta_HDFS` in absolute AP points | `0.01` | `FROZEN_HUMAN_APPROVED` |
| BGL | `delta_BGL` in absolute AP points | `0.01` | `FROZEN_HUMAN_APPROVED` |

Each value must be finite and strictly between 0 and 1, chosen before any KT/baseline score is inspected, and accompanied by one of these defensible frameworks:

| Framework | Scientific interpretation | Sensitivity | Risk when too small | Risk when too large | Effect on decision regions |
|---|---|---|---|---|---|
| **Operational utility — preferred** | Smallest AP gain that justifies extra sequence-model complexity under a documented alert-review/false-alert utility target | Directly tied to intended use, but requires a credible utility statement external to TEST | Trivial gains become “meaningful”; near-ceiling noise may be overinterpreted | Useful sequence gains may be called equivalent/inconclusive | Larger `delta_d` widens equivalence and shrinks gain/harm regions |
| **Resource/feasibility margin — fallback** | Smallest gain worth the engineering/compute cost for this 3-credit project when no operational deployment target exists | Transparent and feasible, but answers a resource question rather than universal practical utility | Same false-importance risk as above | May reject scientifically interesting small effects | Same boundary behavior; must be labeled a feasibility margin |
| Literature benchmark | Transfer a margin from prior log papers | No verified source provides an equivalent AP margin for these exact bytes/protocol | Arbitrary transfer across prevalence/variants | Arbitrary transfer may erase real effects | **Not currently defensible** |
| Zero margin / observed-result margin | Treat any positive delta or a post-result value as meaningful | Maximally result-sensitive | Collapses practical into statistical significance | N/A | **Prohibited** |

A validation-only power or interval-width analysis may check whether the approved margin is measurable with available units. It may not manufacture practical importance from sample size or be used to revise the margin after KT results.

After approval, report sensitivity at `0.5 * delta_d` and `2 * delta_d` as secondary analyses. These do not replace the registered primary margin.

### Completed approval record

```text
delta_HDFS = 0.01 AP
delta_BGL = 0.01 AP
rationale_framework = RESOURCE_FEASIBILITY_MARGIN
rationale = an absolute AP gain below 0.01 does not justify additional
            sequential-model complexity in this constrained 3-credit,
            under-3-month project
approved_by = HUMAN_RESEARCHER
approved_on = 2026-08-22
approval_timing = PRE_EXPERIMENT
result_informed = false
TEST consulted = NO
KT/baseline outcomes consulted = NO
```

## 4. Statistical decision table

Let `[L_d, U_d]` be the registered 95% uncertainty interval for `Delta_AP_d`. For both datasets, `delta_d = 0.01` AP.

| Interval position | Scientific conclusion |
|---|---|
| `L_d > +0.01` | `MEANINGFUL_SEQUENCE_GAIN` |
| `L_d >= -0.01` and `U_d <= +0.01` | `PRACTICAL_EQUIVALENCE` |
| `U_d < -0.01` | `MEANINGFUL_HARM` |
| Any other overlap/crossing | `INCONCLUSIVE` |

Boundary equality belongs to the equivalence interval, not gain/harm. `INCONCLUSIVE` never means “no difference.” The 95% interval is an uncertainty statement conditional on frozen methods/seeds and observed evaluation units; it is not proof of superiority or causal mechanism.

## 5. Paired bootstrap contract

### Common algorithm

1. Join labels and all compared score vectors by immutable evaluation-unit ID.
2. Reject the run if IDs are duplicated/missing, scores are non-finite/missing, or the original evaluation set lacks either class.
3. Sample the registered dependency units with replacement, drawing the original number of units.
4. Apply the same resampled IDs to every paired method/condition.
5. Compute AP for both methods and their difference inside each replicate.
6. Collect exactly 10,000 valid differences using resampling seed `42`.
7. Return the percentile interval at quantiles `0.025` and `0.975`.

HDFS resamples complete block/session units. BGL resamples complete, non-overlapping 100-event parent windows. Individual events are never treated as IID bootstrap observations, and no sequence/window is broken apart. The BGL design preserves dependence inside each parent window but does not model residual dependence between adjacent parents; every report must state this limitation. If a pre-run implementation audit shows that adjacent-parent dependence invalidates this unit, the contract must be amended before metrics rather than switching resampling after outcomes.

A replicate whose resampled labels contain only one class is degenerate: reject it and redraw, count it, and report the rejection rate. Stop after 100,000 total attempts. If 10,000 valid replicates are not reached, return `INCONCLUSIVE_RESAMPLING_FAILURE`; do not switch interval methods after seeing the result.

The interval captures evaluation-unit sampling uncertainty conditional on already selected methods and fixed seeds. It does not include parser/split/model-selection uncertainty, and that limitation must appear in reports.

## 6. Strongest orderless baseline contract

The required primary candidate set is fixed before any validation score:

1. unseen-event type;
2. sequence length;
3. total event count;
4. event count vector;
5. Isolation Forest over order-insensitive count/summary features.

Isolation Forest is promoted from v1.1 `SHOULD` to an EFFECT-001 required primary candidate because a claim against the “strongest eligible orderless baseline” should not omit the registered stronger orderless control. If any required candidate is missing, invalid, or dropped after metrics are seen, the primary comparison is blocked and requires a pre-result protocol amendment.

Eligibility requires normal `BASE_TRAIN` fitting only, no order-derived features, no labels as fit targets/model input, an immutable config/source identity before validation scoring, active contract tests, and a complete finite score for every legal evaluation unit.

For each dataset, select the candidate with maximum `VAL_EXPERT` AP. A stochastic candidate uses mean AP across seeds `42`, `43`, and `44`; deterministic candidates have one run identity. Exact ties within `1e-12` use the fixed simplicity order shown above. TEST never participates.

The final interval conditions on this selected candidate. It does not model selection uncertainty. Reports must state this limitation; fixing the family/config grid, selecting on validation only, and using one final locked TEST contrast are the safeguards against post-hoc cherry-picking.

## 7. Sequential selection and equal budget

Markov/N-gram is the minimal primary sequential family. Its candidate config IDs and tie order are frozen before validation scoring, and selection uses maximum `VAL_EXPERT` AP without TEST.

The orderless family and Markov/N-gram family each receive at most 12 complete candidate configurations per dataset. Allocation and IDs are fixed before the first validation metric; no adaptive extension or transfer of unused budget is allowed. Stochastic configurations run all three seeds; deterministic methods do not create fake repeated seeds.

Both sides use the same legal normal `BASE_TRAIN`, validation access, parser state, frozen event vocabulary, sequence/evaluation-unit IDs, metric code, and one human-owned final TEST access. AP uses scores directly, so threshold tuning is outside the primary comparison. Secondary threshold metrics must use the same validation-only threshold policy.

## 8. Seed aggregation

- deterministic methods: one deterministic run;
- stochastic methods: seeds `42`, `43`, `44`;
- configuration selection: mean seed-specific AP, never the best seed;
- reported central AP: mean of seed-specific AP values;
- report every seed plus mean, standard deviation, minimum, and maximum;
- bootstrap: inside each unit-resample, calculate seed-specific AP and average before forming the method difference;
- bootstrap does not resample seeds; unit-sampling uncertainty and between-seed variability are reported separately.

## 9. Multiple-comparison policy

There is one pre-registered primary contrast per dataset. HDFS and BGL have separate scientific conclusions and no pooled/disjunctive claim. Therefore there is no within-dataset primary multiplicity and no correction is applied to these two separately labeled estimates.

Comparisons against each individual orderless candidate, Markov/N-gram variants, thresholded metrics, latency, and memory are secondary/descriptive. They may have intervals but cannot support a confirmatory sequence-advantage claim. Promoting any secondary family to confirmatory status requires a protocol amendment made before its outcomes are inspected and must specify a multiplicity method. This contract does not add baselines post hoc and then cherry-pick a favorable comparison.

## 10. KT-3 sequence-destruction rule

For each dataset:

```text
Delta_AP_shuffle,d = AP_original_sequence,d - mean(AP_shuffled_sequence,d)
```

The selected sequential comparator is frozen first. Shuffles use deterministic transformation seeds `42`, `43`, and `44`, preserve multiset/count vector/length/label/partition/parent identity, and never mutate raw data. The shuffled AP is averaged across the three registered transformations. The approved `0.01` AP margin, 95% paired bootstrap, and four decision regions apply to each dataset:

| Interval position | KT-3 conclusion |
|---|---|
| Entirely above `+0.01` | `MEANINGFUL_ORDER_SENSITIVITY` |
| Entirely inside `[-0.01, +0.01]` | `NO_MEANINGFUL_ORDER_SENSITIVITY / PRACTICAL_EQUIVALENCE` |
| Entirely below `-0.01` | `SHUFFLED_BETTER_UNEXPECTED` |
| Otherwise | `INCONCLUSIVE` |

The generator must attempt a non-noop permutation. Units that cannot change order (for example, too short or all events identical) remain in the primary population with zero perturbation and a recorded reason, preventing favorable post-hoc exclusion. A perturbable-only analysis is secondary/descriptive.

## 11. Negative-result policy

Every following outcome is valid: an orderless baseline wins, practical equivalence, no meaningful order sensitivity, a dataset cannot support a sequence-advantage claim, or the evidence remains inconclusive. The protocol does not require SeqLogAD or sequence modeling to win.

## 12. TEST and execution gate

At approval time, no scientific baseline, KT-1, KT-2, KT-3, parser-derived experiment, or TEST result had been observed. TEST did not select the margin, baseline, hyperparameter, resampling setting, comparison family, or conclusion boundary.

The addendum is now `FROZEN_HUMAN_APPROVED`, but this is not authorization to execute the scientific pipeline. Split generation, TEST locking, parser fitting, baseline/KT execution, and final TEST remain separate tasks with their own dependencies and human authorization.

## 13. Provenance boundary

The methodological sources support AP-focused evaluation, uncertainty reporting, pre-specified equivalence bounds, and dependency-aware resampling. They do not prescribe SeqLogAD's `0.01` margins, 10,000 replicates, 95% level, seed, baseline family, tuning budget, tie order, or decision labels. Those are explicit SeqLogAD decisions and remain empirical-result-free.
