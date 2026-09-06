# Documentation

**Authoritative scientific plan: [`../Bang_ke_hoach_SeqLogAD.xlsx`](../Bang_ke_hoach_SeqLogAD.xlsx).**
Where any document here disagrees with the workbook, the workbook wins.

## Plan and migration

- [`../configs/plan/excel-roadmap-v1.yaml`](../configs/plan/excel-roadmap-v1.yaml): machine-readable projection of the workbook.
- [`migration/EXCEL-PLAN-MIGRATION-001.md`](migration/EXCEL-PLAN-MIGRATION-001.md): what moved, what was retired, what was reused.
- [`migration/EXCEL-RELEVANCE-AUDIT.md`](migration/EXCEL-RELEVANCE-AUDIT.md): keep / adapt / archive / delete decisions with dependency paths.
- [`references/EXCEL-PLAN-citation-verification.md`](references/EXCEL-PLAN-citation-verification.md): all 11 workbook citations resolved against Crossref/arXiv.

## Phase 1 — Data & Protocol

- [`protocol/P1.1-research-scope.md`](protocol/P1.1-research-scope.md): architecture, unseen target, forbidden fields, fold diagram.
- [`protocol/P1.4-normalisation.md`](protocol/P1.4-normalisation.md): `NORM-CS-001` rules, golden cases, measured effect.
- [`protocol/PHASE-1-RECORD.md`](protocol/PHASE-1-RECORD.md): P1.2–P1.8 with every measured number.

## Implementation contract

- [`research-protocol-v2-domain-adaptive-fusion.md`](research-protocol-v2-domain-adaptive-fusion.md): forward protocol and gate boundary.
- [`research-questions.md`](research-questions.md): cross-architecture RQs.
- [`plan-migration-v1.1-to-v2.md`](plan-migration-v1.1-to-v2.md): the earlier v1.1→v2 decision map (historical).
- [`data-collection-gap-matrix.md`](data-collection-gap-matrix.md): guide-to-repo coverage and deferrals.
- [`data-collection-system.md`](data-collection-system.md): implementation boundary and validator contract.

- [`../configs/active-state.yaml`](../configs/active-state.yaml): synchronized post-PURGE-DECISION execution status plus portable split/parser identities; not a scientific decision source.
- [`audits/PURGE-AUDIT-001.md`](audits/PURGE-AUDIT-001.md): aggregate HDFS purged-versus-retained result, human stop gate, TEST boundary, and deterministic payload identity.
- [`references/PURGE-AUDIT-001-citations.md`](references/PURGE-AUDIT-001-citations.md): verified recent/foundational evidence and exact method classification for the purge audit.
- [`decisions/PURGE-DECISION-001.md`](decisions/PURGE-DECISION-001.md): human-approved Option B, unchanged primary HDFS protocol, and pre-registered secondary purge-sensitivity contract.
- [`references/PURGE-DECISION-001-citations.md`](references/PURGE-DECISION-001-citations.md): newest-first targeted search, source verification, and claim classifications for the decision.
- [`audits/PROJECT-CONTEXT-POST-PARSE-001.md`](audits/PROJECT-CONTEXT-POST-PARSE-001.md): canonical post-PARSE-001 scientific handoff, frozen identities, scope, claim boundaries, and next dependency-correct task.
- [`audits/ORIGINAL-EVALUATION-REMEDIATION.md`](audits/ORIGINAL-EVALUATION-REMEDIATION.md): finding-by-finding comparison between the original redirect evaluation and the verified current repository state.
- [metadata-extraction-contract.md](metadata-extraction-contract.md): implemented
  parser/label-free HDFS grouping and BGL chronology contract used by the
  verified real split.
- [references/META-001-citations.md](references/META-001-citations.md): sources,
  implementation provenance, and scientific boundary for META-001.
- [`project-scope.md`](project-scope.md): v2 scope and preserved foundation.
- [`research-protocol.md`](research-protocol.md): current protocol entry point.
- [`research-protocol-v1.1.md`](research-protocol-v1.1.md): active frozen protocol.
- [`split-clarification-contract.md`](split-clarification-contract.md): binding exact HDFS/BGL allocation, purge, residual, reconciliation, and hash semantics.
- [`split-artifacts-and-test-seal.md`](split-artifacts-and-test-seal.md): verified real structural summaries, identities, artifact policy, and unopened TEST-seal state.
- [`parser-fit-and-freeze.md`](parser-fit-and-freeze.md): real normal-pool and frozen Drain3 identities, immutable transform contract, and derived-artifact policy.
- [`literature/split-protocol-evidence-matrix.md`](literature/split-protocol-evidence-matrix.md): literature-supported versus SeqLogAD-owned split decisions and source conflicts.
- [`statistical-decision-contract.md`](statistical-decision-contract.md): human-approved EFFECT-001 estimand/bootstrap/comparison contract with `0.01 AP` margins.
- [`research-protocol-v1.0.md`](research-protocol-v1.0.md): preserved historical protocol.
- [`literature/prior-art-matrix-v1.1.md`](literature/prior-art-matrix-v1.1.md): completed targeted `LIT-001` matrix and research decisions.
- [`literature/LIT-001-search-log.md`](literature/LIT-001-search-log.md): reproducible queries, screening rules, duplicate handling, and dispositions.
- [`references/LIT-001-citations.md`](references/LIT-001-citations.md): verified source and method-provenance note.
- [`references/EFFECT-001-citations.md`](references/EFFECT-001-citations.md): statistical-method sources and explicit SeqLogAD design boundaries.
- [`references/PARSE-001-citations.md`](references/PARSE-001-citations.md): Drain/Drain3 semantics, recent parsing/granularity evidence, source freshness, and explicit project-owned decisions.
- [`references/ALIGN-FIX-001-citations.md`](references/ALIGN-FIX-001-citations.md): records that ALIGN-FIX-001 changed engineering/status state only and required no new external scientific citation.
- [`references/PROTOCOL-SPLIT-CLARIFY-001-citations.md`](references/PROTOCOL-SPLIT-CLARIFY-001-citations.md): targeted 2024–2026 split/grouping sources, search record, compatibility, and limitations.
- [`references/SCHEMA-COMPAT-001-citations.md`](references/SCHEMA-COMPAT-001-citations.md): internal contract provenance for Protocol-v1.1 schema compatibility.
- [`references/RESEARCH-FREEZE-v1.1-citations.md`](references/RESEARCH-FREEZE-v1.1-citations.md): source and method provenance for the redirect.
- [`datasets/`](datasets/): immutable dataset identity and suitability caveats.
- [`schemas/`](schemas/): implemented schema contracts; not evidence that data artifacts exist.
- [`reproducibility.md`](reproducibility.md): environment/artifact discipline.

Planning, architecture, backlog, roadmap, ADRs, and experiment status live under [`../Plan/`](../Plan/). The active plan is the v2 domain-adaptive-fusion plan; v1.1/V1/V3 plans are historical and labeled superseded.

No documentation file may turn `NOT_RUN` work into a result or treat a placeholder module as implementation.
