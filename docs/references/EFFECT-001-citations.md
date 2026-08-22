# EFFECT-001 — Citation and Method-Provenance Note

**Prepared:** 2026-08-22  
**Empirical status:** `NOT_RUN`  
**Novelty status:** no methodological novelty claim

This note records the external methods consulted for `EFFECT-001`. It does not turn any external result into a SeqLogAD result, and no source supplies `delta_HDFS` or `delta_BGL`.

## EFFECT-CITE-001 — Precision–Recall under imbalance

- **Citation:** Takaya Saito, Marc Rehmsmeier. *The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets*. PLOS ONE 10(3), 2015.
- **DOI:** https://doi.org/10.1371/journal.pone.0118432
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** retaining PR-focused evaluation when anomaly prevalence is imbalanced.
- **Boundary:** does not define Average Precision implementation details or a meaningful numerical AP difference for HDFS/BGL.

## EFFECT-CITE-002 — AUCPR point estimates and uncertainty

- **Citation:** Kendrick Boyd, Kevin H. Eng, C. David Page. *Area Under the Precision-Recall Curve: Point Estimates and Confidence Intervals*. ECML PKDD 2013, LNCS 8190, pp. 451–466.
- **DOI:** https://doi.org/10.1007/978-3-642-40994-3_29
- **Status:** `PEER_REVIEWED / VERIFIED IN LIT-001`.
- **Used for:** requiring uncertainty around AUCPR/AP rather than reporting only a point estimate.
- **Boundary:** does not prescribe SeqLogAD's cluster unit, percentile bootstrap, replicate count, confidence level, or practical margin.

## EFFECT-CITE-003 — Equivalence bounds and smallest effect of interest

- **Citation:** Daniël Lakens, Anne M. Scheel, Peder M. Isager. *Equivalence Testing for Psychological Research: A Tutorial*. Advances in Methods and Practices in Psychological Science 1(2), 2018.
- **DOI:** https://doi.org/10.1177/2515245918770963
- **Status:** `PEER_REVIEWED / VERIFIED`.
- **Used for:** defining the smallest effect of interest before outcomes, separating practical equivalence from inconclusive evidence, and preferring cost/benefit or substantive justification over a generic benchmark.
- **Boundary:** the domain, test examples, numerical bounds, and conventional TOST interval are not transferred mechanically to SeqLogAD. EFFECT-001 uses one conservative 95% project interval and requires human-owned AP margins.

## EFFECT-CITE-004 — Resampling dependent observations

- **Citation:** Hans R. Künsch. *The Jackknife and the Bootstrap for General Stationary Observations*. The Annals of Statistics 17(3), pp. 1217–1241, 1989.
- **DOI:** https://doi.org/10.1214/aos/1176347265
- **Status:** `PEER_REVIEWED / FOUNDATIONAL / VERIFIED`.
- **Used for:** rejecting event-level IID resampling when observations have session/temporal dependence and motivating dependence-preserving resampling units.
- **Boundary:** does not select HDFS blocks, BGL 100-event parents, 10,000 replicates, or any SeqLogAD result.

## SeqLogAD-owned design decisions

The following are pre-registered project choices, not claims attributed to the papers above:

- separate HDFS/BGL estimands;
- non-interpolated Average Precision as the canonical `PR-AUC` interpretation;
- symmetric dataset-specific margins pending human approval;
- 95% paired cluster-percentile interval;
- 10,000 valid replicates, seed `42`, and explicit degenerate-resample handling;
- required orderless candidate set including Isolation Forest;
- 12-config family-level equal budget;
- validation-only selection and fixed tie order;
- no primary multiplicity correction because there is one separately interpreted contrast per dataset and no pooled/disjunctive claim;
- KT-3 reuse of `delta_d` and three fixed transformation seeds;
- valid negative/equivalent/inconclusive outcomes.

## Integrity checklist

- [x] No invented citation, DOI, or paper result.
- [x] No numeric practical-effect margin attributed to literature.
- [x] No SeqLogAD experiment or bootstrap was run.
- [x] No TEST data or labels were accessed.
- [x] External method support is separated from SeqLogAD design decisions.
