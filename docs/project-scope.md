# Project Scope — v2 Domain-Adaptive Fusion

## Problem statement

SeqLogAD studies zero-label cross-system log anomaly detection. The forward
question is whether knowledge learned from heterogeneous source architectures
can transfer to a held-out target architecture and be adapted using only a
predominantly-normal, unlabeled target buffer.

The output is an anomaly score, confidence/uncertainty, contributing experts,
evidence, localisation and an explicit `unknown/review` state when coverage or
confidence is insufficient.

## In scope

- At least three heterogeneous source architectures and leave-one-architecture-
  out folds.
- A unified schema for timestamp, level, service, component and raw message,
  with optional session/trace/template fields and explicit missingness.
- Chronological source/target separation, duplicate checks and label-isolation
  audits.
- Target normal-buffer versioning, contamination/readiness checks, local
  calibration, drift and uncertainty estimation without target labels.
- Llama-3.1-8B + LoRA-Semantic, the same frozen base + separate LoRA-Sequence,
  and Temporal Graph Transformer (GTAT).
- Adaptive fusion against each expert and mandatory equal-weight fusion, with
  source-fold gate training and held-out architecture evaluation.
- Ablations, cold-start/new-template/volume-drift/contaminated-buffer stress
  tests, reproducible artifacts and bounded claims.

## Out of scope for the v2 detector

RAG, agent investigation, regression-test recommendation, API/UI, Elasticsearch
deployment, automatic remediation and universal/general-purpose log detection.
These may consume frozen evidence only after the detector study has its own
scope decision.

## Ownership and scientific safety

AI/Codex prepares schemas, deterministic builders, tests, configs and reports.
The researcher approves dataset eligibility, target-buffer assumptions,
model-selection policy, empirical runs and conclusions. No target label may
enter adaptation, calibration, gate training or selection; labels are reserved
for final evaluation after G4. No result is valid without an immutable,
hash-linked artifact.

## Preserved foundation

The v1.1 HDFS/BGL data-integrity foundation remains available and frozen:
manifests, checksums, metadata extraction, exact split identities, normal-only
Drain3 states, purge decision and physical TEST seals. Its sequence-value
research question and EFFECT-001 margins are historical provenance, not the v2
objective. See [`plan-migration-v1.1-to-v2.md`](plan-migration-v1.1-to-v2.md).
