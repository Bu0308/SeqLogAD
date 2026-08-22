# PROTOCOL-SPLIT-CLARIFY-001 — Exact Raw Split Semantics

| Field | Frozen value |
|---|---|
| Addendum ID | `PROTOCOL-SPLIT-CLARIFY-001` |
| Addendum version | `1.0` |
| Parent | `PROTOCOL-001` v1.1 |
| Status | **FROZEN_HUMAN_APPROVED** |
| Approval date | 2026-08-22 |
| Empirical status | `NOT_RUN` |
| Real split | `NOT_CREATED` |
| Scientific TEST | `NEVER_CREATED / NEVER_OPENED` |
| Machine contract | `configs/protocols/split-clarification-v1.yaml` |
| Evidence matrix | `docs/literature/split-protocol-evidence-matrix.md` |
| Citation record | `docs/references/PROTOCOL-SPLIT-CLARIFY-001-citations.md` |

This binding addendum resolves the allocation-unit, boundary, purge, residual,
reconciliation, and identity ambiguities that stopped `SPLIT-001`. It narrows
how the already approved Protocol v1.1 behavior is executed; it does not create
a split or authorize scientific execution.

The design is chronology-first, leakage-controlled, and label-independent.
Literature supports the general use of HDFS block/session grouping, BGL
chronological evaluation, split-before-window construction, and fixed-entry
windows. The five-way ratio, cumulative-floor algorithm, connected-component
purge, per-partition residual policy, hashing, and physical TEST seal are
SeqLogAD protocol choices. None is presented as a novel method or a universal
literature standard.

## 1. Binding order and non-authorizations

For future scientific work, the active contract is the conjunction of:

1. `docs/research-protocol-v1.1.md`;
2. this split-clarification addendum;
3. `docs/statistical-decision-contract.md`.

If a broad sentence in Protocol v1.1 admits several split implementations,
this addendum selects the one permitted implementation. Historical Protocol
v1.0 remains immutable.

This task does **not** authorize or perform:

- real HDFS/BGL metadata generation or partition assignment;
- real TEST membership creation, label access, or physical unlock;
- Drain3 fitting, template creation, event/sequence construction;
- anomaly-distribution inspection, metrics, baseline/model execution;
- raw-data or accepted dataset-manifest mutation.

## 2. Shared partition contract

The ordered partition family is:

| Index | Partition | Target share |
|---:|---|---:|
| 0 | `BASE_TRAIN` | 0.60 |
| 1 | `FUSION_TRAIN` | 0.10 |
| 2 | `VAL_EXPERT` | 0.10 |
| 3 | `VAL_FUSION` | 0.10 |
| 4 | `TEST` | 0.10 |

The partition family and ratios are `SEQLOGAD_PROTOCOL_DECISION`. They are not
claimed to be standard. Reserved fusion partitions stay reserved even if
fusion remains conditional.

For a dataset-specific allocation universe of size `N`, define cumulative
boundaries:

```text
b0 = 0
b1 = floor(0.60 N)
b2 = floor(0.70 N)
b3 = floor(0.80 N)
b4 = floor(0.90 N)
b5 = N
```

Future code must evaluate these as exact integer divisions (`(60*N)//100`,
`(70*N)//100`, and so on), not binary floating-point multiplication.

Nominal half-open ranges are `[b0,b1)`, `[b1,b2)`, `[b2,b3)`, `[b3,b4)`, and
`[b4,b5)`. Cumulative floor is a `SEQLOGAD_PROTOCOL_DECISION`. It is applied
without class balancing, randomization, or post-hoc ratio repair.

Assignment must not read or derive anomaly labels. Parser state, templates,
event IDs, window content, and downstream outcomes are also forbidden inputs.
Changing labels or parser/template state while structural META-001 identities
remain fixed must leave the split unchanged.

## 3. HDFS mathematical contract

### 3.1 Allocation universe

Read META-001 HDFS line records in source order. A line is structurally
eligible exactly when `assignment_status=ASSIGNED`, meaning that META-001 gave
it at least one usable normalized block identity and a connected-component ID.

Let the eligible lines, after removing structurally unassigned records from the
ranking universe but not from accounting, be:

```text
e0, e1, ..., e(N-1)
```

`N = N_ELIGIBLE_PRE_PURGE`. The rank of `ei` is its position in this eligible
subsequence, not its original zero-based source-line index. Each `ei` receives
the nominal partition containing its eligible rank under the shared boundaries.

META-001 records with `assignment_status=UNASSIGNED` are structurally
ineligible. Their existing reason is retained exactly as one of:

- `NO_BLOCK_ID`;
- `MALFORMED_BLOCK_TOKEN`;
- `DECODE_ERROR`.

They receive no fake block/session/component identity and no scientific
partition. Their manifest disposition is `STRUCTURAL_EXCLUSION`; the preserved
META-001 value is the exclusion reason. A purged real component instead uses
disposition and reason `PURGED_BOUNDARY`.

### 3.2 Atomic connected components

For every META-001 connected component `c`, let `R(c)` be the set of nominal
partition names occupied by all eligible member-line ranks.

```text
if |R(c)| = 1:
    assign every eligible member line and the whole component to that partition
if |R(c)| >= 2:
    exclude every eligible member line and the whole component as PURGED_BOUNDARY
```

There is no split, left/right move, largest-overlap assignment, ratio repair,
or label-based choice. The same rule applies whether a component crosses two,
three, or all five nominal partitions.

Block/session grouping and keeping a session unsplit are
`LITERATURE_SUPPORTED`. META-001 transitive connected components and complete
`PURGED_BOUNDARY` exclusion are a `SEQLOGAD_PROTOCOL_DECISION` needed to make
shared-line atomicity deterministic.

### 3.3 HDFS denominators and reconciliation

Target ratios use `N_ELIGIBLE_PRE_PURGE`.

For partition `p`, the realized line ratio is:

```text
realized_ratio(p) = assigned_eligible_lines(p)
                    / TOTAL_ASSIGNED_ELIGIBLE_AFTER_PURGE
```

The purge ratio is:

```text
purge_ratio = PURGED_BOUNDARY_ELIGIBLE_LINES / N_ELIGIBLE_PRE_PURGE
```

When the corresponding denominator is zero, the ratio is `null`, never `0`,
and the structural manifest is not scientifically execution-ready.

Every future manifest must satisfy exactly:

```text
TOTAL_RAW_LINES
= STRUCTURALLY_INELIGIBLE_LINES
 + ASSIGNED_ELIGIBLE_LINES
 + PURGED_BOUNDARY_ELIGIBLE_LINES

ASSIGNED_ELIGIBLE_LINES
= BASE_TRAIN
 + FUSION_TRAIN
 + VAL_EXPERT
 + VAL_FUSION
 + TEST
```

No line may be silently lost or counted in two categories.

## 4. BGL mathematical contract

### 4.1 Raw allocation

Let `N` be the number of BGL raw-line metadata records. META-001 original
source-line rank `0..N-1` is authoritative. All raw records participate in the
allocation universe; malformed or tied timestamps do not reorder or remove a
line.

Apply the shared cumulative-floor boundaries directly to the raw ranks. This
creates five contiguous raw ranges before parser fitting and before parent
windows. BGL chronological evaluation and raw split-before-window construction
are `LITERATURE_SUPPORTED`; the exact five-way/floor instantiation is a
`SEQLOGAD_PROTOCOL_DECISION`.

### 4.2 Parent windows and residuals

Within each partition independently, begin at that partition's first raw line
and construct consecutive windows of exactly 100 raw lines with stride 100.
Windows never overlap and never cross a partition boundary.

For a partition with `n_p` raw lines:

```text
complete_windows(p) = floor(n_p / 100)
complete_window_lines(p) = 100 * complete_windows(p)
r_p = n_p mod 100
```

If `r_p=0`, there is no residual. If `1<=r_p<=99`, the final `r_p` lines form
one explicit exclusion range with disposition `DROPPED_RESIDUAL_WINDOW`.
Residual lines are not padded, borrowed across partitions, merged backward,
or emitted as an active-v1.1 `EventSequence`.

Fixed-entry, non-overlapping windows are `LITERATURE_SUPPORTED`; 100 events is
`LITERATURE_INFORMED_SEQLOGAD_DECISION` because recent papers also use other
sizes/grouping strategies. Incomplete-window discarding appears in recent
work, while SeqLogAD's exact per-five-partition residual accounting is
`LITERATURE_INFORMED_SEQLOGAD_DECISION` rather than a universal rule.

Every future BGL manifest must satisfy:

```text
TOTAL_RAW_LINES = COMPLETE_WINDOW_LINES + RESIDUAL_EXCLUDED_LINES
```

Every raw line appears exactly once in a complete parent window or exactly
once in a residual exclusion.

## 5. Deterministic identity contract

### 5.1 Canonical serialization

Identity-bearing objects use canonical JSON:

- UTF-8 bytes;
- object keys sorted lexicographically;
- compact separators `,` and `:`;
- non-ASCII retained without semantic rewriting;
- `NaN`/infinity forbidden;
- paths, if present, normalized repository-relative POSIX paths;
- no Python `hash()` or filesystem discovery order.

### 5.2 Canonical split payload and split identity

The canonical split payload has these exact top-level keys:

```text
schema_version
dataset_fingerprint
protocol
split_contract
partition_order
target_ratios
boundary_contract
dataset_semantics
assignments
exclusions
```

It contains deterministic scientific identity only:

- dataset fingerprint;
- protocol ID/version and split-contract ID/version;
- partition semantics and target ratios;
- ordered assignment decisions without derived assignment IDs;
- ordered exclusions without derived assignment IDs.

It excludes timestamps, absolute paths, Git/dirty state, mutable filesystem
metadata, its own hash, final file hash, assignment IDs, and partition hashes.

Every assignment/exclusion decision contains the common fields
`unit_kind`, `structural_unit_id`, `chronological_start`,
`chronological_end_exclusive`, `disposition`, `partition_or_null`, and
`exclusion_reason_or_null`.

Dataset-specific identity-bearing fields are:

- HDFS assigned/purged component: META-001 `component_id`, canonical block-ID
  list, increasing eligible ranks, and increasing original chronology indices;
- HDFS structural line exclusion: raw `record_id`, raw chronology index, and
  exact META-001 unassigned reason;
- BGL complete/residual range: inclusive raw-rank start, exclusive raw-rank
  end, raw-line count, and parent ordinal within partition or `null`.

Assignments are sorted by `(partition_order_index, chronological_start,
structural_unit_id)`. Exclusions are sorted by `(chronological_start,
unit_kind, structural_unit_id)`. HDFS unassigned raw lines are manifest-specific
structural-exclusion records; they are not fabricated as block components.

```text
split_payload_hash = SHA256(canonical_split_payload_utf8_bytes)
split_manifest_id  = "SPLIT-" + split_payload_hash
```

Every SHA-256 identity is a full 64-character lowercase hexadecimal digest.

The existing schema field `split_manifest_sha256` carries this
`split_payload_hash`; it does **not** mean the hash of volatile final manifest
bytes. This naming compatibility avoids rewriting approved SCHEMA-002 records.

### 5.3 Assignment identity

After `split_payload_hash` exists, each assignment/exclusion ID is derived from
canonical JSON containing:

- dataset fingerprint;
- protocol and split-contract identity;
- `split_payload_hash`;
- structural unit identity;
- disposition;
- assigned partition or `null`;
- exclusion reason or `null`.

```text
assignment_id = "PART-" + SHA256(canonical_assignment_identity_bytes)
```

Assignment IDs are never part of the split payload. This breaks the circular
dependency while still binding each derived record to the complete split.

### 5.4 Partition and file hashes

For each partition:

```text
partition_hash = SHA256(canonical_json({
  dataset_fingerprint,
  protocol_id_and_version,
  split_contract_id_and_version,
  split_payload_hash,
  partition_name,
  ordered_structural_membership
}))
```

`ordered_structural_membership` uses records containing only
`structural_unit_id`, `chronological_start`, and
`chronological_end_exclusive`, sorted by `(chronological_start,
structural_unit_id)`. It never uses assignment IDs. Timestamps and filesystem
metadata are excluded.

`manifest_file_hash` is SHA-256 of the exact persisted manifest bytes. It is
artifact-integrity metadata kept in a sidecar or verifier output, not embedded
recursively in the manifest. Volatile audit metadata may change the file hash
but must not change `split_payload_hash`, assignment IDs, or partition hashes.

All hashing choices in this section are `SEQLOGAD_PROTOCOL_DECISION`.

### 5.5 Future TEST seal binding

SPLIT-001's future physical seal must bind at least:

- dataset fingerprint;
- protocol ID/version;
- `split_payload_hash`;
- TEST `partition_hash`.

This addendum defines that binding but neither generates nor opens TEST.

## 6. Synthetic proof fixtures

These examples prove contract arithmetic only. They are not HDFS/BGL results.

### 6.1 HDFS fixture

Synthetic source: 22 raw lines, of which 20 are eligible and two are explicit
structural exclusions (`NO_BLOCK_ID`, `DECODE_ERROR`). For `N=20`:

```text
boundaries = [0, 12, 14, 16, 18, 20]
```

Synthetic components over eligible ranks:

| Component | Eligible ranks | Decision | Assigned lines |
|---|---|---|---:|
| `C0` | 0–3 | `BASE_TRAIN` | 4 |
| `C1` | 4–10 | `BASE_TRAIN` | 7 |
| `CX` | 11, 12 | `PURGED_BOUNDARY` (60% boundary) | 0 |
| `C2` | 13 | `FUSION_TRAIN` | 1 |
| `CY` | 14, 16 | `PURGED_BOUNDARY` (transitively connected, non-contiguous, crosses another boundary) | 0 |
| `C3` | 15 | `VAL_EXPERT` | 1 |
| `C4` | 17 | `VAL_FUSION` | 1 |
| `C5` | 18, 19 | `TEST` | 2 |

Results:

```text
assigned partition counts = [11, 1, 1, 1, 2]
ASSIGNED_ELIGIBLE_LINES = 16
PURGED_BOUNDARY_ELIGIBLE_LINES = 4
STRUCTURALLY_INELIGIBLE_LINES = 2
22 = 2 + 16 + 4
16 = 11 + 1 + 1 + 1 + 2
realized ratios = [0.6875, 0.0625, 0.0625, 0.0625, 0.125]
purge ratio = 4 / 20 = 0.20
```

### 6.2 BGL fixture

Synthetic `N=1037` raw lines:

```text
boundaries = [0, 622, 725, 829, 933, 1037]
partition raw sizes = [622, 103, 104, 104, 104]
complete 100-line windows = [6, 1, 1, 1, 1]
complete window lines = [600, 100, 100, 100, 100]
residual lines = [22, 3, 4, 4, 4]
1037 = 1000 + 37
```

No residual is moved into another partition, and no synthetic label is used.

## 7. Frozen edge-case policy

### Shared

- Empty input: emit a structurally valid, reconciled manifest with zero counts,
  `null` realized ratios, and `execution_ready=false`.
- Very small input/zero-length nominal partitions: preserve cumulative-floor
  output exactly; do not redistribute records to fill empty partitions.
- Duplicate structural identity: reject; never deduplicate silently.
- Missing/unsupported protocol or split-contract version: reject.
- Canonical payload or stored hash mismatch: reject as stale/corrupt.

### HDFS

- Component crossing two, three, four, or five partitions: purge the entire
  component once as `PURGED_BOUNDARY`.
- Component spanning nearly the whole dataset: same rule; no special rescue.
- All eligible lines purged: reconciliation is valid, realized ratios are
  `null`, and scientific execution readiness is false.
- Zero eligible lines: retain all structural exclusions; target/purge/realized
  ratios with zero denominators are `null`; readiness is false.

### BGL

- Partition size `<100`: all its lines become one residual exclusion.
- Partition size `=100`: exactly one parent, no residual.
- Exact positive multiple of 100: complete parents only.
- Entire dataset `<100`: cumulative floor may distribute small raw ranges;
  each non-empty range is an explicit residual, and no partition borrows.
- TEST residual: recorded as an exclusion exactly like other partitions;
  it is not padded or inspected for labels.

## 8. Evidence and claim safety

The normative classification is maintained in
`docs/literature/split-protocol-evidence-matrix.md`. Allowed values are exactly:

- `LITERATURE_SUPPORTED`;
- `LITERATURE_INFORMED_SEQLOGAD_DECISION`;
- `SEQLOGAD_PROTOCOL_DECISION`;
- `INSUFFICIENT_EVIDENCE`.

Literature disagreement is retained rather than hidden. In particular, recent
work uses random and chronological HDFS allocation, several BGL grouping
strategies, multiple window sizes, and different split ratios. Therefore this
contract claims reproducibility and leakage control for SeqLogAD, not universal
optimality.

## 9. Completion and next gate

This addendum is frozen before split generation, parser fitting, any killer
experiment, or TEST creation/access. `SPLIT-001` may now implement this exact
contract under separate authorization. It must first prove the same invariants
on synthetic fixtures, then verify accepted dataset fingerprints, generate the
real structural manifests, and immediately install the physical TEST guard.
