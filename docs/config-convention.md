# Configuration Convention — v2 forward plan with v1.1 foundation

Version-controlled config files are contracts. The forward protocol is `configs/protocols/protocol-v2-domain-adaptive-fusion.yaml`; the frozen v1.1 stack remains the historical HDFS/BGL foundation. Model/experiment files remain non-runnable until their owning task implements validation and commands.

## Required run identity

Every future run config must resolve:

- experiment ID and owner;
- forward protocol ID/version and approval status;
- dataset/architecture/fold identity and target-buffer hash;
- source/target chronology and leakage-audit artifact hashes;
- expert/checkpoint/gate status (`MUST`, `SHOULD`, or an explicitly opened `CONDITIONAL` gate);
- seed, legal fit scope, calibration policy, threshold policy and primary metric;
- output directory and Git/environment snapshot.

## Frozen rules

1. Paths, parameters, thresholds, seeds, and outputs are not hard-coded in implementation.
2. Each v2 fold holds one full architecture out as target and preserves chronology.
3. Target adaptation/calibration uses only a versioned, predominantly-normal unlabeled buffer.
4. Target/TEST labels never participate in fitting, normalization, thresholding, config/model/dataset/claim selection, or novelty decisions before final evaluation.
5. Secrets/API keys never enter committed YAML.
6. Overrides and failed runs are traceable and non-overwriting.
7. EFFECT-001 remains frozen historical provenance for the v1.1 foundation; v2 metrics and gates require their own registered configs.
8. Conditional config cannot be run without a recorded v2 gate decision.
9. Human execution is required for empirical runs/training/tuning and final TEST.
10. Every v2 run snapshots the protocol, data/fold, target buffer, model/gate and environment; overrides cannot change the target-label boundary or gate definitions after evidence is inspected.

`configs/default.yaml` demonstrates shape only and is not a runnable experiment.
