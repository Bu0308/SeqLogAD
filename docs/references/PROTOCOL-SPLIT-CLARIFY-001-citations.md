# PROTOCOL-SPLIT-CLARIFY-001 — Sources and Search Record

This note records the external sources retained for the exact split-semantics
clarification. It contains no SeqLogAD experimental result. Search and
screening were completed before real partition generation.

## 1. Reproducible targeted search

| Field | Value |
|---|---|
| Search date | 2026-08-22 |
| Coverage target | 2024-01-01 through 2026-08-22; older work only when source-defining |
| Priority | 2026, then 2025, then 2024 |
| Sources searched | publisher/DOI pages, ACM/PACMSE, MDPI, Springer Nature, IEEE/IFIP Open Digital Library, arXiv, OpenReview, author/institutional accepted manuscripts |
| Snowballing | backward from retained recent methods and forward/current related-work inspection where available |

Representative queries:

- `2026 HDFS BGL log anomaly block_id session chronological split window 100`
- `Investigating the Impact of Log-Sequence Embeddings anomaly detection HDFS BGL split`
- `ContraLog sequential split leakage HDFS BGL 2026`
- `2025 HDFS BGL anomaly detection chronological shuffled split`
- `LogSD HDFS BGL fixed entry 100 logs chronological 80 20`
- `BGL split raw messages before window temporal leakage`
- `HDFS session split no session across partitions`
- `BGL incomplete trailing window discarded fixed non-overlapping`

Inclusion criteria:

1. HDFS/BGL sequence construction or allocation is stated in the paper;
2. source is peer-reviewed, or a recent primary preprint is clearly labeled;
3. full method text, official publisher metadata, DOI record, or an
   institution-hosted accepted/published manuscript is available;
4. the source directly informs grouping, chronology, boundary leakage,
   windows, residuals, or protocol sensitivity.

Exclusion criteria:

- blogs, SEO pages, AI summaries, and secondary paraphrases;
- papers that mention HDFS/BGL but do not expose relevant grouping/split
  methods;
- implementation repositories used as substitutes for papers;
- recent preprints with no additional split evidence beyond stronger retained
  sources;
- results whose dataset variant/preprocessing could not be distinguished.

Rejected/not retained examples include unrelated 2026 graph-anomaly surveys,
methods that only list benchmark names, and HDFS-only preprints that add no
verifiable split detail. They are not evidence for this contract.

## 2. Retained source inventory

### S1 — Alzahrani (2026)

- **Title:** Investigating the Impact of Log-Sequence Embeddings on Anomaly
  Detection: A Systematic Study
- **Author:** Musaad Alzahrani
- **Year / venue:** 2026, *Information*, 17(3), 228
- **DOI:** [10.3390/info17030228](https://doi.org/10.3390/info17030228)
- **Official URL:** [MDPI publisher page](https://www.mdpi.com/2078-2489/17/3/228)
- **Publication status:** peer-reviewed journal article; published 27 February
  2026
- **Dataset variant:** HDFS, BGL, and Thunderbird benchmark sequences as
  described by the article; equivalence to every SeqLogAD raw byte is not
  assumed
- **Exact methodological support:** HDFS messages are sessionized by
  `block_id`; no HDFS session is split. BGL/Thunderbird raw messages are first
  partitioned chronologically 60/20/20 and then formed into fixed,
  non-overlapping 100-message windows. The paper explicitly connects this
  ordering to preventing windows from crossing split boundaries and temporal
  leakage. Incomplete trailing windows are discarded. It also evaluates 50 and
  200-event BGL windows.
- **Compatibility:** strongest direct support for HDFS atomic sessions, BGL
  raw split-before-window, non-overlap, 100 as a reasonable setting, and
  incomplete-tail exclusion.
- **Limitations for SeqLogAD:** HDFS split is label-stratified; ratios are
  60/20/20; sessions may be truncated/padded for modeling. These details are
  not adopted. It does not define connected-component purge, cumulative floor,
  five residuals, hashing, or TEST sealing.

### S2 — Landauer, Skopik, and Wurzenberger (2024)

- **Title:** A Critical Review of Common Log Data Sets Used for Evaluation of
  Sequence-Based Anomaly Detection Techniques
- **Authors:** Max Landauer, Florian Skopik, Markus Wurzenberger
- **Year / venue:** 2024, *Proceedings of the ACM on Software Engineering*,
  FSE, Article 61
- **DOI:** [10.1145/3660768](https://doi.org/10.1145/3660768)
- **Official/author URL:** [author-hosted published manuscript](https://www.skopik.at/ait/2024_fse.pdf)
- **Publication status:** peer-reviewed ACM journal/conference issue article
- **Dataset variant:** six public log datasets, including HDFS/BGL variants
  analyzed by the paper
- **Exact methodological support:** dataset construction and preprocessing can
  dominate sequence-anomaly conclusions; HDFS raw lines may contain block
  identifiers used for session construction; simple signals expose benchmark
  suitability risks.
- **Compatibility:** supports conservative, falsifiable protocol choices and
  explicit grouping/provenance rather than assuming benchmark suitability.
- **Limitations:** does not prescribe SeqLogAD's five-way chronology, floor
  boundaries, purge, residual, hash, or seal algorithms.

### S3 — Xie, Zhang, and Babar (2024), LogSD

- **Title:** LogSD: Detecting Anomalies from System Logs through
  Self-Supervised Learning and Frequency-Based Masking
- **Authors:** Yongzheng Xie, Hongyu Zhang, Muhammad Ali Babar
- **Year / venue:** 2024, *Proceedings of the ACM on Software Engineering*,
  FSE, Article 93
- **DOI:** [10.1145/3660800](https://doi.org/10.1145/3660800)
- **Official URL:** [ACM DOI page](https://dl.acm.org/doi/10.1145/3660800)
- **Accessible manuscript:** [University of Adelaide repository](https://digital.library.adelaide.edu.au/items/28353949-8bd1-4dff-bd9f-b2e7f329404b)
- **Publication status:** peer-reviewed ACM journal/conference issue article
- **Dataset variant:** public HDFS/BGL/Spirit transformed under the paper's own
  preprocessing
- **Exact methodological support:** HDFS uses BlockId sessions and random
  80/20 sequence allocation. BGL uses initial 80% messages for training and
  later 20% for testing, motivated as chronological leakage prevention. BGL is
  evaluated with fixed-entry sizes 20, 60, and 100.
- **Compatibility:** corroborates HDFS block grouping, BGL chronology, and
  fixed-entry/100-event windows as established choices.
- **Limitations:** random HDFS split conflicts with SeqLogAD; no separate
  validation/TEST contract; BGL consecutive duplicates are removed before
  grouping, which SeqLogAD does not copy; incomplete-tail handling is not the
  primary retained evidence.

### S4 — Dietz, Klede, Nguyen, and Eskofier (2026), ContraLog

- **Title:** ContraLog: Log File Anomaly Detection with Contrastive Learning
  and Masked Language Modeling
- **Authors:** Simon Dietz, Kai Klede, An Nguyen, Bjoern M. Eskofier
- **Year / venue:** 2026, arXiv/OpenReview manuscript
- **Identifier:** [arXiv:2602.03678](https://arxiv.org/abs/2602.03678)
- **Official review URL:** [OpenReview manuscript](https://openreview.net/pdf?id=jOTc6bolV5)
- **Publication status:** preprint / review manuscript; peer-reviewed
  publication was not verified at the search cutoff
- **Dataset variant:** paper-specific HDFS/BGL/Thunderbird preprocessing and
  parser-free representation
- **Exact methodological support:** sequences are allocated in sequential order
  using 60/5/30/5 train/validation/test/reference partitions; oldest sequences
  train and newest test, with a stated real-world/leakage rationale.
- **Compatibility:** corroborates chronological allocation as a current
  methodological choice.
- **Limitations:** preprint status; different ratios; anomalous sequences are
  removed from development partitions and normal TEST samples are balanced,
  so its label-use policy is incompatible. Some parser fitting in compared
  baselines is not SeqLogAD's train-only parser contract.

### S5 — Sedláček, Žádník, and Bartoš (2025)

- **Title:** Anomaly Detection in Log Data: A Comparative Study
- **Authors:** Ondřej Sedláček, Martin Žádník, Václav Bartoš
- **Year / venue:** 2025, 21st International Conference on Network and Service
  Management (CNSM)
- **DOI:** [10.23919/CNSM67658.2025.11297503](https://doi.org/10.23919/CNSM67658.2025.11297503)
- **Official full text:** [IFIP Open Digital Library](https://dl.ifip.org/db/conf/cnsm/cnsm2025/1571164872.pdf)
- **Publication status:** peer-reviewed conference paper
- **Dataset variant:** HDFS, BGL, Thunderbird variants explicitly compared;
  multiple HDFS preprocessing variants are distinguished
- **Exact methodological support:** shows that preprocessing, grouping, and
  shuffled versus sequential evaluation materially change conclusions. Its
  sequential folds preserve time-contiguous train/validation/test segments;
  its other experiment family uses shuffled cross-validation.
- **Compatibility:** directly supports treating chronology/grouping as a
  pre-registered design variable and retaining conflicting protocols.
- **Limitations:** does not specify SeqLogAD's five-way floor split; BGL grouping
  includes component/time-entry alternatives; metrics/results are external and
  are not transferred to SeqLogAD.

### S6 — Li, Shi, and van Leeuwen (2026), Logs2Graphs

- **Title:** Graph Neural Networks Based Log Anomaly Detection and Explanation
- **Authors:** Zhong Li, Jiayang Shi, Matthijs van Leeuwen
- **Year / venue:** 2026, *Data Mining and Knowledge Discovery*, 40, Article 66
- **DOI:** [10.1007/s10618-026-01235-6](https://doi.org/10.1007/s10618-026-01235-6)
- **Official URL:** [Springer Nature](https://link.springer.com/article/10.1007/s10618-026-01235-6)
- **Publication status:** peer-reviewed journal article; published 3 July 2026
- **Dataset variant:** HDFS/Hadoop/BGL/Spirit/Thunderbird under graph grouping
  defined by the paper
- **Exact methodological support:** HDFS is grouped by `block_id`; BGL is
  grouped by node. For Spirit/Thunderbird, every 100 consecutive logs per user
  form a group and a final group shorter than 100 is retained.
- **Compatibility:** corroborates current HDFS block grouping and provides a
  recent, peer-reviewed alternative to BGL fixed windows/residual deletion.
- **Limitations:** its BGL node grouping and retained short groups are not
  SeqLogAD's protocol; it does not establish chronology-first five-way
  allocation.

## 3. Evidence boundaries

External methods/results above remain `EXTERNAL_RESULT`. SeqLogAD has no split,
TEST assignment, parser output, baseline/model result, or metric. Exact source
variants and preprocessing differ, so no published score or anomaly prevalence
is transferred to the accepted SeqLogAD bytes.

No retained source establishes the following as universal or novel:

- `60/10/10/10/10`;
- cumulative-floor boundaries;
- META-001 connected-component boundary purge;
- five-partition residual exclusions;
- canonical split/partition/assignment hashing;
- physical TEST sealing.

Those are explicitly `SEQLOGAD_PROTOCOL_DECISION` or, where a general principle
is externally supported, `LITERATURE_INFORMED_SEQLOGAD_DECISION`.

## 4. Freshness statement

- Newest directly relevant source found: **2026**.
- Newest peer-reviewed directly relevant source: **2026**.
- Newest retained HDFS method evidence: **2026**.
- Newest retained BGL method evidence: **2026**.

The strongest exact BGL split-before-window evidence is S1. The strongest
current conflict evidence is S5/S6. The 2024 sources remain because their
methodological relevance exceeds merely newer but unrelated papers.
