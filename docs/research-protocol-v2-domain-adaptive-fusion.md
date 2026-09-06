# DOMAIN-ADAPTIVE-FUSION-001 — Protocol v2

**Status:** `PLANNED_USER_APPROVED` — 2026-08-28  
**Empirical status:** `NOT_RUN`

This is the forward scientific protocol for SeqLogAD. Its machine contract is [`configs/protocols/protocol-v2-domain-adaptive-fusion.yaml`](../configs/protocols/protocol-v2-domain-adaptive-fusion.yaml), and its implementation plan is [`../Plan/master-implementation-plan-v2-domain-adaptive-fusion.md`](../Plan/master-implementation-plan-v2-domain-adaptive-fusion.md).

## Research question and boundary

Can a fusion system transfer knowledge across heterogeneous source architectures, learn an unseen target's normal behaviour from an unlabeled burn-in buffer, and detect anomalies with calibrated, explainable evidence?

Claims are limited to held-out architectures and observed operating conditions. The protocol does not claim universal generalisation or reliable detection before the target buffer is ready.

## Data and evaluation

- Use at least three heterogeneous source architectures.
- Use leave-one-architecture-out folds; never mix source and target systems in a random split.
- Preserve chronology within each architecture.
- Adapt and calibrate on a versioned, hashed, predominantly-normal target buffer without reading target labels.
- Use target labels only at the final evaluation boundary.
- Report per-target AP/PR-AUC, AUROC, false-alert rate, time-to-detect, latency, calibration, abstention and bootstrap uncertainty.
- Compare each expert, equal-weight fusion, adaptive fusion and no-adaptation ablations; stress cold start, new templates, volume drift and contaminated burn-in.

## Model contract

The semantic expert is **Llama-3.1-8B + LoRA-Semantic**. The sequence expert uses the same frozen base revision with a **separate LoRA-Sequence** adapter. The adapters are independent checkpoints and never share adapter weights. The structural/time expert is **Temporal Graph Transformer (GTAT)** and must report coverage or abstain when target topology fields are unavailable.

Each expert emits score, uncertainty, coverage, evidence and localisation. Scores are converted to target-normal quantiles before fusion. The adaptive gate may use calibrated scores, uncertainty, coverage, drift and sequence context, but its learned weights come only from source episodic folds.

## Gates and ownership

`G0` freezes protocol, architecture folds, schema and leakage controls. `G1` freezes target-buffer assumptions and calibration checks. `G2` requires measured expert diversity. `G3` requires adaptive fusion to be more stable than equal weighting without worsening false-alert control. `G4` freezes data, models, buffer, gate and thresholds before one final held-out evaluation.

AI/Codex prepares schemas, builders, tests and traceable reports. The researcher approves datasets and assumptions, executes training/evaluation and owns conclusions. No metric or checkpoint is valid without an immutable artifact.

## Preserved v1.1 foundation

Protocol v1.1 and its EFFECT-001, split-clarification and purge-decision addenda remain frozen historical provenance. They still protect the existing HDFS/BGL bytes, manifests, parser states, split identities and sealed TEST partitions. They are not the v2 research question and must not be silently rewritten or used as evidence that v2 has run.
