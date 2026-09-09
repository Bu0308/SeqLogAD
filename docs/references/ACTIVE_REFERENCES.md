# Active references

Generated from [`reference_registry.yaml`](reference_registry.yaml) by
`scripts/build_reference_registry.py`. Do not hand-edit: regenerate.

Organised according to `Bang_ke_hoach_SeqLogAD.xlsx`. Verified 2026-09-07 against Crossref, the arXiv API, the Zenodo record API and official pages.

**17 active sources.** Workbook identifiers `S1`-`S11` are preserved; `S12`-`S17` were added by this consolidation for dataset and tooling provenance that the active work relies on.

## Dataset / log sources

| ID | Title | Year | Venue | Link | Used by | Relevance |
| --- | --- | ---: | --- | --- | --- | --- |
| `S1` | Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics | 2023 | IEEE International Symposium on Software Reliability Engineering (ISSRE) | [link](https://doi.org/10.1109/ISSRE59848.2023.00071) | P1.2, P1.3, P1.8, P4.6, P4.8 | Provenance and architecture diversity of the four active corpora. |
| `S16` | Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics (dataset record) | 2023 | Zenodo | [link](https://doi.org/10.5281/zenodo.8196385) | P1.2; P1.8 | Download source, CC-BY-4.0 licence and published MD5 digests. |
| `S12` | Detecting large-scale system problems by mining console logs | 2009 | ACM SIGOPS Symposium on Operating Systems Principles (SOSP) | [link](https://doi.org/10.1145/1629575.1629587) | P1.2; ARCH-HDFS registry row | Origin and block-trace labelling of HDFS_v1. |
| `S13` | What Supercomputers Say: A Study of Five System Logs | 2007 | IEEE/IFIP International Conference on Dependable Systems and Networks (DSN) | [link](https://doi.org/10.1109/DSN.2007.103) | P1.2; ARCH-BGL registry row | Origin of the BGL log and its inline alert markers. |
| `S14` | Log clustering based problem identification for online service systems | 2016 | International Conference on Software Engineering Companion (ICSE-C) | [link](https://doi.org/10.1145/2889160.2889232) | P1.2; ARCH-HADOOP registry row | Origin of the Hadoop corpus and its injected-failure labels. |
| `S15` | DeepLog: Anomaly Detection and Diagnosis from System Logs through Deep Learning | 2017 | ACM SIGSAC Conference on Computer and Communications Security (CCS) | [link](https://doi.org/10.1145/3133956.3134015) | P1.2; ARCH-OPENSTACK registry row | Origin of the OpenStack capture and its anomalous-instance labels. |

## Parsing / normalization

| ID | Title | Year | Venue | Link | Used by | Relevance |
| --- | --- | ---: | --- | --- | --- | --- |
| `S2` | Drain: An Online Log Parsing Approach with Fixed Depth Tree | 2017 | IEEE International Conference on Web Services (ICWS) | [link](https://doi.org/10.1109/ICWS.2017.13) | P1.4 | Fixed-depth-tree log parsing; the optional auxiliary template field only. |
| `S17` | Drain3 — official reference implementation | — | GitHub | [link](https://github.com/logpai/Drain3) | P1.4; configs/parsing/drain3-v1.yaml | Official Drain3 implementation pinned at 0.9.11. |

## Cross-system protocol / domain shift

| ID | Title | Year | Venue | Link | Used by | Relevance |
| --- | --- | ---: | --- | --- | --- | --- |
| `S3` | LogDLR: Unsupervised Cross-System Log Anomaly Detection Through Domain-Invariant Latent Representation | 2025 | IEEE Transactions on Dependable and Secure Computing | [link](https://doi.org/10.1109/TDSC.2025.3548050) | P1.1, P1.2, P1.5, P1.7, P2.1, P2.6, P2.7, P3.1, P3.4, P4.1, P4.2, P4.7, P4.8 | Published evidence that cross-system domain-invariant representation is a live direction. |
| `S4` | ZeroLog: Zero-Label Generalizable Cross-System Log-based Anomaly Detection | 2025 | arXiv | [link](https://arxiv.org/abs/2511.05862) | P1.1, P1.2, P1.5, P1.6, P1.7, P1.8, P2.1, P2.2, P2.3, P3.2, P3.3, P3.7, P4.1, P4.2, P4.4, P4.5, P4.7, P4.8 | Design reference for the zero-label target protocol. |

## LLM / representation

| ID | Title | Year | Venue | Link | Used by | Relevance |
| --- | --- | ---: | --- | --- | --- | --- |
| `S5` | LogLLaMA: Transformer-based log anomaly detection with LLaMA | 2025 | arXiv | [link](https://arxiv.org/abs/2503.14849) | P2.1, P2.2, P2.3, P2.5, P3.6, P4.3, P4.8 | Design reference for LLaMA-family next-log modelling. |
| `S11` | Introducing Llama 3.1: Our most capable models to date | 2024 | Meta AI official release | [link](https://ai.meta.com/blog/meta-llama-3-1/) | P2.1, P2.2, P2.PRE, P4.6, P4.8 | Llama-3.1-8B revision, tokenizer and licence provenance. |

## LoRA / parameter-efficient tuning

| ID | Title | Year | Venue | Link | Used by | Relevance |
| --- | --- | ---: | --- | --- | --- | --- |
| `S7` | LoRA: Low-Rank Adaptation of Large Language Models | 2021 | arXiv (later ICLR 2022) | [link](https://arxiv.org/abs/2106.09685) | P2.1, P2.2, P2.PRE, P4.3, P4.6, P4.8 | Frozen base plus separate low-rank adapters. |

## Graph / temporal expert

| ID | Title | Year | Venue | Link | Used by | Relevance |
| --- | --- | ---: | --- | --- | --- | --- |
| `S6` | LogGT: Cross-system log anomaly detection via heterogeneous graph feature and transfer learning | 2024 | Expert Systems with Applications | [link](https://doi.org/10.1016/j.eswa.2024.124082) | P1.3, P1.4, P1.5, P2.4, P2.5, P2.6, P2.7, P3.1, P3.2, P3.4, P3.7, P3.8, P4.1, P4.2, P4.3, P4.8 | Graph features over log entities for cross-system detection. |

## Adaptation / calibration / uncertainty

| ID | Title | Year | Venue | Link | Used by | Relevance |
| --- | --- | ---: | --- | --- | --- | --- |
| `S8` | Domain-Adversarial Training of Neural Networks | 2016 | Journal of Machine Learning Research, vol. 17, pp. 1-35 | [link](https://www.jmlr.org/papers/v17/15-239.html) | P2.1 | Adversarial domain adaptation, enabled only after a pre-declared diagnostic. |

## Fusion / abstention

| ID | Title | Year | Venue | Link | Used by | Relevance |
| --- | --- | ---: | --- | --- | --- | --- |
| `S9` | SelectiveNet: A Deep Neural Network with an Integrated Reject Option | 2019 | Proceedings of Machine Learning Research, vol. 97 (ICML) | [link](https://proceedings.mlr.press/v97/geifman19a.html) | P1.6, P2.5, P2.7, P3.3, P3.5, P3.7, P3.8, P4.4, P4.5, P4.7, P4.8 | Abstention with an explicit reject option and risk-coverage framing. |

## Baselines

| ID | Title | Year | Venue | Link | Used by | Relevance |
| --- | --- | ---: | --- | --- | --- | --- |
| `S10` | Isolation Forest | 2008 | IEEE International Conference on Data Mining (ICDM) | [link](https://doi.org/10.1109/ICDM.2008.17) | P3.6 | Explicit unsupervised anomaly baseline for P3.6. |

## Publication status

| ID | Status | Note |
| --- | --- | --- |
| `S1` | PEER_REVIEWED | The workbook cites the 2020 arXiv preprint. The peer-reviewed ISSRE 2023 version is the stronger source for the same claim and is recorded as canonical; the preprint URL is retained because the workbook uses it. |
| `S2` | PEER_REVIEWED |  |
| `S3` | PEER_REVIEWED | The workbook attributes this to 'Liu et al.'. Crossref returns the author family names Zhou, Ying, Wang, Zhao. The workbook's Xplore link resolves to the same article; the DOI is added here for durability. |
| `S4` | PREPRINT_NOT_PEER_REVIEWED | Preprint. Design reference only; it establishes no performance for this project. |
| `S5` | PREPRINT_NOT_PEER_REVIEWED | Uses LLaMA-2; it does not validate this project's Llama-3.1-8B choice. |
| `S6` | PEER_REVIEWED |  |
| `S7` | PREPRINT_LATER_PEER_REVIEWED |  |
| `S8` | PEER_REVIEWED | The workbook's year 2015 is the preprint; the JMLR version is 2016. Both are recorded. |
| `S9` | PEER_REVIEWED |  |
| `S10` | PEER_REVIEWED |  |
| `S11` | VENDOR_DOCUMENTATION | Vendor documentation, not peer-reviewed. Correct for licence and revision provenance only. |
| `S12` | PEER_REVIEWED |  |
| `S13` | PEER_REVIEWED |  |
| `S14` | PEER_REVIEWED |  |
| `S15` | PEER_REVIEWED |  |
| `S16` | PUBLISHED_DATASET |  |
| `S17` | SOFTWARE_REPOSITORY |  |

## Historical sources

Retained for provenance; not cited by active work.

| ID | Title | Year | Link |
| --- | --- | ---: | --- |
| `H1` | Deep learning for anomaly detection in log data: A survey | 2023 | [link](https://doi.org/10.1016/j.mlwa.2023.100470) |

## Reference support gaps

### RSG-001

**Claim.** The temporal graph expert is referred to as 'GTAT' in the workbook (P2.4, EXP-GTAT-001).

**Problem.** S6 (LogGT) is a real, verified and relevant cross-system graph paper, but it presents a heterogeneous graph feature with transfer learning. It does not establish the acronym or formulation 'GTAT'.

**Affects.** P2.4, P2.5, P4.3 · resolve before P2.4 write-up (specification required before training)

**Action.** Either cite the specific source of the GTAT formulation, or state plainly that GTAT is a SeqLogAD architectural decision informed by S6.

Methodology changed: `False`.
