# PARSE-001 — Literature and implementation provenance

Status: `VERIFIED 2026-08-23`  
Scope: normal-only `BASE_TRAIN` selection, Drain3 fit/freeze semantics, parser
configuration provenance, and representation-leakage controls. This note does
not report a SeqLogAD anomaly-detection result.

## Evidence boundary

- `EXTERNAL RESULT` means a claim reported by an external source.
- `SEQLOGAD DECISION` means a pre-registered protocol or engineering choice.
- No reviewed source proves that SeqLogAD's exact masks, parameters,
  normal-selection granularity, or unknown-event policy are optimal.
- No paper result below is a `SEQLOGAD RESULT`; scientific experiments remain
  `NOT_RUN`.

## Source records

### Drain3 official implementation documentation

- **Title:** Drain3 — A robust streaming log template miner based on the Drain
  algorithm
- **Authors/maintainer:** LogPAI project contributors
- **Year/venue:** living official software repository; accessed 2026-08-23
- **DOI:** none
- **Official URL:** <https://github.com/logpai/Drain3>
- **Publication status:** primary implementation documentation/source
- **Exact support:** `TemplateMiner.add_log_message` is the training path and
  can create a cluster or change an existing template; `TemplateMiner.match`
  uses learned clusters without creating or modifying them; persistence stores
  and restores the search tree, clusters, message counts, and cluster IDs.
- **Compatibility:** directly supports the explicit separation between
  mutating fit and read-only frozen transform implemented in PARSE-001.
- **Caveat:** it does not prescribe SeqLogAD's data split, normal-only pool,
  masks, parameter values, hashes, or TEST policy.

### Drain

- **Title:** Drain: An Online Log Parsing Approach with Fixed Depth Tree
- **Authors:** Pinjia He, Jieming Zhu, Zibin Zheng, Michael R. Lyu
- **Year/venue:** 2017, IEEE International Conference on Web Services (ICWS)
- **DOI:** <https://doi.org/10.1109/ICWS.2017.13>
- **Official author PDF:**
  <https://pinjiahe.github.io/files/pdf/research/ICWS17.pdf>
- **Publication status:** peer reviewed
- **Exact support:** defines the fixed-depth online Drain parser family and its
  similarity/tree-based template-mining rationale.
- **Compatibility:** supports choosing an established online structured-log
  parser rather than inventing a parser for this project.
- **Caveat:** the paper predates Drain3's current software API and does not
  establish the exact SeqLogAD fit/freeze protocol.

### Impact of Log Parsing on Deep Learning-Based Anomaly Detection

- **Authors:** Zanis Ali Khan, Donghwan Shin, Domenico Bianculli, Lionel C.
  Briand
- **Year/venue:** 2024, *Empirical Software Engineering* 29, article 139
- **DOI:** <https://doi.org/10.1007/s10664-024-10533-w>
- **Official open-access record/PDF:**
  <https://eprints.whiterose.ac.uk/id/eprint/216228/>
- **Publication status:** peer reviewed
- **Exact external result:** evaluates 13 parsers and seven anomaly detectors on
  three public datasets and shows that parser output properties can materially
  affect downstream anomaly-detection accuracy; parser accuracy alone is not a
  sufficient proxy for downstream usefulness.
- **Compatibility:** supports freezing parser representation choices before
  scientific outcome evaluation and treating parser state/config as provenance.
- **Caveat:** it does not by itself prove that fitting a parser on all
  partitions is leakage in every design, nor that normal-only `BASE_TRAIN` is
  the uniquely correct policy.

### A Comprehensive Study of Machine Learning Techniques for Log-Based Anomaly Detection

- **Authors:** Shan Ali, Chaima Boufaied, Domenico Bianculli, Paula Branco,
  Lionel Briand
- **Year/venue:** 2025, *Empirical Software Engineering* 30, article 129
- **DOI:** <https://doi.org/10.1007/s10664-025-10669-3>
- **Official URL:** <https://doi.org/10.1007/s10664-025-10669-3>
- **Publication status:** peer reviewed
- **Exact support used here:** recent comparative context showing that data
  processing, representation, supervision, and evaluation protocol are material
  parts of a log-anomaly experiment rather than neutral implementation details.
- **Compatibility:** supports explicit representation provenance and controlled
  comparisons.
- **Caveat:** no exact normal-only Drain3 freeze rule is attributed to this
  study.

### Anomaly Detection in Log Data: A Comparative Study

- **Authors:** Ondřej Sedláček, Martin Žádník, Václav Bartoš
- **Year/venue:** 2025, International Conference on Network and Service
  Management (CNSM)
- **DOI:** <https://doi.org/10.23919/CNSM67658.2025.11297503>
- **Official PDF:**
  <https://dl.ifip.org/db/conf/cnsm/cnsm2025/1571164872.pdf>
- **Publication status:** peer reviewed
- **Exact support used here:** recent comparative context for preprocessing and
  evaluation choices in log anomaly detection.
- **Compatibility:** reinforces the need to report parser and representation
  contracts explicitly.
- **Caveat:** it is not treated as direct proof of SeqLogAD's exact
  train-fitted, normal-only policy.

### Investigating the Impact of Log-Sequence Embeddings on Anomaly Detection: A Systematic Study

- **Author:** Musaad Alzahrani
- **Year/venue:** 2026, *Information* 17(3), article 228
- **DOI:** <https://doi.org/10.3390/info17030228>
- **Official URL:** <https://www.mdpi.com/2078-2489/17/3/228>
- **Publication status:** peer reviewed
- **Exact external result:** systematically compares template-ID, semantic, and
  hybrid sequence representations with several model heads and analyzes parser,
  sequence-length, and out-of-vocabulary effects.
- **Compatibility:** supports making representation identity and unknown/OOV
  behavior explicit.
- **Caveat:** it does not establish that `EVT_UNSEEN`, SeqLogAD's masks, or its
  exact normal pool are optimal.

### Controlled Granularity Tuning for Log-Based Anomaly Detection in Converged HPC-Cloud Environments

- **Authors:** Dumo Ngwenya, Dhouha Kbaier, Patrick Wong
- **Year/venue:** 2026, Workshops of the 40th ACM International Conference on
  Supercomputing
- **DOI:** <https://doi.org/10.1145/3774895.3813788>
- **Publication status:** peer reviewed
- **Exact external result:** controlled parser-threshold experiments report
  that parser-induced template granularity affects downstream detector results
  and that the relationship need not be monotonic.
- **Compatibility:** strengthens the requirement to freeze and hash parser
  configuration before anomaly outcomes are observed.
- **Caveat:** this source studies deliberate threshold tuning; PARSE-001 does
  not reproduce that tuning and does not call its default configuration optimal.

## Evidence matrix

| Parser decision | Classification | Source | Exact support and limit |
|---|---|---|---|
| Use structured Drain-family parsing | `LITERATURE_SUPPORTED` | Drain 2017; Drain3 official repository | Established online template-mining family and current implementation semantics |
| Separate mutating fit from frozen transform | `LITERATURE_SUPPORTED` for software behavior; `LITERATURE_INFORMED_SEQLOGAD_DECISION` for experiment boundary | Drain3 official repository; Khan et al. 2024 | `add_log_message` mutates/learns while `match` does not; parser representation affects downstream results |
| No TEST fitting or parser selection | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | Khan et al. 2024; recent comparative studies | Representation can affect outcomes, so SeqLogAD applies its frozen leakage-control principle; no reviewed source found proves this exact implementation rule universally |
| Fit only normal `BASE_TRAIN` | `SEQLOGAD_PROTOCOL_DECISION` | — | Frozen supervision/access contract; direct recent evidence for this exact rule was insufficient |
| HDFS whole-component normal selection | `SEQLOGAD_PROTOCOL_DECISION` | official HDFS label granularity documented elsewhere | Preserves session-level labels; exact all-member rule belongs to SeqLogAD |
| BGL normal-event selection within complete BASE windows | `SEQLOGAD_PROTOCOL_DECISION` | official BGL inline-label semantics documented elsewhere | Exact event-level filtering rule belongs to SeqLogAD |
| Freeze after fit and restore independently | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | Drain3 official persistence documentation | Drain3 supports save/restore; exact one-fit/non-overwrite workflow is project-owned |
| `EVT_UNSEEN` for no frozen match | `SEQLOGAD_PROTOCOL_DECISION` | Drain3 official repository | Drain3 `match` may return `None`; the stable event ID is SeqLogAD-owned |
| Drain3 0.9.11, similarity 0.4, depth 4, max children 100, no cluster cap | `OFFICIAL_DEFAULT` / `SEQLOGAD_PROTOCOL_DECISION` | Drain3 default configuration | Pre-registered defaults, not tuned and not claimed optimal |
| Block/IP/hex masks and intentionally unmasked fields | `LITERATURE_INFORMED_SEQLOGAD_DECISION` / `SEQLOGAD_PROTOCOL_DECISION` | Drain/Drain3 masking mechanism | Masking capability is supported; exact regexes and semantic boundary are project-owned |
| BGL empty content sentinel | `SEQLOGAD_PROTOCOL_DECISION` | — | Fail-safe deterministic handling of a source-format edge case discovered before real fit |
| Canonical config, normal-pool, scientific-state, registry, and file SHA-256 identities | `SEQLOGAD_PROTOCOL_DECISION` | — | Reproducibility/integrity engineering; no scientific superiority claim |
| Exact configuration is optimal | `INSUFFICIENT_EVIDENCE` | — | This claim is explicitly not made |

## Search log and freshness

- **Search date:** 2026-08-23.
- **Priority window:** 2026, 2025, 2024; older Drain paper retained as the
  parser-defining source.
- **Sources searched:** publisher/DOI pages, official author repositories/PDFs,
  and the official Drain3 repository/source.
- **Queries included:** `Drain3 training inference match add_log_message
  persistence`, `log parser train split leakage anomaly detection`, `impact log
  parsing anomaly detection 2024`, `log anomaly parser granularity 2025 2026`,
  and `normal-only parser fitting log anomaly detection`.
- **Newest directly relevant parser/granularity source found:** Ngwenya,
  Kbaier, and Wong (2026).
- **Newest representation-focused log-anomaly source found:** Alzahrani (2026).
- **Newest peer-reviewed source directly proving SeqLogAD's exact leakage-safe
  normal-only parser procedure:** none found; support remains indirect and the
  rule is not presented as a literature fact.
- **Primary implementation source:** official LogPAI Drain3 repository and
  source.
- **Contradiction check:** no reviewed newer source requires fitting Drain3 on
  validation or TEST. Recent work emphasizes parser/representation sensitivity,
  which is compatible with pre-registration, but does not prove the exact
  SeqLogAD configuration.

