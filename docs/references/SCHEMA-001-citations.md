# SCHEMA-001 — Citation and Method-Provenance Note

**Task:** Freeze canonical `LogEvent` and `EventTemplate` schemas  
**Status:** **IMPLEMENTED — AWAITING HUMAN AUDIT**  
**Created:** 2026-08-20  
**Research results:** None. No raw data, parser, model, or scientific TEST evaluation was run.

## Sources consulted

### CITE-SCHEMA-001-01 — Frozen SeqLogAD scientific protocol

- **Source:** `docs/research-protocol-v1.0.md`, `PROTOCOL-001` version 1.0.
- **Status:** VERIFIED — HUMAN APPROVED local source of truth.
- **Consulted for:** five-way partition names, label-access rules, TEST sealing, HDFS block/session identity, BGL inline-label isolation, Drain3 fit/freeze boundary, `EVT_UNSEEN`, and deterministic event identity requirements.
- **SeqLogAD use:** Direct internal requirements implemented as schema validators and tests.

### CITE-SCHEMA-001-02 — Loghub dataset contract

- **Citation:** Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, and Michael R. Lyu. *Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics*. IEEE International Symposium on Software Reliability Engineering (ISSRE), 2023.
- **Official source:** https://github.com/logpai/loghub
- **Status:** VERIFIED previously in `PROTOCOL-001-citations.md` and the version-controlled HDFS/BGL acquisition contracts.
- **Consulted for:** HDFS block/session label granularity, BGL line-level inline alert marker, and canonical HDFS/BGL dataset identity.
- **SeqLogAD adaptation:** Dataset-specific grouping and supervision-granularity validation.
- **Not copied:** No Loghub preprocessed event/template/trace, source code, metric, or dataset byte was copied or read for SCHEMA-001.

### CITE-SCHEMA-001-03 — Drain parser identity context

- **Citation:** Pinjia He, Jieming Zhu, Zibin Zheng, and Michael R. Lyu. *Drain: An Online Log Parsing Approach with Fixed Depth Tree*. IEEE International Conference on Web Services (ICWS), 2017.
- **DOI:** https://doi.org/10.1109/ICWS.2017.13
- **Status:** VERIFIED previously in `PROTOCOL-001-citations.md`.
- **Consulted for:** The distinction between a parsed template and an event occurrence, and the parser version/config provenance required around a frozen Drain3 registry.
- **SeqLogAD adaptation:** `EventTemplate` records parser/normalization identities and forbids non-`BASE_TRAIN` fit ownership.
- **Independent decision:** The exact SHA-256 event-ID payload and full-digest `EVT-...` representation are SeqLogAD protocol/schema decisions, not a claim from the Drain paper.

### CITE-SCHEMA-001-04 — Pydantic runtime contract

- **Source:** Pydantic 2 package already declared by `pyproject.toml`; tested environment version is recorded in `requirements.lock`.
- **Official documentation:** https://docs.pydantic.dev/latest/concepts/models/
- **Status:** VERIFIED LOCALLY through the installed dependency contract and schema test suite; no external source code was copied.
- **Consulted for:** Strict field validation, frozen models, nested serialization, field validators, and model validators.
- **SeqLogAD use:** Engineering implementation only; Pydantic is not a scientific contribution.

## Independent SCHEMA-001 decisions

The following are project-owned contract decisions and must not be attributed to cited papers:

- full SHA-256 `EVT-...` deterministic event IDs;
- source-occurrence `LOG-...` record IDs;
- exact canonical JSON serialization;
- immutable tuple-based event attributes;
- reserved supervision-like attribute-key rejection;
- TEST `LogEvent.supervision` being structurally absent;
- explicit `to_model_input()` boundary;
- storing source text timestamp separately from optional timezone-aware UTC time;
- storing parser-state and template-registry hashes on canonical events.

These decisions are untested as research improvements and carry no novelty claim.

## Aletheia status

`Aletheia` was **NOT USED** as a dataset, paper, implementation, or schema source in SCHEMA-001. Adding it later requires a separate verified source, license/provenance review, task scope, and citation note.

## Reuse and licensing

- No external code, figure, table, paper text, model weight, template trace, or raw dataset byte was copied.
- The implementation uses the existing project dependency contract and project-owned schema logic.
- Loghub raw files remain ignored and were not accessed.

## Audit checklist

- [x] Every source consulted for SCHEMA-001 is listed.
- [x] Paper-derived context is separated from project-owned decisions.
- [x] No experimental result or novelty claim is made.
- [x] Aletheia is explicitly recorded as not used.
- [x] No external code or scientific data was copied.
- [ ] Human researcher audits and accepts SCHEMA-001.
