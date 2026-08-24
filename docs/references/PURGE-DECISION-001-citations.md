# PURGE-DECISION-001 — Citations and Search Record

Search/verification date: **2026-08-24**.

This note distinguishes external evidence from SeqLogAD protocol choices. No
external result is treated as a result for the exact SeqLogAD bytes, split,
parser, or models. SeqLogAD still has no scientific performance result.

## 1. Search log

Sources searched: publisher pages and official DOI/proceedings records from
MDPI, Springer Nature, ACM/PACMSE, BMJ, NEJM, institutional publication
records, and general scholarly search used only to locate primary sources.

Newest-first query families:

- `2026 log sequence embeddings anomaly detection HDFS dataset parsing sequence representation DOI`
- `2025 machine learning log anomaly detection HDFS session grouping chronological split DOI`
- `2025 event sequence prediction temporal split leakage duplicate traces DOI`
- `2024 critical review HDFS BGL sequence anomaly detection dataset limitations DOI`
- `2025 pre-specified sensitivity analysis protocol amendment before outcome analysis peer reviewed DOI`
- `2024 sensitivity analysis pre-specified robustness analysis protocol amendment empirical research BMJ DOI`
- `2024 impact log parsing anomaly detection HDFS BGL DOI empirical software engineering`
- `2025 comprehensive study machine learning log anomaly detection HDFS BGL DOI`

Inclusion required a verified publisher/DOI record and direct relevance to at
least one of: HDFS session construction, preprocessing/split sensitivity,
group/temporal leakage, benchmark suitability, or pre-outcome robustness
planning. Preprints, blogs, unverifiable bibliographic records, and papers that
only name HDFS/BGL without usable methods evidence were excluded. Search moved
from 2026 to 2025 to 2024; older work was unnecessary for the final decision.

Eight sources were retained. Duplicate publisher/DOI/PDF records were merged.
No retained source specifically tests SeqLogAD's boundary-spanning connected-
component purge.

## 2. Retained sources

### S1 — Alzahrani (2026)

- **Title:** Investigating the Impact of Log-Sequence Embeddings on Anomaly Detection: A Systematic Study
- **Author:** Musaad Alzahrani
- **Year / venue:** 2026, *Information* 17(3), 228
- **DOI:** [10.3390/info17030228](https://doi.org/10.3390/info17030228)
- **Official URL:** [MDPI](https://www.mdpi.com/2078-2489/17/3/228)
- **Publication status:** peer-reviewed journal article, published 27 February 2026
- **Exact supported claim:** controlled log-anomaly comparisons depend on fixed preprocessing, sequence construction, split, and parser choices; HDFS is commonly sessionized by block ID.
- **Relevance:** supports holding the parser/representation backbone fixed when assessing a split-construction sensitivity.
- **Classification:** `LITERATURE_SUPPORTED`
- **Limit:** paper-specific HDFS/BGL variants and outcomes do not validate SeqLogAD's exact bytes or purge.

### S2 — Ali et al. (2025)

- **Title:** A comprehensive study of machine learning techniques for log-based anomaly detection
- **Authors:** Shan Ali, Chaima Boufaied, Domenico Bianculli, Paula Branco, Lionel Briand
- **Year / venue:** 2025, *Empirical Software Engineering* 30, Article 129
- **DOI:** [10.1007/s10664-025-10669-3](https://doi.org/10.1007/s10664-025-10669-3)
- **Official URL:** [Springer Nature](https://link.springer.com/article/10.1007/s10664-025-10669-3)
- **Publication status:** peer-reviewed journal article, published 23 June 2025
- **Exact supported claim:** preprocessing/grouping/window decisions, traditional-versus-deep comparators, time cost, and hyperparameter sensitivity matter when interpreting log-anomaly methods.
- **Relevance:** reinforces the need to keep comparator and preprocessing budgets fixed rather than changing the primary split after a diagnostic.
- **Classification:** `LITERATURE_SUPPORTED`
- **Limit:** supervision regimes and dataset constructions differ from Protocol v1.1.

### S3 — Pfeiffer et al. (2025)

- **Title:** Learning from the Data to Predict the Process: Generalization Capabilities of Next Activity Prediction Algorithms
- **Authors:** Peter Pfeiffer, Luka Abb, Peter Fettke, Jana-Rebecca Rehse
- **Year / venue:** 2025, *Business & Information Systems Engineering* 67, 357–383
- **DOI:** [10.1007/s12599-025-00936-4](https://doi.org/10.1007/s12599-025-00936-4)
- **Official URL:** [Springer Nature](https://link.springer.com/article/10.1007/s12599-025-00936-4)
- **Publication status:** peer-reviewed research paper, published 22 March 2025
- **Exact supported claim:** event-sequence evaluations can suffer duplicate/example leakage, and temporal versus random splitting changes the generalization question.
- **Relevance:** supports preserving group/trace integrity and the chronological primary design.
- **Classification:** `LITERATURE_SUPPORTED`
- **Limit:** predictive process monitoring is adjacent methodology, not HDFS anomaly detection.

### S4 — Hróbjartsson et al. (2025)

- **Title:** SPIRIT 2025 explanation and elaboration: updated guideline for protocols of randomised trials
- **Authors:** Asbjørn Hróbjartsson, Isabelle Boutron, Sally Hopewell, David Moher, Kenneth F. Schulz, Gary S. Collins, et al.
- **Year / venue:** 2025, *BMJ* 389:e081660
- **DOI:** [10.1136/bmj-2024-081660](https://doi.org/10.1136/bmj-2024-081660)
- **Official URL:** [CONSORT/SPIRIT record](https://www.consort-spirit.org/spirit-e-e)
- **Publication status:** peer-reviewed research-methods/reporting guideline
- **Exact supported claim:** a protocol should state planned sensitivity analyses, their rationale, and methods; sensitivity analyses assess whether primary conclusions vary under alternative assumptions/analyses.
- **Relevance:** informs explicit primary-versus-secondary separation before SeqLogAD outcomes exist.
- **Classification:** `LITERATURE_INFORMED_SEQLOGAD_DECISION`
- **Limit:** randomised-trial guidance does not prescribe ML benchmark policy.

### S5 — Landauer, Skopik, and Wurzenberger (2024)

- **Title:** A Critical Review of Common Log Data Sets Used for Evaluation of Sequence-Based Anomaly Detection Techniques
- **Authors:** Max Landauer, Florian Skopik, Markus Wurzenberger
- **Year / venue:** 2024, *Proceedings of the ACM on Software Engineering*, FSE, Article 61
- **DOI:** [10.1145/3660768](https://doi.org/10.1145/3660768)
- **Official URL:** [AIT publication record](https://publications.ait.ac.at/en/publications/a-critical-review-of-common-log-data-sets-used-for-evaluation-of-/)
- **Publication status:** peer-reviewed ACM article, published 12 July 2024
- **Exact supported claim:** common log datasets, including HDFS/BGL, can expose anomaly signals unrelated to sequence order; dataset construction and simple baselines must be examined.
- **Relevance:** supports retaining the frozen killer controls and treating the purge as a validity concern rather than assuming benchmark suitability.
- **Classification:** `LITERATURE_SUPPORTED`
- **Limit:** does not evaluate the SeqLogAD purge or prescribe Option B.

### S6 — Khan et al. (2024)

- **Title:** Impact of log parsing on deep learning-based anomaly detection
- **Authors:** Zanis Ali Khan, Donghwan Shin, Domenico Bianculli, Lionel C. Briand
- **Year / venue:** 2024, *Empirical Software Engineering* 29, Article 139
- **DOI:** [10.1007/s10664-024-10533-w](https://doi.org/10.1007/s10664-024-10533-w)
- **Official URL:** [Springer Nature](https://link.springer.com/article/10.1007/s10664-024-10533-w)
- **Publication status:** peer-reviewed journal article, published 17 August 2024
- **Exact supported claim:** parser output properties and preprocessing choices can affect downstream anomaly detection; HDFS sequence reductions in the study preserve whole block-ID sequences.
- **Relevance:** supports freezing one parser across primary and secondary analyses and preserving complete components.
- **Classification:** `LITERATURE_SUPPORTED`
- **Limit:** its reduced HDFS sampling and scientific outcomes are not transferred to SeqLogAD.

### S7 — Desai et al. (2024)

- **Title:** Process guide for inferential studies using healthcare data from routine clinical practice to evaluate causal effects of drugs (PRINCIPLED): considerations from the FDA Sentinel Innovation Center
- **Authors:** Rishi J. Desai, Shirley V. Wang, S. K. Sreedhara, L. Zabotka, F. Khosrow-Khavar, Jennifer C. Nelson, et al.
- **Year / venue:** 2024, *BMJ* 384:e076460
- **DOI:** [10.1136/bmj-2023-076460](https://doi.org/10.1136/bmj-2023-076460)
- **Official URL:** [Johns Hopkins publication record](https://pure.johnshopkins.edu/en/publications/process-guide-for-inferential-studies-using-healthcare-data-from-/)
- **Publication status:** peer-reviewed research-methods/reporting article, published 12 February 2024
- **Exact supported claim:** diagnostic evaluation may inform a documented protocol amendment that pre-specifies focused robustness assessments before inferential analyses.
- **Relevance:** directly matches the timing pattern here: purge diagnostic before baseline/model/TEST outcomes.
- **Classification:** `LITERATURE_INFORMED_SEQLOGAD_DECISION`
- **Limit:** causal healthcare methodology is used only as a general pre-specification pattern, not as log-specific authority.

### S8 — Cheng and Hogan (2024)

- **Title:** The Sense and Sensibility of Sensitivity Analyses
- **Authors:** Debbie M. Cheng, Joseph W. Hogan
- **Year / venue:** 2024, *New England Journal of Medicine* 391, 972–974
- **DOI:** [10.1056/NEJMp2403318](https://doi.org/10.1056/NEJMp2403318)
- **Official URL:** [NEJM](https://www.nejm.org/doi/full/10.1056/NEJMp2403318)
- **Publication status:** peer-reviewed commentary, published online 14 September 2024
- **Exact supported claim:** sensitivity analyses assess robustness and require deliberate planning and reporting.
- **Relevance:** corroborates the limited, separately reported secondary design.
- **Classification:** `LITERATURE_INFORMED_SEQLOGAD_DECISION`
- **Limit:** clinical-trial context; no HDFS-specific prescription.

## 3. Evidence classification

| Statement | Classification | Basis |
|---|---|---|
| Group/session integrity, chronology, parser state, and construction choices can affect event/log sequence evaluation | `LITERATURE_SUPPORTED` | S1, S2, S3, S5, S6 |
| A focused sensitivity analysis should be specified before outcomes and kept distinct from the primary analysis | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | S4, S7, S8, with explicit domain limitations |
| Keep the existing frozen HDFS split as primary | `SEQLOGAD_PROTOCOL_DECISION` | Pre-result freeze, unchanged TEST/parser identity, audit concern not fatal, human approval |
| Use exactly all `PURGED_BOUNDARY` components as one secondary evaluation cohort | `SEQLOGAD_PROTOCOL_DECISION` | Smallest direct perturbation of the identified mechanism; no paper prescribes it |
| Execute sensitivity only after the immutable primary HDFS result and never use it for selection | `SEQLOGAD_PROTOCOL_DECISION` | Prevents a second outcome-driven choice under this project's governance |
| Reuse frozen parser and isolate output paths | `ENGINEERING_DECISION` | Prevents parser confounding and artifact overwrite; enforced by contract/tests |
| Preserve existing hashes and expose the decision through a canonical YAML payload | `ENGINEERING_DECISION` | Reproducibility/provenance mechanism |

## 4. Literature verdict and boundaries

The retained literature supports **Option B as scientifically defensible**:
keep the pre-result primary design, document its limitation, and pre-register a
small secondary robustness analysis before inferential outcomes. It does not
prove Option B uniquely optimal, prove the current purge harmless, or provide
evidence that the current primary is fundamentally invalid. No 2024–2026
source found requires primary split replacement.

Accordingly, Option B is a human-approved SeqLogAD protocol decision informed
by literature, not an external theorem. The purge sensitivity remains
`NOT_RUN`; no metric, label-level result, or TEST content is added here.
