# 02 — Research Plan v1.1

## Research story

SeqLogAD first asks whether the verified HDFS/BGL protocol contains sequence information that cannot be explained by unseen event types, length, or counts. It adds model complexity only after cheap falsification.

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

## Baseline strength

MUST: unseen event, sequence length, total count, count vector, and Markov/N-gram. SHOULD: Isolation Forest over order-insensitive features. All use the same legal partitions, selection budget, evaluation unit, and threshold policy.

## Falsification

- Saturating order-insensitive controls prevent a sequence-advantage claim.
- Strong orderless HDFS dependence prevents using HDFS alone as sequence evidence.
- No meaningful shuffle degradation prevents an order-sensitivity claim.
- No residual long-range question removes Transformer from core.
- Failed randomization/counterfactual controls remove localization faithfulness.
- No expert complementarity prevents trainable fusion.

`minimum_practical_effect` is frozen by the human before runs after LIT-001 and validation-only feasibility analysis. It is not selected from observed outcomes.

## Literature status

`LIT-001 = DONE` as a targeted, reproducible review. It confirms material HDFS/BGL ceiling/variant risk, requires strong order-insensitive controls, and finds strong prior art for generic Transformer, fusion/MoE, localization, and synthetic-mutation claims. It establishes no SeqLogAD result and no algorithmic novelty. A new claim-specific systematic search is required before any future novelty claim.

## Scientific integrity

- No parser/model/fusion fit or TEST access occurred during the freeze.
- Real labels are never model inputs/base loss.
- TEST selection is forbidden.
- External findings are never relabeled as project metrics.
- Human owns execution and conclusions; AI prepares code/tests/commands.
- Negative results are retained and reported.
