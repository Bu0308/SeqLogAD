# Research Freeze v1.1 — Citation and Method-Provenance Note

- **Task:** Scientific redirect, scope reduction, negative-control registration, and repository consistency repair
- **Date:** 2026-08-21
- **Protocol:** [`../research-protocol-v1.1.md`](../research-protocol-v1.1.md)
- **Empirical status:** `NOT_RUN`
- **Novelty status:** `UNVERIFIED`

No parser, split, baseline, model, localization, fusion, or TEST experiment was executed for this task. External findings below motivate risks and controls; they are not SeqLogAD results.

## Provenance rule

For every source, SeqLogAD records what was consulted, what was adopted as a control or design constraint, and what remains an untested project hypothesis. No external code, figure, table, model weight, or dataset byte was copied in this task.

## User-supplied audit input

### RF11-AUDIT-01 — `SEQLOGAD_EVAL.md`

- **Type:** User-supplied evaluation report; not treated as peer-reviewed evidence.
- **Use:** Finding inventory for dataset-ceiling risk, sequence-value risk, excessive scope, missing negative controls, TEST sealing, and repository hygiene.
- **Validation rule:** Each material criticism was cross-checked against repository state and, where scientific, against primary literature below.
- **Disposition:** The audit supports hypotheses and tests to run; it does not prove that either HDFS or BGL is unsuitable.

## Verified primary/official sources

### RF11-CITE-01 — Dataset suitability for sequence-based evaluation

- **Citation:** Max Landauer, Florian Skopik, and Markus Wurzenberger. *A Critical Review of Common Log Data Sets Used for Evaluation of Sequence-Based Anomaly Detection Techniques*. Proceedings of the ACM on Software Engineering, FSE, 2024.
- **DOI:** https://doi.org/10.1145/3660768
- **Author-hosted paper:** https://www.skopik.at/ait/2024_fse.pdf
- **Status:** `VERIFIED`.
- **Consulted for:** Evidence that common benchmark anomalies can be detectable through non-sequential properties and that dataset variants/preprocessing matter.
- **SeqLogAD response:** Register KT-1, KT-2, and KT-3 before a complex sequence model.
- **Boundary:** Its reported results are not copied as SeqLogAD results because the exact archive bytes, preprocessing, chronology, grouping, and split contract may differ.

### RF11-CITE-02 — HDFS count-vector representation

- **Citation:** Wei Xu, Ling Huang, Armando Fox, David Patterson, and Michael I. Jordan. *Detecting Large-Scale System Problems by Mining Console Logs*. SOSP, 2009; extended experimental treatment distributed by the authors.
- **Author-hosted paper:** https://people.eecs.berkeley.edu/~jordan/papers/xu-etal-icml10.pdf
- **Status:** `VERIFIED`.
- **Consulted for:** HDFS execution-path representations based on message-count vectors and the relationship between those vectors and manually investigated problem cases.
- **SeqLogAD response:** KT-2 explicitly measures count-vector collision, label dependence, and out-of-sample order-insensitive prediction.
- **Boundary:** The paper does not establish the outcome of KT-2 under SeqLogAD's exact Loghub bytes and chronological protocol.

### RF11-CITE-03 — Evaluation sensitivity in log anomaly detection

- **Citation:** Van-Hoang Le and Hongyu Zhang. *Log-based Anomaly Detection with Deep Learning: How Far Are We?* 2022.
- **Preprint:** https://arxiv.org/abs/2202.04301
- **Status:** `VERIFIED`.
- **Consulted for:** Sensitivity to training selection, grouping, class distribution, and data noise.
- **SeqLogAD response:** Preserve leakage controls, strong baselines, per-dataset reporting, and negative-result acceptance.

### RF11-CITE-04 — Grouping and chronology sensitivity

- **Citation:** Zhuangbin Chen et al. *Experience Report: Deep Learning-based System Log Analysis for Anomaly Detection*. 2021.
- **Preprint:** https://arxiv.org/abs/2107.05908
- **Status:** `VERIFIED`.
- **Consulted for:** Effects of sequence grouping, training contamination, and shuffled versus chronological handling.
- **SeqLogAD response:** Split raw units first, isolate labels, fit parser only on normal `BASE_TRAIN`, and keep BGL chronology.

### RF11-CITE-05 — Self-supervised sequence detector comparison context

- **Citation:** Yongzheng Xie, Hongyu Zhang, and Muhammad Ali Babar. *LogSD: Detecting Anomalies from System Logs through Self-Supervised Learning and Frequency-Based Masking*. Proceedings of the ACM on Software Engineering, FSE, 2024.
- **DOI:** https://doi.org/10.1145/3660800
- **Status:** `VERIFIED`.
- **Consulted for:** Self-supervised log anomaly detection, HDFS session construction, and fixed-entry BGL windows.
- **SeqLogAD response:** Markov/N-gram remains the minimal sequential comparator; a Transformer is conditional, not presumed necessary.

### RF11-CITE-06 — Multi-pattern and multi-model fusion overlap

- **Citation:** Xinjie Wei, Chang-Ai Sun, Xiaoyi Zhang, and Dave Towey. *MulAD: A log-based anomaly detection approach for distributed systems using multi-pattern and multi-model fusion*. Science of Computer Programming, 2025.
- **DOI:** https://doi.org/10.1016/j.scico.2025.103433
- **Status:** `VERIFIED` through the publisher record.
- **Consulted for:** Direct prior-art overlap with multi-pattern representations and multi-model integration over HDFS/BGL/Thunderbird-style evaluation.
- **SeqLogAD response:** Fusion is no longer a primary contribution and cannot open before measured complementarity.

### RF11-CITE-07 — Mixture-of-experts overlap

- **Citation:** Jiaxing Qi et al. *LogMoE: Lightweight Expert Mixture for Cross-System Log Anomaly Detection*. ASE, 2025.
- **DOI:** https://doi.org/10.1109/ASE63991.2025.00035
- **Official venue page:** https://conf.researchr.org/details/ase-2025/ase-2025-papers/13/LogMoE-Lightweight-Expert-Mixture-for-Cross-System-Log-Anomaly-Detection
- **Status:** `VERIFIED`.
- **Consulted for:** Existing MoE/gating work in log anomaly detection and the need to avoid an unsupported fusion-novelty claim.
- **SeqLogAD response:** F2–F8 are removed from the v1.1 core; any later fusion requires a new prior-art and empirical gate.

### RF11-CITE-08 — Localization and counterfactual faithfulness overlap

- **Citation:** Yutszyuk Wong, Wentai Wu, Yuen-Ying Yeung, and Weiwei Lin. *Seeing the Needle in the Haystack: Towards Weakly-Supervised Log Instance Anomaly Localization via Counterfactual Perturbation*. 2026.
- **Preprint:** https://arxiv.org/abs/2605.10988
- **Status:** `VERIFIED AS PREPRINT`; peer-reviewed publication status was not established here.
- **Consulted for:** Weakly supervised instance localization and counterfactual perturbation consistency.
- **SeqLogAD response:** Localization is conditional and must include randomization and counterfactual sanity controls.
- **Boundary:** SeqLogAD does not claim first localization or first counterfactual-faithfulness method.

### RF11-CITE-09 — Hierarchical/modular execution structure

- **Citation:** Lei Ma et al. *KRONE: Hierarchical and Modular Log Anomaly Detection*. 2026.
- **Preprint:** https://arxiv.org/abs/2602.07303
- **Status:** `VERIFIED AS PREPRINT`.
- **Consulted for:** Prior work on recovering/using hierarchical execution structure and modular routing.
- **SeqLogAD response:** A four-expert architecture cannot be justified by architectural novelty alone; execution boundaries and dataset suitability require evidence.

### RF11-CITE-10 — Structured synthetic log generation overlap

- **Citation:** Aja Khanal and Apurva Narayan. *State Machine Guided Multi-Relational Synthetic Data from Logs for Anomaly Detection*. KDD, 2026.
- **DOI:** https://doi.org/10.1145/3770855.3818134
- **Official implementation:** https://github.com/Idsl-group/LogSynthFSM-KDD-2026
- **Status:** `VERIFIED` through the official project record and DOI metadata.
- **Consulted for:** Prior-art risk around structured/state-machine-guided synthetic log generation.
- **SeqLogAD response:** Synthetic mutation is a controlled evaluation/training mechanism, not a novelty claim; raw logs remain immutable.

## Independent v1.1 decisions

The following are pre-registered SeqLogAD design decisions, not findings attributed to a source:

- retain exact verified HDFS/BGL bytes while testing their suitability;
- keep the chronological `60/10/10/10/10` partition ownership contract;
- reserve unused fusion partitions rather than repurpose them after seeing results;
- use PR-AUC as the primary detection metric and seeds `42`, `43`, `44` for stochastic core methods;
- run KT-1 through KT-3 before Transformer/localization/fusion;
- preserve multiset/count/length/label during sequence destruction;
- make practical-effect thresholds `TO_BE_FROZEN_BEFORE_RUN` rather than inventing values;
- accept kill criteria and negative findings as valid outcomes;
- keep RAG/Agent and delivery layers outside the <3-month scientific core.

## Citation safety checklist

- [x] No external result is labeled as a SeqLogAD result.
- [x] No novelty, SOTA, sequence superiority, dataset-unsuitability, or fusion-superiority claim is made.
- [x] Preprints are labeled as preprints.
- [x] No external code/data/model artifact was copied.
- [x] At the v1.1 freeze, LIT-001 remained `IN_PROGRESS`. It was later completed as a targeted review in [`LIT-001-citations.md`](LIT-001-citations.md) and is not represented as an exhaustive systematic review.
