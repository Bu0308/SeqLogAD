# Configuration

`pyproject.toml` is the package/dependency contract. Dataset YAML files are active acquisition/integrity contracts. [`protocols/protocol-v1.1.yaml`](protocols/protocol-v1.1.yaml) is the active machine-readable scientific contract; `protocol-v1.yaml` is historical.

Model/experiment/retrieval/agent YAML files are non-runnable placeholders. Their statuses distinguish `MUST`, `SHOULD`, `CONDITIONAL`, `FUTURE`, and `REMOVED_FROM_CORE`; the presence of a file does not mean implementation exists.

Rules:

- no secrets or private absolute paths;
- raw chronological split precedes fitted transforms/windows;
- no TEST fitting, selection, thresholding, calibration, or architecture/claim choice;
- every run references exact protocol/config/artifact identities;
- Transformer/localization/fusion require recorded gates;
- future downstream placeholders cannot activate dependencies or scope.

See [`../docs/config-convention.md`](../docs/config-convention.md).
