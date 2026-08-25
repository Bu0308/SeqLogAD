# QA & Reproducibility context pack (T8)

## READ BY DEFAULT
[`../../tests/README.md`](../../tests/README.md), [`../../docs/testing/README.md`](../../docs/testing/README.md), [`../../configs/active-state.yaml`](../../configs/active-state.yaml).

## READ IF NEEDED
Relevant contract tests, [`../../docs/reproducibility.md`](../../docs/reproducibility.md), leakage audit, TEST seal, schema, and task-specific source.

## AVOID BY DEFAULT
Opening TEST to validate behavior, broad generated-data scans, unrelated tests, and interpreting placeholders as completed science.

## AUTHORITATIVE CONTRACTS
Protocol v1.1 invariants, binding addenda, active hashes/status, and task-specific acceptance criteria supplied by Primary.

## EXPECTED OUTPUT
Independent implementer handoff review: exact commands/results, deterministic rerun evidence where applicable, link/hash checks, changed-files boundary, TEST and label/leakage statements, then pass/fail recommendation to Primary.

## ESCALATION CONDITIONS
Contract-test failure, nondeterminism, unexplained hash drift, unexpected file change, leakage signal, TEST exposure, or status/result promotion.
