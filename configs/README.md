# Configuration

`pyproject.toml` is the package/dependency contract. Dataset YAML files are active acquisition/integrity contracts. [`protocols/protocol-v1.1.yaml`](protocols/protocol-v1.1.yaml) is the active machine-readable scientific contract; [`protocols/effect-001.yaml`](protocols/effect-001.yaml) is its required statistical addendum; `protocol-v1.yaml` is historical.

EFFECT-001 is not execution-ready until the human researcher approves non-null `delta_HDFS` and `delta_BGL`. Its remaining statistical fields are frozen and covered by protocol contract tests. A null margin is an execution blocker, not a YAML default to be filled from observed results.

Model/experiment/retrieval/agent YAML files are non-runnable placeholders. Their statuses distinguish `MUST`, `SHOULD`, `CONDITIONAL`, `FUTURE`, and `REMOVED_FROM_CORE`; the presence of a file does not mean implementation exists.

Rules:

- no secrets or private absolute paths;
- raw chronological split precedes fitted transforms/windows;
- no TEST fitting, selection, thresholding, calibration, or architecture/claim choice;
- every run references exact protocol/config/artifact identities;
- Transformer/localization/fusion require recorded gates;
- future downstream placeholders cannot activate dependencies or scope.

See [`../docs/config-convention.md`](../docs/config-convention.md).
