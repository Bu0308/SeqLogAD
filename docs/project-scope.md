# Project Scope — Research Freeze v1.1

## 1. Problem statement

SeqLogAD studies whether event order contributes anomaly-detection information beyond event presence, counts, and sequence length in large-scale system logs.

Topic:

> **Sequence-Based Unsupervised Anomaly Detection for Large-Scale Event Logs**

Core question:

> How much additional anomaly-detection value does sequence order provide beyond strong order-insensitive baselines under a leakage-controlled, chronological, and equal-budget protocol?

No sequence advantage, dataset suitability, localization faithfulness, fusion value, or novelty is assumed.

## 2. Product positioning

SeqLogAD is a research prototype for sequence-aware log anomaly analysis. It is not an ELK, Elasticsearch, or Kibana replacement, a generic RAG chatbot, or a generic multi-agent platform. Elasticsearch and downstream AI may be future integrations; neither is a v1.1 contribution.

## 3. Approved direction

`HYBRID_B_PLUS_C`:

- Option B is the frozen core: keep verified HDFS/BGL and measure sequence added value.
- Option C is conditional: evaluate localization faithfulness only after sequence and sanity gates.
- Option A is fallback: dataset expansion requires evidence and a protocol amendment.

## 4. Primary users

| User | Current use |
|---|---|
| Researcher/student | Run reproducible dataset-suitability and sequence-value experiments |
| Supervisor/reviewer | Audit protocol, leakage controls, gates, artifacts, and claims |
| Future QA/SRE user | Consume frozen anomaly evidence only after core research is valid |

## 5. MUST — frozen core

- Preserve verified HDFS/BGL identity and immutable raw bytes.
- Complete targeted `LIT-001`; freeze EFFECT-001 methods and obtain human approval for both dataset-specific margins before runs.
- Create raw chronological `60/10/10/10/10` split manifest and physical TEST guard.
- Preserve HDFS block/session atomicity and BGL non-overlapping 100-event parents.
- Fit Drain3 on normal `BASE_TRAIN` only, freeze it, and transform later partitions read-only.
- Generate deterministic canonical events and partition-contained sequences.
- Implement unseen-event, sequence-length, total-count, and count-vector controls.
- Implement Isolation Forest as a required primary order-insensitive candidate under EFFECT-001.
- Implement Markov/N-gram as the minimal sequential comparator.
- Run KT-1, KT-2, and KT-3 under equal legal data/selection budgets.
- Use PR-AUC as primary detection metric; report secondary error/efficiency metrics.
- Use seeds `42`, `43`, `44` for stochastic core methods.
- Apply pre-registered kill criteria and accept negative results.
- Execute TEST once by the human only after artifact/claim freeze.

## 6. SHOULD

- HDFS count-vector collision, purity/conditional-dependence, and out-of-sample analyses.
- Lightweight reproducibility/CI checks that do not expand scientific scope.

## 7. CONDITIONAL

| Component | Gate |
|---|---|
| Lightweight Transformer | KT-1–KT-3 show meaningful sequence signal and an unresolved long-range question |
| Synthetic localization | Sequence signal exists; deterministic targets valid; KT-4/KT-5 can test faithfulness |
| F0 strongest-single and F1 simple mean | At least two eligible experts show measurable complementarity |
| Additional dataset | Current datasets fail suitability gates and LIT-001 supports a candidate |

Conditional does not mean planned by default. A human decision record must open each branch.

## 8. FUTURE

- Retrieval/RAG and evidence-grounded Agent.
- Regression-test recommendation.
- Elasticsearch adapter.
- FastAPI, Streamlit/dashboard, OpenTelemetry.
- Broader production deployment, feedback memory, and multi-agent work.

## 9. REMOVED FROM CORE

- Fixed four-expert architecture.
- LSTM comparator.
- Normal-reference retrieval expert.
- F2–F8 learned/evidential/structured fusion ladder.
- Fusion as the central contribution.
- RAG/Agent/API/UI as <3-month deliverables.

Historical documents retain these ideas but must be labeled superseded.

## 10. Minimal scientific architecture

```text
raw integrity → raw pre-partition → normal BASE_TRAIN parser fit/freeze
→ canonical events/sequences → order-insensitive controls
→ Markov/N-gram → sequence destruction → gate decision
→ conditional branch only if justified → one locked human TEST
```

## 11. Data and supervision boundaries

Preferred framing:

> **Normal-only self-supervised sequential anomaly detection with synthetic supervision for conditional anomaly localization.**

- Real labels may filter normal pools and support authorized validation/final evaluation.
- Labels never enter parser/model text, model inputs, or base loss.
- Synthetic localization and real-anomaly detection remain separate result families.
- No synthetic mutation touches raw data.
- HDFS preprocessed templates/traces are excluded as scientific inputs.

## 12. TEST boundary

TEST is contractually sealed but not physically sealed. Physical sealing requires a split manifest, partition hashes, and access guard. TEST cannot support fitting, tuning, thresholding, calibration, architecture/dataset/claim selection, or novelty decisions. The human opens it once after freeze.

## 13. Falsification and kill policy

- Order-insensitive saturation blocks sequence-advantage claims.
- Strong HDFS count-label dependence blocks use of HDFS alone as sequence evidence.
- No meaningful shuffle degradation blocks order-sensitivity claims.
- No residual long-range question blocks Transformer work.
- Failed localization sanity controls block localization-faithfulness claims.
- No complementarity blocks trainable fusion.

EFFECT-001 is human-approved with `delta_HDFS = delta_BGL = 0.01 AP` under `RESOURCE_FEASIBILITY_MARGIN`. The margins were fixed before outcomes and cannot be changed retroactively.

## 14. Research and safety non-goals

- No claim that SeqLogAD is better than Elastic/ELK.
- No SOTA, first-method, or novelty claim without verified prior art and experiments.
- No production remediation or arbitrary execution.
- No hidden TEST access by Agent/RAG or any other component.
- No fabricated metric, citation, table, plot, or completed experiment.

## 15. Data/privacy/license boundaries

- Raw benchmarks, archives, private logs, credentials, tokens, and generated bulk artifacts stay out of Git.
- Manifests, configs, source, tests, protocols, and citations are version-controlled.
- Public downloadability is not redistribution permission.
- Project source license remains `OWNER_DECISION_REQUIRED`.

## 16. Core completion criteria

The core is complete only when:

1. LIT-001 is complete and EFFECT-001, including both human-approved numerical margins, is frozen.
2. Raw split/TEST guard, parser, events, and sequences are deterministic and leakage-audited.
3. KT-1–KT-3 have traceable human-executed artifacts.
4. Gate/kill decisions follow the pre-registered protocol.
5. Conditional components are either justified or explicitly cut.
6. Final TEST is opened once after artifact freeze.
7. Claims and limitations map to pipeline-generated evidence.

See [`research-protocol-v1.1.md`](research-protocol-v1.1.md) and [`statistical-decision-contract.md`](statistical-decision-contract.md).
