# Research Questions — v2 Domain-Adaptive Fusion

All questions are `HYPOTHESIS — TO BE TESTED`; no v2 experiment has run.

## RQ1 — Cross-architecture representation

Can a shared representation and the selected experts generalise across log syntaxes and source architectures when one complete architecture is held out?

Evidence: leave-one-architecture-out folds, source-held-out expert reports, per-target AP/PR-AUC and bootstrap uncertainty. The claim is bounded to the architectures evaluated, not universal generalisation.

## RQ2 — Zero-label target adaptation

Can a target normal buffer calibrate scores and uncertainty for an unseen architecture without target labels?

Evidence: buffer hash/provenance, readiness and contamination checks, false alert rate, calibration, abstention and degradation from cold start. The buffer must be versioned before evaluation and cannot silently recalibrate after labels are inspected.

## RQ3 — Adaptive fusion

Does a gate using calibrated score, uncertainty, coverage, drift and context add stable value over each expert and mandatory equal-weight fusion?

Evidence: expert diversity, disagreement/error overlap, held-out architecture results, ablations removing each expert and adaptation, and false-alert control. Fusion is not justified by an arbitrary score sum or by a single target.

## RQ4 — Operating envelope

How does the system behave under cold start, new templates, log-volume drift, missing topology fields and contaminated target burn-in?

Evidence: predeclared scenario bundles, coverage/abstention records, latency and degradation reports. These scenarios describe limits; they do not change the research question or permit target-label tuning.

## Preserved historical questions

The v1.1 questions about sequence added value, order destruction and conditional localization remain documented in [`research-protocol-v1.1.md`](research-protocol-v1.1.md) and [`../Plan/master-implementation-plan-v1.1.md`](../Plan/master-implementation-plan-v1.1.md). They are not v2 gates. Their HDFS/BGL protocol and EFFECT-001 margins remain frozen provenance.
