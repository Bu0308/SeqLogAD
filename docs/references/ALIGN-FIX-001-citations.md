# ALIGN-FIX-001 source and citation note

## Scope classification

`ALIGN-FIX-001` changes repository execution status, portable artifact pointers,
seed/config synchronization, task naming, and license-decision visibility only.
It does not change a scientific hypothesis, dataset, split assignment, parser
state, statistical rule, method family, or empirical result.

## External scientific sources

**NONE.** No external citation is needed for this engineering/status correction,
and no citation was added merely for appearance.

## Internal evidence used

- `configs/protocols/protocol-v1.1.yaml`
- `configs/protocols/effect-001.yaml`
- `configs/protocols/split-clarification-v1.yaml`
- `data/processed/splits/<dataset>/split-manifest.json`
- `data/processed/splits/<dataset>/test-seal.json`
- `data/processed/parsers/<dataset>/parser-manifest.json`
- `docs/split-artifacts-and-test-seal.md`
- `docs/parser-fit-and-freeze.md`
- `docs/audits/PROJECT-CONTEXT-POST-PARSE-001.md`

The generated artifact paths above are repository-relative and ignored by Git;
their identities are copied into `configs/active-state.yaml` and independently
validated against local bytes during ALIGN-FIX-001.
