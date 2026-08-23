# Toolchain Checklist

Last verified: **2026-08-20**. No private hostnames, usernames, serial numbers, credentials, or absolute home paths are recorded here.

## Current development environment

| Tool | Status | Version/details | Impact |
|---|---|---|---|
| Operating system | AVAILABLE | macOS/Darwin | Non-blocking |
| Python | AVAILABLE | 3.12.6 in project-local `.venv` | Matches tested `>=3.12,<3.13` policy |
| Git | AVAILABLE | Repository initialized; branch `main` | Required before experiments |
| Editable package | AVAILABLE | `seqlogad==0.1.0`; canonical namespace `seqlogad.*` | Imports verified outside repository root |
| Build backend | AVAILABLE | setuptools 80.9.0 in isolated builds | Exact version pinned in `pyproject.toml` |
| pytest | AVAILABLE | 9.1.1; current suite must pass in `.venv` | Foundation/environment/protocol/schema suite operational |
| PyArrow | AVAILABLE | 19.0.1 | Satisfies declared `>=17,<20` contract |
| Drain3 | AVAILABLE | 0.9.11 | Import verified; no parser logic implemented |
| Polars | AVAILABLE | 1.43.2 | Satisfies declared `>=1,<2` contract |
| Pydantic | AVAILABLE | 2.13.4 | Satisfies declared `>=2,<3` contract |
| Docker | AVAILABLE at Day 1 check | Dockerfile now declares canonical Python 3.12; image build not run in v1.1 freeze | Non-blocking |
| Docker Compose | AVAILABLE at Day 1 check | No scientific service stack configured | Non-blocking |

## Resolved environment contract

1. `pyproject.toml` is the dependency contract; `requirements.lock` is the tested Python 3.12/macOS ARM64 resolution snapshot used as installation constraints.
2. Source uses the conventional `src/seqlogad/` layout and canonical imports use `seqlogad.*`.
3. `python -m pip install -c requirements.lock -e ".[dev]"` succeeds in a clean project-local `.venv`.
4. Imports and installed CLI help run outside the repository root without `PYTHONPATH` or `sys.path` modification.
5. `python -m pip check` reports no broken requirements in `.venv`.
6. The global interpreter still has unrelated conflicts, but it is not the project execution environment.

Future ML, retrieval, agent, API, and UI dependencies are intentionally absent until their owning implementation tasks begin.

## Current blocking classification

- **Documentation/Git review:** no toolchain blocker.
- **Schema/split contracts:** SCHEMA-001/002 and SCHEMA-COMPAT-001 tests pass; SPLIT-001 real HDFS/BGL artifacts validate and both TEST seals remain unopened.
- **Parsing:** Drain3 package availability is verified; parser-state semantics and parsing implementation remain future work.
- **Scientific experiments:** LIT/effect policy, five-way split/TEST guard, parser/events/sequences, and human-run protocol are required first.

## Verified commands

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -c requirements.lock -e ".[dev]"
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
```

Installed CLI entrypoints are `seqlogad-download-data`, `seqlogad-build-dataset-manifest`, and `seqlogad-verify-dataset`. Dataset paths are resolved from the explicit `--project-root` argument when commands run outside the repository.
