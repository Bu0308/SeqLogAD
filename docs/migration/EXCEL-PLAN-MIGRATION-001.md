# EXCEL-PLAN-MIGRATION-001 — migration to the workbook as the authoritative plan

| Field | Value |
| --- | --- |
| Migration ID | `EXCEL-PLAN-MIGRATION-001` |
| Date | 2026-09-06 |
| Authoritative plan | `Bang_ke_hoach_SeqLogAD.xlsx` |
| Workbook SHA-256 | `c33aad3333c0d1b032ad324459392f2e5da4b65eb85603d80c2130dfd174d56b` |
| Machine-readable projection | `configs/plan/excel-roadmap-v1.yaml` |
| Authority | Human researcher declaration |
| Empirical status | `NOT_RUN` |

## What changed

The researcher declared `Bang_ke_hoach_SeqLogAD.xlsx` the primary and authoritative
scientific roadmap. Where the workbook and any earlier plan disagree, the workbook
wins. This is an approved plan migration, not a contract violation.

The workbook is not a restatement of the v1.1 study. It defines a different research
programme: **Domain-Adaptive Fusion for zero-label cross-system log anomaly
detection**, in four phases (P1 Data & Protocol, P2 Representation & Experts,
P3 Adaptation & Fusion, P4 Cross-System Validation) with five gates G0–G4, 32
micro-tasks and 11 verified citation keys.

Much of that direction had already been captured in this repository as the
user-approved v2 protocol (`DOMAIN-ADAPTIVE-FUSION-001`) on 2026-08-28. The
workbook and the existing v2 contract agree on objective, expert stack, LOAO folds,
zero-label target adaptation and the gate ladder. That prior work is therefore
**reused, not rewritten**; this migration promotes the workbook above it as the
source of truth and adds the machine-readable projection, the task IDs and the
Phase 1 implementation the v2 contract only described.

## Disposition table

| Artifact | Old role | New role | Classification | Action | Active? | Provenance retained | Rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Bang_ke_hoach_SeqLogAD.xlsx` | new input | authoritative plan | — | promoted | yes | yes | Researcher declaration |
| `configs/plan/excel-roadmap-v1.yaml` | — | machine-readable plan | new | created | yes | yes | Lets code/tests/CI bind to workbook task IDs |
| `configs/protocols/protocol-v2-domain-adaptive-fusion.yaml` | forward plan | implementation contract under the workbook | `REUSE_AS_IS` | kept | yes | yes | Agrees with the workbook on every scientific point |
| `docs/research-protocol-v2-domain-adaptive-fusion.md` | forward contract | human-readable companion | `REUSE_AS_IS` | kept | yes | yes | Same |
| `docs/plan-migration-v1.1-to-v2.md` | v1.1→v2 record | historical migration record | `KEEP_FOR_PROVENANCE_ONLY` | kept | no | yes | Explains how the direction changed |
| `configs/protocols/protocol-v1.1.yaml` | active protocol | historical foundation | `SUPERSEDED` | retained | no | yes | Binds the frozen HDFS/BGL artifacts |
| `configs/protocols/effect-001.yaml` | binding addendum | historical | `SUPERSEDED` | retained | no | yes | Effect size for the retired order-sensitivity study |
| `configs/protocols/split-clarification-v1.yaml` | binding addendum | historical | `SUPERSEDED` | retained | no | yes | Clarifies the retired 5-way split |
| `configs/protocols/purge-decision-v1.yaml` | binding addendum | historical | `KEEP_FOR_PROVENANCE_ONLY` | retained | no | yes | Human-approved decision on a real data property |
| `configs/protocols/canonical-nul-decision-v1.yaml` | pending amendment | **reused policy** | `REUSE_WITH_EXISTING_DECISION` | adopted | yes | yes | See "NUL policy" below |
| `data/processed/splits/{hdfs,bgl}` | active splits | historical | `SUPERSEDED_FOR_ACTIVE_EXCEL_PROTOCOL` | retained untouched | no | yes | Not LOAO; hashes still referenced by frozen records |
| `data/processed/parsers/{hdfs,bgl}` | frozen Drain3 state | optional template source | `KEEP_FOR_PROVENANCE_ONLY` | retained untouched | no | yes | Workbook P1.4 makes templates auxiliary |
| `src/seqlogad/evaluation/split.py` | active split engine | historical engine | `SUPERSEDED` | retained | no | yes | Regenerates/validates the frozen artifacts |
| `src/seqlogad/evaluation/test_seal.py` | TEST sealing | historical | `KEEP_FOR_PROVENANCE_ONLY` | retained | no | yes | Frozen TEST seals must stay verifiable |
| `src/seqlogad/parsing/canonical_events.py` | canonical corpus | historical | `SUPERSEDED` | retained | no | yes | Bound to the retired 5-partition split |
| `src/seqlogad/parsing/normalization.py` | HDFS/BGL field split | historical; generalised | `REUSE_WITH_ADAPTATION` | superseded by `protocol/architectures.py` | no | yes | Its label-stripping idea is carried forward |
| `src/seqlogad/ingestion/*` | dataset provenance | still provenance | `REUSE_AS_IS` | kept | yes | yes | Checksums, manifests, acquisition |
| `src/seqlogad/common/checksum.py` | hashing | hashing | `REUSE_AS_IS` | kept | yes | yes | Used by every new artifact |
| `src/seqlogad/common/schemas/events.py` | canonical event schema | historical schema | `KEEP_FOR_PROVENANCE_ONLY` | retained | no | yes | Superseded for the active path by `LOG-UNIFY-001` |
| `src/seqlogad/protocol/*` | — | Phase 1 implementation | new | created | yes | yes | Implements workbook P1.1–P1.8 |
| `src/seqlogad/{agent,api,rag,retrieval,scoring,sequences,storage,testing,feedback,models,ui}` | product expansion | none | `SAFE_TO_DELETE` | **deleted** | no | git history | All one-line placeholders, zero imports |
| `configs/models/baselines.yaml`, `configs/experiments/detector_baselines.yaml` | retired baseline ladder | frozen EFFECT-001 seed-policy witnesses | `KEEP_FOR_PROVENANCE_ONLY` | kept | no | yes | Re-classified from delete: a required historical test binds them |
| `.ai/` | agent routing for v1.1 | conflicting plan pointer | `SUPERSEDED` | retired in place | no | yes | See "Blocked cleanup" |
| `Plan/master-implementation-plan*.md`, `Plan/0*_*.md` | earlier plans | historical | `KEEP_FOR_PROVENANCE_ONLY` | retained | no | yes | Already self-labelled historical |
| `outputs/final_plan_2026_08_28/` | plan snapshot | stale duplicate | `SAFE_TO_DELETE` | **deleted** | no | hashes recorded below | Duplicate of the root workbook and Word plan |

## Retired from active execution

The following were active routing or scientific contracts under the v1.1 plan and
are **not** active under the workbook. None is deleted; each is retained as
historical provenance and must not control task routing, gates or definitions of
done.

- Sequence-order-added-value as the primary research question
- `EFFECT-001` effect-size contract for that question
- `KT-1`, `KT-2`, `KT-3` knowledge-transfer ladder
- Mandatory Markov / N-gram comparator ladder
- Conditional Transformer gate and conditional localization/fusion gate
- `THEORY-COMPLETE-001` routing
- `SEQ-001` as the next authorized task
- `CANONICAL-EVENT-001` as the next scientific task
- The HDFS/BGL-only 5-partition split as the active evaluation design
- The one-time sealed-TEST final-evaluation workflow as the active endpoint

`NEXT_AUTHORIZED_TASK` is now `P2.1` (freeze the Llama-3.1-8B base, tokenizer,
licence and GPU budget), taken directly from the workbook.

## NUL policy

`CANONICAL-NUL-DECISION-001` recommended Option A, `seqlogad-nul-escape-v1`, and was
frozen in `HUMAN_REVIEW_READY` state under the v1.1 plan. Its codec, status
vocabulary, collision grammar and hash contract are fully specified and
unambiguous.

Workbook P1.3/P1.4 independently require a deterministic, reversible, provenance-
preserving canonical message that never silently drops a record. Rather than invent
a second, competing policy for the same problem, the existing decision is adopted
verbatim as the byte-safety layer of the new multi-source schema.

Classification: **`REUSE_WITH_EXISTING_DECISION`** — not a new methodological
choice. `src/seqlogad/protocol/nul.py` transcribes the specification; nothing in it
was redesigned. The frozen decision covers `0x00` only, so other C0 control bytes
are left untouched by the codec and are handled one layer later by the
`NORM-CS-001` rule `control_char`, which keeps the approved codec byte-identical to
what was reviewed.

The v1.1-scoped consequences of that decision (regenerating the HDFS/BGL canonical
corpus, `CANONICAL-EVENT-001`) remain blocked and unexecuted; they belong to the
retired plan.

## Cleanup executed

Deletion was denied by the sandbox during the initial run and was completed in the
pre-sign audit. **75 files removed**, all git-tracked and therefore recoverable:

1. `src/seqlogad/{agent,api,rag,retrieval,scoring,sequences,storage,testing,feedback,models,ui}`
   plus `src/seqlogad/evaluation/{agent_eval,detector_eval,replay,retrieval_eval,leakage_audit}.py`
   and `src/seqlogad/parsing/bgl_adapter.py` — every one a one-line docstring
   placeholder, re-verified programmatically before removal.
2. 23 one-line placeholder test files, and the retired-plan configs under
   `configs/{agent,retrieval,models,experiments}` **except** the two re-classified
   below.
3. `outputs/final_plan_2026_08_28/` and `Plan/Question.md`.

   | File | SHA-256 |
   | --- | --- |
   | `Bang_ke_hoach_SeqLogAD.xlsx` (root, authoritative) | `c33aad3333c0d1b032ad324459392f2e5da4b65eb85603d80c2130dfd174d56b` |
   | `outputs/final_plan_2026_08_28/Bang_ke_hoach_SeqLogAD.xlsx` (deleted duplicate) | `d376553fa71bcda3f9507206de2c5554f7c66f16006122cf32810cd7faf4cfd6` |
   | `Ke_hoach_cuoi_SeqLogAD.docx` (both copies were identical) | `ecdaa6c65523c775391ce298f284c3a921bfd16c383071fd339f5da1318b0e9e` |

   The two workbook copies differed only in cell `Task Register!K4` (P1.1 status
   `Ready` → `Done`), and the retained root copy is the newer one.

**Re-classified, not deleted:** `configs/models/baselines.yaml` and
`configs/experiments/detector_baselines.yaml`. A pre-deletion re-audit found them
bound to the frozen, human-approved `EFFECT-001` seed policy through a historical
consistency test, so they carry real provenance value.

`.ai/` was retired in place rather than deleted — it is untracked, so deletion would
be unrecoverable, and its routing structure is useful infrastructure. Its files now
state that the workbook is authoritative, and the three context packs describing
retired workstreams carry a HISTORICAL banner.

`_agent_ops/` and `_agent_workspace_pack/` are untracked, git-ignored local agent
tooling (the latter contains its own `.git`). They carry no scientific content and
are out of scope.

## Counts

| Classification | Count |
| --- | --- |
| `REUSE_AS_IS` | 5 |
| `REUSE_WITH_ADAPTATION` | 2 |
| `REUSE_WITH_EXISTING_DECISION` | 1 |
| `KEEP_FOR_PROVENANCE_ONLY` | 6 |
| `SUPERSEDED` (retired from active execution) | 6 |
| `REMOVED_FROM_ACTIVE` (routing pointers retired) | 10 |
| `SAFE_TO_DELETE` (executed) | 75 files |

## Active-plan invariant

After this migration there is exactly one scientific plan:
`Bang_ke_hoach_SeqLogAD.xlsx`, projected to `configs/plan/excel-roadmap-v1.yaml`.
Everything else is supporting implementation, supporting evidence, or explicitly
labelled historical provenance. `tests/test_excel_plan_authority.py` asserts that no
retired pointer is reachable from `configs/active-state.yaml`.
