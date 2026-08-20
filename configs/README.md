# Configuration

Dataset YAML files are active acquisition/integrity contracts. Model, retrieval, agent, and experiment YAML files are non-runnable placeholders until their owning tasks validate schemas and commands.

V3 requires explicit five-way split scope, expert identity, calibration/fusion input artifacts, seed, dataset fingerprint, and human-run ownership. `protocols/protocol-v1.yaml` freezes the chronological `60/10/10/10/10` scientific protocol; it is not a runnable experiment config.

Rules:

- no secrets or private absolute paths;
- no TEST fitting/tuning;
- all overrides and selected artifacts are traceable;
- structural Expert D is P0; dense retrieval is P1;
- no future dependency is activated merely because a placeholder exists.

See [`../docs/config-convention.md`](../docs/config-convention.md).
