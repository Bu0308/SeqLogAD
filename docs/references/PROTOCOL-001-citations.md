# PROTOCOL-001 v1.0 — Historical Citation and Method-Provenance Note

> Preserved for [`research-protocol-v1.0.md`](../research-protocol-v1.0.md). Active v1.1 provenance is recorded in [`RESEARCH-FREEZE-v1.1-citations.md`](RESEARCH-FREEZE-v1.1-citations.md).

**Task:** Freeze supervision, raw pre-partition, split, leakage, and evaluation protocol  
**Status:** **FROZEN — HUMAN APPROVED**  
**Created:** 2026-08-20  
**Approved:** 2026-08-20  
**Protocol:** [`../research-protocol-v1.0.md`](../research-protocol-v1.0.md)
**Research claims:** None. No experiment has been run and no cited result is treated as a SeqLogAD result.

## Citation rule for this project

Every future research or implementation task that consults papers, official documentation, prior code, or benchmark conventions must add a task-specific file at:

```text
docs/references/<TASK-ID>-citations.md
```

Each note must record:

1. the complete source identity and verified link/DOI;
2. what part was consulted;
3. whether SeqLogAD copies, adapts, compares against, or rejects that idea;
4. what remains an independent project decision;
5. code/data license obligations when code or assets are reused;
6. `VERIFIED` or `UNVERIFIED` citation status;
7. no invented citation, DOI, finding, or novelty claim.
8. if no external source was used, explicitly state `NO EXTERNAL REFERENCES USED` instead of omitting the note.

## Sources consulted for PROTOCOL-001

### CITE-PROTOCOL-001-01 — Loghub dataset source

- **Citation:** Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, and Michael R. Lyu. *Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics*. IEEE International Symposium on Software Reliability Engineering (ISSRE), 2023.
- **Official source:** https://github.com/logpai/loghub
- **Status:** VERIFIED through the official LogPAI repository.
- **Consulted for:** HDFS/BGL dataset identity, label granularity, dataset scale, source terms, and the distinction between HDFS block sessions and BGL line-level alerts.
- **SeqLogAD use:** Dataset contract and dataset-specific sequence design.
- **Not copied:** No Loghub preprocessed template, event trace, model output, or experimental metric is treated as a SeqLogAD artifact.

### CITE-PROTOCOL-001-02 — Drain parser

- **Citation:** Pinjia He, Jieming Zhu, Zibin Zheng, and Michael R. Lyu. *Drain: An Online Log Parsing Approach with Fixed Depth Tree*. IEEE International Conference on Web Services (ICWS), 2017.
- **DOI:** https://doi.org/10.1109/ICWS.2017.13
- **Author-hosted paper:** https://pinjiahe.github.io/files/pdf/research/ICWS17.pdf
- **Status:** VERIFIED.
- **Consulted for:** Drain's online, state-updating parsing behavior and fixed-depth parse-tree design.
- **SeqLogAD adaptation:** Fit Drain3 only on the authorized training scope, persist its state, then transform later partitions without updating that state.
- **Independent project decision:** The exact freeze/restore contract, OOV event policy, deterministic event-ID hashing, and leakage tests are SeqLogAD protocol decisions rather than claims from the Drain paper.

### CITE-PROTOCOL-001-03 — Empirical evaluation of log anomaly detectors

- **Citation:** Zhuangbin Chen, Jinyang Liu, Wenwei Gu, Yuxin Su, Jieming Zhu, Yongqiang Yang, and Michael R. Lyu. *Experience Report: Deep Learning-based System Log Analysis for Anomaly Detection*. 2021.
- **Preprint:** https://arxiv.org/abs/2107.05908
- **Status:** VERIFIED through the paper preprint.
- **Consulted for:** The sensitivity of reported performance to log grouping, training-data anomaly contamination, sequence construction, and shuffled versus chronological handling—especially for BGL.
- **SeqLogAD adaptation:** Explicit normal-pool filtering, chronological pre-partitioning, dataset-specific grouping, and a contamination/leakage audit.
- **Not copied:** SeqLogAD does not copy the paper's exact train/test split, six-hour BGL grouping, model hyperparameters, or reported metrics.

### CITE-PROTOCOL-001-04 — LogSD

- **Citation:** Yongzheng Xie, Hongyu Zhang, and Muhammad Ali Babar. *LogSD: Detecting Anomalies from System Logs through Self-Supervised Learning and Frequency-Based Masking*. Proceedings of the ACM on Software Engineering, 1(FSE), Article 93, 2098–2120, 2024.
- **DOI:** https://doi.org/10.1145/3660800
- **Status:** VERIFIED through the ACM DOI record.
- **Consulted for:** Chronological BGL splitting, fixed-entry sequence construction, and the need to report behavior under different sequence/window sizes.
- **SeqLogAD adaptation:** A non-overlapping fixed-entry BGL parent-window design to prevent cross-window leakage and correlated evaluation units.
- **Independent project decision:** The 100-event primary parent window, five-way 60/10/10/10/10 split, internal causal contexts, and final parent-level aggregation are human-approved SeqLogAD protocol choices.

### CITE-PROTOCOL-001-05 — LogBERT

- **Citation:** Haixuan Guo, Shuhan Yuan, and Xintao Wu. *LogBERT: Log Anomaly Detection via BERT*. 2021.
- **Preprint:** https://arxiv.org/abs/2103.04475
- **Status:** VERIFIED through the paper preprint and official author repository.
- **Official implementation:** https://github.com/HelenGuohx/logbert
- **Consulted for:** Normal-pattern learning through self-supervised objectives and evaluation on HDFS/BGL-style log sequences.
- **SeqLogAD relationship:** Background for the normal-only/self-supervised framing and a future comparison family, not an implementation template for SeqLogAD-T.
- **Not copied:** No LogBERT architecture, source code, objective, split, checkpoint, or metric has been copied into SeqLogAD.

## Independent PROTOCOL-001 decisions

The following frozen rules are not attributed to a cited paper and must not be presented as prior-work findings:

- five-way `BASE_TRAIN/FUSION_TRAIN/VAL_EXPERT/VAL_FUSION/TEST` ownership;
- chronological ratio `60/10/10/10/10`;
- splitting `VAL_FUSION` into calibration and selection regions;
- TEST-label sealing and human-only unlock;
- HDFS boundary-spanning group/component purge;
- separate mutation pools for expert and fusion training;
- token/gap/transition localization coordinates;
- deterministic mutation IDs and event-ID hashing;
- KEEP/DEMOTE/REMOVE complementarity gate;
- proposed practical marginal-value thresholds;
- F0–F8 comparison ownership and final-test lock procedure.

These are **HUMAN-APPROVED PROJECT DESIGN DECISIONS**, not proven improvements, experimental findings, or novelty claims.

## Reuse and licensing status

- No external paper text, figure, table, code, model weight, or dataset byte was copied while drafting PROTOCOL-001.
- Ideas are summarized and adapted at the method-contract level.
- Any future source-code reuse requires a separate license check and exact file-level attribution before code enters the repository.
- Loghub raw data remains excluded from Git and subject to the source's research/academic usage terms.

## Review checklist

- [x] Every source mentioned in the PROTOCOL-001 proposal is recorded here.
- [x] Adapted ideas are distinguished from independent project decisions.
- [x] No experimental result is claimed.
- [x] No novelty claim is made.
- [x] No external code is copied.
- [x] Human researcher approves the protocol and citation mapping.
