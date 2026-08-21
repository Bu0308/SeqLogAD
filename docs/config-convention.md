# Configuration Convention — Research Freeze v1.1

Version-controlled config files are contracts. The active protocol is `configs/protocols/protocol-v1.1.yaml`; model/experiment files remain non-runnable until their owning task implements validation and commands.

## Required run identity

Every future run config must resolve:

- experiment ID and owner;
- protocol version `1.1`;
- dataset ID/version/fingerprint;
- split/parser/sequence artifact hashes;
- method status (`MUST`, `SHOULD`, or an explicitly opened `CONDITIONAL` gate);
- seed, legal fit partition, selection partition, threshold policy, primary metric;
- output directory and Git/environment snapshot.

## Frozen rules

1. Paths, parameters, thresholds, seeds, and outputs are not hard-coded in implementation.
2. Split is raw chronological `60/10/10/10/10`; reserved fusion partitions are not silently repurposed.
3. Drain3 fit scope is normal `BASE_TRAIN` only.
4. TEST never participates in fitting, normalization, thresholding, config/model/dataset/claim selection, or novelty decisions.
5. Secrets/API keys never enter committed YAML.
6. Overrides and failed runs are traceable and non-overwriting.
7. Practical-effect thresholds remain `TO_BE_FROZEN_BEFORE_RUN` until the human approves `EFFECT-001`.
8. Conditional config cannot be run without a recorded gate decision.
9. Human execution is required for empirical runs/training/tuning and final TEST.

`configs/default.yaml` demonstrates shape only and is not a runnable experiment.
