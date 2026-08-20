# Configuration Convention — V3

Config files are version-controlled contracts. Current model/experiment YAML files are non-runnable placeholders until their implementation tasks validate them.

## Logical shape

```yaml
project:
  name: seqlogad
  experiment_id: EXP-YYYYMMDD-NNN
  seed: 42

dataset:
  name: TODO
  version: TODO
  fingerprint: TODO
  raw_path: TODO
  processed_path: TODO

parsing:
  parser: drain3
  fit_partition: BASE_TRAIN
  state_artifact: TODO

sequence:
  strategy: TODO
  grouping_key: TODO
  window_size: TODO

split:
  strategy: raw_chronological
  base_train: 0.60
  fusion_train: 0.10
  val_expert: 0.10
  val_fusion: 0.10
  test: 0.10

experts:
  enabled: [transformer, markov, isolation_forest, normal_reference]
  configs: TODO

calibration:
  fit_partition: VAL_FUSION
  method: TODO

fusion:
  enabled: false
  method: TODO
  input_artifact: TODO

output:
  root: outputs
  run_dir: outputs/runs/EXP-YYYYMMDD-NNN
```

The split values and scientific access rules are frozen by `PROTOCOL-001`. `configs/protocols/protocol-v1.yaml` is the machine-readable protocol source of truth. It is a contract, not a runnable experiment config; model and artifact fields in other placeholders still require implementation-time validation.

## Rules

1. Do not hard-code paths, parameters, thresholds, seeds, partitions, or output directories in implementation code.
2. Every run stores the selected config path, resolved snapshot, overrides, Git state, dataset fingerprint, and artifact IDs.
3. Secrets/API keys never enter committed YAML.
4. Parser/expert/reference/calibration/fusion/threshold fit scopes are explicit.
5. TEST never participates in fitting, tuning, checkpoint selection, or config selection.
6. Failed and multi-seed runs receive distinct non-overwriting experiment IDs.
7. Human execution is required for training, tuning, fusion training, and final TEST.
8. Config validation and package compatibility must pass before a config loses placeholder status.

## Priority

- P0: structural normal-reference retrieval and core experts/fusion controls.
- P1: dense retrieval, partial unfreezing, Elasticsearch, API/UI, downstream polish.
- P2/P3: disabled unless an explicit scope decision activates them.
