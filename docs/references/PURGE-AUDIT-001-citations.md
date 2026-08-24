# PURGE-AUDIT-001 — Citations and Method Provenance

Searched on **2026-08-24**. This note separates external evidence from
SeqLogAD's observed audit result. No cited paper is treated as a result for the
exact frozen SeqLogAD bytes or split.

## Search log

Databases/endpoints: ACM Digital Library/DOI, SpringerLink, Wiley Online
Library, IFIP Digital Library, Zenodo, publisher/author institutional records,
and general scholarly web search used only to locate primary records.

Representative queries:

- `2026 2025 2024 HDFS BGL sequence anomaly dataset preprocessing grouping`;
- `selection bias exclusion representativeness filtered sample`;
- `difference between independent proportions Wilson Newcombe interval`;
- `cluster session dependence unit of analysis confidence interval`;
- `HDFS block session grouping dataset construction`;
- `chronological split leakage log anomaly detection preprocessing effect`.

Inclusion required a verifiable publisher, proceedings, DOI, or authoritative
institutional record and direct relevance to dataset construction,
preprocessing/grouping, clustered units, or interval estimation. Blogs,
unverifiable bibliographic records, and papers whose result could not support
the stated claim were rejected. Newer sources were preferred only when they
were at least as direct and methodologically useful as older sources.

## Recent domain evidence

| Claim / decision | Classification | Source | Year | Status | DOI / official URL | Applicability and limitation |
|---|---|---|---:|---|---|---|
| HDFS/BGL construction and preprocessing choices can materially affect anomaly-detection conclusions | `LITERATURE_SUPPORTED` | Landauer, Skopik, Wurzenberger, “A Critical Review of Common Log Data Sets Used for Evaluation of Sequence-Based Anomaly Detection Techniques,” *PACMSE/FSE* | 2024 | Peer reviewed | [10.1145/3660768](https://doi.org/10.1145/3660768) | Directly studies common log datasets and simple anomaly manifestations. It does not evaluate SeqLogAD's frozen connected-component purge. |
| Parser/preprocessing output can change downstream anomaly-detection behavior, so parser state must remain outside this audit | `LITERATURE_SUPPORTED` | Khan et al., “Impact of log parsing on deep learning-based anomaly detection,” *Empirical Software Engineering* 29:139 | 2024 | Peer reviewed, open access | [10.1007/s10664-024-10533-w](https://doi.org/10.1007/s10664-024-10533-w) | Supports treating parsing as a consequential design variable. Its reduced HDFS variants and model experiments are not SeqLogAD evidence. |
| Chronology, grouping, and preprocessing are protocol variables rather than innocuous implementation details | `LITERATURE_SUPPORTED` | Sedláček, Žádník, Bartoš, “Anomaly Detection in Log Data: A Comparative Study,” CNSM | 2025 | Peer reviewed | [10.23919/CNSM67658.2025.11297503](https://doi.org/10.23919/CNSM67658.2025.11297503) | Direct log-anomaly domain evidence. Some experiments use shuffled cross-validation, so its outcome protocol is not imported into SeqLogAD. |
| Recent work still treats HDFS as block/session-grouped and BGL preprocessing as an explicit design choice | `LITERATURE_SUPPORTED` | Alzahrani, “Investigating the Impact of Log-Sequence Embeddings on Anomaly Detection: A Systematic Study,” *Information* 17(3):228 | 2026 | Peer reviewed | [10.3390/info17030228](https://doi.org/10.3390/info17030228) | Recent domain context. Its split/label handling differs from Protocol v1.1 and cannot justify or validate SeqLogAD's purge. |
| Exact HDFS bytes and labels belong to a published Loghub dataset snapshot | `LITERATURE_SUPPORTED` | Zhu, He, He, Liu, Lyu, “Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics,” ISSRE | 2023 | Peer reviewed | [10.1109/ISSRE59848.2023.00071](https://doi.org/10.1109/ISSRE59848.2023.00071); [Zenodo 8196385](https://zenodo.org/records/8196385) | Supports provenance and dataset identity, not representativeness of the derived split. |

## Foundational dataset/statistical methodology

| Claim / decision | Classification | Source | Year | Status | DOI / official URL | Applicability and limitation |
|---|---|---|---:|---|---|---|
| HDFS block IDs define execution/session context, making component/session the defensible primary outcome unit after mapping validation | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | Xu et al., “Detecting Large-Scale System Problems by Mining Console Logs,” SOSP | 2009 | Peer reviewed | [10.1145/1629575.1629587](https://doi.org/10.1145/1629575.1629587) | Foundational HDFS construction. SeqLogAD additionally verifies one label per META-001 component on its exact bytes. |
| Inference must respect clustering; raw lines cannot be treated as independent binary labels when the outcome is component/session-level | `LITERATURE_SUPPORTED` | Billot, Copas, Leyrat, Forbes, Turner, “How should a cluster randomized trial be analyzed?”, *Journal of Epidemiology and Population Health* 72(1) | 2024 | Peer reviewed | [10.1016/j.jeph.2024.202196](https://doi.org/10.1016/j.jeph.2024.202196) | General cluster-analysis principle; the clinical trial setting differs from this observational finite-dataset audit. |
| The naive Wald interval for a difference of proportions has poor coverage; the hybrid Wilson/Newcombe interval is a practical alternative | `LITERATURE_SUPPORTED` | Newcombe, “Interval estimation for the difference between independent proportions: comparison of eleven methods,” *Statistics in Medicine* 17(8) | 1998 | Peer reviewed | [10.1002/(SICI)1097-0258(19980430)17:8<873::AID-SIM779>3.0.CO;2-I](https://onlinelibrary.wiley.com/doi/10.1002/%28SICI%291097-0258%2819980430%2917%3A8%3C873%3A%3AAID-SIM779%3E3.0.CO%3B2-I) | Direct support for the chosen two-proportion interval. It assumes independent inferential units; residual temporal dependence across HDFS components remains a limitation. |
| Modern review continues to identify limitations of simple Wald intervals for two independent proportions | `LITERATURE_SUPPORTED` | Shan, Lou, Wu, “Continuity Corrected Wilson Interval for the Difference of Two Independent Proportions,” *Journal of Statistical Theory and Applications* 22 | 2023 | Peer reviewed | [10.1007/s44199-023-00054-8](https://doi.org/10.1007/s44199-023-00054-8) | Corroborating interval-method evidence; SeqLogAD uses Newcombe's uncorrected hybrid-score method rather than this paper's corrected variant. |

## SeqLogAD-specific decisions

| Claim / decision | Classification | Support | Limitation |
|---|---|---|---|
| `PURGED` is the public `PURGED_BOUNDARY` set and `RETAINED` is its complement in the full META-001 component universe | `SEQLOGAD_PROTOCOL_DECISION` | Frozen SPLIT-001 and PROTOCOL-SPLIT-CLARIFY-001 | No paper establishes this exact rule as optimal. |
| Population identities are fixed before opening the label file | `ENGINEERING_DECISION` | One-way audit implementation and regression tests | Enforces the frozen label boundary; it is not a literature result. |
| Use connected components as primary units only after exact one-to-one label mapping is verified | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | Xu et al. 2009 plus exact local mapping audit | Independence across components is an explicit assumption, not proven by the dataset. |
| Report Newcombe–Wilson 95% CI, absolute difference, prevalence ratio, population sizes, and structural mechanism; report no p-value | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | Newcombe 1998; clustered-unit principle above | No practical-equivalence margin for prevalence was approved. |
| Classify the result `PURGE_REPRESENTATIVENESS_CONCERN` and return it to the human researcher without split repair | `SEQLOGAD_PROTOCOL_DECISION` | Observed 22.7374% raw-line purge, prevalence ratio 0.8902, CI excluding zero, and strong structural selection | This is not a causal claim and does not prove HDFS invalid. Human review is required before the pipeline proceeds. |

## Literature/protocol conflicts

- Some recent log-anomaly studies use random/stratified splitting or shuffled
  cross-validation. Those practices conflict with SeqLogAD's frozen
  label-independent chronological protocol and are recorded as
  `LITERATURE_PROTOCOL_CONFLICT`; they are not imported.
- No reviewed source validates SeqLogAD's exact connected-component purge or
  provides a transferable practical-equivalence margin for anomaly-prevalence
  differences. Therefore no `ACCEPTABLE` conclusion is available.
