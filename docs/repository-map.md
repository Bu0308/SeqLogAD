# Repository Map

This document describes the repository after Day 2 dataset acquisition foundations. All later pipeline work remains deferred.

## Top-level areas

| Path | Responsibility | Current status |
|---|---|---|
| `configs/` | Version-controlled dataset, model, retrieval, agent and experiment configuration | HDFS/BGL acquisition contracts; later configs remain placeholders |
| `data/` | Raw, manifest, parsed, processed and knowledge-base stages | Raw directories empty; no dataset downloaded; manifest policy documented |
| `docs/` | Architecture, research, experiment, testing and Day 1 conventions | Active documentation |
| `notebooks/` | Exploration and result visualization only | README only |
| `src/` | Reusable production modules | Day 2 checksum/acquisition/manifest tooling only |
| `tests/` | Unit, integration, API, agent, security and performance tests | Day 1 smoke test, Day 2 offline tests and later placeholders |
| `scripts/` | Thin orchestration entry points | Day 2 download, manifest-build and verification commands |
| `outputs/` | Experiment-specific checkpoints, indexes, results, reports, traces and run metadata | README only |
| `docker/` | Container/deployment documentation | README only |
| `.github/workflows/` | Future CI workflows | README only |

## Source modules

| Module | Responsibility | First relevant task |
|---|---|---|
| `src/ingestion/` | Dataset acquisition, presence, manifest and future source adapters | DATA-001 active |
| `src/parsing/` | Drain3 and BGL canonical parsing | PARSE-001/002 |
| `src/sequences/` | Session, block, sliding and time-window construction | SEQ-001 |
| `src/models/` | Statistical, Isolation Forest, LSTM and optional Transformer detectors | DET-002–005 |
| `src/scoring/` | Event-to-sequence aggregation and thresholds | DET-001 |
| `src/retrieval/` | BM25, dense, sequential and hybrid retrieval | RETR-001–006 |
| `src/rag/` | Knowledge base, evidence, hypotheses and verifier | KB-001, RAG-001/002 |
| `src/agent/` | Bounded single-agent workflow, tools and traces | AGT-001/002 |
| `src/evaluation/` | Splits, leakage audits and benchmark evaluation | SEQ-002, EVAL-001 |
| `src/api/` | Future FastAPI thin layer | API-001 |
| `src/common/` | Shared checksum now; canonical schemas later | DATA-001 active, DATA-002 next |
| `src/storage/` | Backend-independent storage boundary | RETR-001, ELK-001 |
| `src/testing/` | Structured test recommendation and optional skeleton validation | TEST-001/002 |
| `src/feedback/` | Future human-review persistence | FEED-001 |
| `src/ui/` | Future Streamlit views | UI-001 |

## Deliberate differences from the reference map

- Dataset configs use `configs/datasets/hdfs.yaml` and `configs/datasets/bgl.yaml`, not one combined file.
- Real manifests live under `data/manifests/`; tiny synthetic bytes under `tests/fixtures/datasets/` are test data, not HDFS/BGL samples.
- Model configs are grouped under `configs/models/`.
- `src/storage/` exists because the architecture requires a backend boundary before Elasticsearch integration.
- No `data/evaluation/`, `src/common/config/`, `src/common/logging/` or implementation-only directories were added because they are not needed for Day 1.
- Detailed planning artifacts remain local-only; public operational contracts live under `docs/`.
