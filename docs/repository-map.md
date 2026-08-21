# Repository Map — V3

This map distinguishes the implemented dataset-integrity foundation from planned V3 research modules.

## Top-level areas

| Path | Responsibility | Current status |
|---|---|---|
| `configs/` | Version-controlled dataset, scientific protocol, and future experiment contracts | Dataset configs and `protocols/protocol-v1.yaml` active; model/experiment configs are non-runnable placeholders |
| `data/raw/` | Immutable local HDFS/BGL bytes | Present locally; contents ignored by Git |
| `data/manifests/` | Exact accepted raw-file identities | HDFS and BGL manifests implemented and verified |
| `data/parsed/` | Future canonical events/templates | Planned; generated contents ignored |
| `data/processed/` | Future sequences/splits/features/evidence | Planned; generated contents ignored |
| `docs/` | Active public scope, research, dataset, and reproducibility contracts | Active V3 documentation |
| `Plan/` | Version-controlled historical and V3 planning/decision records | V3 synchronization active; older master preserved |
| `src/seqlogad/` | Canonical installable Python package | Ingestion integrity and CLI modules implemented; other areas placeholders |
| `scripts/` | Compatibility wrappers for installed command entrypoints | Dataset acquisition/manifest/verification wrappers implemented |
| `tests/` | Offline unit/integration/security/performance contracts | 73 active foundation/environment/protocol/schema tests; future tests are placeholders |
| `outputs/` | Experiment-specific artifacts | Generated contents ignored |
| `docker/` | Future container setup | Documentation placeholder |
| `.github/workflows/` | Future CI | Documentation placeholder only |

## V3 module responsibilities

| Module | V3 responsibility | Status |
|---|---|---|
| `src/seqlogad/ingestion/` | Dataset contracts, acquisition, checksums, manifests, verification | Implemented |
| `src/seqlogad/common/schemas/` | Canonical events, sequences, mutations, ExpertEvidence, claims | `LogEvent`/`EventTemplate` approved; sequence/localization/mutation contracts await audit; evidence schemas planned |
| `src/seqlogad/parsing/` | Frozen train-fitted Drain3 and dataset adapters | Planned |
| `src/seqlogad/sequences/` | HDFS block/BGL windows and token/gap/transition mutation labels | Planned |
| `src/seqlogad/models/` | Statistical/LSTM baselines and experts A–C | Planned |
| `src/seqlogad/retrieval/` | Expert D structural normal-reference retrieval; dense P1 | Planned |
| `src/seqlogad/scoring/` | Aggregation, thresholds, calibration, masks | Planned |
| `src/seqlogad/evaluation/` | Five-way split, leakage audit, expert/complementarity/fusion metrics | Planned |
| `src/seqlogad/rag/` | Downstream evidence schemas and verifier | Planned downstream |
| `src/seqlogad/agent/` | Read-only consumer of frozen evidence artifacts | Planned downstream |
| `src/seqlogad/testing/` | Structured regression-test recommendation | Planned downstream |
| `src/seqlogad/storage/` | Backend-independent local/Elasticsearch boundary | Planned |
| `src/seqlogad/api/`, `src/seqlogad/ui/` | Thin future delivery surfaces | Planned P1 |

## Active execution flow

Implemented foundation flows are:

```text
dataset YAML → path/config validation → acquisition/checksum policy
→ required-file validation → manifest build/reload → integrity verification

synthetic schema input → strict LogEvent/EventTemplate/EventSequence/MutationRecord validation
→ deterministic identity/serialization → label-free model-input view
```

No real log has been parsed into canonical events. The V3 scientific path from parser execution onward remains planned.

## Architecture boundaries

- Experts and fusion do not depend on FastAPI, Streamlit, Elasticsearch, or an LLM provider.
- Expert D uses only `BASE_TRAIN` normal references.
- Agent/RAG cannot fit or alter detectors and cannot perform production writes.
- All future commands remain thin wrappers over tested `seqlogad.*` package logic.
- Installed commands accept an explicit repository root for data/config resolution; imports never depend on cwd.
