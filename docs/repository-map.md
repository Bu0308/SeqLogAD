# Repository Map — Research Freeze v1.1

## Top-level areas

| Path | Responsibility | Current status |
|---|---|---|
| `configs/` | Dataset contracts, active protocol v1.1, and clearly gated placeholders | Dataset/protocol active; model/experiment placeholders non-runnable |
| `data/raw/` | Immutable local HDFS/BGL bytes | Present locally; ignored by Git |
| `data/manifests/` | Accepted raw-file hashes and dataset fingerprints | Implemented, verified, version-controlled |
| `data/parsed/` | Future parser/canonical-event artifacts | Empty/generated contents ignored |
| `data/processed/` | Future split/sequence/control artifacts | Empty/generated contents ignored |
| `docs/` | Active scope, protocol, RQs, dataset cards, literature, citations | v1.1 active; v1.0 preserved |
| `Plan/` | Active v1.1 plan plus historical V1/V2/V3 plans and ADRs | Intended to be version-controlled |
| `src/seqlogad/` | Canonical installable Python package | Ingestion and schemas implemented; scientific pipeline placeholders |
| `scripts/` | Compatibility wrappers for installed data-foundation CLIs | Implemented for acquisition/manifest/verification only |
| `tests/` | Active foundation/schema/protocol contracts and labeled future placeholders | Current suite must pass; placeholders are not implementation claims |
| `outputs/` | Experiment-specific outputs | Generated contents ignored |
| `docker/` | Container documentation | Minimal runtime skeleton only |
| `.github/workflows/` | Continuous integration | Minimal Python/pip/pytest workflow |

## Package modules

| Module | Active responsibility | Status/scope |
|---|---|---|
| `seqlogad.ingestion` | Dataset config, acquisition, checksums, manifests, verification | Implemented |
| `seqlogad.common.schemas` | Canonical event/template and sequence/localization/mutation contracts | Implemented/tested; no real artifact generated |
| `seqlogad.parsing` | Future normal-BASE Drain3 fit/freeze/read-only transform | MUST / not implemented |
| `seqlogad.sequences` | HDFS/BGL construction and sequence-destruction provenance | MUST / not implemented |
| `seqlogad.models` | Order-insensitive controls and Markov/N-gram | MUST/SHOULD / not implemented; neural models conditional/non-core |
| `seqlogad.evaluation` | Raw split, TEST guard, leakage audit, KT-1–KT-3 metrics | MUST / not implemented |
| `seqlogad.scoring` | Validation-only aggregation/threshold contracts | MUST when detector exists |
| `seqlogad.retrieval`, `rag`, `agent`, `testing` | Former V3/downstream modules | FUTURE / placeholders only |
| `seqlogad.api`, `ui`, `storage` | Delivery/backend boundaries | FUTURE / placeholders only |

## Active execution flow

Implemented today:

```text
dataset YAML → source/path checks → acquisition policy → required-file checks
→ deterministic manifest/fingerprint → independent verification

synthetic schema fixture → strict validation → deterministic serialization/identity
```

Not implemented today:

```text
raw pre-partition → parser fit/freeze → canonical artifacts → sequences
→ baselines → Markov → sequence destruction → scientific gate → TEST
```

## Boundaries

- Imports use installed `seqlogad.*`, not cwd/PYTHONPATH hacks.
- Raw bytes/manifests are not changed by scientific planning.
- TEST remains unavailable to routine model/data-selection code.
- Future downstream modules cannot fit, change, or override detectors.
- Historical documents are evidence of prior decisions, not active requirements.
