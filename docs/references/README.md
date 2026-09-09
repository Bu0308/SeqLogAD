# References

**The authoritative reference registry is
[`reference_registry.yaml`](reference_registry.yaml).**

References are organised according to **`Bang_ke_hoach_SeqLogAD.xlsx`**, the
project's authoritative scientific roadmap. Active scientific work should cite
registry entries by their ID rather than create new ad-hoc citation files.

| File | Role |
| --- | --- |
| [`reference_registry.yaml`](reference_registry.yaml) | Machine-readable source of truth. Regenerate with `python scripts/build_reference_registry.py`; a test fails if it goes stale. |
| [`ACTIVE_REFERENCES.md`](ACTIVE_REFERENCES.md) | Human-readable view, generated from the registry. |
| [`REFERENCE_CLEANUP_REPORT.md`](REFERENCE_CLEANUP_REPORT.md) | What this consolidation scanned, merged, corrected and deleted. |

## How to cite

Use the registry ID. `S1`–`S11` are the workbook's own identifiers and are never
renumbered; their task mappings are derived from
[`../../configs/plan/excel-roadmap-v1.yaml`](../../configs/plan/excel-roadmap-v1.yaml)
so they cannot drift from the workbook. `S12`–`S17` were added by this
consolidation for dataset and tooling provenance the active work relies on.

Every claim attached to a source carries one of four classifications, and a citation
may not be used to make a SeqLogAD-specific choice look prescribed by literature:

| Classification | Meaning |
| --- | --- |
| `LITERATURE_SUPPORTED` | The cited work establishes the claim. |
| `LITERATURE_INFORMED_SEQLOGAD_DECISION` | The literature motivated the choice but does not establish it. |
| `SEQLOGAD_PROTOCOL_DECISION` | A project decision. No citation makes it true. |
| `ENGINEERING_DECISION` | An implementation choice. |

Where an active claim lacks adequate support, it is recorded as a
**`REFERENCE_SUPPORT_GAP`** in the registry rather than papered over with a
loosely-related citation. One is open: `RSG-001` (the "GTAT" naming in P2.7).

## Historical citation packs

The files below are **HISTORICAL / SUPERSEDED**. They are the reproducible search
logs and citation notes for the retired v1.1 sequence-order study, and they are
retained only because they back frozen decisions, frozen artifact identities, or
completed audits that the repository still has to explain. Each carries a banner at
its top. **None of them is an active reference source, and none should be cited by
new work.**

| File | Backs |
| --- | --- |
| `CANONICAL-NUL-DECISION-001-citations.md` | The NUL codec, which is **reused verbatim** by the active `LOG-UNIFY-001` schema |
| `PURGE-AUDIT-001-citations.md` | `PURGE-AUDIT-001`, cited by exception `EXC-002` |
| `PURGE-DECISION-001-citations.md` | The frozen, human-approved purge decision |
| `PROTOCOL-SPLIT-CLARIFY-001-citations.md` | The frozen split-clarification addendum |
| `PARSE-001-citations.md` | The frozen Drain3 fit whose state hashes are still registered |
| `EFFECT-001-citations.md` | The frozen `EFFECT-001` statistical contract |
| `META-001-citations.md` | The metadata-extraction contract still implemented by `raw_metadata.py` |
| `RESEARCH-FREEZE-v1.1-citations.md` | Protocol v1.1, the historical foundation |
| `CANONICAL-EVENT-001-citations.md` | The retired canonical-event task |
| `LIT-001-citations.md` | The completed prior-art review that fixed the project's no-novelty-claim boundary |
| `PROTOCOL-001-citations.md` | Protocol v1.0 |
| `SCHEMA-001-citations.md`, `SCHEMA-002-citations.md` | The frozen event and sequence schemas |
| `SPLIT-001-citations.md` | The frozen HDFS/BGL split artifacts |

Related historical material lives in [`../literature/`](../literature): the
`LIT-001` search log, the prior-art matrix, and the split-protocol evidence matrix
(the last is still referenced by an active contract test).
