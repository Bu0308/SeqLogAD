# LIT-001 — Targeted Prior-Art and Dataset-Suitability Review

| Field | Value |
|---|---|
| Task | `LIT-001` |
| Status | **DONE — TARGETED REVIEW COMPLETE** |
| Search date | 2026-08-21 |
| Primary window | 2024-08 through 2026-08 |
| Older work | Included only for dataset provenance, baseline lineage, localization sanity, and statistical method |
| Search log | [`LIT-001-search-log.md`](LIT-001-search-log.md) |
| Citation/provenance note | [`../references/LIT-001-citations.md`](../references/LIT-001-citations.md) |
| SeqLogAD model results | **NONE — all scientific experiments remain `NOT_RUN`** |

This is a reproducible **targeted** review serving Protocol v1.1, not a claim of an exhaustive systematic review. Completion means the current baseline, dataset-risk, and contribution decisions have enough verified prior-art support to proceed to `EFFECT-001`. It does not establish algorithmic novelty.

## 1. Executive verdict

The literature **supports** Protocol v1.1's risk-first design and **challenges** any assumption that sequence models must outperform simple order-insensitive controls on HDFS/BGL.

- HDFS and BGL remain usable, but only **conditionally**: published results show strong ceiling, variant, preprocessing, grouping, and chronology risks.
- Unseen-event, length, total-count/count-vector, and a minimal Markov/N-gram comparator are mandatory. Isolation Forest remains a useful stronger order-insensitive comparator, but no equivalent literature result under the exact SeqLogAD protocol was found.
- A within-sample sequence-destruction control that preserves multiset/count/length is scientifically justified. ContraLog provides direct position-change precedent, but the search did **not** establish an equivalent standardized paired real-label/PR-AUC protocol; KT-3 is a control, not a novelty claim.
- Transformer, heterogeneous fusion/MoE, localization, faithfulness testing, and synthetic mutation all have substantial prior art. None is a current novelty claim or an automatic implementation requirement.
- No source provides a defensible universal numerical `minimum_practical_effect` for PR-AUC. `EFFECT-001` must define dataset-specific practical margins before runs, with paired uncertainty and an inconclusive region.

## 2. Evidence boundary

`EXTERNAL RESULT` means a result reported by a cited source under that source's dataset variant and protocol. `SEQLOGAD RESULT` means a result produced from the exact accepted bytes and frozen SeqLogAD protocol. This review contains **no SeqLogAD result**.

External F1/PR-AUC values must not be copied into SeqLogAD result tables. Differences in Loghub/Xu/LogDeep variants, parser output, sequence grouping, split order, training labels, threshold selection, and evaluation units prevent direct transfer.

## 3. Core prior-art matrix

| ID | Paper, year, venue, official source | Dataset / variant | Supervision regime | Representation and order sensitivity | Evaluation protocol / primary metrics | `EXTERNAL RESULT` relevant to SeqLogAD | Limitations and exact SeqLogAD implication |
|---|---|---|---|---|---|---|---|
| S01 | Landauer, Skopik, Wurzenberger, *A Critical Review of Common Log Data Sets Used for Evaluation of Sequence-Based Anomaly Detection Techniques*, 2024, PACMSE/FSE, [DOI](https://doi.org/10.1145/3660768) | Multiple HDFS variants; BGL CFDR/Loghub-style constructions; Thunderbird | Mostly normal-pattern learning/simple rules; labels used for evaluation | Unseen event, length, event-count vector (ECVC), n-gram/edit/timing, DeepLog, LogAnomaly; mixed orderless/sequential | Random and chronological settings; F1; repeated random runs where applicable | Variant-specific HDFS ECVC reached F1 96.0/96.5 in random evaluation, while BGL constructions were often highly predictable from new event types; chronology and grouping materially changed results | Strongest direct evidence of ceiling risk. It does not prove the outcome for SeqLogAD's exact bytes or 60/10/10/10/10 split. **KEEP KT-1/KT-2/KT-3.** |
| S02 | Ali, Boufaied, Bianculli, Branco, Briand, *A Comprehensive Study of Machine Learning Techniques for Log-Based Anomaly Detection*, 2025, Empirical Software Engineering, [DOI](https://doi.org/10.1007/s10664-025-10669-3) | HDFS, BGL, and other public benchmarks; source variants differ by experiment | Supervised, semi-supervised, and unsupervised families | Traditional count/feature and deep sequence/semantic methods | Common preprocessing framework; accuracy/F1, prediction time, hyperparameter sensitivity | Traditional and deep methods can be similar on benchmark detection and traditional methods can be less sensitive to tuning; the paper reiterates simple-signal risks in HDFS/BGL | Broader regimes are not equal to SeqLogAD normal-only training. **KEEP equal-budget classical controls and latency.** |
| S03 | Sedláček, Žádník, Bartoš, *Anomaly Detection in Log Data: A Comparative Study*, 2025, IEEE/IFIP CNSM, [official PDF](https://dl.ifip.org/db/conf/cnsm/cnsm2025/1571164872.pdf) | HDFS Xu and Loghub variants, BGL, Thunderbird | Method-dependent; includes classical and neural detectors | Event-count vectors, template sequences, embeddings; orderless and sequential | Unified Drain pipeline; shuffled and temporally continuous evaluation; Precision/Recall/F1 | Minor preprocessing and variant choices can shift F1 by more than 10 percentage points; Transformer-based methods degrade under sequential evaluation while classical methods are more robust | Uses shuffled cross-validation/tuning choices unlike SeqLogAD. **KEEP chronology, parser provenance, exact variant labeling, and no cross-paper score comparison.** |
| S04 | Khan, Shin, Bianculli, Briand, *Impact of Log Parsing on Deep Learning-Based Anomaly Detection*, 2024, Empirical Software Engineering, [DOI](https://doi.org/10.1007/s10664-024-10533-w) | Three public log datasets; 13 parsers and seven detectors | Method-dependent | Parsed templates feeding traditional/deep detectors | Parser accuracy/distinguishability versus detector performance; anomaly-detection metrics including F1 | Parser accuracy itself was not strongly correlated with anomaly-detection accuracy; output distinguishability was more relevant | Does not authorize fitting Drain3 on all data. **KEEP BASE-only parser fit/freeze and record both parser identity and downstream distinguishability risks.** |
| S05 | Xie, Zhang, Babar, *LogSD: Detecting Anomalies from System Logs through Self-Supervised Learning and Frequency-Based Masking*, 2024, PACMSE/FSE, [DOI](https://doi.org/10.1145/3660800) | HDFS sessions; BGL fixed-entry windows; Spirit | Normal-data/semi-supervised convention with a self-supervised objective | Sequence-sensitive masked-event representation with frequency-aware masking | Paper-specific random/chronological construction; Precision/Recall/F1 | Demonstrates active self-supervised sequence-detector prior art and that sequence construction differs by dataset | Not equal to SeqLogAD split or primary PR-AUC endpoint. **Transformer/self-supervision are known families; no novelty claim.** |
| S06 | Zhang et al., *End-to-End AutoML for Unsupervised Log Anomaly Detection (LogCraft)*, 2024, ASE, [DOI](https://doi.org/10.1145/3691620.3695535) | HDFS, BGL, Thunderbird and two additional public datasets | Unsupervised model-selection framework | Count, sequence, semantic and dataset-level meta-features; mixed order sensitivity | Paper-specific random/time windows; F1 and deployment cost | No single manually selected representation/model is uniformly best; feature and preprocessing selection materially affect outcomes | AutoML search budget is not equal to SeqLogAD. **Do not use result-driven architecture search; preserve equal-budget comparisons.** |
| S07 | Dietz et al., *ContraLog: Log File Anomaly Detection with Contrastive Learning and Masked Language Modeling*, 2026, arXiv preprint, [arXiv:2602.03678](https://arxiv.org/abs/2602.03678) | HDFS sessions; BGL/Thunderbird 60-second windows; Loghub variants described by manuscript | Normal-only self-supervised | Parser-free message embeddings plus sequence encoder; point/context ablations and position/add/delete perturbations | Chronological non-overlapping windows; Precision/Recall/F1, ROC-AUC appendix, anomaly-score perturbation analysis | Message-only scores are strong on BGL/Thunderbird; moving HDFS messages generally changes score less than deletion/addition, although some one-position moves have large effects | Preprint; baseline/parser/tuning details differ and some appendix analyses inspect TEST. It is direct partial precedent for KT-3, not an equivalent leakage-safe paired PR-AUC result. |
| S08 | Xu et al., *Detecting Large-Scale System Problems by Mining Console Logs*, 2009, SOSP/author extended study, [DOI](https://doi.org/10.1145/1629575.1629587) | Original HDFS execution traces, not automatically identical to current Loghub archive | Problem cases investigated with labeled execution behavior | Per-execution message-count vectors; order-insensitive | PCA/decision-tree style detection; precision/recall and operational investigation | HDFS's foundational analysis explicitly used count-vector representations | Historical dataset/label lineage, not an exact current benchmark result. **KT-2 must quantify count-label dependence on accepted bytes.** |
| S09 | Du et al., *DeepLog: Anomaly Detection and Diagnosis from System Logs through Deep Learning*, 2017, CCS, [DOI](https://doi.org/10.1145/3133956.3134015) | HDFS and system-specific logs | Normal-only/semi-supervised next-event learning | LSTM next-event and parameter models; sequence-sensitive | Top-k next-event anomaly decision; Precision/Recall/F1 | Establishes next-event prediction as mature sequence baseline family | Older protocol and model complexity exceed the minimum comparator. **Do not implement before Markov and sequence-value gate.** |
| S10 | Meng et al., *LogAnomaly: Unsupervised Detection of Sequential and Quantitative Anomalies in Unstructured Logs*, 2019, IJCAI, [DOI](https://doi.org/10.24963/ijcai.2019/658) | HDFS and BGL-style production logs as described by the paper | Normal-pattern/unsupervised framing | Sequential model plus quantitative count information and semantic template vectors | Precision/Recall/F1 under paper protocol | Directly combines sequential and quantitative signals | Demonstrates that hybrid sequence/count evidence is known. **Any future improvement must isolate order contribution rather than credit mixed features.** |
| S11 | Wei, Sun, Zhang, Towey, *MulAD: A Log-Based Anomaly Detection Approach for Distributed Systems Using Multi-Pattern and Multi-Model Fusion*, online 2025 / volume 2026, Science of Computer Programming, [DOI](https://doi.org/10.1016/j.scico.2025.103433) | HDFS, BGL, Thunderbird, Ray as reported by the paper | Paper-specific labeled/evaluation regime | Sequential, semantic, quantitative, temporal and parametric patterns; RF integrates LSTM/Transformer/GNN | Paper-specific F1 comparison | Direct multi-pattern and multi-model log-anomaly fusion prior art | Strong overlap with retired V3 four-expert narrative. **Trainable fusion is not core and not novel.** |
| S12 | Qi et al., *LogMoE: Lightweight Expert Mixture for Cross-System Log Anomaly Detection*, 2025, ASE, [DOI](https://doi.org/10.1109/ASE63991.2025.00035) | Eight cross-system log datasets; exact variants must be checked before replication | Labeled source-system logs with scarce labeled/pseudo-labeled target adaptation | System/domain-specific lightweight LoRA experts over a shared frozen BERT encoder plus a learned gate | Cross-system Precision/Recall/F1 and efficiency | Establishes direct log-specific MoE/gating prior art | Different objective/supervision from SeqLogAD, but enough to block a generic MoE novelty claim. **DROP fusion from core.** |
| S13 | Wang et al., *FAME: Failure-Aware Mixture-of-Experts for Message-Level Log Anomaly Detection*, 2026, arXiv preprint; accepted at ISSRE 2026 according to the manuscript, [arXiv:2605.22779](https://arxiv.org/abs/2605.22779) | BGL and Thunderbird; line/message-level task | Label-efficient, template-stratified labeled examples | Failure-domain experts and router; message-level, not session-order focused | F1/Recall and annotation-effort reporting | Reports strong BGL message-level performance and unseen-EventID detection without requiring the SeqLogAD order question | Final proceedings/DOI were not available in this review. **Further evidence that BGL line identity can dominate and MoE/localization are active prior art.** |
| S14 | Iglesias, Zseby, Martínez, Zimek, *On Heterogeneous Ensembles for Anomaly Detection*, 2026, Expert Systems with Applications, [DOI](https://doi.org/10.1016/j.eswa.2026.133468) | General tabular anomaly datasets, not logs | Unsupervised anomaly ensembles | 14 heterogeneous algorithms; score normalization and aggregation | Average Precision/AUROC and ensemble-size analysis | Reports that small complementary ensembles and normalization/aggregation choices matter | Domain mismatch prevents transfer to logs. **Confirms complementarity/redundancy analysis is established infrastructure, not novelty.** |
| S15 | Li et al., *SwissLog: Robust Anomaly Detection and Localization for Interleaved Unstructured Logs*, online 2022 / IEEE TDSC volume 2023, [DOI](https://doi.org/10.1109/TDSC.2022.3162857) | Interleaved system logs and public benchmarks in the paper | Paper-specific learned detection/localization | Sequence/session modeling with localization | Detection and localization measures reported by paper | Establishes pre-2024 log anomaly localization prior art | Exact token/gap/transition contract differs. **Localization cannot be advertised as new and remains conditional.** |
| S16 | Wong et al., *Seeing the Needle in the Haystack: Towards Weakly-Supervised Log Instance Anomaly Localization via Counterfactual Perturbation (LogMILP)*, 2026, arXiv preprint, [arXiv:2605.10988](https://arxiv.org/abs/2605.10988) | BGL, Spirit, ZooKeeper as described in manuscript | Bag-level weak supervision | Instance localization with prototypes and counterfactual perturbation consistency | F1 plus Loc@3 and Success Rate; validation thresholding | Direct localization and counterfactual-faithfulness overlap | Preprint; bag labels and message coordinates differ from SeqLogAD synthetic token/gap/transition targets. **KEEP only as conditional prior-art/sanity reference.** |
| S17 | Huo et al., *AutoLog: A Log Sequence Synthesis Framework for Anomaly Detection*, 2023, ASE, [DOI](https://doi.org/10.1109/ASE56229.2023.00133) | Source-code-derived paths for Java systems | Generated sequence labels/paths | Static-analysis control-flow sequence synthesis; order-sensitive | Coverage/plausibility and downstream detector metrics | Establishes code-guided log-sequence synthesis before SeqLogAD | SeqLogAD mutations are controlled experimental devices, not a generation contribution. **No novelty claim.** |
| S18 | Li et al., *AnomalyGen: Enhancing Log-Based Anomaly Detection with Code-Guided Data Augmentation*, 2026, arXiv preprint, [arXiv:2604.11107](https://arxiv.org/abs/2604.11107) | HDFS and ZooKeeper plus source-code coverage analysis | Synthetic labeled training augmentation | Static-analysis paths plus LLM validation; sequence-sensitive generated examples | F1 across model/augmentation settings | Reports benchmark template-coverage gaps and that naive insertion/deletion/modification can degrade several models | Preprint; generated training anomalies conflict with SeqLogAD's separated evaluation contract if copied blindly. **Synthetic localization remains conditional and isolated from real-anomaly evaluation.** |
| S19 | Khanal, Narayan, *State Machine Guided Multi-Relational Synthetic Data from Logs for Anomaly Detection (LogSynthFSM)*, 2026, KDD, [DOI](https://doi.org/10.1145/3770855.3818134) | Structured synthetic logs from state-machine relations | Synthetic data generation | State-machine/relational sequential generation | Downstream anomaly-detection and generation evaluation | Establishes structured/state-machine-guided synthetic log generation as active prior art | Not the same objective as controlled mutations, but blocks generic synthetic-sequence novelty. **Do not expand scope.** |
| S20 | Zhang et al., *Reducing Events to Augment Log-Based Anomaly Detection Models: An Empirical Study (LogCleaner)*, 2024, ESEM, [DOI](https://doi.org/10.1145/3674805.3695403) | Three public datasets and six models | Method-dependent | Event filtering/reduction; emphasizes event-type contribution | Detection F1, event reduction, inference speed | Reports that event families differ greatly in predictive usefulness and large reductions can preserve/improve detection | Filtering changes the scientific input and is not adopted. **Supports checking whether a few event types dominate.** |

## 4. Methodological support matrix

| ID | Source | What it supports | Boundary for SeqLogAD |
|---|---|---|---|
| M01 | Zhu et al., *Loghub*, ISSRE 2023, [DOI](https://doi.org/10.1109/ISSRE59848.2023.00071), and [canonical Zenodo record](https://doi.org/10.5281/zenodo.8196385) | Dataset provenance, variants, raw file availability and citation terms | The exact accepted archive/manifests remain the project identity; a paper's HDFS/BGL label does not guarantee byte equivalence |
| M02 | Oliner, Stearley, *What Supercomputers Say*, DSN 2007, [DOI](https://doi.org/10.1109/DSN.2007.103) | BGL origin and line-level operational context | Does not define SeqLogAD's future 100-event parent-window result |
| M03 | Adebayo et al., *Sanity Checks for Saliency Maps*, NeurIPS 2018, [official proceedings](https://proceedings.neurips.cc/paper/2018/hash/294a8ed24b1ad22ec2e7efea049b8737-Abstract.html) | Model/data randomization as explanation sanity tests | General explanation methodology, not log-specific evidence; only conditional localization uses it |
| M04 | Saito, Rehmsmeier, *The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets*, 2015, PLOS ONE, [DOI](https://doi.org/10.1371/journal.pone.0118432) | PR curves make positive-prediction quality visible under imbalance | Supports PR-AUC reporting, not a universal effect-size threshold |
| M05 | Boyd, Eng, Page, *Area Under the Precision-Recall Curve: Point Estimates and Confidence Intervals*, 2013, ECML PKDD, [DOI](https://doi.org/10.1007/978-3-642-40994-3_29) | AUCPR uncertainty estimation rather than point estimates alone | SeqLogAD must still choose a resampling unit that respects sessions/windows and chronology |
| M06 | Lakens, Scheel, Isager, *Equivalence Testing for Psychological Research: A Tutorial*, 2018, AMPPS, [DOI](https://doi.org/10.1177/2515245918770963) | Pre-specifying a smallest effect size of interest and distinguishing equivalence from failure to reject | Domain is not log detection; use decision logic, not its example values or an unadapted parametric test |
| M07 | Liu, Ting, Zhou, *Isolation Forest*, ICDM 2008, [DOI](https://doi.org/10.1109/ICDM.2008.17) | Unsupervised isolation-based anomaly scoring and efficient subsampling | General tabular method; no equivalent HDFS/BGL result under Protocol v1.1 was found, so its value remains empirical |
| M08 | Künsch, *The Jackknife and the Bootstrap for General Stationary Observations*, Annals of Statistics, 1989, [DOI](https://doi.org/10.1214/aos/1176347265) | Block-based resampling for dependent stationary observations | Supports preserving dependence in uncertainty estimation; exact block construction for HDFS/BGL must still be frozen in `EFFECT-001` |

## 5. Dataset suitability matrix

The first two columns identify SeqLogAD's intended artifacts; the evidence columns explicitly describe **external, variant-dependent** findings.

| Dataset | Variant/source | Label granularity | Sequence unit | Known trivial signals | Order-dependence evidence | Ceiling risk | Leakage risks | Suitability for SeqLogAD core RQ |
|---|---|---|---|---|---|---|---|---|
| HDFS | Exact accepted `HDFS_v1` from Loghub Zenodo `10.5281/zenodo.8196385`; manifest/fingerprint in repo | Block/session label file | Block/session atomic unit; final sequence artifact not built | External variants show strong length, event-presence, and especially event-count-vector signal; original HDFS analysis used count vectors | Reviews describe weak/ambiguous order need; ContraLog position perturbations show smaller average score effects than deletion/addition, but no KT-3 result exists for exact SeqLogAD bytes/protocol | **HIGH** | Block IDs spanning nominal boundaries; random block split; parser/vocabulary fit on later partitions; Loghub/Xu/LogDeep variant mismatch; use of preprocessed templates/traces; duplicate/near-duplicate execution patterns | **CONDITIONAL / KEEP.** Suitable for measuring incremental order value and a possible negative result; not sufficient alone to claim sequence superiority |
| BGL | Exact accepted `BGL.zip` from Loghub Zenodo `10.5281/zenodo.8196385`; manifest/fingerprint in repo | Inline line-level anomaly indicator | Protocol-defined non-overlapping 100-event parent windows after raw chronological assignment | External variants show many anomalies associated with unseen/new event types; message semantics may predict anomalies without sequence context | Chronological sampling and window construction strongly affect performance; no exact multiset-preserving order-destruction result exists for SeqLogAD | **HIGH** for event-identity saturation; chronology may expose harder drift | Random splitting; overlapping/sliding windows; one line appearing in several windows; template/vocabulary fit on future data; window-label propagation; time drift; CFDR/Loghub variant mismatch | **CONDITIONAL / KEEP.** Useful for chronological robustness and quantifying added value; weak as sole evidence that order is necessary |

### Dataset decision

`KEEP HDFS` and `KEEP BGL` under Protocol v1.1. Do not add or replace datasets during LIT-001. If KT-1–KT-3 fail their pre-registered gates, a later protocol amendment may consider another dataset, but literature alone does not authorize that change.

## 6. Strong baseline matrix

All numeric values below are `EXTERNAL RESULT` from S01 and are variant/protocol-specific F1 values. They are included only to justify baseline priority.

| Method | Order-sensitive? | Supervision | Features | Dataset / variant | External result | Relevance to SeqLogAD |
|---|---:|---|---|---|---|---|
| Unseen event-type | No | Normal-reference membership | Event/template presence | HDFS Xu-style and BGL CFDR/time-window variants | HDFS random/chronological F1 53.9/73.3; BGL CFDR sequence F1 98.8; BGL time-window random/chronological F1 68.0/47.0 | **MUST.** Cheap test for novelty-by-event-ID and BGL ceiling |
| Sequence length | No | Validation threshold only | Length | HDFS Xu-style | Random/chronological F1 56.0/4.6 | **MUST.** Detects label/window artifacts; instability itself is informative |
| Event + length | No | Normal-reference rules | Event presence and length | HDFS Xu-style | Random/chronological F1 72.0/5.6 | **MUST diagnostic.** Prevents attributing combined trivial cues to order |
| Event-count vector (ECVC/TF-IDF variant) | No | Normal reference / unsupervised feature model | Per-template counts | HDFS Xu-style | ECVC random/chronological F1 96.0/53.9; ECVC-idf 96.5/82.9 | **MUST.** Strongest direct order-insensitive challenge and KT-2 input |
| PCA on count vectors | No | Normal-only/unsupervised | Count vector | HDFS lineage and later benchmark variants | Published protocols report strong but variant-sensitive behavior; no exact SeqLogAD score | **SHOULD comparator** if implementation budget permits; feature source must be frozen |
| Isolation Forest | No | Unsupervised fit; external tuning regime varies | Count-vector/summary features; no order features | ContraLog Loghub-based HDFS/BGL/Thunderbird construction | Tuned external F1 66.44/48.64/83.00; tuning used a labeled subset and protocol differs | **SHOULD.** Empirically test under legal SeqLogAD selection rather than transfer these values |
| Markov/N-gram | Yes, local | Normal-only transition counts | Adjacent or short-context event transitions | HDFS/BGL variants in S01 | HDFS 2-gram random/chronological F1 86.2/53.8; values remain variant-sensitive | **MUST.** Minimum fair sequential comparator |
| DeepLog | Yes | Normal-only next-event | LSTM event sequence | HDFS/BGL variants | HDFS random/chronological F1 85.6/86.8 in one S01 setting | **CONDITIONAL.** Known comparator, but not needed before Markov gate |
| LogAnomaly | Mixed | Normal-pattern learning | Sequence plus quantitative/semantic signal | HDFS/BGL variants | HDFS random/chronological F1 87.4/88.1 in one S01 setting | Not a clean order-only comparator; use only with signal attribution |
| Within-sequence shuffle/order destruction | Negative control | N/A | Preserves multiset/count/length; destroys transition/order | ContraLog HDFS position-change perturbation; no equivalent standardized benchmark located | Position moves often changed anomaly score less than deletion/addition, but some one-position moves caused large increases; real-label paired PR-AUC was not the endpoint | **MUST KT-3.** Direct partial precedent exists; pre-register SeqLogAD's stricter diagnostic and make no novelty claim |

## 7. Contribution and novelty-risk matrix

Allowed classifications for this task are `SUPPORTED GAP`, `PARTIAL OVERLAP`, `STRONG PRIOR ART`, and `NOT ENOUGH EVIDENCE`. They describe the targeted search, not an absolute global novelty proof.

| Proposed contribution / claim | Classification | Evidence and decision |
|---|---|---|
| Controlled incremental value of order over strong orderless baselines | **PARTIAL OVERLAP** | S01–S04 already compare simple and sequential families and expose protocol sensitivity. SeqLogAD's exact chronological/equal-budget/PR-AUC/negative-control protocol is a defensible replication-extension question, not a new algorithm claim |
| Exact HDFS/BGL suitability under accepted bytes and frozen split | **PARTIAL OVERLAP** | Variants are extensively studied, but exact byte/protocol outcome remains empirical. Project-specific verification is valuable without being method novelty |
| Multiset-preserving within-sample order destruction as a log control | **PARTIAL OVERLAP** | ContraLog directly perturbs HDFS message positions and studies anomaly-score response. It does not match SeqLogAD's paired real-label PR-AUC design, minimal Markov comparator, or exact frozen protocol |
| Lightweight Transformer/next-event sequence model | **STRONG PRIOR ART** | DeepLog, LogSD, LogCraft, ContraLog and many Transformer-family methods cover sequence learning |
| Heterogeneous multi-model anomaly system | **STRONG PRIOR ART** | MulAD and general heterogeneous-ensemble research directly overlap |
| Mixture-of-experts/gating for log anomaly detection | **STRONG PRIOR ART** | LogMoE and FAME directly overlap |
| Generic anomaly localization | **STRONG PRIOR ART** | SwissLog and LogMILP directly overlap |
| Counterfactual/randomization-based localization faithfulness | **STRONG PRIOR ART** | LogMILP and general saliency sanity checks cover the family |
| Separate token/gap/transition localization coordinates | **NOT ENOUGH EVIDENCE** | No exact match was established in this targeted review; it remains an engineering/scientific contract, not a novelty claim |
| Synthetic insertion/deletion/replacement/reorder mutations | **STRONG PRIOR ART** | AutoLog, AnomalyGen, LogSynthFSM and prior robustness augmentation cover synthetic sequence generation/transformation families |
| Structured fusion/F8 | **STRONG PRIOR ART** at the family level | MulAD, LogMoE and heterogeneous-ensemble literature make generic fusion novelty untenable; F8 remains outside v1.1 core |
| Evidence-grounded RAG/Agent/test recommendation | **NOT ENOUGH EVIDENCE** in this review | It is outside the core RQ and was not searched deeply enough for a novelty conclusion; remains future integration only |

## 8. Minimum practical effect research input

### Evidence conclusion

No reviewed log-anomaly paper supplies a transferable universal threshold such as “ΔPR-AUC = X is practically meaningful.” Choosing a number from these papers would be arbitrary because baseline prevalence, sequence unit, dataset variant, alert cost, and achievable ceiling differ.

### Recommendation for `EFFECT-001`

Freeze the following **before KT-1 or KT-3 is run**:

1. **Primary estimand per dataset:** paired `ΔAP = AP_sequence − AP_strongest_orderless` over the same legal evaluation units.
2. **Secondary descriptive estimand:** relative headroom/error reduction, reported only alongside absolute ΔAP and baseline AP.
3. **Dataset-specific margin `δ_d`:** owned and approved by the human researcher; justify from an operational alert-cost/latency trade-off. If no credible utility model exists, call it a precision/feasibility margin rather than a practical effect.
4. **Dependence-aware uncertainty:** paired cluster/block bootstrap over HDFS block/session units and BGL parent-window/time blocks; freeze resampling count, CI level/method, and seed before use.
5. **Decision regions:**
   - meaningful gain: lower confidence bound is above `+δ_d`;
   - practical equivalence/no meaningful gain: interval is fully inside `[-δ_d, +δ_d]`;
   - meaningful harm: upper confidence bound is below `-δ_d`;
   - otherwise: **INCONCLUSIVE**.
6. **No TEST-derived margin:** do not set `δ_d`, choose the bootstrap, or alter the claim after seeing TEST.

The literature supports this decision framework (PR-focused evaluation, uncertainty intervals, and pre-specified equivalence bounds) but is **insufficient to freeze a numeric `δ_d` today**.

## 9. Implications for SeqLogAD

| Decision | Item | Reason |
|---|---|---|
| **KEEP** | HDFS and BGL under exact manifests | They can answer the incremental-value question, including a negative answer |
| **KEEP** | Chronology, split-before-fit, TEST sealing, parser freeze | External studies show material chronology/preprocessing sensitivity |
| **KEEP** | Unseen-event, length, total-count/count-vector, Markov/N-gram | Strongest cheap falsification set directly supported by evidence |
| **KEEP** | PR-AUC primary plus paired uncertainty | Imbalance and near-ceiling comparisons require more than point F1 |
| **MODIFY** | Novelty wording | LIT-001 is complete, but it establishes **no algorithm novelty**; the contribution is a controlled empirical study if executed correctly |
| **MODIFY** | EFFECT-001 | Freeze a dataset-specific margin and dependence-aware paired inference; do not invent one global number |
| **DROP** | Generic Transformer, MoE, fusion, localization, or synthetic-mutation novelty claims | Strong prior art exists |
| **DROP** | Fixed four-expert/F2–F8 core implementation | It does not answer the current RQ before complementarity evidence |
| **CONDITIONAL** | Isolation Forest | Strong, fair orderless comparator if implementation budget permits; exact benefit must be measured |
| **CONDITIONAL** | Transformer | Only after KT-1–KT-3 reveal a residual long-range sequence question |
| **CONDITIONAL** | Localization and simple fusion | Only after their existing protocol gates; prior art and sanity controls apply |
| **CONDITIONAL** | Dataset expansion | Only after HDFS/BGL fail registered suitability gates and a new amendment is approved |

## 10. LIT-001 completion statement

The targeted review covers all requested buckets, records reproducible queries and dispositions, maps exact dataset-variant boundaries, defines a strong baseline set, assesses contribution overlap, and provides a non-arbitrary input to `EFFECT-001`. No scientific implementation or experiment was performed.

Any future claim of a new method, SOTA, first-of-kind contribution, or new RAG/Agent contribution requires a fresh, claim-specific systematic search. `LIT-001 = DONE` does not waive that rule.
