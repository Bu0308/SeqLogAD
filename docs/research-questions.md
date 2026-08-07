# Research Questions

All hypotheses below are marked **HYPOTHESIS — TO BE TESTED**. No result is implied by this document.

## RQ1 — Sequence anomaly detection

**Question:** Can sequence-based unsupervised models detect behavioral event-sequence anomalies more effectively than simple statistical baselines under leakage-safe chronological evaluation?

- **Priority:** CORE / P0
- **Objective:** Determine whether modeling event order and context adds measurable value beyond event frequency, n-gram/Markov transitions and count-based features.
- **Hypothesis:** HYPOTHESIS — TO BE TESTED. A sequence model may have an advantage when the anomaly depends on ordering, omission, repetition, timing or context, but it is not assumed to beat statistical baselines on every dataset.
- **Required experiment:** Compare statistical baselines and a P0 sequence detector using identical preprocessing, sequence strategy, chronological split and leakage controls.
- **Primary metrics:** Precision, Recall, F1, PR-AUC, FPR, inference latency and throughput.
- **Required components:** HDFS, BGL, parser, sequence builder, frequency/ngram/Markov baselines, Isolation Forest baseline, LSTM detector and evaluator.
- **Analysis slices:** dataset, anomaly type, sequence strategy, score aggregation and threshold strategy.

## RQ2 — Sequence-aware retrieval

**Question:** Does hybrid retrieval combining semantic and sequential similarity retrieve more relevant normal executions and incidents than dense semantic retrieval alone?

- **Priority:** CORE / P0
- **Objective:** Measure whether event ordering and transition similarity improve retrieval beyond semantic text similarity.
- **Hypothesis:** HYPOTHESIS — TO BE TESTED. Hybrid retrieval may improve Recall@k, MRR or nDCG, with a possible latency and weight-calibration trade-off.
- **Required experiment:** Compare BM25, dense, sequential and hybrid retrieval with relevance judgments, validation-only fusion-weight tuning and a held-out evaluation split.
- **Primary metrics:** Recall@1, Recall@3, Recall@5, MRR, nDCG and latency.
- **Required components:** Knowledge base, BM25, dense retrieval, sequential similarity, hybrid ranker and retrieval evaluator.

## RQ3 — Evidence verification

**Question:** Does explicit evidence verification reduce unsupported root-cause conclusions and hallucinations in an AI investigation agent?

- **Priority:** CORE / P0
- **Objective:** Measure the safety and grounding effect of an explicit verifier after retrieval and generation.
- **Hypothesis:** HYPOTHESIS — TO BE TESTED. Verification may reduce unsupported conclusions and hallucinations, potentially increasing `INSUFFICIENT_EVIDENCE` outcomes and latency.
- **Required experiment:** Compare LLM-only, RAG without verifier and RAG with verifier on curated investigation cases with supporting, contradicting, irrelevant and missing evidence.
- **Primary metrics:** Citation correctness, evidence precision, evidence recall, unsupported conclusion rate, hallucination rate and root-cause Top-1/Top-3 accuracy when ground truth is available.
- **Required components:** Evidence schema, retrieval context, structured generator, deterministic verifier, single-agent workflow and evaluation cases.

## RQ4 — Test recommendation

**Question:** Can an investigation agent convert detected sequence anomalies and evidence-grounded hypotheses into relevant, structured and potentially executable regression tests?

- **Priority:** CORE / P0 for structured recommendations; P1/P2 for executable skeletons and execution.
- **Objective:** Determine whether investigation context can be converted into actionable QA artifacts.
- **Hypothesis:** HYPOTHESIS — TO BE TESTED. Recommendations grounded in observed/expected sequences and verified evidence may have higher relevance and human acceptance than recommendations without sequence context.
- **Required experiment:** Evaluate structured recommendations using curated anomaly cases and human review; compare contextual and reduced-context conditions if feasible.
- **Primary metrics:** Test relevance, step completeness, expected-result correctness, human acceptance rate and executable-test rate if skeleton generation is implemented.
- **Required components:** Investigation context, expected/observed sequence comparison, verified hypotheses, documentation/test retrieval, recommendation schema and feedback review.

## Claim status policy

Research results must be labeled `Proposed`, `Hypothesis`, `Supported`, `Partially supported`, `Unsupported` or `Rejected`. Novelty is not decided here; it is deferred to `LIT-001`.
