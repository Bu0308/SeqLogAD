# SeqLogAD — Master Research and Implementation Plan v1.1

**Status:** ACTIVE  
**Approved:** 2026-08-21  
**Empirical status:** `NOT_RUN`  
**Novelty status:** `UNVERIFIED`

## 1. Scientific objective

Topic:

> **Sequence-Based Unsupervised Anomaly Detection for Large-Scale Event Logs**

Core question:

> How much additional anomaly-detection value does sequence order provide beyond strong order-insensitive baselines under a leakage-controlled, chronological, and equal-budget protocol?

The project is not committed to proving sequence superiority. A null/negative result is valid. Localization is secondary and conditional; fusion and downstream AI are not primary contributions.

## 2. Current verified foundation

- HDFS/BGL canonical archives, raw-byte manifests, checksums, and fingerprints verified.
- Python 3.12 project-local environment, editable package, dependency lock, and CLIs verified.
- Canonical event/template and sequence/localization/mutation schema contracts implemented and tested; no real scientific event/sequence artifact generated.
- Protocol v1.1 frozen at contract level; no physical split or TEST guard yet.
- No parser run, baseline/model fit, training, tuning, scientific TEST access, or result.

## 3. Scope classification

| Class | Work |
|---|---|
| `MUST` | LIT-001 completion; raw five-way split + TEST guard; normal-only frozen Drain3; canonical events/sequences; unseen-event, length, count/count-vector baselines; Markov/N-gram; KT-1–KT-3; PR-AUC/secondary metrics; human final TEST; reproducibility |
| `SHOULD` | Isolation Forest as a strong order-insensitive comparator; duplicate/collision and label-dependence diagnostics; paired uncertainty analysis |
| `CONDITIONAL` | Transformer; synthetic localization and KT-4/KT-5; F0/F1 and KT-6 after complementarity |
| `FUTURE` | Dataset expansion, retrieval/RAG/Agent, regression-test recommendation, Elasticsearch, API/UI, dashboard |
| `REMOVED_FROM_CORE` | LSTM, normal-reference expert, fixed four-expert architecture, F2–F8 trainable fusion ladder, multi-agent and production platform scope |

## 4. Critical path

```text
LIT-001 + practical-effect freeze
→ protocol/schema identity compatibility check
→ metadata/group extraction
→ raw chronological split manifest + physical TEST guard
→ normal BASE_TRAIN Drain3 fit/freeze
→ canonical events and partition-contained sequences
→ KT-1 order-insensitive ceiling
→ KT-2 HDFS count-label dependence
→ Markov/N-gram
→ KT-3 sequence destruction
→ human gate decision
→ conditional branch or robustness/replication
→ frozen artifacts
→ one human TEST run
→ report
```

## 5. Dataset protocol

- Keep exact verified HDFS/BGL bytes and fingerprints.
- Split raw atomic units chronologically `60/10/10/10/10` before fitted transforms and windows.
- HDFS preserves block/session components and purges boundary-spanning groups.
- BGL uses non-overlapping 100-event parents after partitioning.
- Drain3 fits normal `BASE_TRAIN` only and then freezes.
- Reserved fusion partitions remain reserved unless an approved future amendment says otherwise.
- TEST is contractually sealed now and physically sealed only after split hashes/access guard exist.

## 6. Experiment ladder

1. `KT-1`: unseen-event, length, count/count-vector, optional Isolation Forest, and Markov under equal legal scope.
2. `KT-2`: count-vector collision, purity/conditional dependence, and out-of-sample order-insensitive prediction on HDFS.
3. `KT-3`: destroy order while preserving multiset/count/length/label and compare paired performance.
4. Apply KC-1–KC-4.
5. If justified, open Transformer or conditional localization; otherwise report the negative/limited sequence result.
6. Open any fusion only after at least two experts demonstrate measurable complementarity.

No practical-effect threshold is invented. It is frozen by the human before the first run using LIT-001 and validation-only feasibility analysis.

## 7. Ownership

AI/Codex prepares implementation, tests, configs, deterministic builders, and commands. The human executes empirical runs/training/tuning, freezes thresholds, selects validation-only configurations, opens TEST once, and owns scientific conclusions. Metrics stay empty until a traceable artifact exists.

## 8. Scope cuts

If schedule pressure appears, cut in this order: conditional fusion, localization, Transformer, Isolation Forest, extra datasets, then all downstream/demo work. Never cut data identity, split/leakage discipline, trivial controls, Markov comparator, KT-3, TEST lock, or reproducibility.

## 9. Completion criteria

The core is complete only when:

1. LIT-001 and practical-effect policy are frozen.
2. Split/parser/events/sequences are deterministic, hashed, and leakage-audited.
3. KT-1–KT-3 are human-executed without TEST tuning.
4. Sequence claims follow pre-registered kill criteria.
5. Conditional components are either justified by gate evidence or explicitly removed.
6. Final TEST is opened once by the human after artifact freeze.
7. Reported metrics come from immutable run outputs with uncertainty and limitations.

Detailed rules are in [`../docs/research-protocol-v1.1.md`](../docs/research-protocol-v1.1.md).
