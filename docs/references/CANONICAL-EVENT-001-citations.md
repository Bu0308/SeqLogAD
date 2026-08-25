# CANONICAL-EVENT-001 — Canonical Event Transformation Evidence Note

| Field | Value |
|---|---|
| Task | `CANONICAL-EVENT-001-EVIDENCE` |
| Role | T2 Literature & Evidence |
| Search/access date | 2026-08-24 |
| Review type | Small targeted current-evidence check; not a systematic-review or novelty claim |
| Frozen scientific version | Protocol `PROTOCOL-001` v1.1; `EFFECT-001` v1.0; parser contract `PARSE-001` v1.0 |
| Empirical status | `NOT_RUN`; no scientific metric computed |
| TEST status | HDFS and BGL `SEALED / NEVER_OPENED`; no TEST data, labels, counts, previews, or metrics accessed |

## Scope and evidence boundary

This note checks only four questions needed by canonical event transformation:

1. whether inference through a frozen parser should be non-mutating;
2. how Drain/Drain3 distinguish training from matching;
3. whether fitted preprocessing and representation state must be learned only from training data; and
4. which HDFS/BGL parsing and grouping practices are externally documented.

External evidence is recorded below newest-first. It supports or contextualizes the already-frozen SeqLogAD design; it does **not** define SeqLogAD's five-way split, normal-pool policy, masks, parser parameters, event digest, `EVT_UNSEEN`, TEST policy, or any scientific gate. No protocol, code, configuration, dataset, split, parser state, or gate was changed by this task.

## Frozen local inputs checked read-only

| Input | SHA-256 | Relevant frozen fact |
|---|---|---|
| `docs/research-protocol-v1.1.md` | `57fae10dd2e55a10fadc1fe6cb3418d9725aaa7b884bf4b0bd82b884981caa2a` | Fit Drain3 only on authorized normal `BASE_TRAIN`; transform later permitted partitions read-only; reserve `EVT_UNSEEN`; TEST cannot inform parsing. |
| `configs/protocols/protocol-v1.1.yaml` | `c75db25f8e496fcc7c1fd6cecf90838bde84827b2fd3bc108748e85af28ba4ea` | Active frozen Protocol v1.1 machine contract. |
| `configs/protocols/effect-001.yaml` | `2ba2fb40ae1fb6c8224bbf196e3ace7d67b16b5196c256370f1b7b58411dddfe` | Frozen EFFECT-001 remains unchanged and outside this evidence task. |
| `configs/parsing/drain3-v1.yaml` | `907852b75740faf8ff19ba423d62c6347104594baeff1dafbbb1cf80de19cac9` | Drain3 `0.9.11`; `BASE_TRAIN` normal-only fit; `FROZEN_READ_ONLY`; frozen normalization/masking and identity rules. |
| `src/seqlogad/parsing/drain_parser.py` | `bc6a9afd85818519fe0c24d846a6a53f49d7de46674d07fa9dc03a17eab7efeb` | Existing frozen wrapper calls `TemplateMiner.match`, checks state before/after, and does not expose mutating inference. |
| HDFS parser manifest | `35400de68ede9907a4f2d3445125bdc27ae434c61dcf2f93c48b825b4000a025` | `FIT_COMPLETED_FROZEN`; normal `BASE_TRAIN`; `test_accessed=false`; parser state `7d9bd804...da8d91`; registry `054c9363...421ccb`. |
| BGL parser manifest | `bc2fd7df13ee231c0e9e63597e3237cd48ebb1658c4609524f04087cf49cfd66` | `FIT_COMPLETED_FROZEN`; normal `BASE_TRAIN`; `test_accessed=false`; parser state `e44649d2...6aee4f6`; registry `bc4ac9e2...47d17f`. |
| HDFS / BGL TEST seals | `a07330861b42821e20b44724e80ddd86c7dbb362916bc50be67b1ebe65c70658` / `f474006fea58f8e3e8e7e3e2c1f2af2faf7694069ac403da4c9a8da8dbbdc2d8` | Both report `status=SEALED`, `never_opened=true`, `open_count=0`, `unlock_records=0`. |

Ellipses in the two manifest summaries are display abbreviations only; the exact manifest-file hashes above identify the complete inputs.

## External evidence — peer-reviewed sources, newest first

### CE-CITE-001 — Current HDFS/BGL representation and sequence practice

- **Title:** *Investigating the Impact of Log-Sequence Embeddings on Anomaly Detection: A Systematic Study*
- **Authors:** Musaad Alzahrani
- **Year / venue:** 2026, *Information* 17(3), article 228
- **DOI / official URL:** https://doi.org/10.3390/info17030228
- **Publication status:** `PEER_REVIEWED / PUBLISHED 2026-02-27 / VERIFIED ON PUBLISHER RECORD`
- **Exact supported claim:** The study represents raw logs as parsed templates and template-ID sequences; uses HDFS `block_id` sessions; uses chronological, non-overlapping 100-message BGL windows created after splitting; keeps a fixed Drain parsing backbone for its main comparisons; builds the template vocabulary from the training split; and explicitly handles OOV templates.
- **SeqLogAD relevance:** This is current corroboration for treating parsing/vocabulary as a fitted representation, preserving HDFS session identity, avoiding BGL windows across split boundaries, and making unseen-template behavior explicit.
- **Limitation:** The paper's 60/20/20 split, HDFS label-stratified partitioning, pre-parsed HDFS templates, discarded residual BGL windows, model supervision, and evaluation policy are not SeqLogAD's frozen protocol. It does not establish SeqLogAD's `BASE_TRAIN` normal-only fit, five-way split, `EVT_UNSEEN`, or TEST seal.
- **Classification:** `LITERATURE_SUPPORTED`
- **Access date:** 2026-08-24

### CE-CITE-002 — Fitted preprocessing leakage

- **Title:** *Overview of Leakage Scenarios in Supervised Machine Learning*
- **Authors:** L. Sasse; E. Nicolaisen-Sobesky; J. Dukart; S. B. Eickhoff; M. Götz; S. Hamdan; V. Komeyer; A. Kulkarni; J. M. Lahnakoski; B. C. Love; F. Raimondo; Kaustubh R. Patil
- **Year / venue:** 2025, *Journal of Big Data* 12, article 135
- **DOI / official URL:** https://doi.org/10.1186/s40537-025-01193-8
- **Publication status:** `PEER_REVIEWED / PUBLISHED 2025-05-29 / VERIFIED ON PUBLISHER RECORD`
- **Exact supported claim:** Estimating preprocessing parameters on the full dataset invalidates train/test separation because training examples become transformed using test information. The leakage-safe pattern is to learn preprocessing parameters on training data and apply that learned transformation to training and held-out data without refitting.
- **SeqLogAD relevance:** A learned parser template inventory, normalization rule selected from data, vocabulary, or representation mapping is part of the fitted pipeline and must not learn from later partitions. This supports the frozen fit-then-read-only-transform direction.
- **Limitation:** The paper is general ML methodology, not log parsing, and does not prescribe SeqLogAD's normal-only pool, partitions, Drain parameters, event identities, or unknown-event policy.
- **Classification:** `LITERATURE_SUPPORTED`
- **Access date:** 2026-08-24

### CE-CITE-003 — Large-scale parser evaluation and rare-event risk

- **Title:** *A Large-Scale Evaluation for Log Parsing Techniques: How Far Are We?*
- **Authors:** Zhihan Jiang; Jinyang Liu; Junjie Huang; Yichen Li; Yintong Huo; Jiazhen Gu; Zhuangbin Chen; Jieming Zhu; Michael R. Lyu
- **Year / venue:** 2024, ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA 2024), Technical Papers
- **DOI / official URL:** https://doi.org/10.1145/3650212.3652123 ; https://2024.issta.org/details/issta-2024-papers/19/A-Large-Scale-Evaluation-for-Log-Parsing-Techniques-How-Far-Are-We-
- **Publication status:** `PEER_REVIEWED CONFERENCE PAPER / PUBLISHED / VERIFIED ON OFFICIAL VENUE RECORD`
- **Exact supported claim:** Log parsing transforms unstructured messages into structured data used by downstream analysis. On Loghub-2.0, the authors re-evaluate 15 parsers, including Drain, on large datasets including HDFS and BGL, and identify rare system-event logs as especially challenging to parse accurately.
- **SeqLogAD relevance:** Canonical event transformation must preserve parser provenance and expose unmatched/OOV behavior instead of silently growing or rewriting the representation on later data.
- **Limitation:** The paper evaluates parsing quality and scalability, not SeqLogAD's anomaly-detection split, frozen-inference lifecycle, canonical event schema, or `EVT_UNSEEN` mapping. The relevance of explicit unmatched handling is a conservative SeqLogAD interpretation, not a prescription from the paper.
- **Classification:** `LITERATURE_SUPPORTED` (the explicit unmatched/OOV handling in the relevance statement is separately a `LITERATURE_INFORMED_SEQLOGAD_DECISION`)
- **Access date:** 2026-08-24

### CE-CITE-004 — Downstream sensitivity to parsing

- **Title:** *Impact of Log Parsing on Deep Learning-Based Anomaly Detection*
- **Authors:** Zanis Ali Khan; Donghwan Shin; Domenico Bianculli; Lionel C. Briand
- **Year / venue:** 2024, *Empirical Software Engineering* 29(6), article 139
- **DOI / official URL:** https://doi.org/10.1007/s10664-024-10533-w
- **Publication status:** `PEER_REVIEWED / PUBLISHED 2024-08-17 / VERIFIED ON PUBLISHER RECORD`
- **Exact supported claim:** Across multiple parsers and anomaly detectors, downstream anomaly-detection behavior depends materially on properties of the parsing result; the paper finds distinguishability of parsed normal versus abnormal behavior consequential and includes HDFS and a BGL follow-up analysis.
- **SeqLogAD relevance:** Parser configuration, template registry, and event mapping are scientifically material representation state and therefore should be frozen, hashed, and held constant across downstream comparisons.
- **Limitation:** The study does not show that one parser is universally best, does not justify fitting on evaluation data, and does not define SeqLogAD's inference, identity, split, label, or TEST policies.
- **Classification:** `LITERATURE_SUPPORTED`
- **Access date:** 2026-08-24

### CE-CITE-005 — Drain algorithm foundation

- **Title:** *Drain: An Online Log Parsing Approach with Fixed Depth Tree*
- **Authors:** Pinjia He; Jieming Zhu; Zibin Zheng; Michael R. Lyu
- **Year / venue:** 2017, IEEE 24th International Conference on Web Services (ICWS 2017), pp. 33–40
- **DOI / official URL:** https://doi.org/10.1109/ICWS.2017.13
- **Publication status:** `PEER_REVIEWED CONFERENCE PAPER / PUBLISHED 2017-09-07 / VERIFIED ON IEEE-LINKED INSTITUTIONAL RECORD`
- **Exact supported claim:** Drain is an online parser that incrementally groups raw log messages into templates using a fixed-depth parse tree; the original evaluation includes large HDFS and BGL corpora and demonstrates Drain as a log-parsing stage for downstream analysis.
- **SeqLogAD relevance:** Because original Drain is online and incremental, allowing later partitions through the training/update path would change learned cluster/template state. SeqLogAD's frozen inference path prevents that representation drift.
- **Limitation:** The paper's online adaptation is not itself a train/test protocol and does not specify Drain3's `match` API, SeqLogAD's freeze point, exact parameters, event-ID digest, or unknown-event handling.
- **Classification:** `LITERATURE_SUPPORTED` (the frozen-lifecycle inference in the relevance statement is separately a `LITERATURE_INFORMED_SEQLOGAD_DECISION`)
- **Access date:** 2026-08-24

## External evidence — official Drain3/LogPAI sources

### CE-CITE-006 — Drain3 training versus inference behavior

- **Title:** *Drain3 README — Training vs. Inference Modes* (official project documentation)
- **Authors:** LogPAI Drain3 maintainers and contributors
- **Year / venue:** Living project documentation; release section includes Drain3 `0.9.11`; GitHub
- **DOI / official URL:** No DOI; https://github.com/logpai/Drain3/blob/master/README.md#training-vs-inference-modes
- **Publication status:** `OFFICIAL SOFTWARE DOCUMENTATION / NOT PEER_REVIEWED / VERIFIED`
- **Exact supported claim:** `template_miner.add_log_message` may create clusters or change existing templates, whereas `template_miner.match` matches only against already-learned clusters, creates no clusters, changes no templates, and returns `None` when no perfect match exists. The documentation also recommends supplying the unstructured free-text portion after removing structured fields such as timestamp and hostname.
- **SeqLogAD relevance:** This directly verifies the API-level basis for using `TemplateMiner.match` during frozen transformation and for parsing HDFS/BGL `Content` rather than labels or structured metadata.
- **Limitation:** Official API behavior is not an experimental methodology. Drain3 does not choose SeqLogAD's data split, normal filtering, masks, match-search strategy, state assertions, `EVT_UNSEEN`, or stable event identities.
- **Classification:** `ENGINEERING_DECISION`
- **Access date:** 2026-08-24

### CE-CITE-007 — Official HDFS/BGL field extraction practice

- **Title:** *LogPAI logparser Drain benchmark configuration* (official source file)
- **Authors:** LogPAI team and contributors
- **Year / venue:** Living source repository, copyright header 2016–2023; GitHub
- **DOI / official URL:** No DOI; https://github.com/logpai/logparser/blob/main/logparser/Drain/benchmark.py
- **Publication status:** `OFFICIAL REFERENCE IMPLEMENTATION / NOT PEER_REVIEWED / VERIFIED`
- **Exact supported claim:** The reference benchmark describes HDFS as `<Date> <Time> <Pid> <Level> <Component>: <Content>` and BGL as `<Label> <Timestamp> <Date> <Node> <Time> <NodeRepeat> <Type> <Component> <Level> <Content>`, then invokes Drain with dataset-specific preprocessing and parameters.
- **SeqLogAD relevance:** This corroborates separating structured HDFS/BGL fields from parser input and excluding the BGL inline label from message content.
- **Limitation:** The reference benchmark uses 2k samples, different similarity thresholds/preprocessing details, and a continuously updating parser. It does not define SeqLogAD's full-corpus frozen state, masking policy, label boundary, split, or canonical IDs.
- **Classification:** `ENGINEERING_DECISION`
- **Access date:** 2026-08-24

## SeqLogAD decisions — explicitly not supplied by external sources

The following are frozen project decisions. Evidence above supports their direction or documents the chosen API, but no paper is represented as having prescribed the exact choice.

| SeqLogAD decision | Classification | Evidence boundary |
|---|---|---|
| Fit Drain3 once on the authorized normal `BASE_TRAIN` pool and apply the fitted representation unchanged later. | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | General leakage evidence supports train-only fit; normal-only eligibility and exact partition ownership are Protocol v1.1 decisions. |
| Use `TemplateMiner.match` for frozen inference and reject any parser-state mutation. | `ENGINEERING_DECISION` | Drain3 documents non-mutating `match`; SeqLogAD adds state hashing/assertions and fail-closed behavior. |
| Parse only normalized HDFS/BGL `Content`; labels and structured metadata are not parser features. | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | Drain3/LogPAI document free-text extraction; the exact SeqLogAD normalization and exclusion boundary is frozen locally. |
| Map no frozen match to `EVT_UNSEEN` without expanding vocabulary. | `SEQLOGAD_PROTOCOL_DECISION` | Literature motivates explicit rare/OOV handling; the reserved ID and no-expansion semantics are SeqLogAD-owned. |
| Derive scientific event identity from a versioned SHA-256 digest rather than Drain discovery-order cluster numbers. | `SEQLOGAD_PROTOCOL_DECISION` | No retained source prescribes this exact identity scheme. |
| Keep exact masks, Drain3 `0.9.11`, threshold/depth/children, full-search strategy, persistence, and normalization versions fixed. | `SEQLOGAD_PROTOCOL_DECISION` | These are pre-registered parser-contract choices, not results of this evidence check. |
| Deny routine scientific TEST access; TEST cannot update parser, vocabulary, normalization, or event mapping. | `SEQLOGAD_PROTOCOL_DECISION` | Leakage literature supports isolation in general; SeqLogAD's physical seal and human-only final opening are frozen project rules. |
| Preserve HDFS block/session identity and BGL chronology/partition containment. | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | External practice corroborates these units; exact connected-component purge, five-way allocation, 100-event parent/residual rules, and labels remain frozen SeqLogAD decisions. |

No scientific decision changed. No new gate was created.

## Reproducible query and verification log

Searches were evaluated newest-first (`2026`, then `2025`, then `2024`), followed by foundational and official implementation sources where newer peer-reviewed work did not document Drain3 API semantics. Search-engine hits were used only for discovery; retained claims were checked against publisher, official venue, institutional bibliographic, or official repository pages.

| ID | Exact query | Disposition |
|---|---|---|
| Q01 | `2026 2025 2024 peer reviewed log parsing train test leakage frozen parser log anomaly detection HDFS BGL` | Broad discovery; retained only primary records. |
| Q02 | `2025 2024 log parsing benchmark HDFS BGL Drain peer reviewed DOI` | Led to current parser-impact and evaluation records. |
| Q03 | `Drain log parser paper DOI ICWS 2017 HDFS BGL loghub` | Verified foundational Drain paper and DOI. |
| Q04 | `Drain3 official match add_log_message training inference match GitHub documentation` | Verified official train-vs-match semantics. |
| Q05 | `2026 peer reviewed data leakage preprocessing fit training data only machine learning DOI` | Recent leakage discovery. |
| Q06 | `2025 2024 peer reviewed machine learning preprocessing leakage train test transformation fit only training DOI` | Retained 2025 leakage overview. |
| Q07 | `data preprocessing leakage train test fit transformer on training data peer reviewed paper DOI Kaufman Rosset Perlich leakage` | Foundational cross-check; not retained because the 2025 overview directly supports the narrow claim. |
| Q08 | `scikit-learn common pitfalls data leakage fit transform training test official` | Official cross-check; not retained because peer-reviewed support was available. |
| Q09 | `"Investigating the Impact of Log-Sequence Embeddings" "doi"` | Verified 2026 publisher record and DOI. |
| Q10 | `"Investigating the Impact of Log-Sequence Embeddings" authors 2026` | Verified author and publication metadata. |
| Q11 | `Experience Report System Log Analysis for Anomaly Detection HDFS BGL authors DOI 2016` | Dataset/practice cross-check; not retained because Drain and newer direct sources sufficed. |
| Q12 | `Log-based anomaly detection with deep learning How far are we ICSE 2022 DOI HDFS BGL parsing split leakage` | Evaluation-practice cross-check; already covered by `LIT-001`. |
| Q13 | `Loghub large collection system log datasets ISSRE 2023 DOI HDFS BGL` | Dataset provenance cross-check; no new canonical-event decision. |
| Q14 | `Large-scale evaluation log parsing techniques ISSTA 2024 DOI HDFS BGL Loghub 2.0` | Retained ISSTA 2024 official venue record. |
| Q15 | `site:github.com/logpai/logparser HDFS Drain log_format Content` | Verified official HDFS format/reference implementation. |
| Q16 | `site:github.com/logpai/logparser BGL Drain log_format Label Timestamp Date Node Content` | Verified official BGL format/reference implementation. |

### Source-verification actions

- Publisher metadata and relevant methods text checked for CE-CITE-001, CE-CITE-002, and CE-CITE-004.
- Official ISSTA 2024 venue page and DOI checked for CE-CITE-003.
- IEEE-linked institutional bibliographic record and DOI checked for CE-CITE-005.
- Official LogPAI repositories checked for CE-CITE-006 and CE-CITE-007, including the exact `add_log_message`/`match` distinction and HDFS/BGL format entries.
- Duplicate preprint/search-result versions were not promoted when a final publisher or official venue record was available.

## Integrity and stopping statement

- No citation, DOI, publication status, or reported result was invented.
- No external result was imported as a SeqLogAD result.
- No scientific metric, model run, parser refit, canonical event corpus, or sequence was produced.
- Labels were not read during this task; only existing manifest booleans and frozen contract text were inspected.
- TEST remained sealed and unopened.
- The targeted search stopped when each requested question had direct peer-reviewed support or official API/source verification and further candidates did not alter the evidence boundary.
