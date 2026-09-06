# QA & Reproducibility context pack (T8)

## READ BY DEFAULT
[`../../tests/README.md`](../../tests/README.md), [`../../docs/testing/README.md`](../../docs/testing/README.md), [`../../configs/active-state.yaml`](../../configs/active-state.yaml).

## READ IF NEEDED
Relevant contract tests, [`../../docs/reproducibility.md`](../../docs/reproducibility.md), leakage audit, TEST seal, schema, and task-specific source.

## AVOID BY DEFAULT
Opening TEST to validate behavior, broad generated-data scans, unrelated tests, and interpreting placeholders as completed science.

## AUTHORITATIVE CONTRACTS
`Bang_ke_hoach_SeqLogAD.xlsx` and its projection [`../../configs/plan/excel-roadmap-v1.yaml`](../../configs/plan/excel-roadmap-v1.yaml); the Phase 1 contracts (`LOG-UNIFY-001`, `NORM-CS-001`, `CS-SPLIT-001`, `ADAPT-INPUT-001`, `LEAK-CS-001`) and their hashes in [`../../data/processed/protocol/G0-receipt.json`](../../data/processed/protocol/G0-receipt.json). Protocol v1.1 and its addenda are **historical** and bind only the frozen HDFS/BGL artifacts.

## EXPECTED OUTPUT
Independent implementer handoff review: exact commands/results, deterministic rerun evidence where applicable, link/hash checks, changed-files boundary, TEST and label/leakage statements, then pass/fail recommendation to Primary.

## ESCALATION CONDITIONS
Contract-test failure, nondeterminism, unexplained hash drift, unexpected file change, leakage signal, TEST exposure, or status/result promotion.
