# Configuration Convention — Research Freeze v1.1

Version-controlled config files are contracts. The active protocol is `configs/protocols/protocol-v1.1.yaml`; its statistical addendum is `configs/protocols/effect-001.yaml`. Model/experiment files remain non-runnable until their owning task implements validation and commands.

## Required run identity

Every future run config must resolve:

- experiment ID and owner;
- protocol version `1.1`;
- EFFECT-001 contract version and approval status;
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
7. EFFECT-001 method fields are frozen, but `delta_HDFS` and `delta_BGL` remain `HUMAN_DECISION_REQUIRED`; null margins force `execution_ready: false`.
8. Conditional config cannot be run without a recorded gate decision.
9. Human execution is required for empirical runs/training/tuning and final TEST.
10. Future run configs must snapshot both the parent protocol and statistical addendum; overrides cannot change estimands, margins, bootstrap settings, candidate family, or decision regions without a pre-result amendment.

`configs/default.yaml` demonstrates shape only and is not a runnable experiment.
