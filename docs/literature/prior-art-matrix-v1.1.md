# LIT-001 — Targeted Prior-Art Matrix for Research Freeze v1.1

**Status:** `IN_PROGRESS`  
**Search window targeted by the active task:** 2024-08 through 2026-08, with older foundational/evaluation papers retained where directly necessary  
**Cutoff used for this snapshot:** 2026-08-21  
**Empirical SeqLogAD results:** none

This is a targeted decision matrix, not a completed systematic literature review. Full search strings, inclusion/exclusion logs, duplicate handling, backward/forward snowballing, and contribution classification remain required before `LIT-001 = DONE`.

| Topic | Verified source | What prior work establishes or studies | Relevance to SeqLogAD v1.1 | Current decision |
|---|---|---|---|---|
| HDFS/BGL suitability | Landauer et al., FSE 2024, DOI `10.1145/3660768` | Examines whether common benchmark anomalies are sequential and evaluates simple detection mechanisms | Direct warning that a sequence claim needs trivial controls; exact SeqLogAD bytes/protocol still require empirical tests | `RISK_CONFIRMED; EXACT_OUTCOME_NEEDS_TEST` |
| HDFS count vectors | Xu et al., SOSP 2009/author-hosted extended paper | Represents HDFS execution paths with message-count vectors for problem detection | Motivates KT-2 count-label dependence and collision analysis | `FOUNDATIONAL_OVERLAP` |
| Evaluation fragility | Le & Zhang 2022; Chen et al. 2021 | Studies sensitivity to grouping, training composition, noise, chronology, and other evaluation choices | Supports strict split, contamination, and equal-budget controls | `PROTOCOL_SUPPORT` |
| Self-supervised sequence AD | LogSD, FSE 2024, DOI `10.1145/3660800` | Studies self-supervised log anomaly detection on HDFS/BGL/Spirit | Confirms active sequence-model prior art; no Transformer novelty claim is available | `KNOWN_FAMILY` |
| Multi-pattern/multi-model fusion | MulAD, 2025, DOI `10.1016/j.scico.2025.103433` | Integrates multiple log-pattern and model families | Strong overlap with the former four-expert/fusion framing | `HIGH_PRIOR_ART_RISK` |
| Log MoE/gating | LogMoE, ASE 2025, DOI `10.1109/ASE63991.2025.00035` | Uses lightweight experts and gating for cross-system log anomaly detection | Fusion/MoE cannot be presumed a contribution | `HIGH_PRIOR_ART_RISK` |
| Instance localization | LogMILP, arXiv `2605.10988` | Weakly supervised log-instance localization with counterfactual perturbation | Localization requires faithfulness controls and is conditional | `ACTIVE_PRIOR_ART; PEER_REVIEW_STATUS_TO_VERIFY` |
| Hierarchical execution modeling | KRONE, arXiv `2602.07303` | Hierarchical/modular log anomaly detection and routing | Reduces plausibility of broad “structured heterogeneous evidence” novelty claims | `ACTIVE_PRIOR_ART; PEER_REVIEW_STATUS_TO_VERIFY` |
| Structured synthetic logs | LogSynthFSM, KDD 2026, DOI `10.1145/3770855.3818134` | State-machine-guided multi-relational synthetic log generation | Synthetic generation/mutation is not a novelty claim | `KNOWN_ACTIVE_AREA` |

## Gap-status snapshot

| Candidate contribution | Status after targeted audit | Reason |
|---|---|---|
| “Sequence models beat simple baselines on HDFS/BGL” | `HYPOTHESIS_TO_BE_TESTED` | Dataset-ceiling and orderless-feature risks are material |
| Four heterogeneous experts | `REMOVED_FROM_FROZEN_CORE` | Scope too large; complementarity absent until measured |
| Structured fusion/F8 | `REMOVED_FROM_FROZEN_CORE` | Direct fusion/MoE prior art and no empirical complementarity |
| Transformer | `CONDITIONAL_METHOD` | Known family; only justified by residual long-range sequence question |
| Sequence added value over orderless controls | `PRIMARY_EMPIRICAL_QUESTION` | Measurable, falsifiable, feasible; not claimed novel |
| Localization faithfulness | `CONDITIONAL_SECONDARY_QUESTION` | Active prior art; requires randomization/counterfactual controls |
| RAG/Agent test recommendation | `FUTURE_INTEGRATION` | Does not answer the frozen core research question |

## Remaining LIT-001 work

1. Register exact search strings/databases and 2024-08–2026-08 inclusion/exclusion criteria.
2. Verify publisher status and final versions for all 2026 preprints.
3. Add strong order-insensitive HDFS/BGL baselines and dataset-variant mapping.
4. Add sequence-destruction/negative-control work beyond log-specific papers.
5. Complete backward/forward snowballing for MulAD, LogMoE, LogMILP, KRONE, and LogSynthFSM.
6. Freeze novelty/contribution states only after the matrix is complete.

Full source annotations and links are in [`../references/RESEARCH-FREEZE-v1.1-citations.md`](../references/RESEARCH-FREEZE-v1.1-citations.md).
