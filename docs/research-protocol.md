# SeqLogAD Scientific Protocol — Current Entry Point

> **The authoritative scientific plan is [`../Bang_ke_hoach_SeqLogAD.xlsx`](../Bang_ke_hoach_SeqLogAD.xlsx)**
> (machine-readable projection: [`../configs/plan/excel-roadmap-v1.yaml`](../configs/plan/excel-roadmap-v1.yaml)).
> The contract below is the *implementation* contract. It agrees with the workbook
> and is subordinate to it: on any conflict, the workbook wins. Phase 1 is complete;
> G0 is `PROTOCOL_READY_PENDING_RESEARCHER_SIGNATURE`. See
> [`protocol/PHASE-1-RECORD.md`](protocol/PHASE-1-RECORD.md) and
> [`migration/EXCEL-PLAN-MIGRATION-001.md`](migration/EXCEL-PLAN-MIGRATION-001.md).

The implementation contract is **DOMAIN-ADAPTIVE-FUSION-001 (v2)**:

- human-readable: [`research-protocol-v2-domain-adaptive-fusion.md`](research-protocol-v2-domain-adaptive-fusion.md);
- machine-readable: [`../configs/protocols/protocol-v2-domain-adaptive-fusion.yaml`](../configs/protocols/protocol-v2-domain-adaptive-fusion.yaml);
- forward plan: [`../Plan/master-implementation-plan-v2-domain-adaptive-fusion.md`](../Plan/master-implementation-plan-v2-domain-adaptive-fusion.md);
- migration record: [`plan-migration-v1.1-to-v2.md`](plan-migration-v1.1-to-v2.md).

## Scientific boundary

SeqLogAD studies whether a fusion system can transfer knowledge across heterogeneous source architectures, adapt to an unseen target from an unlabeled predominantly-normal buffer, and produce calibrated, explainable anomaly evidence. The minimum fold contains three source architectures and one held-out target architecture. Splits are leave-one-architecture-out and chronological; random mixed-system splits are forbidden.

Target labels are excluded from adaptation, calibration, gate training and selection. They are visible only at the final evaluation boundary after G4. The target buffer is versioned, hashed, contamination-bounded and must pass readiness checks. Claims are limited to evaluated architectures and conditions; universal generalisation and cold-start detection are not claimed.

The fixed model stack is Llama-3.1-8B + independent LoRA-Semantic and LoRA-Sequence adapters, plus a Temporal Graph Transformer (GTAT). The adapters share a frozen base revision but never adapter weights or checkpoints. Equal-weight fusion is mandatory. Adaptive fusion is allowed only after G0–G2 and is accepted only if G3 shows stable benefit without worse false-alert control.

## Preserved v1.1 foundation

Protocol v1.1 and its binding EFFECT-001, split-clarification and purge-decision addenda remain frozen historical contracts. They preserve the verified HDFS/BGL manifests, deterministic split identities, normal-only Drain3 states and physical TEST seals. They are reusable source-domain provenance, not the v2 research question, and no v2 result may be inferred from them.

The historical contracts remain available at:

- [`research-protocol-v1.1.md`](research-protocol-v1.1.md);
- [`../configs/protocols/protocol-v1.1.yaml`](../configs/protocols/protocol-v1.1.yaml);
- [`statistical-decision-contract.md`](statistical-decision-contract.md);
- [`split-clarification-contract.md`](split-clarification-contract.md);
- [`../configs/protocols/split-clarification-v1.yaml`](../configs/protocols/split-clarification-v1.yaml).

No scientific experiment, v2 model fit, target adaptation or final TEST run has occurred. Model/experiment configs are planning contracts until their gates and implementation exist.
