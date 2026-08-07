# Toolchain Checklist

Checked on **2026-08-07**. No private hostnames, usernames, serial numbers, credentials or full private machine paths are recorded.

## Development environment

| Tool | Status | Version/details | Day 1 impact |
|---|---|---|---|
| Operating system | AVAILABLE | macOS/Darwin environment | Non-blocking |
| Python | AVAILABLE | 3.12.6 | Compatible with current `>=3.11` policy |
| pip | AVAILABLE | 26.0.1 | Non-blocking |
| Git executable | AVAILABLE | 2.48.1 | Non-blocking |
| Git repository metadata | MISSING | Current folder has no `.git` directory | Non-blocking Day 1; reproducibility limitation |
| pytest module | AVAILABLE | 9.0.3 via `python3 -m pytest` | Non-blocking |
| pytest executable | MISSING | `pytest` is not on PATH | Non-blocking; use `python3 -m pytest` or activate project environment |
| pytest-cov module | MISSING | Optional coverage plugin is not installed | Non-blocking Day 1; needed before coverage reporting |
| Docker | AVAILABLE | 28.1.1 | Non-blocking check passed |
| Docker Compose | AVAILABLE | v2.35.1-desktop.1 | Non-blocking check passed |

## Python policy

The repository currently requires Python `>=3.11`. Recommended development range is Python 3.11–3.12 for the planned PyTorch, Polars, PyArrow, Drain3, LangGraph and FastAPI stack. The current Python 3.12.6 installation is retained; no upgrade or downgrade is performed on Day 1.

## Dependency policy

No future-stack dependency was installed or added today. `pyproject.toml` contains only the existing Phase 1 foundation and development test metadata. PyTorch, FAISS, LangGraph, Streamlit, FastAPI and Elasticsearch clients remain deferred until their tasks require them.

## Blocking issues

- None for Day 1 scope/config/documentation work.

## Non-blocking issues

- `pytest` executable is unavailable on PATH, although `python3 -m pytest` works.
- `pytest-cov` is not installed in the current Python environment.
- Current directory is not a Git repository.
- Dataset and future ML dependencies are intentionally not installed.

## Recommended actions for Day 2+

1. Create or select the project virtual environment.
2. Install the minimal project/dev dependencies in that environment.
3. Make the repository a Git repository before reproducibility experiments begin.
4. Keep Docker available for later optional integration checks.
