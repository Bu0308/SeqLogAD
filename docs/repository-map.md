# Repository Map — V3

This map distinguishes the implemented dataset-integrity foundation from planned V3 research modules.

## Top-level areas

| Path | Responsibility | Current status |
|---|---|---|
| `configs/` | Version-controlled dataset and future experiment contracts | Dataset configs active; model/experiment configs are non-runnable placeholders |
| `data/raw/` | Immutable local HDFS/BGL bytes | Present locally; contents ignored by Git |
| `data/manifests/` | Exact accepted raw-file identities | HDFS and BGL manifests implemented and verified |
| `data/parsed/` | Future canonical events/templates | Planned; generated contents ignored |
| `data/processed/` | Future sequences/splits/features/evidence | Planned; generated contents ignored |
| `docs/` | Active public scope, research, dataset, and reproducibility contracts | Active V3 documentation |
| `Plan/` | Version-controlled historical and V3 planning/decision records | V3 synchronization active; older master preserved |
| `src/` | Reusable implementation modules | Ingestion integrity implemented; other areas placeholders |
| `scripts/` | Thin command entrypoints | Dataset acquisition/manifest/verification implemented |
| `tests/` | Offline unit/integration/security/performance contracts | 27 active foundation tests; future tests are placeholders |
| `outputs/` | Experiment-specific artifacts | Generated contents ignored |
| `docker/` | Future container setup | Documentation placeholder |
| `.github/workflows/` | Future CI | Documentation placeholder only |

## V3 module responsibilities

| Module | V3 responsibility | Status |
|---|---|---|
| `src/ingestion/` | Dataset contracts, acquisition, checksums, manifests, verification | Implemented |
| `src/common/schemas/` | Canonical events, sequences, mutations, ExpertEvidence, claims | Planned |
| `src/parsing/` | Frozen train-fitted Drain3 and dataset adapters | Planned |
| `src/sequences/` | HDFS block/BGL windows and token/gap/transition mutation labels | Planned |
| `src/models/` | Statistical/LSTM baselines and experts A–C | Planned |
| `src/retrieval/` | Expert D structural normal-reference retrieval; dense P1 | Planned |
| `src/scoring/` | Aggregation, thresholds, calibration, masks | Planned |
| `src/evaluation/` | Five-way split, leakage audit, expert/complementarity/fusion metrics | Planned |
| `src/rag/` | Downstream evidence schemas and verifier | Planned downstream |
| `src/agent/` | Read-only consumer of frozen evidence artifacts | Planned downstream |
| `src/testing/` | Structured regression-test recommendation | Planned downstream |
| `src/storage/` | Backend-independent local/Elasticsearch boundary | Planned |
| `src/api/`, `src/ui/` | Thin future delivery surfaces | Planned P1 |

## Active execution flow

Today the only implemented flow is:

```text
dataset YAML → path/config validation → acquisition/checksum policy
→ required-file validation → manifest build/reload → integrity verification
```

The V3 scientific path from canonical event onward is planned, not implemented.

## Architecture boundaries

- Experts and fusion do not depend on FastAPI, Streamlit, Elasticsearch, or an LLM provider.
- Expert D uses only `BASE_TRAIN` normal references.
- Agent/RAG cannot fit or alter detectors and cannot perform production writes.
- All future commands remain thin wrappers over tested `src/` logic.
- The existing `src.*` import/package convention requires a packaging review before implementation expansion.
