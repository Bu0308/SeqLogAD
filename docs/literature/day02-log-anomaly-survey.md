# Day 2 Reading Note — Log Anomaly Detection Survey

> **HISTORICAL READING NOTE.** This artifact records the Day 2 V1/V2 reading state. Active V3 research questions and contribution status are defined in `docs/research-questions.md` and `Plan/02_RESEARCH_PLAN.md`.

## Source and reading scope

Primary survey: Landauer et al., [Deep Learning for Anomaly Detection in Log Data: A Survey](https://arxiv.org/abs/2207.03820), published in *Machine Learning with Applications* (2023). Day 2 selectively reviewed the problem framing, preprocessing pipeline, anomaly concepts, sequential approaches, datasets and evaluation discussion. This is a reading note, not full LIT-001 gap validation.

## Extracted knowledge

Log anomaly detection is not a single input/output problem. Results depend on log collection, parsing/template extraction, grouping into sequences or windows, representation, detector objective and evaluation split. Consequently, detector comparisons are only meaningful when preprocessing and leakage controls are aligned.

Sequence models can learn context and event ordering, while count/frequency representations summarize occurrence patterns. Neither family is assumed to be universally superior. Dataset-specific labels, grouping choices, class imbalance and inconsistent evaluation practices can dominate reported results. The survey structures prior work; it does not prove this project's hypotheses or provide a controlled benchmark result for our pipeline.

## Frequency versus behavioral sequence anomaly

A frequency anomaly is an unusual count or rate: for example, `LOGIN_FAILURE` occurs 50 times instead of its normal 2 times in a window. A behavioral sequence anomaly can preserve ordinary event identities and frequencies while violating expected order or context:

```text
Expected: A → B → C → D
Observed: A → C → B → D
```

Both sequences contain each event once, so a count vector may be identical. The behavior differs because `B → C` is replaced by `C → B`.

Likewise:

```text
Expected: LOGIN_REQUEST → TOKEN_VALIDATE → USER_LOOKUP → SESSION_CREATE → LOGIN_SUCCESS
Observed: LOGIN_REQUEST → USER_LOOKUP → SESSION_CREATE → LOGIN_SUCCESS
```

No individual event must be rare and no `ERROR` is required; the missing validation step is the anomaly. This motivates n-gram/transition baselines and a next-event sequence model, while still requiring direct measurement against simpler baselines.

## Architectural impact

- Preserve event ordering and grouping metadata in later canonical schemas.
- Use the same parsing and chronological split for baseline/model comparisons.
- Evaluate event-level and sequence-level scores, not only raw frequencies.
- Audit parser, sequence-length, padding and threshold leakage before RQ1 claims.
- Treat HDFS block traces and BGL time/window sequences as different preliminary constructions.

## Claim safety

Status of all Day 2 conclusions: `PROPOSED` or `HYPOTHESIS — TO BE TESTED`. The survey does not establish novelty, sequence-model superiority, RAG benefit or accurate agent RCA. Full gap validation remains LIT-001.
