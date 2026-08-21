# LIT-001 — Citation and Method-Provenance Note

- **Task:** Targeted prior-art and dataset-suitability review
- **Search date:** 2026-08-21
- **Primary window:** 2024-08 through 2026-08
- **SeqLogAD empirical status:** `NOT_RUN`
- **Novelty claim:** none

This note records the primary/official sources consulted for `LIT-001`, what was taken from each source, and the boundary on reuse. No external table, implementation, model weight, dataset byte, or metric is represented as a SeqLogAD artifact or result.

## A. Dataset suitability, evaluation, and model lineage

### LIT-CITE-001 — HDFS/BGL sequence-dataset critique

- **Citation:** Max Landauer, Florian Skopik, Markus Wurzenberger. *A Critical Review of Common Log Data Sets Used for Evaluation of Sequence-Based Anomaly Detection Techniques*. Proceedings of the ACM on Software Engineering, FSE, 2024.
- **DOI:** https://doi.org/10.1145/3660768
- **Accessible author copy:** https://www.skopik.at/ait/2024_fse.pdf
- **Status:** `PEER_REVIEWED / VERIFIED`; one month before the preferred window, retained as the central methodological foundation.
- **Used for:** HDFS/BGL variant mapping; unseen-event, length, count-vector and n-gram controls; ceiling and chronology risk.
- **Boundary:** Reported F1 values belong to the paper's variants and splits, not SeqLogAD.

### LIT-CITE-002 — Broad ML comparison

- **Citation:** Shan Ali, Chaima Boufaied, Domenico Bianculli, Paula Branco, Lionel Briand. *A Comprehensive Study of Machine Learning Techniques for Log-Based Anomaly Detection*. Empirical Software Engineering 30, 129, 2025.
- **DOI:** https://doi.org/10.1007/s10664-025-10669-3
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Traditional-versus-deep comparison, hyperparameter sensitivity, dataset/supervision taxonomy, runtime considerations.
- **Boundary:** The paper covers regimes broader than SeqLogAD's normal-only protocol.

### LIT-CITE-003 — Unified comparative evaluation

- **Citation:** Ondřej Sedláček, Martin Žádník, Václav Bartoš. *Anomaly Detection in Log Data: A Comparative Study*. 21st IEEE/IFIP International Conference on Network and Service Management, 2025.
- **Official PDF:** https://dl.ifip.org/db/conf/cnsm/cnsm2025/1571164872.pdf
- **Status:** `PEER_REVIEWED / VERIFIED`; no DOI was established from the official copy during this task.
- **Used for:** HDFS variant/preprocessing sensitivity, BGL grouping/window sensitivity, shuffled-versus-temporally-continuous evaluation.
- **Boundary:** Its cross-validation and tuning are not the SeqLogAD protocol.

### LIT-CITE-004 — Parser impact

- **Citation:** Zanis Ali Khan, Donghwan Shin, Domenico Bianculli, Lionel C. Briand. *Impact of Log Parsing on Deep Learning-Based Anomaly Detection*. Empirical Software Engineering 29(6), article 139, 2024.
- **DOI:** https://doi.org/10.1007/s10664-024-10533-w
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Distinguishability versus parser-accuracy risk and the need to freeze parser identity.
- **Boundary:** Does not justify fitting the parser on evaluation partitions.

### LIT-CITE-005 — Self-supervised sequence detection

- **Citation:** Yongzheng Xie, Hongyu Zhang, Muhammad Ali Babar. *LogSD: Detecting Anomalies from System Logs through Self-Supervised Learning and Frequency-Based Masking*. Proceedings of the ACM on Software Engineering 1(FSE), 2024.
- **DOI:** https://doi.org/10.1145/3660800
- **Status:** `PEER_REVIEWED / VERIFIED`; foundational 2024 source.
- **Used for:** Current self-supervised sequence-model family, HDFS session/BGL fixed-window comparison context.
- **Boundary:** No reported result is equivalent to SeqLogAD's frozen split or primary endpoint.

### LIT-CITE-006 — Unsupervised AutoML

- **Citation:** Shenglin Zhang et al. *End-to-End AutoML for Unsupervised Log Anomaly Detection*. ASE 2024.
- **DOI:** https://doi.org/10.1145/3691620.3695535
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Representation/model-selection sensitivity and evidence that no single detector family is uniformly sufficient.
- **Boundary:** AutoML search and paper-specific F1 are not a fair substitute for SeqLogAD's equal-budget gate.

### LIT-CITE-007 — Parser-free self-supervised sequence modeling

- **Citation:** Simon Dietz, Kai Klede, An Nguyen, Bjoern M. Eskofier. *ContraLog: Log File Anomaly Detection with Contrastive Learning and Masked Language Modeling*. 2026.
- **Preprint:** https://arxiv.org/abs/2602.03678
- **Status:** `PREPRINT / VERIFIED AS PREPRINT`.
- **Used for:** Recent evidence that message representations may carry anomaly signal without sequence context on BGL/Thunderbird; count-vector Isolation Forest comparison; HDFS message-position/add/delete perturbations.
- **Boundary:** The position-change analysis uses anomaly scores on modified normal sequences rather than SeqLogAD's paired real-label PR-AUC endpoint; baseline fitting/tuning and TEST usage also differ. Peer-reviewed status was not established.

### LIT-CITE-008 — HDFS count-vector foundation

- **Citation:** Wei Xu, Ling Huang, Armando Fox, David Patterson, Michael I. Jordan. *Detecting Large-Scale System Problems by Mining Console Logs*. SOSP 2009.
- **DOI:** https://doi.org/10.1145/1629575.1629587
- **Author-hosted extended study:** https://people.eecs.berkeley.edu/~jordan/papers/xu-etal-icml10.pdf
- **Status:** `PEER_REVIEWED/FOUNDATIONAL / VERIFIED`.
- **Used for:** HDFS execution-level count-vector lineage and KT-2 motivation.
- **Boundary:** Original HDFS artifacts and current Loghub bytes are not assumed identical.

### LIT-CITE-009 — DeepLog

- **Citation:** Min Du, Feifei Li, Guineng Zheng, Vivek Srikumar. *DeepLog: Anomaly Detection and Diagnosis from System Logs through Deep Learning*. ACM CCS 2017.
- **DOI:** https://doi.org/10.1145/3133956.3134015
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Normal-only next-event/LSTM baseline lineage.
- **Boundary:** A known method family, not a SeqLogAD contribution or immediate implementation requirement.

### LIT-CITE-010 — Sequential plus quantitative detection

- **Citation:** Weibin Meng et al. *LogAnomaly: Unsupervised Detection of Sequential and Quantitative Anomalies in Unstructured Logs*. IJCAI 2019.
- **DOI:** https://doi.org/10.24963/ijcai.2019/658
- **Official proceedings:** https://www.ijcai.org/proceedings/2019/658
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Prior-art overlap between sequential and quantitative signals.
- **Boundary:** Mixed signals cannot demonstrate order contribution without ablation/controls.

### LIT-CITE-011 — Evaluation fragility

- **Citation:** Van-Hoang Le, Hongyu Zhang. *Log-Based Anomaly Detection with Deep Learning: How Far Are We?* ICSE 2022.
- **Preprint:** https://arxiv.org/abs/2202.04301
- **Status:** `PEER_REVIEWED WORK / ACCESS COPY VERIFIED`.
- **Used for:** Grouping, training composition, parsing/noise, and evaluation sensitivity.
- **Boundary:** Older supporting source; not used for a current novelty classification.

### LIT-CITE-012 — Chronology and grouping

- **Citation:** Zhuangbin Chen et al. *Experience Report: Deep Learning-Based System Log Analysis for Anomaly Detection*. 2021.
- **Preprint:** https://arxiv.org/abs/2107.05908
- **Status:** `FOUNDATIONAL EVALUATION SOURCE / VERIFIED`.
- **Used for:** Chronological handling, grouping, contamination, and model-evaluation sensitivity.
- **Boundary:** Supports controls, not a numerical practical-effect margin.

## B. Fusion, ensembles, localization, and synthetic data

### LIT-CITE-013 — Multi-pattern/multi-model fusion

- **Citation:** Xinjie Wei, Chang-Ai Sun, Xiaoyi Zhang, Dave Towey. *MulAD: A Log-Based Anomaly Detection Approach for Distributed Systems Using Multi-Pattern and Multi-Model Fusion*. Science of Computer Programming 251, 103433; online metadata 2025, volume record 2026.
- **DOI:** https://doi.org/10.1016/j.scico.2025.103433
- **Publisher record:** https://www.sciencedirect.com/science/article/pii/S0167642325001716
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Direct overlap with heterogeneous patterns/models and learned integration.
- **Boundary:** Enough to reject generic fusion novelty; not enough to infer SeqLogAD fusion performance.

### LIT-CITE-014 — Log-specific MoE

- **Citation:** Jiaxing Qi et al. *LogMoE: Lightweight Expert Mixture for Cross-System Log Anomaly Detection*. ASE 2025.
- **DOI:** https://doi.org/10.1109/ASE63991.2025.00035
- **Official venue page:** https://conf.researchr.org/details/ase-2025/ase-2025-papers/13/LogMoE-Lightweight-Expert-Mixture-for-Cross-System-Log-Anomaly-Detection
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Expert routing/gating prior-art overlap.
- **Boundary:** Cross-system objective and supervision differ; no metric transfer.

### LIT-CITE-015 — Message-level MoE

- **Citation:** Huanchi Wang et al. *FAME: Failure-Aware Mixture-of-Experts for Message-Level Log Anomaly Detection*. 2026.
- **Preprint:** https://arxiv.org/abs/2605.22779
- **Status:** `PREPRINT`; manuscript states acceptance at ISSRE 2026, but a final DOI/proceedings record was not verified.
- **Used for:** Active message-level MoE/localization overlap and unseen-EventID behavior on BGL.
- **Boundary:** Label-efficient message-level supervision differs from SeqLogAD's normal-only sequence question.

### LIT-CITE-016 — General heterogeneous anomaly ensembles

- **Citation:** Félix Iglesias, Tanja Zseby, Conrado Martínez, Arthur Zimek. *On Heterogeneous Ensembles for Anomaly Detection: Empirical Insights and Guidelines for the Design*. Expert Systems with Applications 332(A), 133468, 2026.
- **DOI:** https://doi.org/10.1016/j.eswa.2026.133468
- **Institutional record:** https://repositum.tuwien.at/handle/20.500.12708/229331
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Normalization, aggregation, ensemble size, diversity, and metric dependence.
- **Boundary:** Tabular anomaly data, not log sequences; methodological overlap only.

### LIT-CITE-017 — Earlier log localization

- **Citation:** Xiaoyun Li, Pengfei Chen, Linxiao Jing, Zilong He, Guangba Yu. *SwissLog: Robust Anomaly Detection and Localization for Interleaved Unstructured Logs*. IEEE Transactions on Dependable and Secure Computing; online 2022, volume 20(4), 2023.
- **DOI:** https://doi.org/10.1109/TDSC.2022.3162857
- **Official implementation:** https://github.com/IntelligentDDS/SwissLog
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Demonstrating that log anomaly localization predates SeqLogAD.
- **Boundary:** Does not establish equivalence with token/gap/transition coordinates.

### LIT-CITE-018 — Counterfactual localization

- **Citation:** Yutszyuk Wong, Wentai Wu, Yuen-Ying Yeung, Weiwei Lin. *Seeing the Needle in the Haystack: Towards Weakly-Supervised Log Instance Anomaly Localization via Counterfactual Perturbation*. 2026.
- **Preprint:** https://arxiv.org/abs/2605.10988
- **Status:** `PREPRINT / VERIFIED AS PREPRINT`.
- **Used for:** Bag-label supervision, Loc@3/Success Rate, and counterfactual perturbation consistency.
- **Boundary:** No peer-reviewed status or exact SeqLogAD coordinate overlap established.

### LIT-CITE-019 — Explanation randomization sanity

- **Citation:** Julius Adebayo et al. *Sanity Checks for Saliency Maps*. NeurIPS 2018.
- **Official proceedings:** https://proceedings.neurips.cc/paper/2018/hash/294a8ed24b1ad22ec2e7efea049b8737-Abstract.html
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Model-parameter and data randomization as explanation sanity checks.
- **Boundary:** General explanation methodology, not log-localization evidence.

### LIT-CITE-020 — Code-guided sequence synthesis

- **Citation:** Yintong Huo et al. *AutoLog: A Log Sequence Synthesis Framework for Anomaly Detection*. ASE 2023.
- **DOI:** https://doi.org/10.1109/ASE56229.2023.00133
- **Preprint:** https://arxiv.org/abs/2308.09324
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Static-analysis-derived log execution paths and synthetic sequence prior art.
- **Boundary:** Different from deterministic mutation controls; neither is claimed novel.

### LIT-CITE-021 — Code-guided augmentation

- **Citation:** Xinyu Li et al. *AnomalyGen: Enhancing Log-Based Anomaly Detection with Code-Guided Data Augmentation*. 2026.
- **Preprint:** https://arxiv.org/abs/2604.11107
- **Status:** `PREPRINT / VERIFIED AS PREPRINT`; placeholder DOI in manuscript, therefore no final DOI is asserted.
- **Used for:** Benchmark template-coverage risk and insertion/deletion/modification augmentation evidence.
- **Boundary:** Synthetic training data and reported F1 are not adopted; real-anomaly and synthetic-localization evaluation stay separate.

### LIT-CITE-022 — State-machine synthetic logs

- **Citation:** Aja Khanal, Apurva Narayan. *State Machine Guided Multi-Relational Synthetic Data from Logs for Anomaly Detection*. KDD 2026.
- **DOI:** https://doi.org/10.1145/3770855.3818134
- **Official project:** https://github.com/Idsl-group/LogSynthFSM-KDD-2026
- **Status:** `PEER_REVIEWED RECORD / VERIFIED`.
- **Used for:** Structured/state-machine synthetic generation overlap.
- **Boundary:** No code/data copied and no metric transferred.

### LIT-CITE-023 — Event reduction and event dominance

- **Citation:** Lingzhe Zhang, Tong Jia, Kangjin Wang, Mengxi Jia, Yong Yang, Ying Li. *Reducing Events to Augment Log-Based Anomaly Detection Models: An Empirical Study*. ESEM 2024.
- **DOI:** https://doi.org/10.1145/3674805.3695403
- **Preprint:** https://arxiv.org/abs/2409.04834
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Event families can contribute unevenly; a small subset may dominate detection.
- **Boundary:** SeqLogAD does not filter scientific input events during LIT-001.

## C. Dataset provenance and statistical method

### LIT-CITE-024 — Loghub and exact archive source

- **Citation:** Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, Michael R. Lyu. *Loghub: A Large Collection of System Log Datasets for AI-Driven Log Analytics*. ISSRE 2023.
- **DOI:** https://doi.org/10.1109/ISSRE59848.2023.00071
- **Canonical archive record:** https://doi.org/10.5281/zenodo.8196385
- **Official repository:** https://github.com/logpai/loghub
- **Status:** `PEER_REVIEWED + CANONICAL DATA RECORD / VERIFIED`.
- **Used for:** HDFS/BGL source identity, variant warning, and usage/citation terms.
- **Boundary:** Availability is not permission to commit or redistribute raw files.

### LIT-CITE-025 — BGL origin

- **Citation:** Adam Oliner, Jon Stearley. *What Supercomputers Say: A Study of Five System Logs*. DSN 2007.
- **DOI:** https://doi.org/10.1109/DSN.2007.103
- **Status:** `PEER_REVIEWED/FOUNDATIONAL / VERIFIED`.
- **Used for:** BGL operational origin and line-level context.
- **Boundary:** Does not define SeqLogAD's 100-event window or result.

### LIT-CITE-026 — PR evaluation under imbalance

- **Citation:** Takaya Saito, Marc Rehmsmeier. *The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets*. PLOS ONE 10(3), 2015.
- **DOI:** https://doi.org/10.1371/journal.pone.0118432
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** PR-focused evaluation under class imbalance.
- **Boundary:** Does not prescribe a practical ΔPR-AUC threshold.

### LIT-CITE-027 — AUCPR uncertainty

- **Citation:** Kendrick Boyd, Kevin H. Eng, C. David Page. *Area Under the Precision-Recall Curve: Point Estimates and Confidence Intervals*. ECML PKDD 2013, LNCS 8190, pp. 451–466.
- **DOI:** https://doi.org/10.1007/978-3-642-40994-3_29
- **Institutional record:** https://scholars.duke.edu/publication/1393181
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Need to report AUCPR uncertainty, not only point estimates.
- **Boundary:** SeqLogAD still requires dependence-aware session/window resampling.

### LIT-CITE-028 — Equivalence and smallest effect of interest

- **Citation:** Daniël Lakens, Anne M. Scheel, Peder M. Isager. *Equivalence Testing for Psychological Research: A Tutorial*. Advances in Methods and Practices in Psychological Science 1(2), 2018.
- **DOI:** https://doi.org/10.1177/2515245918770963
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** Pre-specifying a smallest effect size of interest and distinguishing equivalence from an inconclusive null result.
- **Boundary:** Psychology examples and numerical bounds are not transferred to log anomaly detection.

### LIT-CITE-029 — Isolation Forest

- **Citation:** Fei Tony Liu, Kai Ming Ting, Zhi-Hua Zhou. *Isolation Forest*. Eighth IEEE International Conference on Data Mining, pp. 413–422, 2008.
- **DOI:** https://doi.org/10.1109/ICDM.2008.17
- **Status:** `PEER_REVIEWED/FOUNDATIONAL / VERIFIED`.
- **Used for:** Order-insensitive unsupervised anomaly baseline lineage and computational rationale.
- **Boundary:** The source evaluates general anomaly datasets, not the exact HDFS/BGL protocol; no SeqLogAD performance is inferred.

### LIT-CITE-030 — Block bootstrap for dependent observations

- **Citation:** Hans R. Künsch. *The Jackknife and the Bootstrap for General Stationary Observations*. The Annals of Statistics 17(3), pp. 1217–1241, 1989.
- **DOI:** https://doi.org/10.1214/aos/1176347265
- **Status:** `PEER_REVIEWED/FOUNDATIONAL / VERIFIED`.
- **Used for:** Methodological basis for resampling blocks rather than pretending temporally dependent observations are IID.
- **Boundary:** The paper does not specify SeqLogAD's HDFS/BGL resampling unit; that design remains an explicit `EFFECT-001` decision.

## D. Decisions derived from the combined evidence

These are SeqLogAD design decisions, not findings copied from one paper:

- retain exact HDFS/BGL bytes and test their suitability rather than declare them suitable/unsuitable from literature;
- require unseen-event, length, count/count-vector, and Markov/N-gram before complex models;
- retain within-sample order destruction as a pre-registered negative control;
- keep Transformer, localization, and fusion conditional;
- make no component-level novelty claim;
- freeze a dataset-specific practical margin and paired uncertainty method in `EFFECT-001` before any run;
- accept negative/equivalent/inconclusive results;
- keep RAG/Agent outside the scientific core.

## E. Citation safety checklist

- [x] Every retained work has a DOI, official URL, or explicitly labeled preprint URL.
- [x] Preprints are labeled as preprints; manuscript acceptance claims are not promoted to verified final publication.
- [x] External results are separated from SeqLogAD results.
- [x] Dataset variants and protocol mismatches are stated.
- [x] No source result was used to invent a practical-effect number.
- [x] No novelty, SOTA, first-method, sequence-superiority, fusion-superiority, or localization-faithfulness claim is made.
- [x] No scientific implementation or experiment was performed for LIT-001.
