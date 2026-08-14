# Toolchain Checklist

Last documentation audit: **2026-08-14**. No private hostnames, usernames, serial numbers, credentials, or absolute home paths are recorded here.

## Current development environment

| Tool | Status | Version/details | Impact |
|---|---|---|---|
| Operating system | AVAILABLE | macOS/Darwin | Non-blocking |
| Python | AVAILABLE | 3.12.6 | Within current `>=3.11` policy |
| Git | AVAILABLE | Repository initialized; branch `main` | Required before experiments |
| pytest | AVAILABLE | 27 foundation tests pass through `python3 -m pytest` | Foundation suite operational |
| Drain3 import | MISSING | Declared in `pyproject.toml`, absent from current interpreter | Blocks parsing, not documentation |
| Docker | AVAILABLE at Day 1 check | Not reconfigured by V3 docs task | P1, non-blocking |
| Docker Compose | AVAILABLE at Day 1 check | Not reconfigured by V3 docs task | P1, non-blocking |

## Known environment-contract issues

1. `pyproject.toml` declares `pyarrow>=17,<20`; the currently observed environment has PyArrow 23.x. Compatibility has not been established, so the bound is not changed by documentation work.
2. Setuptools discovers packages below `src/`, while current runtime imports use the `src.*` namespace. Editable-install/import behavior must be tested and resolved before adding V3 implementation modules.
3. Drain3 is declared in `pyproject.toml` but is not importable in the current interpreter. Install/lock it only in the dedicated environment task before parsing.
4. PyTorch, scikit-learn, FAISS, calibration, and downstream framework dependencies must be introduced only when their implementation task begins.
5. `python3 -m pip check` reports existing global-environment conflicts: Streamlit expects `protobuf<5` while 7.35.1 is installed, and OpenCV expects NumPy 2.x while 1.26.4 is installed. These packages are not used by the current foundation, but a clean project environment is required before future phases.
6. A reproducible package lock/environment snapshot is still missing.

## Current blocking classification

- **Documentation/Git review:** no toolchain blocker.
- **Canonical-event implementation:** packaging/import contract must be resolved first.
- **Parsing:** Drain3 availability and parser-state persistence must be verified.
- **Model experiments:** dependency lock, five-way split, configs, and human-run protocol are required.

No dependency was installed or version bound changed during the V3 documentation task.
