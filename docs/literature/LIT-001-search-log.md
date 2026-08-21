# LIT-001 — Reproducible Search Log

| Field | Value |
|---|---|
| Task | `LIT-001` |
| Search date | 2026-08-21 |
| Primary publication window | 2024-08-01 through 2026-08-21 |
| Older-source rule | Retain only dataset provenance, foundational baselines, evaluation methodology, localization sanity, or statistical methodology needed by the active RQ |
| Review type | Targeted decision-oriented review; not a PRISMA/systematic-review claim |
| Main matrix | [`prior-art-matrix-v1.1.md`](prior-art-matrix-v1.1.md) |
| Source annotations | [`../references/LIT-001-citations.md`](../references/LIT-001-citations.md) |

## 1. Research question and buckets

Primary question:

> How much additional anomaly-detection value does sequence order provide beyond strong order-insensitive baselines under leakage-controlled, chronological, and equal-budget evaluation?

Mandatory buckets searched:

- log anomaly detection;
- sequence-sensitive and order-insensitive methods;
- unseen-event, frequency, length, count/count-vector, Isolation Forest, Markov/N-gram;
- HDFS/BGL limitations, ceiling effects, variants, grouping, chronology, and leakage;
- sequence-order contribution and order-destruction controls;
- unsupervised, normal-only, and self-supervised learning;
- heterogeneous ensembles, fusion, and mixture-of-experts;
- anomaly localization and localization faithfulness;
- synthetic anomaly generation and mutation;
- minimum practical effect, PR-AUC, and uncertainty.

## 2. Sources searched

The general search engine was used only for discovery. A record was retained only after checking a primary or official source where available.

| Source/database | Use |
|---|---|
| ACM Digital Library / DOI records | FSE, ASE, CCS, ESEM and KDD papers |
| IEEE/IFIP conference pages and official PDFs | ISSRE, CNSM, DSN and ASE records |
| SpringerLink | Empirical Software Engineering and related journal work |
| ScienceDirect / publisher DOI records | MulAD and ensemble literature |
| IJCAI proceedings | LogAnomaly official paper |
| NeurIPS proceedings | Localization/explanation sanity methodology |
| PLOS and SAGE publisher pages | PR-curve and equivalence-method sources |
| arXiv | Recent 2026 work not yet available as a verified final publication |
| Zenodo and official Loghub repository | Dataset source, variants, license/citation terms |
| DBLP / institutional repositories | Bibliographic cross-check and legal author copies when publisher text was inaccessible |
| Backward/forward snowballing | Landauer 2024, Ali 2025, Sedláček 2025, MulAD, LogMoE, LogMILP, AnomalyGen and LogSynthFSM |

## 3. Query ledger

Queries are recorded exactly enough to rerun. Variants differed only in quotation marks or site restriction.

| ID | Query | Primary bucket |
|---|---|---|
| Q01 | `2024 2025 2026 log anomaly detection sequence order HDFS BGL simple baseline unseen event count vector official paper` | Dataset ceiling / baselines |
| Q02 | `2024 2025 2026 log anomaly detection sequence shuffle order destruction negative control paper` | Order destruction |
| Q03 | `"shuffle" "event order" "log anomaly detection" paper` | Order destruction |
| Q04 | `"order sensitivity" "log anomaly detection"` | Order contribution |
| Q05 | `2025 benchmark log anomaly detection chronological split HDFS BGL` | Chronology / leakage |
| Q06 | `2025 systematic review log anomaly detection sequence HDFS BGL official DOI` | Recent surveys/benchmarks |
| Q07 | `"A Critical Review of Common Log Data Sets" DOI` | HDFS/BGL suitability |
| Q08 | `"Anomaly Detection in Log Data: A Comparative Study" CNSM 2025` | Unified benchmark |
| Q09 | `"A comprehensive study of machine learning techniques for log-based anomaly detection"` | ML comparison |
| Q10 | `"Impact of log parsing on deep learning-based anomaly detection" DOI` | Parsing/variant sensitivity |
| Q11 | `"LogSD" FSE 2024 DOI` | Self-supervised sequence AD |
| Q12 | `"End-to-End AutoML for Unsupervised Log Anomaly Detection" DOI` | Unsupervised/model selection |
| Q13 | `"ContraLog" log anomaly detection` | Message-only versus sequence context |
| Q14 | `"DeepLog" 10.1145/3133956.3134015` | Foundational sequence model |
| Q15 | `"LogAnomaly" sequential quantitative anomalies IJCAI` | Mixed sequence/count model |
| Q16 | `2025 2026 heterogeneous ensemble mixture of experts fusion log anomaly detection official paper` | Fusion/MoE |
| Q17 | `"MulAD" multi-pattern multi-model fusion` | Log-specific fusion |
| Q18 | `"LogMoE" "ASE 2025" official` | Log-specific MoE |
| Q19 | `"FAME" failure-aware mixture-of-experts log anomaly` | Message-level MoE |
| Q20 | `"On Heterogeneous Ensembles for Anomaly Detection" 133468` | General heterogeneous ensembles |
| Q21 | `2025 2026 log anomaly detection localization faithfulness synthetic mutation official paper` | Localization/faithfulness |
| Q22 | `"Seeing the Needle in the Haystack" LogMILP` | Counterfactual localization |
| Q23 | `"SwissLog" anomaly detection localization DOI` | Earlier localization |
| Q24 | `site:proceedings.neurips.cc "Sanity Checks for Saliency Maps"` | Randomization sanity tests |
| Q25 | `log anomaly detection synthetic sequence mutation missing insertion replacement reorder paper` | Synthetic mutations |
| Q26 | `"AutoLog: A Log Sequence Synthesis Framework" DOI` | Code-guided synthesis |
| Q27 | `"AnomalyGen" log anomaly code-guided data augmentation` | Synthetic augmentation |
| Q28 | `"State Machine Guided Multi-Relational Synthetic Data from Logs" DOI` | Structured synthetic logs |
| Q29 | `"Reducing Events to Augment Log-based Anomaly Detection Models" DOI` | Event-type dominance |
| Q30 | `minimum effect size of interest methodology equivalence testing Lakens DOI` | Practical effect |
| Q31 | `precision recall AUC confidence interval bootstrap paper DOI` | PR-AUC uncertainty |
| Q32 | `PR AUC imbalanced datasets Saito Rehmsmeier 2015 PLOS` | PR-AUC rationale |
| Q33 | `"Loghub: A Large Collection of System Log Datasets" DOI` | Dataset provenance |
| Q34 | `Loghub HDFS BGL Zenodo 8196385` | Exact source record |
| Q35 | `Isolation Forest Liu Ting Zhou 2008 ICDM DOI` | Order-insensitive baseline lineage |
| Q36 | `Kunsch 1989 jackknife bootstrap stationary observations DOI block bootstrap` | Dependence-aware uncertainty |

## 4. Inclusion criteria

A work was retained when all applicable criteria held:

1. It directly informs at least one mandatory bucket or the active research question.
2. It is peer-reviewed, publisher-hosted, or clearly labeled as a preprint.
3. A primary/official record exposes enough metadata to verify title, authors, year/status, and URL/DOI.
4. Its dataset, supervision, representation, evaluation, or methodological role can be distinguished from SeqLogAD's protocol.
5. For older work, it is necessary to establish provenance, baseline lineage, or the statistical/control method.

## 5. Exclusion criteria

A candidate was rejected or not promoted to the main matrix when any applied:

- secondary blog, vendor page, auto-generated summary, or social post where an original paper exists;
- duplicate preprint/final record without additional relevant information;
- unrelated non-log anomaly domain, except a clearly labeled transferable statistical or explanation-sanity method;
- failure prediction, root-cause analysis, parsing, or drift work with no direct implication for the active RQ;
- incomplete bibliographic identity or inaccessible evidence that prevented reliable classification;
- another paper already provided stronger and more direct evidence for the same narrow point;
- a method/result could not be mapped to dataset variant and evaluation regime with adequate confidence.

## 6. Duplicate handling

No unstable search-engine “number of results” was treated as a scientific count. Duplicate families were resolved manually:

| Duplicate family | Retained record |
|---|---|
| Publisher DOI + arXiv + ResearchGate/secondary mirror | Publisher/final record; arXiv only as accessible copy when useful |
| Loghub arXiv + GitHub + Zenodo + ISSRE paper | ISSRE paper for scholarship; Zenodo for exact archive identity; GitHub for current dataset documentation |
| LogSD arXiv + ACM + university repository | ACM DOI/final paper |
| LogCraft arXiv/author PDF + ACM | ACM DOI/final paper |
| LogCleaner arXiv + venue page | ESEM DOI/final record |
| 2026 work with no verified final proceedings | arXiv retained and explicitly labeled `PREPRINT` |

## 7. Retained-paper ledger

The detailed annotations and links are in [`../references/LIT-001-citations.md`](../references/LIT-001-citations.md).

| IDs | Retained category |
|---|---|
| S01–S04 | Dataset suitability, benchmark and preprocessing sensitivity |
| S05–S10 | Self-supervised, orderless, sequential, and mixed-signal detector lineage |
| S11–S14 | Multi-model fusion, MoE, and heterogeneous ensemble overlap |
| S15–S16, M03 | Localization and faithfulness prior art / sanity methodology |
| S17–S20 | Synthetic generation/mutation and event-dominance overlap |
| M01–M02 | HDFS/BGL provenance |
| M04–M08 | PR-AUC, dependence-aware uncertainty, minimum-practical-effect, and Isolation Forest methodology |

## 8. Rejected/deferred ledger

| Candidate/category | Disposition | Reason |
|---|---|---|
| Vendor/Elastic/AIOps articles | `REJECTED` | Secondary/product material; no need when primary research exists |
| Generic anomaly-detection surveys | `REJECTED` | Too broad for the sequence-order question |
| Vision/biomedical sequence-shuffle papers | `REJECTED` | Domain and causal structure mismatch; no log-specific support |
| Random-vs-chronological sampling papers presented as order-destruction | `REJECTED AS EQUIVALENT CONTROL` | Sampling order is not the same intervention as shuffling events within a sequence while preserving counts |
| KDLog/adaptation/drift-only papers | `DEFERRED` | Useful for future non-stationarity work, not needed for v1.1's first gate |
| LADLE/multi-log-type localization | `DEFERRED` | Localization evidence already covered more directly by SwissLog/LogMILP; outside core gate |
| Logs2Graphs/explanation papers | `DEFERRED` | Relevant if localization gate opens; not required to select the minimal baseline set |
| LogPDGMoE/switch-router variants | `DEFERRED` | Marginal evidence after MulAD, LogMoE, FAME; does not change the current fusion decision |
| RAG/Agent/RCA/test-generation papers | `DEFERRED, NOT CLASSIFIED` | Outside the primary RQ and frozen scientific core; no novelty conclusion made |
| Candidate alternative datasets | `DEFERRED` | Protocol retains HDFS/BGL until pre-registered suitability gates run; LIT-001 does not change datasets |

## 9. Snowballing record

- **Backward:** inspected references from S01–S04 for HDFS/BGL provenance, DeepLog, LogAnomaly, grouping, parser, and simple-feature baselines.
- **Forward/recent:** inspected 2025–2026 works that cite or build on common HDFS/BGL benchmark practice, especially S07, S11–S13, S16, and S18.
- **Contribution-specific:** followed MulAD/LogMoE to fusion/MoE work; LogMILP to localization/counterfactual work; AnomalyGen/AutoLog to synthetic transformations; S01/S03 to benchmark and chronology issues.
- Snowballing stopped when additional candidates did not change the baseline set, dataset risk classification, novelty-risk classification, or `EFFECT-001` recommendation.

## 10. Reproducibility and limitations

- Search results can change after 2026-08-21; all source statuses are frozen to the access date.
- Some 2026 records are preprints. They remain evidence of active overlap, not peer-reviewed findings.
- Paywalled abstracts support high-level classification only; no unverified detailed result was imported.
- Citation databases were not used to claim exhaustive coverage or formal recall.
- A new claim-specific systematic review is required before any future novelty/first/SOTA claim.
- LIT-001 searched RAG/Agent only enough to keep it outside scope; it makes no downstream novelty judgment.

## 11. Search completion

All mandatory buckets have a retained source, a conservative `NOT ENOUGH EVIDENCE` decision, or an explicit outside-scope disposition. That is the stopping rule for this targeted task.
