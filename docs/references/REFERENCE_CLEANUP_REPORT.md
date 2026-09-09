# REFERENCE-CONSOLIDATION-001 — reference cleanup report

| Field | Value |
| --- | --- |
| Task | `REFERENCE-CONSOLIDATION-001` |
| Date | 2026-09-07 |
| Authoritative plan | `Bang_ke_hoach_SeqLogAD.xlsx` (SHA-256 `c33aad33…d174d56b`) |
| Authoritative registry | [`reference_registry.yaml`](reference_registry.yaml) |
| Methodology changed | **No** |
| Gate state changed | **No** — G0 remains `PROTOCOL_READY` |

## Counts

| Metric | Value |
| --- | ---: |
| `FILES_SCANNED` | 262 |
| `UNIQUE_SOURCES_FOUND` (distinct DOI / arXiv / official URL repo-wide) | 149 |
| `ACTIVE_SOURCES` | 17 |
| `HISTORICAL_SOURCES` (in the registry) | 1 |
| `HISTORICAL_CITATION_PACKS_RETAINED` | 14 in `docs/references/` + 3 in `docs/literature/` |
| `DUPLICATES_MERGED` | 4 |
| `INCORRECT_REFERENCES_FIXED` | 3 |
| `NEW_SOURCES_ADDED` | 6 (`S12`–`S17`) |
| `OBSOLETE_REFERENCES_DELETED` | 4 files |
| `BROKEN_LINKS_FIXED` | 7 |
| `REFERENCE_SUPPORT_GAPS` | 1 (`RSG-001`) |

## Verification

All 17 active sources were resolved against an authoritative service on 2026-09-07,
not accepted as written: Crossref (`api.crossref.org`) for DOIs, the arXiv API for
preprints, the Zenodo record API for the dataset record, and direct HTTP for
official pages. Nothing in the registry is inferred.

## Incorrect references fixed

| # | Where | Problem | Correction |
| --- | --- | --- | --- |
| 1 | Workbook `S3` (LogDLR) | Attributed to **"Liu et al."** | Crossref returns author family names **Zhou, Ying, Wang, Zhao**. Recorded in the registry with `workbook_label` preserved so the discrepancy stays visible. The workbook itself was **not** edited — it is authoritative and its hash is bound into the G0 receipt. |
| 2 | Workbook `S1` (Loghub) | Cites the 2020 arXiv preprint only | A peer-reviewed version exists: ISSRE 2023, DOI `10.1109/ISSRE59848.2023.00071`. Recorded as canonical; the preprint URL is retained because the workbook uses it. |
| 3 | Workbook `S8` (DANN) | Year given as 2015 | 2015 is the preprint; the JMLR version is vol. 17 (2016), confirmed by the arXiv `journal_ref`. Both recorded. |

`S3`'s IEEE Xplore link returns HTTP 418 to non-browser clients. That is bot
protection, not a bad citation; the DOI was added for durability.

## Duplicates merged

| Source | Previously appeared in | Merged into |
| --- | --- | --- |
| Xu et al., SOSP 2009 (`10.1145/1629575.1629587`) | `LIT-001-citations.md`, `META-001-citations.md`, `PURGE-AUDIT-001-citations.md`, `prior-art-matrix-v1.1.md` | `S12` |
| Oliner & Stearley, DSN 2007 (`10.1109/DSN.2007.103`) | `LIT-001-citations.md`, `META-001-citations.md`, `prior-art-matrix-v1.1.md` | `S13` |
| Du et al., CCS 2017 (`10.1145/3133956.3134015`) | `LIT-001-citations.md`, `LIT-001-search-log.md`, `prior-art-matrix-v1.1.md` | `S15` |
| Loghub (`arXiv:2008.06448` / ISSRE 2023) | workbook, `LIT-001-citations.md`, `META-001-citations.md`, `PURGE-AUDIT-001-citations.md`, `CANONICAL-EVENT-001-citations.md` | `S1` |

Identity matching used DOI first, then title plus authors/year, then arXiv ID.
`DUPLICATE_DOI_ENTRIES = 0` in the registry.

## New sources added

`S12`–`S17` were added because active work depends on them and no registry entry
existed. Each has a non-empty `used_by`.

| ID | Source | Why it is active |
| --- | --- | --- |
| `S12` | Xu et al., SOSP 2009 | Origin and block-trace labelling of `ARCH-HDFS`; required by P1.2 dataset provenance |
| `S13` | Oliner & Stearley, DSN 2007 | Origin and alert-marker labelling of `ARCH-BGL` |
| `S14` | Lin et al., ICSE-C 2016 | Origin and injected-failure labels of `ARCH-HADOOP` |
| `S15` | Du et al., CCS 2017 (DeepLog) | Origin of the `ARCH-OPENSTACK` capture and its anomalous-instance labels |
| `S16` | Loghub Zenodo record, DOI `10.5281/zenodo.8196385` | The actual download source, CC-BY-4.0 licence and published MD5 digests cited by the dataset registry and both dataset configs |
| `S17` | Drain3 official repository, pinned 0.9.11 | The implementation behind the frozen parser state and the auxiliary template field |

## Obsolete references deleted

| Path | Why obsolete | Replacement | Dependency check |
| --- | --- | --- | --- |
| `docs/references/ALIGN-FIX-001-citations.md` | **Zero external sources.** A scope note stating that a repository-hygiene task changed no science. The task is retired. | Repository hygiene is documented in `docs/migration/EXCEL-PLAN-MIGRATION-001.md` | 3 inbound links (README, `Plan/06_DECISIONS.md`, `docs/README.md`) — all repaired |
| `docs/references/SCHEMA-COMPAT-001-citations.md` | **Zero external sources.** Internal provenance note for the retired schema-compatibility task. | `SCHEMA-001` / `SCHEMA-002` citation packs, both retained as historical | 3 inbound links (`Plan/06_DECISIONS.md`, `docs/README.md`, `docs/schemas/event-sequences-and-localization.md`) — all repaired |
| `docs/references/EXCEL-PLAN-citation-verification.md` | Superseded: every row is now in the registry with fuller, re-verified metadata | `reference_registry.yaml` + `ACTIVE_REFERENCES.md` | 1 inbound link (`docs/README.md`) — repaired |
| `docs/literature/day02-log-anomaly-survey.md` | **Orphan** (zero inbound links), self-declared historical Day-2 reading note superseded by `LIT-001` | Its one source (Landauer et al.) is preserved in the registry as `H1` so nothing is lost | 0 inbound links |

Nothing was deleted whose sources are not preserved in the registry, and nothing was
deleted that backs a frozen decision.

## Historical citation packs retained

Fourteen packs in `docs/references/` and three files in `docs/literature/` were
**not** deleted. Each backs a frozen decision, a frozen artifact identity, or a
completed audit the repository still has to explain, and several are reproducible
search logs whose provenance a citation list cannot replace. Every one now carries a
`HISTORICAL / SUPERSEDED` banner at the top and is listed as historical in
[`README.md`](README.md).

Two deserve specific note:

- `CANONICAL-NUL-DECISION-001-citations.md` backs the NUL codec, which is **reused
  verbatim** by the active `LOG-UNIFY-001` schema, so it supports an active claim.
- `docs/literature/split-protocol-evidence-matrix.md` is still referenced by an
  active contract test (`tests/test_split_clarification_contract.py`) and by
  `configs/protocols/split-clarification-v1.yaml`; deleting it would break both.

## Broken links fixed

| # | Location | Fix |
| --- | --- | --- |
| 1–3 | README, `Plan/06_DECISIONS.md`, `docs/README.md` → `ALIGN-FIX-001-citations.md` | Repointed to the registry / migration record |
| 4–6 | `Plan/06_DECISIONS.md`, `docs/README.md`, `docs/schemas/event-sequences-and-localization.md` → `SCHEMA-COMPAT-001-citations.md` | Repointed to the retained schema packs |
| 7 | `.ai/context-packs/transformer.md` → `configs/models/transformer.yaml` | Pre-existing break from the earlier cleanup; the link is now inline text noting the file was deleted with the retired plan |

Stale citation pointers in `docs/datasets/hdfs.md` and `docs/datasets/bgl.md` were
also repaired: they pointed at retired-plan literature and described KT-1/KT-2/KT-3
and Markov experiment roles. They now cite `S12`/`S13`, `S1` and `S16`, and state
the architecture's role under the workbook.

`BROKEN_REFERENCE_LINKS = 0` across 279 relative Markdown links.

## Reference support gaps

One is open. It is recorded, not papered over, and **no methodology was changed**.

**`RSG-001`** — the workbook names the temporal graph expert "GTAT" (P2.7,
`EXP-GTAT-001`) and cites `S6`. `S6` (LogGT) is real, verified and relevant, but it
presents a heterogeneous graph feature with transfer learning; it does not establish
the acronym or formulation "GTAT". Before the P2.7 write-up, either cite the
specific source of the GTAT formulation or state plainly that GTAT is a SeqLogAD
architectural decision informed by `S6`. Unresolved, the correct classification is
`LITERATURE_INFORMED_SEQLOGAD_DECISION`, not `LITERATURE_SUPPORTED`.

## Audit results

| Check | Result |
| --- | --- |
| `BROKEN_REFERENCE_LINKS` | 0 |
| `MISSING_ACTIVE_REFERENCE_IDS` | 0 |
| `DUPLICATE_DOI_ENTRIES` | 0 |
| `ACTIVE_SOURCE_WITHOUT_USED_BY` | 0 |
| `ACTIVE_CLAIM_WITH_UNKNOWN_REFERENCE` | 0 (one declared gap, `RSG-001`) |
