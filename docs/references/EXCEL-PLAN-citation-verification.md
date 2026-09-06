# Citation verification — `Bang_ke_hoach_SeqLogAD.xlsx` `Research Sources`

Date: 2026-09-06 · Workbook SHA-256 `c33aad3333c0d1b032ad324459392f2e5da4b65eb85603d80c2130dfd174d56b`

Every `S#` key in the workbook was resolved against an authoritative metadata service
rather than accepted as written: Crossref (`api.crossref.org`) for DOIs and the arXiv
API (`export.arxiv.org`) for preprints. The "resolved title" column is what the
service returned, not what the workbook says.

| Key | Workbook label | Verification | Resolved title / venue | Verdict |
| --- | --- | --- | --- | --- |
| S1 | Loghub — Zhu et al. (2020) | arXiv API, `2008.06448` | *Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics*, published 2020-08-14 | **Verified** |
| S2 | Drain — He et al. (2017) | Crossref, `10.1109/ICWS.2017.13` | *Drain: An Online Log Parsing Approach with Fixed Depth Tree*, IEEE ICWS 2017 | **Verified** |
| S3 | LogDLR — Liu et al. (2025) | Crossref title search (IEEE Xplore returns HTTP 418 to non-browser clients) | *LogDLR: Unsupervised Cross-System Log Anomaly Detection Through Domain-Invariant Latent Representation*, IEEE TDSC, 2025-07, DOI `10.1109/TDSC.2025.3548050` | **Verified** — the workbook's Xplore link is correct; add the DOI for durability |
| S4 | ZeroLog — Zhao et al. (2025) | arXiv API, `2511.05862` | *ZeroLog: Zero-Label Generalizable Cross-System Log-based Anomaly Detection*, published 2025-11-08 | **Verified** — preprint; the workbook already marks it as a design reference only |
| S5 | LogLLaMA — Yang & Harris (2025) | arXiv API, `2503.14849` | *LogLLaMA: Transformer-based log anomaly detection with LLaMA*, published 2025-03-19 | **Verified** — preprint; uses LLaMA-2, so it does not validate this project's Llama-3.1 choice, exactly as the workbook's use boundary states |
| S6 | LogGT — Wang et al. (2024) | Crossref, `10.1016/j.eswa.2024.124082` | *LogGT: Cross-system log anomaly detection via heterogeneous graph feature and transfer learning*, Expert Systems with Applications 2024 | **Verified with a note** — see below |
| S7 | LoRA — Hu et al. (2021) | arXiv API, `2106.09685` | *LoRA: Low-Rank Adaptation of Large Language Models*, published 2021-06-17 | **Verified** |
| S8 | DANN — Ganin et al. (2015) | arXiv API, `1505.07818` | *Domain-Adversarial Training of Neural Networks*, published 2015-05-28 | **Verified** — the workbook's "JMLR / arXiv" type is accurate (JMLR 2016 journal version) |
| S9 | SelectiveNet — Geifman & El-Yaniv (2019) | PMLR URL, HTTP 200 | PMLR v97 (ICML 2019) | **Verified** |
| S10 | Isolation Forest — Liu et al. (2008) | Crossref, `10.1109/ICDM.2008.17` | *Isolation Forest*, IEEE ICDM 2008 | **Verified** |
| S11 | Meta Llama 3.1 (2024) | Official Meta URL, HTTP 200 | Meta Llama 3.1 release page | **Verified** — vendor page, not peer-reviewed; correct for licence/revision provenance |

## Note on S6

The workbook describes S6 as supplying the "Event/component/time graph and GTAT
direction". The resolved paper is about a **heterogeneous graph feature with transfer
learning** for cross-system log anomaly detection. It is a legitimate and relevant
graph-based cross-system reference, and the workbook's use boundary ("architecture
reference; results are not copied into this project") is honoured. But the acronym
"GTAT" as used in the plan is *not* established by this citation. When P2.7 is
written up, either cite the specific source of the GTAT formulation or state plainly
that GTAT is a SeqLogAD architectural decision informed by S6.

Classification: `LITERATURE_INFORMED_SEQLOGAD_DECISION`, not `LITERATURE_SUPPORTED`.

## Dataset licence verification

The Loghub Zenodo record `10.5281/zenodo.8196385` was queried directly. Its metadata
reports `license: cc-by-4.0` and `access_right: open`. The published MD5 digests for
`HDFS_v1.zip` (`76a24b4d9a6164d543fb275f89773260`) and `BGL.zip`
(`4452953c470f2d95fcb32d5f6e733f7a`) match the values already recorded in
`configs/datasets/{hdfs,bgl}.yaml`, which independently corroborates the existing
acquisition contracts.

The two architectures added for P1.2 were downloaded from the same record and their
digests were recomputed locally:

| Archive | Published MD5 | Recomputed MD5 | Match |
| --- | --- | --- | --- |
| `OpenStack.tar.gz` | `66bd42c07837a094d9b0ea2d036b5713` | `66bd42c07837a094d9b0ea2d036b5713` | yes |
| `Hadoop.zip` | `34e28a9943704fd54933e2b455829fcc` | `34e28a9943704fd54933e2b455829fcc` | yes |

## Evidence classification for Phase 1 decisions

| Statement | Classification |
| --- | --- |
| Loghub distributes these four corpora under CC-BY-4.0 with the stated digests | `LITERATURE_SUPPORTED` (Zenodo record metadata) |
| Cross-system transfer with a domain-invariant representation is an active research direction | `LITERATURE_SUPPORTED` (S3) |
| A zero-label target protocol is a coherent research design | `LITERATURE_INFORMED_SEQLOGAD_DECISION` (S4, a preprint) |
| An architecture is a distinct log-producing system, not an EventID grouping | `SEQLOGAD_PROTOCOL_DECISION` |
| Segment fractions 50 / 5 / 15 / 30 | `SEQLOGAD_PROTOCOL_DECISION` |
| Cut selection minimises records displaced from the nominal segment | `SEQLOGAD_PROTOCOL_DECISION` |
| A grouping unit crossing a cut is excluded from every partition | `SEQLOGAD_PROTOCOL_DECISION` |
| The burn-in buffer is a label-blind chronological prefix | `SEQLOGAD_PROTOCOL_DECISION` (required by the workbook's P1.6 DoD) |
| Declared contamination bound of 5% | `SEQLOGAD_PROTOCOL_DECISION` — an assumption, not a measurement |
| `seqlogad-nul-escape-v1` codec | `SEQLOGAD_PROTOCOL_DECISION`, reused verbatim from `CANONICAL-NUL-DECISION-001` |
| The specific masking regexes in `NORM-CS-001` | `ENGINEERING_DECISION` |
| `array.array` accumulation, Arrow zero-copy, Parquet stream index | `ENGINEERING_DECISION` |
| OpenStack is source-only | `SEQLOGAD_PROTOCOL_DECISION`, derived from an observed label-blind property of the raw capture structure |

Nothing in this file was inferred. Each row is backed by a service response recorded
on 2026-09-06 or by a digest recomputed locally.
