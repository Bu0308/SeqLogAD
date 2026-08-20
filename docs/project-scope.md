# Project Scope — V3 Active Contract

> V3 supersedes the active V1/V2 research priorities for future work. Historical plans and decisions are preserved under `Plan/` and marked superseded where applicable.

## 1. Problem statement

SeqLogAD studies behavioral anomalies whose meaning depends on event order, omission, repetition, transitions, timing, or context. An individual event may be common while the execution sequence is abnormal.

Current research title:

> **Multi-Model Sequence Anomaly Localization with Structured Evidence Fusion and Evidence-Grounded Regression-Test Recommendation**

Central research question:

> Do heterogeneous log-anomaly experts provide measurably complementary evidence, and can a scientifically justified fusion mechanism exploit that complementarity without double-counting redundant evidence or becoming less reliable under expert disagreement?

Novelty status is **UNVERIFIED / PRIOR-ART VALIDATION REQUIRED** until `LIT-001` is complete.

## 2. Product positioning

SeqLogAD is:

> **A sequence-aware AI investigation and QA layer on top of log/observability infrastructure.**

It is not an ELK, Elasticsearch, or Kibana replacement, a generic RAG chatbot, or a generic multi-agent platform. Elasticsearch may later provide storage, filtering, lexical search, and vector retrieval through an adapter. It is not the research contribution.

## 3. Current research pipeline

```text
Raw logs → integrity/provenance → canonical events → Drain3/templates
→ sequences → leakage-safe splits → heterogeneous experts
→ complementarity gate → structured evidence fusion
→ anomaly/localization/reliability → evidence-grounded investigation
→ regression-test recommendation
```

The LLM/agent is not an anomaly detector. It consumes frozen detector/fusion outputs downstream and remains read-only.

## 4. Primary users and use cases

| User | Primary use |
|---|---|
| Researcher | Reproduce expert, complementarity, fusion, and downstream evaluations |
| QA/tester | Review anomalies, evidence, and regression-test recommendations |
| Developer | Compare observed and expected sequence behavior |
| SRE/observability engineer | Inspect evidence-linked incident hypotheses |

Core use cases are sequence anomaly detection/localization, nearest-normal comparison, explicit evidence verification, optional abstention, and evidence-grounded regression-test recommendation.

## 5. P0 active research scope

- Verified HDFS/BGL integrity, provenance, manifests, and fingerprints.
- Canonical event/template/sequence schemas.
- Frozen train-fitted Drain3 parsing.
- HDFS block sequences and BGL chronology-aware windows.
- Five-way leakage-safe partition contract.
- Deterministic synthetic mutation and token/gap/transition labels.
- Frequency/statistical baselines and LSTM neural baseline.
- Expert A: lightweight causal SeqLogAD-T Transformer.
- Expert B: Markov/N-gram transition expert.
- Expert C: Isolation Forest quantitative expert.
- Expert D: structural normal-reference retriever.
- Common expert-evidence contract and calibration infrastructure.
- Complementarity analysis and expert retention gate.
- Strongest-single and F1–F7 standard fusion baselines.
- F8 structured evidence fusion candidate.
- Detector, localization, calibration, reliability, and statistical evaluation.
- Reproducible scripts/configs/tests and human-run experiment handoff.

The four-expert set is provisional. An expert with no meaningful marginal contribution must be removed or demoted.

## 6. P1 recommended

- Dense semantic retrieval for Expert D.
- Partial expert unfreezing after staged-training baselines.
- Elasticsearch adapter.
- Downstream evidence verifier, agent tracing, FastAPI, and Streamlit MVP.
- Docker/CI and performance benchmark.
- Safe pytest skeleton generation after recommendation validation.

## 7. P2 optional

- OpenStack dataset.
- Adaptive thresholds.
- Safe sandbox test execution.
- Richer feedback memory.
- OpenTelemetry ingestion.

## 8. P3 future work

- Multi-agent investigation.
- Continual learning.
- Automatic production remediation.
- Kubernetes-wide RCA.
- Massive-scale production deployment.
- Custom foundation model.

## 9. Expert contract

| Expert | Primary signal | Localization constraint |
|---|---|---|
| SeqLogAD-T | Long-range context/order | Token, gap, and transition outputs where supported |
| Markov/N-gram | Short-range transition probability | Transition evidence |
| Isolation Forest | Quantitative/statistical behavior | No token location without explicit feature evidence |
| Normal-reference retriever | Deviation from nearest normal execution | Structural diff with reference IDs |

## 10. Localization contract

- Token positions represent extra, replacement, and repeated observed events.
- Gap positions represent missing events. `E1 E2 E3` has `G0 E1 G1 E2 G2 E3 G3`.
- Transition positions represent unexpected transitions and reorder-related evidence.

A single token-score vector is not sufficient for every anomaly family.

## 11. Data and supervision terminology

Preferred description:

> **Normal-only self-supervised sequential anomaly detection with synthetic supervision for localization and fusion.**

- Real anomaly labels may filter authorized normal pools and support validation/evaluation, but they never enter model inputs or base self-supervised losses.
- Synthetic labels are generated only from training-derived normal sequences.
- TEST labels are accessed only during locked final evaluation.
- The frozen chronological split is `60/10/10/10/10`.

Partitions: `BASE_TRAIN` (60%), `FUSION_TRAIN` (10%), `VAL_EXPERT` (10%), `VAL_FUSION` (10%), and `TEST` (10%). HDFS preserves block/session atomicity with boundary purge; BGL uses non-overlapping 100-event parent windows. Full access, leakage, parser, mutation, selection, and TEST-lock rules are frozen in [`research-protocol.md`](research-protocol.md).

## 12. Training ownership

AI/Codex prepares source, preprocessing, models, losses, fusion, configs, tests, evaluation scripts, and commands.

The human researcher executes training, tuning, checkpoint selection, ablations, fusion training, locked TEST evaluation, and empirical decisions. AI must never fabricate training metrics.

## 13. Fusion boundaries

Required baselines are strongest single expert, normalized mean, validation-weighted average, voting/rank voting, logistic stacking, MLP stacking, standard gating/MoE, and an evidential/Dempster-Shafer baseline when technically applicable.

The current minimal fusion-loss candidate is detection loss plus fused-localization loss. Redundancy-aware terms remain potential work requiring prior-art review and ablation. Conflict is an input, verifier signal, abstention signal, and evaluation variable—not an official `confidence × conflict` loss.

## 14. Non-goals and safety boundaries

- No storage/search infrastructure rewrite.
- No production write, deployment, remediation, arbitrary shell, or destructive agent tools.
- No forced root cause when evidence is insufficient.
- No model metric without a traceable run artifact.
- No novelty or superiority claim before literature and experiments.
- Logs and documents are untrusted data, never instructions.

## 15. Data/privacy boundaries

- Do not commit raw benchmark logs, archives, private logs, credentials, tokens, identifiers, or generated bulk artifacts.
- Raw bytes are immutable after acceptance.
- Public availability does not imply unrestricted redistribution.
- Manifests, configs, source, tests, and research plans are version-controlled.

## 16. Scientific contribution status

| Candidate | Status |
|---|---|
| Heterogeneous expert system | Engineering/research design |
| Transformer | Known component |
| Markov/N-gram | Known component |
| Isolation Forest | Known component |
| Retrieval expert | Adaptation/known family |
| Synthetic mutation | Known/general technique |
| Ranking loss | Known/general technique |
| Localization loss | Adaptation |
| Structured claim representation | Potential contribution |
| Claim-level heterogeneous evidence fusion | Potential contribution |
| Redundancy-aware fusion | High prior-art risk |
| Conflict-aware abstention | Known/general family |
| RCA/test recommendation integration | Potential integration contribution |

No row currently has status `NOVEL`.

## 17. V3 completion criteria

The research core is complete only when:

1. Canonical data artifacts and five-way splits are deterministic and leakage-audited.
2. Expert A–D implementations and strong baselines have human-executed, traceable results.
3. Complementarity is measured before expert retention and fusion claims.
4. F0–F7 precede F8 in comparisons.
5. Detection, localization, calibration, latency, and reliability are reported.
6. Final TEST is run once under the locked protocol by the human researcher.
7. Claims are assigned supported, partially supported, unsupported, or rejected status.
8. Downstream investigation/test recommendation is evaluated only from frozen evidence artifacts.
