# SCHEMA-002 — Citation and Method-Provenance Note

**Task:** Freeze partition, event-sequence, localization, and mutation schemas  
**Status:** **IMPLEMENTED — AWAITING HUMAN AUDIT**  
**Created:** 2026-08-21  
**Research results:** None. No raw data, parser, sequence builder, mutation generator, model, or scientific TEST evaluation was run.

## Sources consulted

### CITE-SCHEMA-002-01 — Frozen SeqLogAD scientific protocol

- **Source:** `docs/research-protocol.md`, `PROTOCOL-001` version 1.0.
- **Status:** VERIFIED — HUMAN APPROVED local source of truth.
- **Consulted for:** `60/10/10/10/10` partitions, HDFS atomic/purge semantics, BGL non-overlapping 100-event parents and residual rule, label-access boundaries, TEST sealing, normal-only synthetic source pools, mutation taxonomy, and token/gap/transition separation.
- **SeqLogAD use:** Direct internal requirements represented as strict schemas and synthetic-only tests.

### CITE-SCHEMA-002-02 — SCHEMA-001 canonical event contract

- **Source:** `docs/schemas/canonical-events.md` and `src/seqlogad/common/schemas/events.py`, schema version 1.0.
- **Status:** VERIFIED — HUMAN APPROVED local source of truth.
- **Consulted for:** event/record identity formats, dataset fingerprint, partition vocabulary, supervision access vocabulary, canonical JSON, immutability, and label-free model-input boundary.
- **SeqLogAD use:** SCHEMA-002 composes but does not alter SCHEMA-001 identities.

### CITE-SCHEMA-002-03 — Loghub dataset context

- **Citation:** Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, and Michael R. Lyu. *Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics*. IEEE International Symposium on Software Reliability Engineering (ISSRE), 2023.
- **Official source:** https://github.com/logpai/loghub
- **Status:** VERIFIED previously in `docs/references/PROTOCOL-001-citations.md` and repository dataset contracts.
- **Consulted for:** HDFS block/session-level dataset organization and BGL line-level alert context already frozen by PROTOCOL-001.
- **SeqLogAD adaptation:** Dataset-specific parent-sequence and label-aggregation schema constraints.
- **Not copied:** No raw log, preprocessed template/trace, code, result, table, or metric was accessed or copied for SCHEMA-002.

### CITE-SCHEMA-002-04 — LogSD fixed-entry sequence precedent

- **Citation:** Yongzheng Xie, Hongyu Zhang, and Muhammad Ali Babar. *LogSD: Detecting Anomalies from System Logs through Self-Supervised Learning and Frequency-Based Masking*. Proceedings of the ACM on Software Engineering, 1(FSE), Article 93, 2098–2120, 2024.
- **Status:** VERIFIED previously in `docs/references/PROTOCOL-001-citations.md`; no new literature search was performed in SCHEMA-002.
- **Consulted for:** Previously verified context for chronological BGL splitting and fixed-entry sequence construction.
- **SeqLogAD decision:** Exact BGL size 100, non-overlap, split-before-windowing, and residual threshold 20 are frozen project protocol decisions, not claims made by this paper.

## No new external literature search

**NO NEW EXTERNAL REFERENCES WERE SEARCHED OR INTRODUCED IN SCHEMA-002.** The task implemented the already human-approved protocol and approved SCHEMA-001 contract. Previously verified references are repeated here only so this task remains independently auditable.

## Independent SCHEMA-002 decisions

The following are project-owned engineering/research-contract decisions and are not attributed as paper findings:

- full-digest `SPLIT-`, `PART-`, `SEQ-`, and `MUT-` identities;
- exact canonical payloads used by those identities;
- separate source/provenance and ordered-event content hashes;
- `None` meaning unsupported while an empty tuple means supported with no affected position;
- zero-based token, gap, and transition coordinate bounds;
- deterministic parameter sorting in mutation identity;
- literal normal source label in `MutationRecord`;
- structural absence of TEST supervision and rejection of pre-final TEST mutation records;
- exact schema field names and Pydantic validation implementation.

These choices are contracts to be audited. They are not empirical improvements and carry no novelty claim.

## Aletheia status

`Aletheia` was **NOT USED** as a dataset, paper, implementation, mutation taxonomy, or schema source in SCHEMA-002. Adding it later requires separate verified provenance, license review, scientific role, protocol decision, and citation note.

## Reuse and licensing

- No external code, figure, table, paper prose, model weight, processed trace, or raw dataset byte was copied.
- Tests use synthetic identifiers only and do not read HDFS, BGL, labels, or manifests.
- Runtime implementation uses the already declared Pydantic dependency; Pydantic is engineering infrastructure, not a scientific contribution.

## Human audit checklist

- [x] Every source actually consulted for implementation is listed.
- [x] Previously verified background is distinguished from new research.
- [x] Project-owned coordinate and identity decisions are explicit.
- [x] No result, metric, novelty, or implementation-completeness claim is made.
- [x] Aletheia is explicitly recorded as not used.
- [ ] Human researcher audits and accepts SCHEMA-002.
