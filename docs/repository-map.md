# Repository map

**Authoritative plan: `Bang_ke_hoach_SeqLogAD.xlsx`** (projected to
`configs/plan/excel-roadmap-v1.yaml`). Phase 1 is implemented under
`src/seqlogad/protocol/`; the v1.1 HDFS/BGL machinery is retained as historical
provenance and controls nothing.

## Top-level areas

| Path | Responsibility | Current status |
|---|---|---|
| `configs/` | v2 forward protocol/model/experiment contracts plus frozen v1.1 foundation | v2 planning-only; v1.1 data contracts preserved |
| `research_records/` | Append-only v2 process-evidence JSONL record root | Schema-ready; no raw events or target-adaptation labels |
| `data/raw/` | Immutable local HDFS/BGL bytes | Present locally; ignored by Git |
| `data/manifests/` | Accepted raw-file hashes and dataset fingerprints | Implemented, verified, version-controlled |
| `data/parsed/` | Future parser/canonical-event artifacts | Empty/generated contents ignored |
| `data/processed/` | Derived split/parser/sequence/control artifacts | Real local split and frozen parser artifacts present and verified; generated contents ignored |
| `docs/` | v2 scope/protocol/RQs plus v1.1 literature, audits and citations | v2 forward; v1.1 preserved |
| `Plan/` | v2 plan/migration plus historical v1.1/V1/V3 plans and ADRs | Version-controlled |
| `src/seqlogad/protocol/` | **Phase 1 implementation** (schema, NUL codec, normaliser, architectures, chronology, folds, buffer, labels, audit, freeze) | Implemented; artifacts materialised |
| `src/seqlogad/` | Canonical installable Python package | Ingestion, checksums and Phase 1 protocol implemented; retired-plan placeholder modules pending removal (see relevance audit) |
| `data/registry/` | `DATA-REG-001` active dataset registry | Implemented; 4 active architectures |
| `data/processed/protocol/` | Stream indices, folds, buffers, isolation audits, G0 receipt | Implemented; generated contents ignored by Git |
| `scripts/` | Compatibility wrappers for installed foundation CLIs | Acquisition/manifest/metadata/split wrappers implemented |
| `tests/` | Active foundation/schema/protocol contracts and labeled future placeholders | Current suite must pass; placeholders are not implementation claims |
| `outputs/` | Experiment-specific outputs | Generated contents ignored |
| `docker/` | Container documentation | Minimal runtime skeleton only |
| `.github/workflows/` | Continuous integration | Minimal Python/pip/pytest workflow |

## Package modules

| Module | Active responsibility | Status/scope |
|---|---|---|
| `seqlogad.ingestion` | Dataset config, acquisition, checksums, manifests, verification | Implemented |
| `seqlogad.common.schemas` | Canonical event/template and sequence/localization/mutation contracts | Implemented/tested; no real artifact generated |
| `seqlogad.parsing` | Scoped normal-BASE selection, Drain3 fit/freeze/restore, immutable match, unknown-event policy | PARSE-001 implemented/tested; canonical event adapters remain CANONICAL-EVENT-001 |
| `seqlogad.sequences` | Historical HDFS/BGL construction and sequence-destruction provenance | v1.1 preserved; v2 unified sequence view planned |
| `seqlogad.models` | Historical order-insensitive controls plus v2 expert boundaries | v2 experts/fusion not implemented |
| `seqlogad.evaluation` | Historical raw split/TEST guard plus v2 LOAO evaluation boundary | v2 evaluation planned |
| `seqlogad.collection` | Validated append-only process records and package-level audit checks | v2 collection core implemented |
| `seqlogad.scoring` | Validation-only aggregation/threshold contracts | MUST when detector exists |
| `seqlogad.retrieval`, `rag`, `agent`, `testing` | Former V3/downstream modules | FUTURE / placeholders only |
| `seqlogad.api`, `ui`, `storage` | Delivery/backend boundaries | FUTURE / placeholders only |

## Preserved foundation execution flow

Implemented today:

```text
dataset YAML → source/path checks → acquisition policy → required-file checks
→ deterministic manifest/fingerprint → independent verification

synthetic schema fixture → strict validation → deterministic serialization/identity

verified raw bytes → META-001 structural identity → deterministic five-way split
→ exact reconciliation/hashes → physical TEST seal

ordinary BASE membership → scoped normal-label selection → normal-pool identity
→ Drain3 fit/freeze → independent restore → immutable frozen match
```

Not implemented today (v2):

```text
unified multi-architecture registry → LOAO folds → target buffer
→ Llama adapters/GTAT → calibration → adaptive gate → held-out evaluation
```

## Boundaries

- Imports use installed `seqlogad.*`, not cwd/PYTHONPATH hacks.
- Raw bytes/manifests are not changed by scientific planning.
- TEST remains unavailable to routine model/data-selection code.
- Future downstream modules cannot fit, change, or override detectors.
- Historical documents are evidence of prior decisions, not active requirements.
