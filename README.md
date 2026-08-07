<div align="center">

# SeqLogAD

### Sequence-Based Unsupervised Anomaly Detection for Large-Scale Event Logs

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
![Tests](https://img.shields.io/badge/tests-27%20passed-brightgreen)
![Stage](https://img.shields.io/badge/stage-data%20integrity-orange)
![Type](https://img.shields.io/badge/type-research%20prototype-8A2BE2)

An eight-week research project exploring behavioral anomaly detection in event-log sequences, with a planned evidence-grounded investigation and QA layer.

</div>

> [!IMPORTANT]
> The repository currently implements the **dataset acquisition, provenance, checksum, manifest, and verification foundation**. Parsing, sequence construction, anomaly models, retrieval, RAG, and the investigation agent are planned but not implemented yet.

## Why sequence-aware anomaly detection?

Many operational failures are invisible to event-frequency monitoring. Every event may be common and no `ERROR` message may appear, while the execution order is still wrong.

```text
Expected: LOGIN_REQUEST → TOKEN_VALIDATE → USER_LOOKUP → SESSION_CREATE → LOGIN_SUCCESS
Observed: LOGIN_REQUEST →                  USER_LOOKUP → SESSION_CREATE → LOGIN_SUCCESS
```

The anomaly is the missing validation step, not an unusual individual log line. SeqLogAD is designed to study missing, extra, reordered, repeated, unexpected-transition, timing, and contextual sequence anomalies.

## Project positioning

SeqLogAD is intended to become a **sequence-aware AI investigation and QA layer on top of log and observability infrastructure**.

It is not an Elasticsearch or Kibana replacement. Elasticsearch may later provide storage, filtering, lexical search, and vector retrieval; the research focus remains sequence intelligence, evidence verification, and test recommendation.

## Current status

| Capability | Status | What exists today |
|---|---|---|
| Dataset contracts | ✅ Implemented | Strict Pydantic/YAML contracts for HDFS and BGL |
| Safe acquisition | ✅ Implemented | Dry-run, timeout, temporary `.part` file, checksum gate, no extraction |
| File integrity | ✅ Implemented | Streaming MD5/SHA-256 helpers and source checksum validation |
| Dataset manifests | ✅ Implemented | Deterministic JSON manifests and content-based fingerprints |
| Manifest verification | ✅ Implemented | Required-file, size, checksum, and mutation checks |
| Real BGL acceptance | ✅ Verified | Canonical archive and extracted bytes verified end to end |
| Real HDFS acceptance | 🟡 Partial | Extracted bytes verified; canonical source archive re-check remains open |
| Parsing and event templates | ⏳ Planned | Module placeholders only |
| Sequence construction and splits | ⏳ Planned | Module placeholders only |
| Baselines, LSTM, Transformer | ⏳ Planned | Module placeholders only |
| Retrieval, RAG, agent, API, UI | ⏳ Planned | Module placeholders only |

## Target architecture

```mermaid
flowchart LR
    A["Raw event logs"] --> B["Dataset integrity gate<br/>Implemented"]
    B --> C["Parsing and event templates<br/>Planned"]
    C --> D["Event sequences<br/>Planned"]
    D --> E["Unsupervised anomaly detection<br/>Planned"]
    E --> F["Sequence-aware retrieval<br/>Planned"]
    F --> G["Evidence-grounded investigation<br/>Planned"]
    G --> H["Root-cause hypotheses and QA tests<br/>Planned"]

    classDef active fill:#d1fae5,stroke:#059669,color:#064e3b;
    classDef planned fill:#f3f4f6,stroke:#9ca3af,color:#374151;
    class B active;
    class A,C,D,E,F,G,H planned;
```

## Dataset provenance

Raw benchmark data is intentionally excluded from Git. Version-controlled manifests identify the exact extracted bytes expected by this project.

| Dataset | Manifested files | Manifested bytes | Required files | Manifest | Source archive gate |
|---|---:|---:|---|---|---|
| HDFS_v1 | 6 | 1,828,041,800 | 2/2 present | ✅ Verified | 🟡 Archive re-check pending |
| BGL | 1 | 743,185,031 | 1/1 present | ✅ Verified | ✅ Verified |

<details>
<summary>Dataset fingerprints</summary>

- **HDFS_v1:** `0103c63b2847ba98b0b309a9e06eebb80ac8030e2f92d1f62320742537a34013`
- **BGL:** `c9ee7a8db13d37c88f896e305ed12dc7a66b586cdae4e388db4949f78afbe861`

</details>

See the [HDFS dataset card](docs/datasets/hdfs.md), [BGL dataset card](docs/datasets/bgl.md), and [acquisition policy](docs/dataset-acquisition.md) for source checksums, expected paths, integrity status, and usage notes.

## Quick start

### 1. Clone and create an environment

```bash
git clone https://github.com/Bu0308/SeqLogAD.git
cd SeqLogAD

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

### 2. Run the offline test suite

```bash
python3 -m pytest -q
```

Current expected result:

```text
27 passed
```

### 3. Prepare datasets

Datasets are not included in the repository. Follow [docs/dataset-acquisition.md](docs/dataset-acquisition.md) and preserve the expected layout:

```text
data/raw/hdfs/HDFS_v1/
├── HDFS.log
└── preprocessed/anomaly_label.csv

data/raw/bgl/BGL/
└── BGL.log
```

Preview configured download destinations without network transfer:

```bash
python3 -m scripts.download_data --dataset all --dry-run
```

### 4. Verify local bytes against the manifests

```bash
python3 -m scripts.verify_dataset --dataset hdfs --json
python3 -m scripts.verify_dataset --dataset bgl --json
```

For initial dataset registration, `scripts.build_dataset_manifest` creates the manifest only when required files are complete. It refuses to overwrite an existing manifest unless `--force` is explicitly supplied and never modifies raw files.

## Implemented command-line tools

| Command | Purpose |
|---|---|
| `python3 -m scripts.download_data --dataset <name>` | Safely download the configured source archive without extraction |
| `python3 -m scripts.download_data --dataset all --dry-run` | Resolve sources and destinations without network access |
| `python3 -m scripts.build_dataset_manifest --dataset <name>` | Build a deterministic manifest from local bytes |
| `python3 -m scripts.verify_dataset --dataset <name> --json` | Recompute and report required-file and manifest integrity |

Supported dataset keys are `hdfs` and `bgl`.

## Testing

The active suite contains 27 network-independent tests covering:

- streaming checksums for text, empty, binary, changed, and missing files;
- strict dataset configuration and path validation;
- `PRESENT`, `PARTIAL`, and `MISSING` dataset states;
- safe download success, failure, interruption, checksum mismatch, and dry-run behavior;
- deterministic manifest ordering and fingerprints;
- manifest reload and independent verification;
- synthetic raw-file mutation detection;
- supported Python runtime smoke testing.

Future parser/model/RAG test files are explicit placeholders and do not count as implemented coverage.

## Repository map

```text
configs/datasets/     Version-controlled HDFS and BGL contracts
data/manifests/       Real dataset identity and integrity manifests
docs/                 Scope, research questions, acquisition, and reproducibility
scripts/              Thin dataset acquisition and verification CLIs
src/common/           Streaming checksum utilities
src/ingestion/        Config, acquisition, presence, manifest, and verification logic
tests/                Offline unit/integration tests and synthetic fixtures
```

Other `src/` modules currently reserve planned boundaries; they are not working implementations.

## Research direction

SeqLogAD separates evaluation into four layers:

1. **Detection:** statistical baselines versus sequence models under leakage-safe chronological evaluation.
2. **Retrieval:** lexical, dense, sequential, and hybrid retrieval.
3. **Evidence grounding:** LLM-only versus RAG versus RAG with explicit evidence verification.
4. **Investigation and QA:** bounded tool use, supported hypotheses, and structured regression-test recommendations.

All research statements remain hypotheses until supported by controlled experiments. See [research questions](docs/research-questions.md) and [project scope](docs/project-scope.md).

## Engineering principles

- Raw datasets are immutable and excluded from Git.
- Scientific identity is content-based; filesystem modification time is excluded.
- Configuration and manifests are version-controlled.
- Chronological splits are the default for future detector evaluation.
- Baselines come before complex sequence models.
- The future investigation agent is single-agent, read-only, bounded, and evidence-linked.
- The system may return `INSUFFICIENT_EVIDENCE`; it is never forced to invent a root cause.
- No claim of novelty or superiority is made before literature and experimental validation.

## Documentation

- [Project scope](docs/project-scope.md)
- [Research questions](docs/research-questions.md)
- [Dataset acquisition](docs/dataset-acquisition.md)
- [Reproducibility](docs/reproducibility.md)
- [Configuration convention](docs/config-convention.md)
- [Repository map](docs/repository-map.md)
- [Testing strategy](docs/testing/README.md)

## Data and usage notice

HDFS and BGL are obtained from the canonical [LogPAI Loghub](https://github.com/logpai/loghub) / [Zenodo record 8196385](https://doi.org/10.5281/zenodo.8196385). Dataset downloadability does not grant unrestricted redistribution. Review and retain the source usage terms and citations. This repository distributes configs, manifests, documentation, and synthetic fixtures—not benchmark raw logs.
