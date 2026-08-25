# Transformer context pack (T6-R / T6-I)

## READ BY DEFAULT
[`../../docs/research-protocol-v1.1.md`](../../docs/research-protocol-v1.1.md) Transformer gate and [`../../configs/active-state.yaml`](../../configs/active-state.yaml).

## READ IF NEEDED
[`../../configs/models/transformer.yaml`](../../configs/models/transformer.yaml), sequence contracts, EFFECT-001, and an explicit human gate record supplied by Primary.

## AVOID BY DEFAULT
Implementation/training while the gate is closed, LSTM/fusion scope, TEST data, and historical Transformer requirements.

## AUTHORITATIVE CONTRACTS
Protocol v1.1: Transformer is conditional and follows KT-1–KT-3 plus `GATE-SEQ-001`; all upstream frozen contracts remain binding. T6-R is closed before the CANONICAL QA pass and may research/prepare contracts only during explicitly authorized `THEORY-COMPLETE-001`. T6-I implementation/training remains closed until a recorded human execution-gate opening.

## EXPECTED OUTPUT
Before the CANONICAL QA pass or without explicit `THEORY-COMPLETE-001` authorization, T6-R returns `SCIENTIFIC_GATE_REQUIRED`; during that authorized task it may produce only assigned research/contract preparation. T6-I returns `SCIENTIFIC_GATE_REQUIRED` while its implementation/training gate is closed; after opening it may produce only assigned implementation, then handoff to T8. Empirical status remains traceable.

## ESCALATION CONDITIONS
No verified `THEORY-COMPLETE-001` authorization or T6-I execution-gate record for the requested role, architecture/budget/seed change, training/tuning request outside human ownership, leakage risk, or TEST access.
