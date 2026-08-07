# Sequence-Aware Log Anomaly + RAG + AI Agent Platform

Repository skeleton for the 8-week MVP described in [`00_MASTER_PLAN.md`](00_MASTER_PLAN.md).

## Current status

This repository has completed the Day 1 contract and Day 2 dataset acquisition foundation:

- directory structure;
- documentation skeletons;
- configuration placeholders;
- dependency metadata for Phase 1;
- offline checksum, acquisition, presence, manifest and verification tooling;
- synthetic fixtures and tests for dataset integrity behavior.

No HDFS/BGL data has been downloaded. No parser, sequence builder, model, RAG, agent, API or dashboard implementation has started.

## P0 / P1 / P2

- **P0:** parsing, sequence construction, leakage-safe splits, baselines, LSTM detector, retrieval, evidence verification, single read-only agent, structured test recommendation, tests and reproducibility.
- **P1:** Transformer comparison, tracing, FastAPI, Streamlit, Elasticsearch adapter, Docker/CI and performance benchmarks.
- **P2:** pytest skeleton generation, safe sandbox execution, OpenStack, adaptive thresholds and feedback memory.

## Start point

The first implementation work begins with `PLAN-001`, followed by the data contract and Phase 1 pipeline. See [`03_TASK_BACKLOG.md`](03_TASK_BACKLOG.md).

Day 1 contracts:

- [`docs/project-scope.md`](docs/project-scope.md)
- [`docs/research-questions.md`](docs/research-questions.md)
- [`docs/repository-map.md`](docs/repository-map.md)
- [`docs/config-convention.md`](docs/config-convention.md)
- [`docs/reproducibility.md`](docs/reproducibility.md)
- [`docs/toolchain-checklist.md`](docs/toolchain-checklist.md)

Day 2 dataset contracts:

- [`docs/dataset-acquisition.md`](docs/dataset-acquisition.md)
- [`docs/datasets/hdfs.md`](docs/datasets/hdfs.md)
- [`docs/datasets/bgl.md`](docs/datasets/bgl.md)
- [`data/README.md`](data/README.md)

## Important boundary

The project is a sequence-aware AI investigation and QA layer on top of observability infrastructure. It is not an ELK replacement.
