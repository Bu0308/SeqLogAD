# 02 — Research Plan v1.1

## Research story

SeqLogAD first asks whether the verified HDFS/BGL protocol contains sequence information that cannot be explained by unseen event types, length, or counts. It adds model complexity only after cheap falsification.

Execution is currently paused before canonical-event generation. The
pre-model HDFS purge audit returned `PURGE_REPRESENTATIVENESS_CONCERN` because
the non-random purge removed 22.7374% of eligible lines and aggregate purged
component prevalence differs from retained prevalence. This is a
data-validity result, not an answer to any RQ. `PURGE-DECISION-001` human review
must resolve the stop gate without silently changing the frozen split.

## Questions

| ID | Question | Scope | Status |
|---|---|---|---|
| RQ1 | Are HDFS/BGL suitable evidence for a non-trivial sequence claim under this exact protocol? | MUST | HYPOTHESIS / NOT_RUN |
| RQ2 | How much value does Markov/N-gram add over strong order-insensitive controls? | MUST | HYPOTHESIS / NOT_RUN |
| RQ3 | Does order destruction materially reduce sequential performance while preserving counts/length? | MUST | HYPOTHESIS / NOT_RUN |
| RQ4 | Can anomaly positions/transitions be localized faithfully beyond sanity controls? | CONDITIONAL | HYPOTHESIS / NOT_RUN |

Fusion and downstream AI are not primary RQs.

## Killer experiment ladder

1. **KT-1:** trivial/strong order-insensitive ceiling versus Markov under equal scope.
2. **KT-2:** HDFS count-vector collision/dependence and out-of-sample prediction.
3. **KT-3:** deterministic sequence destruction preserving multiset/count/length/label.
4. Apply KC-1–KC-4 before any Transformer.
5. If gates open, pre-register KT-4/KT-5 localization controls.
6. Only after measured complementarity, consider KT-6 and simple fusion.

## Baseline strength and EFFECT-001

MUST: unseen event, sequence length, total count, count vector, Isolation Forest over order-insensitive features, and Markov/N-gram. EFFECT-001 requires all five orderless candidates so “strongest eligible” cannot be weakened after outcomes. The orderless and sequential families each receive at most 12 pre-registered configurations per dataset and the same legal partitions, parser/vocabulary, validation access, evaluation units, and metric implementation.

The per-dataset primary estimand is `Delta_AP_d = AP_sequence,d - AP_strongest_orderless,d`. EFFECT-001 freezes a 95% paired cluster-percentile bootstrap with 10,000 valid replicates, seed `42`, HDFS block/session units, BGL non-overlapping 100-event parent windows, separate seed reporting, no pooled HDFS/BGL claim, and four outcomes: meaningful gain, practical equivalence, meaningful harm, or inconclusive.

## Falsification

- Saturating order-insensitive controls prevent a sequence-advantage claim.
- Strong orderless HDFS dependence prevents using HDFS alone as sequence evidence.
- No meaningful shuffle degradation prevents an order-sensitivity claim.
- No residual long-range question removes Transformer from core.
- Failed randomization/counterfactual controls remove localization faithfulness.
- No expert complementarity prevents trainable fusion.

`delta_HDFS` and `delta_BGL` are human-approved at `0.01 AP` under `RESOURCE_FEASIBILITY_MARGIN`, before any scientific outcome. A sequence gain is meaningful only when the 95% interval lies entirely above `+0.01`; equivalence lies inside `[-0.01,+0.01]`; harm lies below `-0.01`; otherwise the result is inconclusive. These values cannot be changed retroactively.

## Literature status

`LIT-001 = DONE` as a targeted, reproducible review. It confirms material HDFS/BGL ceiling/variant risk, requires strong order-insensitive controls, and finds strong prior art for generic Transformer, fusion/MoE, localization, and synthetic-mutation claims. It establishes no SeqLogAD result and no algorithmic novelty. A new claim-specific systematic search is required before any future novelty claim.

## Scientific integrity

- No parser/model/fusion fit or TEST access occurred during the freeze.
- Real labels are never model inputs/base loss.
- TEST selection is forbidden.
- External findings are never relabeled as project metrics.
- Human owns execution and conclusions; AI prepares code/tests/commands.
- Negative results are retained and reported.
