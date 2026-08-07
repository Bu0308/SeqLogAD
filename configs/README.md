# Configuration

Configuration is split by concern: datasets, models, retrieval, agent and experiments. Values are placeholders until the corresponding task starts.

The cross-cutting configuration shape is documented in [`../docs/config-convention.md`](../docs/config-convention.md), with the Day 1 skeleton at `configs/default.yaml`.

Rules:

- No secrets in YAML.
- Every run records the selected config path.
- Train-only fitting and chronological split behavior must be explicit.
- P0 configurations are implemented before P1/P2 configurations are activated.
