# SCHEMA-002 — Event Sequence, Partition, Localization, and Mutation Contract

| Field | Value |
|---|---|
| Task | `SCHEMA-002` |
| Sequence schema version | `1.0` |
| Mutation schema version | `1.0` |
| Status | **IMPLEMENTED — AWAITING HUMAN AUDIT** |
| Implementation date | 2026-08-21 |
| Source module | `src/seqlogad/common/schemas/sequences.py` |
| Scientific protocol | `docs/research-protocol.md` |
| Method provenance | `docs/references/SCHEMA-002-citations.md` |

This contract makes sequence provenance, partition ownership, coordinate-aware localization, and deterministic synthetic-mutation provenance machine-checkable. It validates supplied synthetic records only. It does **not** split datasets, parse logs, build real sequences, mutate events, access TEST labels, or run an experiment.

## 1. Contract boundary

```text
future split implementation
  → PartitionAssignment + split manifest identity

future sequence builder + SCHEMA-001 LogEvents
  → EventSequence
  → SequenceModelInput (label-free)

future mutation generator + normal EventSequence
  → MutationRecord + LocalizationCoordinates
```

The schema checks record consistency after those future components have produced values. It does not claim that those components already exist.

## 2. Partition identity

`PartitionIdentity` carried by an `EventSequence` records:

- protocol ID/version: `PROTOCOL-001` / `1.0`;
- `SPLIT-<sha256>` split-manifest identity and exact content hash;
- deterministic raw-unit assignment ID;
- one of `BASE_TRAIN`, `FUSION_TRAIN`, `VAL_EXPERT`, `VAL_FUSION`, or `TEST`;
- frozen target ratio `0.60/0.10/0.10/0.10/0.10`.

Target ratio is not realized ratio. A future split manifest must report realized ratios and exclusions after atomicity/purge rules.

`PartitionAssignment` represents both included and deliberately excluded raw units:

| Dataset unit | Assigned form | Exclusion form |
|---|---|---|
| HDFS connected block component | `hdfs_block_component` + partition | `PURGED_BOUNDARY` with reason |
| BGL chronological raw range | `bgl_raw_range` + partition | `DROPPED_SHORT_WINDOW` with reason when residual length `<20` |

HDFS components carry sorted, unique block IDs. BGL ranges cannot carry HDFS group IDs. Excluded units have no scientific partition, and assigned units have no exclusion reason.

The deterministic assignment identity hashes the verified dataset fingerprint, split-manifest ID, unit type/key, chronology, disposition, assigned partition, group IDs, and exclusion reason. This prevents a changed assignment decision from silently retaining the same ID.

## 3. EventSequence

An `EventSequence` is one ordered, unpadded parent sequence. It records:

- dataset ID/version/fingerprint;
- partition and assignment identity;
- dataset-specific sequence strategy and source key;
- aligned ordered `record_ids`, `event_ids`, source-line numbers, and chronological indices;
- SHA-256 of ordered event IDs;
- frozen parser-state and template-registry hashes;
- BGL window metadata when applicable;
- controlled non-TEST sequence supervision.

Its deterministic ID is derived from dataset fingerprint, partition-assignment ID, strategy, source key, and ordered source record IDs. Its content hash is derived separately from ordered event IDs. Consequently, source/provenance identity and sequence content identity cannot be confused.

### 3.1 HDFS strategy

- Strategy: `hdfs_block_session`.
- Dataset key must be `hdfs`.
- One block/session component produces one variable-length sequence.
- Fixed-window and residual flags are forbidden.
- Real supervision uses the external HDFS block-label source and block-source aggregation.
- Real HDFS labels remain sequence-level only; they provide no token, gap, or transition ground truth.

### 3.2 BGL strategy

- Strategy: `bgl_fixed_parent_window`.
- Dataset key must be `bgl`.
- Normal parent length is exactly 100 events.
- A final residual sequence is valid only from 20 through 99 events.
- Real supervision uses the separated inline source-alert marker and any-source-alert aggregation.
- Optional real alert localization is token-only and must stay distinct from synthetic localization.

This schema does not make windows or perform label aggregation; those are future builder responsibilities.

## 4. Label and TEST boundary

| Partition | Permitted canonical sequence state |
|---|---|
| `BASE_TRAIN` | Normal supervision, `normal_pool_filtering` access |
| `FUSION_TRAIN` | Normal supervision, `normal_pool_filtering` access |
| `VAL_EXPERT` | Controlled supervision, `validation_evaluation` access |
| `VAL_FUSION` | Controlled supervision, `validation_evaluation` access |
| `TEST` | `supervision` must be absent |

`EventSequence.to_model_input()` returns only `sequence_id`, ordered `event_ids`, and `valid_length`. It excludes dataset identity, partition, source locations, labels, label access, and mutation targets. The returned sequence is unpadded; future batching must add and mask padding outside this contract.

## 5. Localization coordinate contract

All positions are zero-based and interpreted against the **observed** sequence.

For observed sequence `E0 E1 E2`:

```text
tokens:       E0      E1      E2       valid positions 0..2
gaps:      G0    G1      G2      G3    valid positions 0..3
transitions:    T0      T1             valid positions 0..1
```

Coordinate families are not interchangeable:

- token positions locate observed extra, repeated, replaced, or reordered events;
- gap positions locate absent expected events;
- transition positions locate affected observed transitions;
- `sequence_level=true` identifies the parent as anomalous independently of local coordinates.

The distinction between unsupported and empty is explicit:

- `null` / `None`: the evidence source does not support that coordinate family;
- `[]` / empty tuple: the family is supported, but this operation has no target in it.

This prevents missing-event anomalies from being forced into an incorrect token target and prevents unsupported real localization from being scored as a correct empty prediction.

## 6. MutationRecord

`MutationRecord` is provenance for a future synthetic mutation. It contains:

- deterministic mutation ID;
- source sequence, source partition, verified dataset and split identities;
- literal normal source label;
- generator version, non-negative seed, operation ordinal, and canonical parameters;
- expected/observed ordered-event hashes and lengths;
- all three supported localization families;
- literal `synthetic=true`.

Mutations sourced from `TEST` are rejected by this pre-final schema. Equal expected and observed hashes are rejected as no-ops. Parameters are unique by name, sorted before identity hashing, and cannot contain non-finite floating-point values.

The mutation ID binds the source sequence, generator version, seed, operation, ordinal, canonical parameters, expected/observed content hashes and lengths, and localization target. A changed generated result therefore cannot silently retain the same mutation ID.

### 6.1 Frozen operation invariants

| Operation | Length rule | Token target | Gap target | Transition target |
|---|---|---|---|---|
| `missing` | observed = expected − 1 | empty | required | supported, may be empty |
| `extra` | observed = expected + 1 | required | empty | supported, may be empty |
| `repeated` | observed = expected + 1 | required | empty | supported, may be empty |
| `replacement` | equal lengths | required | empty | required |
| `reorder` | equal lengths | required | empty | required |

`unexpected_transition` is not a separate mutation operation in protocol v1. It remains derived evidence/analysis so the Markov expert does not define the benchmark on which it is evaluated.

## 7. Determinism and serialization

All SCHEMA-002 models inherit the SCHEMA-001 strict contract:

- immutable after validation;
- unknown fields rejected;
- canonical compact JSON with stable key order;
- canonical SHA-256 support;
- non-finite numbers rejected where scalar mutation parameters are allowed.

Identity helpers use full lowercase SHA-256 digests with type prefixes: `SPLIT-`, `PART-`, `SEQ-`, and `MUT-`. The prefixes are type markers, not security boundaries.

## 8. Explicitly not implemented

SCHEMA-002 does not implement or execute:

- raw pre-partitioning or split-manifest generation;
- HDFS block extraction/connected components;
- BGL parent-window construction;
- Drain3 parsing or template generation;
- real sequence artifact generation;
- synthetic mutation sampling or byte/event modification;
- model tensors, padding, models, training, thresholding, or metrics;
- scientific TEST access;
- retrieval, RAG, agent, API, or UI behavior.

## 9. Human audit gate

Before this contract is marked frozen, the human reviewer should verify:

1. partition identities are sufficient for later leakage audits;
2. token/gap/transition definitions match intended evaluation coordinates;
3. HDFS and BGL sequence constraints match `PROTOCOL-001`;
4. TEST records cannot expose supervision or pre-final mutations;
5. each mutation family has scientifically correct length and localization invariants;
6. no field implies that real artifacts or experiments already exist.

Any accepted change after approval requires a new schema version or an explicit compatibility decision.
