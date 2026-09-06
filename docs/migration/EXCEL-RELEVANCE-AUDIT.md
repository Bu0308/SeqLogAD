# EXCEL-RELEVANCE-AUDIT — what the workbook needs, and what it does not

Every component below was tested with one question: *does
`Bang_ke_hoach_SeqLogAD.xlsx` need this, directly or indirectly?* Relevance to the
workbook decides the outcome — not the effort already spent, and not who wrote it.

Dependency paths were derived from the import graph, config references and test
references, not from filenames.

## KEEP — active under the workbook

| Artifact | Workbook task/phase | Dependency path | Decision | Rationale |
| --- | --- | --- | --- | --- |
| `Bang_ke_hoach_SeqLogAD.xlsx` | all | root | KEEP | Authoritative plan |
| `configs/plan/excel-roadmap-v1.yaml` | all | `scripts/extract_excel_roadmap.py` → tests | KEEP | Machine-readable plan; lets tests bind to real task IDs |
| `scripts/extract_excel_roadmap.py` | all | → roadmap yaml | KEEP | Keeps the projection reproducible and staleness-checkable |
| `src/seqlogad/protocol/schema.py` | P1.3 | → folds, audit, freeze | KEEP | `LOG-UNIFY-001` |
| `src/seqlogad/protocol/nul.py` | P1.3, P1.4 | → chronology | KEEP | Byte-safety codec |
| `src/seqlogad/protocol/normalizer.py` | P1.4 | → chronology → folds | KEEP | `NORM-CS-001` |
| `configs/parsing/normalizer-cs-v1.yaml` | P1.4 | → normalizer → every manifest hash | KEEP | Versioned rule table |
| `src/seqlogad/protocol/architectures.py` | P1.1, P1.2, P1.3 | → chronology, registry | KEEP | Architecture registry and adapters |
| `src/seqlogad/protocol/chronology.py` | P1.5 | → folds, buffer, audit | KEEP | Chronological stream index |
| `configs/protocols/cross-system-split-v1.yaml` | P1.5 | → folds | KEEP | `CS-SPLIT-001` |
| `src/seqlogad/protocol/folds.py` | P1.5 | → buffer, audit, freeze | KEEP | LOAO folds |
| `configs/protocols/target-buffer-v1.yaml` | P1.6 | → buffer | KEEP | `ADAPT-INPUT-001` |
| `src/seqlogad/protocol/buffer.py` | P1.6 | → freeze | KEEP | Target burn-in |
| `src/seqlogad/protocol/labels.py` | P1.2, P1.7, P4.2 | → registry inventory only | KEEP | Evaluation-only boundary |
| `src/seqlogad/protocol/audit.py` | P1.7 | → freeze | KEEP | `LEAK-CS-001` |
| `src/seqlogad/protocol/registry.py` | P1.2 | → freeze | KEEP | `DATA-REG-001` |
| `src/seqlogad/protocol/freeze.py` | P1.8 / G0 | → receipt | KEEP | G0 receipt |
| `scripts/build_streams.py`, `scripts/build_protocol.py` | P1.2–P1.8 | drivers | KEEP | Reproduction commands |
| `src/seqlogad/common/checksum.py` | P1.2, P1.8, P4.6 | → everything | KEEP | SHA-256 identities |
| `src/seqlogad/ingestion/*` | P1.2 | → dataset CLIs, manifests | KEEP | Provenance, checksums, acquisition |
| `configs/datasets/{hdfs,bgl}.yaml` | P1.2 | → ingestion | KEEP | Acquisition contracts with verified source MD5 |
| `configs/protocols/protocol-v2-domain-adaptive-fusion.yaml` | all | → active-state | KEEP | Implementation contract, agrees with workbook |
| `docs/research-protocol-v2-domain-adaptive-fusion.md` | all | companion | KEEP | Human-readable form |
| `src/seqlogad/collection/*`, `configs/collection/v2.yaml` | P4.6 | → collection CLI, tests | KEEP | Append-only run/provenance records for reproducibility |
| `requirements.lock`, `pyproject.toml`, `Dockerfile`, `.github/workflows` | P1.8, P4.6 | environment | KEEP | Environment lock and CI |

## ADAPT — mechanism reused, old scientific instance retired

| Artifact | Old scientific instance | Reused mechanism | Decision |
| --- | --- | --- | --- |
| `src/seqlogad/parsing/normalization.py` | HDFS/BGL-only field extraction with BGL label stripping | The *idea* that inline ground truth is stripped at the adapter, generalised to four architectures in `protocol/architectures.py` | ADAPT |
| `src/seqlogad/evaluation/split.py` | 5-partition HDFS/BGL split | Deterministic floor boundaries, atomic manifest writes, membership hashing — re-expressed for LOAO in `protocol/folds.py` | ADAPT |
| `configs/protocols/canonical-nul-decision-v1.yaml` | v1.1 corpus amendment | The codec itself, adopted verbatim | ADAPT (`REUSE_WITH_EXISTING_DECISION`) |

## KEEP FOR PROVENANCE ONLY — historical, not active

These document completed decisions or bind immutable artifact identities. They are
retained, clearly labelled, and must not control routing or definitions of done.

`configs/protocols/protocol-v1.1.yaml` · `configs/protocols/effect-001.yaml` ·
`configs/protocols/split-clarification-v1.yaml` ·
`configs/protocols/purge-decision-v1.yaml` · `data/processed/splits/{hdfs,bgl}` ·
`data/processed/parsers/{hdfs,bgl}` · `data/manifests/*` ·
`src/seqlogad/evaluation/{split,test_seal,purge_audit}.py` ·
`src/seqlogad/parsing/{canonical_events,drain_parser,normal_pool,normalization}.py` ·
`src/seqlogad/ingestion/raw_metadata.py` · `src/seqlogad/common/schemas/events.py` ·
`docs/decisions/*` · `docs/audits/*` · `docs/references/*` ·
`docs/research-protocol-v1.{0,1}.md` · `Plan/*.md` · their contract tests

## DELETE — executed

Every item below satisfies all eight deletion conditions: not required by the
workbook, not useful infrastructure for anything the workbook requires, no
reproducibility or provenance value, no active import, no config reference, no
required test, no artifact reference, and no future workbook phase needs it.

**Every Python file removed was a one-line docstring placeholder with zero
implementation** — re-verified programmatically at deletion time (0 candidates had
more than one line).

### Two candidates were re-classified and NOT deleted

A pre-deletion re-audit found that `configs/models/baselines.yaml` and
`configs/experiments/detector_baselines.yaml` are referenced by
`tests/test_active_state_contract.py`, which checks that the **frozen, human-approved
`EFFECT-001` seed policy** is internally consistent with them. They therefore have
genuine provenance value and fail the "no required test dependency" and "no
provenance value" conditions. They are re-classified `KEEP_FOR_PROVENANCE_ONLY`.
P3.6 will need a fresh baseline config under the workbook; these two describe the
retired ladder and are kept only so the frozen contract stack stays verifiable.

Deleted: **75** files (77 candidates − 2 re-classified).

| Group | Items | Evidence |
| --- | --- | --- |
| Product-expansion packages | `src/seqlogad/{agent,api,rag,retrieval,scoring,sequences,storage,testing,feedback,models}` (48 files) | All 1 line; `grep` for `seqlogad.<pkg>` across `src`, `tests`, `scripts` returns 0 references except `models` (2, both from retired configs) |
| Placeholder evaluation stubs | `src/seqlogad/evaluation/{agent_eval,detector_eval,replay,retrieval_eval,leakage_audit}.py` | All 1 line; `leakage_audit` is superseded by the implemented `protocol/audit.py` |
| Placeholder parser stub | `src/seqlogad/parsing/bgl_adapter.py` | 1 line; BGL parsing lives in `protocol/architectures.py` |
| Placeholder tests | 23 one-line files under `tests/unit`, `tests/agent`, `tests/security` | All 1 line, assert nothing |
| Retired-plan configs | `configs/agent/default.yaml`, `configs/retrieval/default.yaml`, `configs/models/{lstm,transformer,baselines}.yaml`, `configs/experiments/{agent,retrieval,detector_baselines}.yaml` | Describe the retired RAG/agent product and the retired baseline ladder |
| Stale plan duplicate | `outputs/final_plan_2026_08_28/` | Duplicate of the root workbook and Word plan; hashes recorded in `EXCEL-PLAN-MIGRATION-001.md` |
| Question scratch | `Plan/Question.md` | Open questions from the retired direction, answered or obsolete |

All were git-tracked, so every deletion is recoverable from history. Executed:

```bash
git rm -r src/seqlogad/{agent,api,rag,retrieval,scoring,sequences,storage,testing,feedback,models}
git rm src/seqlogad/evaluation/{agent_eval,detector_eval,replay,retrieval_eval,leakage_audit}.py
git rm src/seqlogad/parsing/bgl_adapter.py
git rm -r tests/agent tests/security
git rm tests/unit/test_{feedback,hybrid_ranker,evidence_verifier,isolation_forest,recommendation}.py
git rm tests/unit/test_{bgl_adapter,scoring,rag_schemas,retrieval_contracts,sequential_similarity}.py
git rm tests/unit/test_{lstm_detector,schemas,generation_adapter,statistical_models}.py
git rm tests/unit/test_{transformer_detector,sequence_builder,dense_retriever,bm25_retriever}.py
git rm -r configs/agent configs/retrieval
git rm configs/models/{lstm,transformer}.yaml
git rm configs/experiments/{agent,retrieval}.yaml
git rm Plan/Question.md
rm -rf outputs/final_plan_2026_08_28
```

`configs/models/baselines.yaml` and `configs/experiments/detector_baselines.yaml`
are deliberately absent from that list.

### Post-deletion verification

- `ACTIVE_REFERENCE_COUNT = 0`. Two textual occurrences of `seqlogad.models` remain,
  in `tests/unit/test_split.py:164` and `tests/unit/test_purge_audit.py:236` — both
  are **negative assertions** that the module is *not* imported, so they are guards
  rather than dependencies and are now trivially satisfied.
- All 10 `pyproject.toml` console-script entry points still resolve.
- Full suite: 311 passed.

`.ai/` was **not** deleted. It is untracked, so deletion would be unrecoverable, and
its routing structure is useful infrastructure rather than dead weight. It has been
retired in place: `.ai/README.md` now states that the workbook is authoritative and
that the v1.1 routing it describes is historical.

`_agent_ops/` and `_agent_workspace_pack/` are untracked, git-ignored local agent
tooling (the latter contains its own `.git`). They carry no scientific content and
are out of scope for this migration.

## Counts

| Outcome | Count |
| --- | --- |
| `FILES_KEPT` (active) | 27 groups |
| `FILES_ADAPTED` | 3 |
| `FILES_ARCHIVED` (provenance only) | 20 groups + 2 re-classified from delete |
| `FILES_DELETED` | **75 executed** |

`OLD_PLAN_ACTIVE_REFERENCES_REMAINING = 0` — no retired pointer
(`SEQ-001`, `THEORY-COMPLETE-001`, `KT-1/2/3`, `EFFECT-001`, `CANONICAL-EVENT-001`
as next task, the Transformer/fusion gates) is reachable from
`configs/active-state.yaml`, and `tests/test_excel_plan_authority.py` asserts it.
The retired names still appear inside historical documents, which is where they
belong.
