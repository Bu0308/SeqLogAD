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
- Canonical event/template and sequence/localization/mutation contracts plus Protocol-v1.1/KT-3 provenance compatibility implemented and tested; no real scientific event/sequence/control artifact generated.
- Parser-independent HDFS block/component and BGL source-chronology metadata
  extraction implemented and tested.
- Protocol v1.1, EFFECT-001, and PROTOCOL-SPLIT-CLARIFY-001 are frozen. Exact allocation/purge/residual/hash semantics are implemented as deterministic real HDFS/BGL split artifacts; both physical TEST guards are `SEALED / NEVER_OPENED`.
- No parser run, baseline/model fit, training, tuning, scientific TEST access, or result.

## 3. Scope classification

| Class | Work |
|---|---|
| `MUST` | LIT-001 completion; EFFECT-001 approval; raw five-way split + TEST guard; normal-only frozen Drain3; canonical events/sequences; unseen-event, length, count/count-vector/Isolation Forest baselines; Markov/N-gram; KT-1–KT-3; AP/paired uncertainty/secondary metrics; human final TEST; reproducibility |
| `SHOULD` | Duplicate/collision and label-dependence diagnostics; additional robustness summaries |
| `CONDITIONAL` | Transformer; synthetic localization and KT-4/KT-5; F0/F1 and KT-6 after complementarity |
| `FUTURE` | Dataset expansion, retrieval/RAG/Agent, regression-test recommendation, Elasticsearch, API/UI, dashboard |
| `REMOVED_FROM_CORE` | LSTM, normal-reference expert, fixed four-expert architecture, F2–F8 trainable fusion ladder, multi-agent and production platform scope |

## 4. Critical path

```text
LIT-001 + approved EFFECT-001 (`0.01 AP` per dataset) + SCHEMA-COMPAT-001
→ metadata/group extraction
→ frozen exact split-semantics addendum
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
- Exact boundaries use cumulative floor without labels or ratio repair.
- HDFS ranks eligible raw lines, preserves connected components, and purges every component occupying multiple nominal partitions.
- BGL splits source ranks first, then builds non-overlapping 100-event parents independently per partition and records every 1–99-line tail as `DROPPED_RESIDUAL_WINDOW`.
- Drain3 fits normal `BASE_TRAIN` only and then freezes.
- Reserved fusion partitions remain reserved unless an approved future amendment says otherwise.
- TEST is physically sealed by dataset, split-payload, and partition hashes; future access requires the separate human-only audited workflow.

## 6. Experiment ladder

1. `KT-1`: unseen-event, length, total-count, count-vector, required Isolation Forest, and Markov under equal legal scope.
2. `KT-2`: count-vector collision, purity/conditional dependence, and out-of-sample order-insensitive prediction on HDFS.
3. `KT-3`: destroy order while preserving multiset/count/length/label and compare paired performance.
4. Apply KC-1–KC-4.
5. If justified, open Transformer or conditional localization; otherwise report the negative/limited sequence result.
6. Open any fusion only after at least two experts demonstrate measurable complementarity.

EFFECT-001 freezes the statistical method family and human-approved `delta_HDFS = delta_BGL = 0.01 AP` under `RESOURCE_FEASIBILITY_MARGIN`. The values were fixed pre-experiment, are not literature-universal thresholds, and cannot change after outcomes.

## 7. Ownership

AI/Codex prepares implementation, tests, configs, deterministic builders, and commands. The human executes empirical runs/training/tuning, freezes thresholds, selects validation-only configurations, opens TEST once, and owns scientific conclusions. Metrics stay empty until a traceable artifact exists.

## 8. Scope cuts

If schedule pressure appears, cut in this order: conditional fusion, localization, Transformer, extra datasets, then all downstream/demo work. Isolation Forest is required by EFFECT-001 unless a pre-result amendment changes the primary candidate family. Never cut data identity, split/leakage discipline, orderless controls, Markov comparator, KT-3, TEST lock, or reproducibility.

## 9. Completion criteria

The core is complete only when:

1. LIT-001 is complete and EFFECT-001, including both human-approved margins, is frozen.
2. Split/parser/events/sequences are deterministic, hashed, and leakage-audited.
3. KT-1–KT-3 are human-executed without TEST tuning.
4. Sequence claims follow pre-registered kill criteria.
5. Conditional components are either justified by gate evidence or explicitly removed.
6. Final TEST is opened once by the human after artifact freeze.
7. Reported metrics come from immutable run outputs with uncertainty and limitations.

Detailed rules are in [`../docs/research-protocol-v1.1.md`](../docs/research-protocol-v1.1.md), [`../docs/split-clarification-contract.md`](../docs/split-clarification-contract.md), and [`../docs/statistical-decision-contract.md`](../docs/statistical-decision-contract.md).
