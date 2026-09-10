# Task routing

Task IDs come from `Bang_ke_hoach_SeqLogAD.xlsx` (`Task Register` sheet), projected
to [`../configs/plan/excel-roadmap-v1.yaml`](../configs/plan/excel-roadmap-v1.yaml).
Do not invent task IDs and do not resurrect retired ones.

## Phase graph

```text
P1 Data & Protocol      P1.1 → P1.2 → P1.3 → P1.4 ┐
                                     P1.3 → P1.5 ─┼→ P1.6 → P1.7 → P1.8 → [G0]
P2 Representation       [G0] → P2.PRE → P2.1 → P2.2 → P2.3 → P2.4 → P2.5 → P2.6 → P2.7 → [G2]
P3 Adaptation & Fusion  [G2] → P3.1 → P3.2 → P3.3 → P3.4 → P3.5 → P3.6 → P3.7 → P3.8 → [G3]
                                     P1.6 ────────┘                    (P3.7 is Conditional)
P4 Cross-System Valid.  [G3] → P4.1 → P4.2 → {P4.3, P4.4, P4.5} → P4.6 → P4.7 → P4.8 → [G4]
```

## Gate rules

| Gate | Decision | Forbidden before it passes |
| --- | --- | --- |
| G0 | Protocol Ready | Representation or target-adaptation training |
| G1 | Adaptation Ready | Using target labels; silent recalibration |
| G2 | Expert Diversity | Adaptive learned fusion |
| G3 | Fusion Justified | Claiming fusion is superior |
| G4 | Final Evaluation | Post-hoc tuning; universal-generalisation claims |

Every gate is signed by the researcher. An agent may prepare the evidence and report
which criteria hold; it may not declare a gate passed.

## Current state

`CURRENT_PHASE = P1_COMPLETE` · `G0 = PASSED` (signed 2026-09-06) ·
`NEXT_AUTHORIZED_TASK = P2.PRE`, metadata policies frozen; authenticated access still required;
P2.PRE completion BLOCKED pending gated metadata/access evidence; P2.1 execution_authorized=false ·
`G1..G4 = NOT_PASSED` · `EXC-003` blocks G1 for the ARCH-HADOOP fold.

## Retired routing

The following are **historical** and must not be scheduled, referenced as "next", or
treated as gates: `SEQ-001`, `THEORY-COMPLETE-001`, `KT-1`, `KT-2`, `KT-3`,
`EFFECT-001`, `CANONICAL-EVENT-001` as the next scientific task, `BASE-001/2/3`, the
mandatory Markov/N-gram ladder, the conditional Transformer gate and the old
localization/fusion gates.

Namespace: P2_ARCH_V1. Crosswalk and amendment ledger:
`configs/protocols/phase2-roadmap-migration-v1.yaml`.
P2.PRE must PASS before P2.1 execution can be authorized. Source-label C2 remains
UNRESOLVED_DENY; supervised P2.6/P2.7 evidence and G2 depend on its resolution.
P3.1 consumes the P2.6/P2.7 handoff; it does not own duplicate diversity evaluation.
Phase 3 remains disabled.
