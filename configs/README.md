# Configuration

`pyproject.toml` is the package/dependency contract. Dataset YAML files are active acquisition/integrity contracts. [`protocols/protocol-v1.1.yaml`](protocols/protocol-v1.1.yaml) is the active machine-readable scientific contract; [`protocols/effect-001.yaml`](protocols/effect-001.yaml) is its required statistical addendum; [`protocols/split-clarification-v1.yaml`](protocols/split-clarification-v1.yaml) is its binding exact-split addendum; [`protocols/purge-decision-v1.yaml`](protocols/purge-decision-v1.yaml) binds the human-approved HDFS primary/secondary purge disposition; `protocol-v1.yaml` is historical.

EFFECT-001 is `FROZEN_HUMAN_APPROVED` with `delta_HDFS = delta_BGL = 0.01 AP` under `RESOURCE_FEASIBILITY_MARGIN`. The statistical addendum is complete and contract-tested. Experiment placeholders remain non-runnable until their independent split/parser/evaluation dependencies are implemented and authorized.

PROTOCOL-SPLIT-CLARIFY-001 is `FROZEN_HUMAN_APPROVED`. SPLIT-001 instantiated it for both datasets; the config records the real payload/TEST hashes and `SEALED_NEVER_OPENED`.

PURGE-DECISION-001 is `FROZEN_HUMAN_APPROVED`. The existing HDFS split/parser/TEST/EFFECT identities remain unchanged; `HDFS-PURGE-SENSITIVITY-001` is secondary, robustness-only, non-selection, and `NOT_RUN`.

[`parsing/drain3-v1.yaml`](parsing/drain3-v1.yaml) is the pre-fit PARSE-001 contract. It freezes Drain3 0.9.11 parameters, masks, message normalization, normal-selection granularity, frozen-match behavior, `EVT_UNSEEN`, identities, and non-overwrite persistence. The real HDFS/BGL states were fitted under this contract; it does not authorize canonical-event generation or scientific experiments.

Model/experiment/retrieval/agent YAML files are non-runnable placeholders. Their statuses distinguish `MUST`, `SHOULD`, `CONDITIONAL`, `FUTURE`, and `REMOVED_FROM_CORE`; the presence of a file does not mean implementation exists.

Rules:

- no secrets or private absolute paths;
- raw chronological split precedes fitted transforms/windows;
- no TEST fitting, selection, thresholding, calibration, or architecture/claim choice;
- every run references exact protocol/config/artifact identities;
- Transformer/localization/fusion require recorded gates;
- future downstream placeholders cannot activate dependencies or scope.

See [`../docs/config-convention.md`](../docs/config-convention.md).
