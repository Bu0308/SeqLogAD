# Primary context

## 1. What is authoritative?

`Bang_ke_hoach_SeqLogAD.xlsx` — the researcher's workbook — is the primary and
authoritative scientific roadmap. Where it conflicts with any other document, the
workbook wins.

Machine-readable projection: [`../configs/plan/excel-roadmap-v1.yaml`](../configs/plan/excel-roadmap-v1.yaml)
(regenerate with `python scripts/extract_excel_roadmap.py`; a test fails if it goes
stale).

Implementation contract, subordinate to the workbook and in agreement with it:
[`../configs/protocols/protocol-v2-domain-adaptive-fusion.yaml`](../configs/protocols/protocol-v2-domain-adaptive-fusion.yaml).

Operational pointer registry: [`../configs/active-state.yaml`](../configs/active-state.yaml).
It is a registry, not an amendment mechanism.

## 2. What is the objective?

Domain-Adaptive Fusion for zero-label cross-system log anomaly detection: learn from
several source architectures, adapt to an unseen target architecture using only an
unlabelled normal burn-in buffer, and detect anomalies with calibrated, explainable
evidence and a first-class abstain state.

## 3. Who owns decisions?

No agent owns or may amend the workbook. Dataset eligibility, buffer assumptions,
model selection, empirical runs and conclusions are researcher-owned. Gates G0–G4
are signed by the researcher, never by an agent.

## 4. What is active versus historical?

Active: the workbook, its projection, the v2 protocol contract, and the Phase 1
implementation under `src/seqlogad/protocol/`.

Historical provenance, controlling nothing: protocol v1.1 and its addenda
(`effect-001`, `split-clarification-v1`, `purge-decision-v1`), the HDFS/BGL five-way
split and sealed TEST artifacts, the frozen Drain3 parser state, the earlier master
plans under `Plan/`, and the retired task ladder
(`SEQ-001`, `THEORY-COMPLETE-001`, `KT-1/2/3`, `EFFECT-001`, the Transformer and
localization gates). See
[`../docs/migration/EXCEL-PLAN-MIGRATION-001.md`](../docs/migration/EXCEL-PLAN-MIGRATION-001.md).

## 5. What is complete and what is next?

Phase 1 (P1.1–P1.8) is **complete and signed**. All eight tasks are `DONE` and
**G0 = `PASSED`** (19/19 criteria), signed by the researcher on 2026-09-06. The four
signatures are in `../configs/protocols/g0-signatures.yaml` and are re-verified by
exact payload match on every build.

`NEXT_AUTHORIZED_TASK = P2.1` — freeze the Llama-3.1-8B base, tokenizer, licence and
GPU budget (`LLM-BASE-001`), owner Người nghiên cứu. **Authorised, not started.**

G1–G4 remain `NOT_PASSED`. `EXC-003` blocks G1 for the ARCH-HADOOP fold: its burn-in
buffer is `REJECTED` under `BUFFER-REJECT-001`, so that fold may not build target
memory, calibrate, fit drift or set abstention thresholds. Relaxing the readiness
minima is a forbidden remedy.

Scientific results: `NOT_RUN`. No model has been trained.

## 6. What must never happen?

Target anomaly labels may not reach training, adaptation, calibration, routing,
fusion fitting, model selection, normaliser fitting or parser fitting. In particular
a burn-in buffer may never be built by selecting records whose label is normal. The
only place ground truth may be opened is
[`../src/seqlogad/protocol/labels.py`](../src/seqlogad/protocol/labels.py), under an
explicit evaluation scope, and every access is recorded.
