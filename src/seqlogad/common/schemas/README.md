# Schemas

Implemented in `SCHEMA-001`:

- strict, immutable `LogEvent` and `EventTemplate` contracts;
- deterministic event-occurrence and template identities;
- dataset/source/group/partition provenance;
- structurally isolated supervision and label-free model-input view;
- canonical JSON/hash helpers and schema regression tests.

Input: versioned parser output plus previously assigned provenance and authorized non-TEST supervision. Output: validated schema version `1.0` records. Dependencies: Pydantic and the frozen `PROTOCOL-001` contract.

Planned after SCHEMA-001:

- `EventSequence`, split-manifest identity and localization coordinates (`SCHEMA-002`);
- `MutationRecord`, `ExpertEvidence` and structured claims;
- downstream anomaly, evidence, hypothesis, incident, test, investigation and feedback records.

No parser, sequence, mutation, detector, fusion, RAG or agent behavior is implemented here. See `docs/schemas/canonical-events.md`.
