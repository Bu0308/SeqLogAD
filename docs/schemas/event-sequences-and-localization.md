# SCHEMA-002 — Event Sequence, Partition, Localization, and Mutation Contract

| Field | Value |
|---|---|
| Task | `SCHEMA-002` |
| Sequence schema version | `1.0` |
| Mutation schema version | `1.0` |
| KT-3 control schema version | `1.0` |
| Status | **FROZEN — PROTOCOL v1.1 COMPATIBLE** |
| Implementation date | 2026-08-21 |
| Compatibility freeze | 2026-08-22 (`SCHEMA-COMPAT-001`) |
| Source module | `src/seqlogad/common/schemas/sequences.py` |
| Scientific protocol | `docs/research-protocol-v1.1.md` |
| Method provenance | `docs/references/SCHEMA-002-citations.md`; `docs/references/SCHEMA-COMPAT-001-citations.md` |

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

future KT-3 control generator + VAL_EXPERT/authorized TEST EventSequence
  → SequenceDestructionRecord
```

The schema checks record consistency after those future components have produced values. It does not claim that those components already exist.

## 2. Partition identity

`PartitionIdentity` carried by an `EventSequence` records:

- protocol ID `PROTOCOL-001` and an explicit supported version (`1.0` historical or `1.1` active);
- `SPLIT-<sha256>` split-manifest identity and exact content hash;
- deterministic raw-unit assignment ID;
- one of `BASE_TRAIN`, `FUSION_TRAIN`, `VAL_EXPERT`, `VAL_FUSION`, or `TEST`;
- frozen target ratio `0.60/0.10/0.10/0.10/0.10`.

Target ratio is not realized ratio. A future split manifest must report realized ratios and exclusions after atomicity/purge rules.

`protocol_version` has no implicit default. Historical canonical payloads remain valid only when they explicitly retain `"1.0"`; they are never relabeled. New artifacts must use `build_active_partition_identity(...)`, which derives the split ID and target ratio and pins `"1.1"`. Unsupported or omitted versions are rejected.

Event, sequence, mutation, and KT-3 record `schema_version` values remain separate from the scientific `protocol_version`. Their `1.0` values are record-format versions, not stale Protocol-v1.0 claims.

The split has no random seed field because Protocol v1.1 assignment is deterministic and chronological. Transformation/model seeds remain separate provenance; introducing randomized split assignment would require a protocol amendment and split-schema review.

### 2.1 Compatibility matrix

| Contract | Historical v1.0 | Active v1.1 | Final state |
|---|---|---|---|
| `EventTemplate` / `LogEvent` | Record-format schema `1.0` | Protocol-independent parser/raw provenance and label isolation | Compatible; unchanged |
| `PartitionIdentity` | Explicit `"1.0"` parses and round-trips | Active factory pins `"1.1"` | Compatible; no implicit version |
| Five partitions/ratios | Supported | Same `60/10/10/10/10` contract | Compatible |
| HDFS parent | Block/component identity | Block/component identity | Compatible |
| BGL parent | 100 events; explicit historical residual 20–99 supported | Exactly 100 events | Version-aware |
| `MutationRecord` | Normal-source synthetic anomaly provenance | Linked through its source sequence/split identity | Unchanged; not KT-3 |
| `SequenceDestructionRecord` | N/A | Active-v1.1 KT-3 provenance | Added |

`PartitionAssignment` represents both included and deliberately excluded raw units:

| Dataset unit | Assigned form | Exclusion form |
|---|---|---|
| HDFS connected block component | `hdfs_block_component` + partition | `PURGED_BOUNDARY` with reason |
| BGL chronological raw range | `bgl_raw_range` + partition | historical `DROPPED_SHORT_WINDOW` for `<20`; active-v1.1 `DROPPED_RESIDUAL_WINDOW` for a trailing `1–99` events |

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
- Active Protocol v1.1 parents contain exactly 100 events and cannot claim a residual window.
- Explicit historical Protocol v1.0 records may retain the former 20–99 event residual rule.
- Real supervision uses the separated inline source-alert marker and any-source-alert aggregation.
- Optional real alert localization is token-only and must stay distinct from synthetic localization.

This schema validates one parent at a time. Non-overlap across the BGL parent collection and partition containment remain future split/sequence-builder responsibilities. A future active-v1.1 manifest can retain trailing-residual provenance with `DROPPED_RESIDUAL_WINDOW`; it cannot emit that residual as an `EventSequence`.

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

`MutationRecord` is not reused for KT-3: it defines a synthetic anomaly from a normal source, forbids no-ops, and carries localization targets. Those semantics conflict with EFFECT-001's paired order-destruction control.

## 7. SequenceDestructionRecord

`SequenceDestructionRecord` is the minimal provenance contract for future KT-3 controls. It records:

- original sequence and parent/session linkage;
- the complete active Protocol-v1.1 partition/split/assignment identity;
- verified dataset fingerprint, generator version, and shuffle seed;
- original/destroyed ordered-event hashes;
- original/destroyed multiset hashes and lengths, which must match pairwise;
- `applied` or `noop_unperturbable` status, with a mandatory reason for a retained no-op;
- one controlled validation label/access shared by the original/destroyed pair, while TEST records must omit both and retain their label only in the future sealed evaluator;
- literal `raw_data_mutated=false`.

The control is restricted to `VAL_EXPERT` and future human-authorized `TEST`. It stores provenance only: no shuffle implementation, score, metric, AP result, or TEST unlock exists in this task.

## 8. Determinism and serialization

All SCHEMA-002 models inherit the SCHEMA-001 strict contract:

- immutable after validation;
- unknown fields rejected;
- canonical compact JSON with stable key order;
- canonical SHA-256 support;
- non-finite numbers rejected where scalar mutation parameters are allowed.

Identity helpers use full lowercase SHA-256 digests with type prefixes: `SPLIT-`, `PART-`, `SEQ-`, `MUT-`, and `CTRL-KT3-`. The prefixes are type markers, not security boundaries.

## 9. Explicitly not implemented

SCHEMA-002 does not implement or execute:

- raw pre-partitioning or split-manifest generation;
- HDFS block extraction/connected components;
- BGL parent-window construction;
- Drain3 parsing or template generation;
- real sequence artifact generation;
- synthetic mutation sampling or byte/event modification;
- KT-3 shuffling, destruction-manifest generation, scoring, or execution;
- model tensors, padding, models, training, thresholding, or metrics;
- scientific TEST access;
- retrieval, RAG, agent, API, or UI behavior.

## 10. Compatibility freeze

SCHEMA-COMPAT-001 verified with synthetic unit fixtures that:

1. explicit historical v1.0 identity still parses and round-trips;
2. active v1.1 identity is created only through the pinned factory;
3. unsupported/missing protocol versions fail;
4. all five frozen partitions and ratios are retained;
5. HDFS component/group and BGL 100-event parent identities are representable;
6. serialization preserves protocol, split, assignment, dataset, and parent provenance;
7. KT-3 can record applied and retained no-op controls without weakening TEST label isolation;
8. no field implies that a real split, sequence, shuffle, experiment, or TEST access exists.

Any accepted change after approval requires a new schema version or an explicit compatibility decision.
