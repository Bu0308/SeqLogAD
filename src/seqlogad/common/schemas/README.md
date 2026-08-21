# Schemas

Implemented and human-approved in `SCHEMA-001`:

- strict, immutable `LogEvent` and `EventTemplate` contracts;
- deterministic event-occurrence and template identities;
- dataset/source/group/partition provenance;
- structurally isolated supervision and label-free model-input view;
- canonical JSON/hash helpers and schema regression tests.

Input: versioned parser output plus previously assigned provenance and authorized non-TEST supervision. Output: validated schema version `1.0` records. Dependencies: Pydantic and the frozen `PROTOCOL-001` contract.

Implemented in `SCHEMA-002`, awaiting human audit:

- deterministic partition-assignment and split-manifest identities;
- HDFS block/session and BGL 100-event/residual `EventSequence` contracts;
- label-free `SequenceModelInput`;
- separate token, gap and transition coordinates;
- deterministic normal-source `MutationRecord` contracts for five frozen mutation families.

Planned after SCHEMA-002:

- split manifest and processed-artifact envelope schemas where required by the implementation task;
- `ExpertEvidence` and structured claims;
- downstream anomaly, evidence, hypothesis, incident, test, investigation and feedback records.

No parser, sequence-builder, mutation-generator, detector, fusion, RAG or agent behavior is implemented here. See `docs/schemas/canonical-events.md` and `docs/schemas/event-sequences-and-localization.md`.
