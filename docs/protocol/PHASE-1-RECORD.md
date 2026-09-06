# Phase 1 record — P1.2 to P1.8

Companion to `docs/protocol/P1.1-research-scope.md` and
`docs/protocol/P1.4-normalisation.md`. Every number here was produced by
`scripts/build_streams.py` followed by `scripts/build_protocol.py` and is bound by
SHA-256 in `data/processed/protocol/G0-receipt.json`.

## P1.2 — Dataset portfolio (`DATA-REG-001`)

Registry: `data/registry/dataset_registry.{csv,json}`.
Source: Loghub, Zenodo record `10.5281/zenodo.8196385`, licence CC-BY-4.0, open
access — read from the record's own metadata API, not assumed.

| Architecture | Dataset | Domain | Raw bytes | Records | Role | Ground truth |
| --- | --- | --- | ---: | ---: | --- | --- |
| `ARCH-HDFS` | HDFS_v1 | distributed storage | 1.58 GB | 11,175,629 | source + target | 16,838 / 575,061 anomalous blocks |
| `ARCH-BGL` | BGL | HPC supercomputer | 743 MB | 4,747,963 | source + target | 348,460 / 4,747,963 alert lines |
| `ARCH-HADOOP` | Hadoop | batch compute framework | 48.6 MB | 394,310 | source + target | 44 / 55 failure-injected applications |
| `ARCH-OPENSTACK` | OpenStack | cloud IaaS control plane | 61.4 MB | 207,820 | **source only** | 4 anomalous VM instances |

Total: 16,525,722 records across four architectures. Every fold therefore has three
source architectures, meeting the Excel G0 minimum.

Label counts are aggregate inventories opened through the evaluation-only boundary
under scope `PROTOCOL_LABEL_INVENTORY`, and each access is appended to
`data/processed/protocol/label-access-audit.jsonl`. No per-record label was
materialised anywhere in Phase 1.

Two architectures were added for this phase. Both were downloaded from the same
Zenodo record and their MD5 digests were recomputed and matched against the record's
published values before use. Candidates considered and not taken — Thunderbird,
Spirit, Spark, HDFS_v2, HDFS_v3_TraceBench and the unlabelled Loghub corpora — carry
their reasons in the registry. Thunderbird is the notable loss: a genuinely distinct
HPC architecture, rejected only because its ~2.0 GB archive expands beyond the
2.2 GB of free space available, and an unverifiable dataset may not enter the
registry.

## P1.3 — Canonical schema (`LOG-UNIFY-001`)

`src/seqlogad/protocol/schema.py`, schema version 1.0. Per-architecture mapping
contracts in `SOURCE_MAPPINGS` declare which fields are present, which are
declared-absent, how each derived field is computed, and — for BGL — that the inline
alert marker in column 0 is stripped by the adapter and never enters a record.

Parse outcomes, counted and typed rather than dropped:

| Architecture | `OK` | `CONTINUATION` | `MALFORMED` | Dropped |
| --- | ---: | ---: | ---: | ---: |
| `ARCH-HDFS` | 11,175,629 | 0 | 0 | 0 |
| `ARCH-BGL` | 4,747,963 | 0 | 0 | 0 |
| `ARCH-HADOOP` | 180,896 | 213,414 | 0 | 0 |
| `ARCH-OPENSTACK` | 207,812 | 0 | 8 | 0 |

**One raw line always yields exactly one canonical record.** Hadoop's 213,414
`CONTINUATION` records are wrapped stack traces and YARN container diagnostics that
carry no log header; they are retained as first-class records with a null timestamp
and an honest status rather than discarded. OpenStack's 8 `MALFORMED` lines are
likewise retained.

## P1.5 — Cross-system folds (`CS-SPLIT-001`)

Contract: `configs/protocols/cross-system-split-v1.yaml`. Fully deterministic; no
seed is used.

Each architecture's chronological stream is cut into `EARLY` (50%), `GUARD` (5%),
`MID` (15%) and `LATE` (30%) by cumulative record count. Roles map segments to
partitions identically whether the architecture is a source or the target, which
removes role-dependent leakage by construction.

Two label-blind rules handle grouping units (HDFS blocks, Hadoop applications,
OpenStack instances):

- **Integrity** — a unit follows the segment of its last record, so no unit is split.
- **Boundary handling** — a boundary that no unit straddles can be reached either by
  keeping the nominal cut and excluding the units alive across it, or by snapping the
  cut to a quiet instant when no unit is alive. Both cost records; the declared rule
  takes whichever costs fewer, measured in records displaced from the nominal
  segment. Every choice, strategy and cost is recorded in the stream index.

Measured cost of that rule:

| Architecture | Strategy at each cut | Records excluded |
| --- | --- | ---: |
| `ARCH-HDFS` | nominal + exclusion ×3 | 2,207,427 (19.8%) |
| `ARCH-BGL` | nominal ×3 (no grouping units) | 0 |
| `ARCH-HADOOP` | snap, forced-monotonic, snap | 0 |
| `ARCH-OPENSTACK` | nominal + exclusion ×3 | 75 (0.04%) |

HDFS's 19.75% is the block-lifetime boundary problem, and it is **required**, not
inherited. Verified by counterfactual: with group integrity but no boundary
exclusion, the chronological invariant fails outright — `TARGET_BURN_IN` would end
at 2008-11-10 22:44:38 while `TARGET_EVALUATION` begins at 2008-11-10 20:39:03, and
**1,096,271 burn-in records would carry timestamps at or after the first evaluation
record**. HDFS also has effectively no idle instant (one quiet-instant candidate in
the whole corpus; 55,554 blocks alive at the first cut), so the cut cannot be
snapped. Excel P1.5's DoD *"không có thời điểm evaluation đi vào train/buffer"*
therefore forces the exclusion.

### What the older purge audit does and does not establish

`PURGE-AUDIT-001` measured 22.74% under the superseded five-way split. The two are
comparable in some respects and **not** in the one that matters most:

| | Comparable? | Evidence |
| --- | --- | --- |
| Corpus | yes | Both over the same 11,175,629 lines and 575,061 blocks |
| Unit | yes | Verified here: **zero** HDFS lines reference two distinct block ids, so a META-001 connected component is exactly one block |
| Mechanism | yes | Both remove units whose observations span a chronological boundary |
| Magnitude | yes | 19.75% vs 22.74%; the difference follows from 3 cuts instead of 4 |
| **Excluded population** | **no** | Only 70,659 blocks are in both sets — 53.05% of the old, 67.27% of the new, **Jaccard 0.4217**. 34,383 blocks are newly excluded that the old split retained; 62,525 old-purged blocks are now retained |

Because the excluded populations differ that much, `PURGE-AUDIT-001`'s measured
anomaly-prevalence differential (0.026745 purged vs 0.030045 retained, D = −0.0033,
≈11% relative) **does not transfer** to the new exclusion set, and
`PURGE-DECISION-001` — a human decision about the superseded split — neither
authorises nor validates it. The new exclusion is non-random by construction (it
selects long-lived blocks); whether that shifts prevalence is **unmeasured**.

Recorded as `EXC-001` and `EXC-002` in
[`../../configs/protocols/leak-cs-001-exceptions.yaml`](../../configs/protocols/leak-cs-001-exceptions.yaml).
Before any P4 claim about HDFS as a target, the researcher should authorise an
aggregate purged-versus-retained prevalence audit of *this* exclusion set, under the
same evaluation-boundary scope previously approved for `PURGE-AUDIT-001`.

Resulting folds:

| Fold | `SOURCE_TRAIN` | `SOURCE_VALIDATION` | `TARGET_BURN_IN` | `TARGET_EVALUATION` |
| --- | ---: | ---: | ---: | ---: |
| target `ARCH-HDFS` | 2,715,308 | 853,440 | 4,746,575 | 4,191,330 |
| target `ARCH-BGL` | 5,087,902 | 1,167,140 | 2,373,981 | 2,136,584 |
| target `ARCH-HADOOP` | 7,224,454 | 1,769,225 | 237,429 | 156,881 |

## P1.6 — Target burn-in buffer (`ADAPT-INPUT-001`)

Contract: `configs/protocols/target-buffer-v1.yaml`. The buffer is the `EARLY`
segment and nothing else — selected by time and record order, never by label. The
forbidden operation `select records where label == normal` is unreachable: the
buffer module imports no label code and no buffer record has a label field.

Contamination is a **declared assumption** (bound 5%), not a measurement. Measuring
realised contamination needs target ground truth and is a P4 activity
(`ROB-CONTAM-001`).

Readiness, measured on the buffer segment itself against pre-declared minima:

| Buffer | Records | Verdict | Failing checks |
| --- | ---: | --- | --- |
| `BUFFER-ARCH-HDFS` | 4,746,575 | `READY` | — |
| `BUFFER-ARCH-BGL` | 2,373,981 | `READY` | — |
| `BUFFER-ARCH-HADOOP` | 237,429 | **`NOT_READY` → `REJECTED`** | time gap 0.68 > 0.25; parse-OK 0.51 < 0.95; level and component coverage 0.51 < 0.90 |

Rejection is governed by `BUFFER-REJECT-001` in the buffer contract: a rejected
buffer may not build target memory (P3.2), calibrate an expert (P3.3), fit drift
baselines (P3.4) or set abstention thresholds (P3.5), and **G1 may not be claimed
for that fold**. Relaxing the minima to obtain a pass is a forbidden remedy.

**The Hadoop buffer is not adaptation-ready.** Half its records are header-less
container continuations with no level or component, and the cluster sat idle for
~18 hours inside the burn-in window. The minima were declared before any of this was
measured and have **not** been relaxed to obtain a pass. Buffer readiness gates G1
(Adaptation Ready), not G0 — the workbook puts "normal burn-in assumption,
contamination bound, local-memory/calibration tests" behind G1 — so this does not
block G0, but G1 must not be claimed for the Hadoop fold until the researcher rules
on it. The receipt lists it explicitly under criterion `G0-16`.

## P1.7 — Isolation and leakage audit (`LEAK-CS-001`)

Seventeen checks were **executed** per fold, not asserted. All three folds:
`PASS` — 15 pass, 0 fail, 0 blocked, 2 informational.

`L01` architecture overlap · `L02` exact raw duplicate overlap · `L03` normalised
duplicate overlap · `L04` source-record overlap between partitions · `L05`
session/trace unit split · `L06` chronological inversion within partition · `L07`
future information across a time boundary · `L08` burn-in/evaluation overlap · `L09`
target-label exposure on the adaptation path · `L10` normaliser fitted on target
evaluation · `L11` parser/template fitting · `L12` feature-fitting ownership · `L13`
fold manifest collision · `L14` source/target contamination · `L15` absolute or
private path leakage · `L16` guard segment unused.

`L02` and `L03` are reported as `INFORMATIONAL` because no threshold was declared in
advance, and an informational result is never counted as a pass. Their measured
value is worth stating: **zero** distinct target-evaluation messages, raw or
normalised, also occur in source training, on every fold. The architectures really
are disjoint in content.

## P1.8 — Freeze and G0

Receipt: `data/processed/protocol/G0-receipt.json`, binding 26 artifact digests
including the workbook itself, all four contract files, the registry, every stream
index and parquet, every fold, buffer and audit.

```text
G0 = PROTOCOL_READY   ·   19 of 19 criteria PASS, 0 FAIL, 0 PENDING_HUMAN
     Signed by the researcher on 2026-09-06.
```

Phase 1 required **four** researcher signatures, all supplied on 2026-09-06 and
recorded in [`../../configs/protocols/g0-signatures.yaml`](../../configs/protocols/g0-signatures.yaml):

| Task | Approves | Payload |
| --- | --- | --- |
| P1.1 | Scope memo, fold diagram, forbidden-field policy | `APPROVE P1.1 RESEARCH SCOPE — DOMAIN-ADAPTIVE-FUSION-001` |
| P1.6 | Buffer contract v1.1 and `BUFFER-REJECT-001` | `APPROVE ADAPT-INPUT-001 v1.1 TARGET BURN-IN CONTRACT AND BUFFER-REJECT-001` |
| P1.7 | Exception register `EXC-001..EXC-006` | `APPROVE LEAK-CS-001-EXCEPTIONS v1.0 (EXC-001..EXC-006)` |
| P1.8/G0 | The G0 receipt | `APPROVE G0 PROTOCOL READY — SeqLogAD Phase 1 (Bang_ke_hoach_SeqLogAD.xlsx)` |

The gate does not turn on a status flag. `G0-15` and `G0-19` compare each ledger
entry byte for byte against the payload its contract declares, and that comparison
is re-derived on every build. Verified by tampering: altering one character of the
G0 payload reverts the gate to `PROTOCOL_READY_PENDING_RESEARCHER_SIGNATURE` and
names the mismatched signature.

### What signing G0 did and did not do

Signing lifts exactly one prohibition — the workbook's *"Representation or target
adaptation training"* forbidden before G0 — which authorises **P2.1**. It does not
touch G1–G4, and it does not resolve the exceptions:

- `EXC-003` still blocks **G1 for the ARCH-HADOOP fold**. Approval acknowledged the
  rejection; it did not lift it, and the readiness minima were not relaxed.
- `EXC-001` and `EXC-002` remain open caveats for any P4 claim about HDFS as a
  target.
- Scientific results remain `NOT_RUN`. The workbook makes G0 a
researcher-owned gate and P1.8's definition of done is *"G0 được ký"* — signed. The
receipt cannot sign itself, so it reports the pending state rather than `PASSED`.

Signature payload:
`APPROVE G0 PROTOCOL READY — SeqLogAD Phase 1 (Bang_ke_hoach_SeqLogAD.xlsx)`

## Reproduction

```bash
python scripts/extract_excel_roadmap.py
python scripts/build_streams.py
python scripts/build_protocol.py
```

The first rebuilds the machine-readable plan from the workbook, the second rescans
the raw corpora (~11 minutes), the third derives every artifact from the stream
indices without touching raw logs.
