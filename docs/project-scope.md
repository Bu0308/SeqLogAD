# Project Scope

## 1. Problem Statement

The project detects and investigates behavioral anomalies in event sequences extracted from system logs. A single event can be normal while the ordering, omission, repetition, timing or context of events is abnormal.

The target flow is:

```text
raw logs → canonical events → event sequences → anomaly scores
→ sequence-aware evidence retrieval → evidence verification
→ root-cause hypotheses → structured test recommendation → human review
```

## 2. Product Positioning

The product is:

> **A sequence-aware AI investigation and QA layer on top of log/observability infrastructure.**

It is **not**:

- an Elasticsearch replacement;
- a Kibana replacement;
- “ELK but better”.

## 3. What Elastic/ELK already does well

Elastic/ELK is strong in:

- ingestion;
- storage;
- indexing;
- generic full-text and metadata search;
- dashboards and visualization;
- monitoring and alerting;
- time-series and observability infrastructure;
- integrations at operational scale.

This project does not compete with Elastic on those dimensions.

## 4. Project Differentiation

The research and product layer focuses on:

1. behavioral event-sequence anomaly detection;
2. sequence-aware retrieval;
3. evidence-grounded investigation;
4. root-cause hypothesis verification;
5. regression-test recommendation;
6. tester feedback and review.

Elasticsearch may become a backend dependency for storage, filtering, BM25, vector search and retrieval. It is not the research contribution. Detector, agent, evidence verifier and test recommendation must depend on stable interfaces, not on Elasticsearch implementation details.

## 5. Primary Users

| User | Primary need |
|---|---|
| QA/tester | Validate anomaly, root cause and recommended regression test |
| Developer | Inspect observed versus expected event sequences |
| SRE/observability engineer | Investigate incidents with traceable evidence |
| Researcher | Reproduce and compare detector, retrieval and agent experiments |

## 6. Core Use Cases

- Detect missing, extra, reordered, repeated, delayed or unexpected events.
- Retrieve nearest normal sequences and similar incidents.
- Inspect surrounding logs and documentation.
- Generate evidence-linked root-cause hypotheses.
- Return `INSUFFICIENT_EVIDENCE` when evidence is inadequate.
- Produce structured test recommendations.
- Capture tester verdicts for anomaly, root cause and test.

## 7. P0 MVP

P0 is mandatory for the 8-week MVP. These items are scoped today but are not implemented on Day 1:

- HDFS dataset;
- BGL dataset;
- reproducible dataset and configuration convention;
- Drain3 parser;
- canonical event schema;
- sequence construction;
- chronological split;
- statistical baselines;
- LSTM next-event detector;
- anomaly scoring;
- detector evaluation;
- knowledge base;
- BM25 retrieval;
- dense retrieval;
- sequential retrieval;
- hybrid retrieval;
- evidence ID schema;
- evidence verification;
- single investigation agent;
- structured incident report;
- structured test recommendation;
- automated tests;
- research evaluation;
- reproducible README and technical report.

## 8. P1 Recommended

- lightweight Transformer comparison;
- Elasticsearch adapter;
- Streamlit MVP;
- Docker and GitHub Actions;
- agent tracing and replay;
- performance benchmark;
- human feedback model;
- pytest skeleton generation, subject to safety validation.

## 9. P2 Optional

- OpenStack dataset;
- adaptive threshold;
- sandbox test execution;
- richer feedback memory;
- OpenTelemetry ingestion.

## 10. P3 / Future Work

- multi-agent investigation;
- continual learning;
- automatic remediation;
- Kubernetes-wide RCA;
- massive-scale production deployment;
- custom foundation model.

## 11. Non-goals

- Replacing Elasticsearch, Kibana or the Elastic Stack.
- Building distributed log storage or a generic search engine.
- Production write actions, deployment changes or automatic remediation.
- Arbitrary shell execution.
- Claiming universal root-cause accuracy.
- Claiming novelty before `LIT-001` and literature review are complete.

## 12. Research Boundaries

The four research questions are defined in [`research-questions.md`](research-questions.md). Every question is a hypothesis to be tested, not a proven claim. Detector, retrieval, evidence/RAG and agent quality are evaluated as separate layers.

## 13. Safety Boundaries

- The MVP agent is read-only.
- Logs and documentation are untrusted data, not instructions.
- Every RCA hypothesis requires resolvable evidence IDs.
- The agent may return `INSUFFICIENT_EVIDENCE`.
- No production remediation tool is exposed.

## 14. Data/Privacy Boundaries

- Do not commit secrets, access tokens, passwords, private raw logs or private identifiers.
- Raw and generated data remain in ignored paths unless explicitly approved.
- Public dataset acquisition instructions should be preferred over copying data into Git.
- Private datasets must remain outside version control or in explicitly ignored paths.
- Dataset provenance and checksums will be recorded in later data tasks.

## 15. MVP Acceptance Criteria

The MVP is complete when:

1. HDFS and BGL have reproducible data/config conventions.
2. Raw logs can become canonical events.
3. Sequences are deterministic and chronological splits are leakage-audited.
4. Statistical baselines and at least one P0 sequence detector are evaluated.
5. BM25, dense, sequential and hybrid retrieval have a benchmark protocol.
6. Evidence IDs are used end-to-end.
7. A read-only agent can investigate, retrieve evidence, generate hypotheses, verify evidence and return insufficient evidence.
8. The agent can generate a structured test recommendation.
9. Core pipeline and safety behavior have automated tests.
10. Main experiments are reproducible and claims are tied to results.

## 16. Research Claim Safety

The following claims are prohibited until evidence exists:

- “our system is better than Elastic”;
- “our approach is novel”;
- “the sequence model is superior”;
- “RAG improves detection”;
- “the agent identifies root cause accurately”.

Allowed claim states are:

`Proposed` · `Hypothesis` · `Supported` · `Partially supported` · `Unsupported` · `Rejected`.

Novelty status remains `UNVALIDATED` until `LIT-001`.

## 17. Day 1 Locked Decisions

- Product positioning is a sequence-aware investigation/QA layer.
- HDFS and BGL are core datasets.
- LSTM is the P0 neural sequence detector; Transformer is P1.
- The agent is single-agent, LangGraph-based and read-only.
- Local Parquet/FAISS is the first backend path; Elasticsearch is an adapter later.
- Chronological evaluation is the default.
- Evidence IDs are mandatory for RCA claims.
- Metrics and experiment facts must be pipeline-generated where possible.
