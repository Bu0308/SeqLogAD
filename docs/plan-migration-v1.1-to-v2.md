# Migration record: v1.1 → v2 Domain-Adaptive Fusion

## Decision

On 2026-08-28 the forward research direction changed to **Domain-Adaptive Fusion for Zero-Label Cross-System Log Anomaly Detection**. The v2 plan and `DOMAIN-ADAPTIVE-FUSION-001` are now the forward source-of-truth. This is a planning transition only; empirical status remains `NOT_RUN`.

## Superseded from v1.1

| Former v1.1 scope | v2 disposition | Reason |
|---|---|---|
| HDFS/BGL as the sole research population | Superseded as the final target population; retained as reusable source-domain assets | v2 tests transfer across heterogeneous architectures |
| Sequence added-value as the primary question | Superseded by cross-architecture transfer and target-only adaptation | The new user-approved question is domain adaptation plus fusion |
| KT-1/KT-2/KT-3 as the main scientific ladder | Historical, not a v2 gate | They answer the former order-sensitivity question |
| Mandatory unseen-event/length/count/Markov/Isolation Forest family | Historical v1.1 controls; v2 keeps equal-weight and explicit baseline comparisons where applicable | v2 must compare experts and adaptation, not inherit an old benchmark ladder as its objective |
| Conditional Transformer/localization/simple F0/F1 fusion | Superseded by the selected semantic, sequence and GTAT experts plus adaptive fusion | The model stack is fixed by the user-approved v2 plan |
| RAG/Agent/API/UI/Elasticsearch product expansion | Still outside the v2 detector core | These are downstream delivery concerns, not the research decision |

## Still effective and preserved

- Immutable raw bytes, manifests, checksums and provenance.
- Label isolation from fitting/adaptation and chronological evaluation.
- Physical TEST sealing and one-time human-owned final evaluation discipline.
- Deterministic identities, non-overwriting artifacts, reproducible configs and explicit ownership of empirical claims.
- Existing HDFS/BGL split/parser artifacts and purge decision as historical provenance; no v2 plan may mutate them silently.

## New v2 contracts required before model work

1. Dataset registry with at least three source architectures and held-out target folds.
2. Unified log schema retaining raw messages and recording missing fields.
3. Leave-one-architecture-out chronological split and leakage audit.
4. Target normal-buffer contract: duration, contamination bound, readiness, hash and rejection policy.
5. Independent LoRA adapter/checkpoint identity and common evidence/uncertainty schema.
6. Target calibration, drift, coverage and abstention contracts.
7. Gate receipts G0–G4 and cross-architecture result/ablation provenance.

No data-collection instruction can alter these scientific decisions.
