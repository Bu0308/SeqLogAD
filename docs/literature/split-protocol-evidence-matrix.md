# PROTOCOL-SPLIT-CLARIFY-001 — Literature Evidence Matrix

**Search date:** 2026-08-22

**Search cutoff:** 2026-08-22

**Empirical SeqLogAD status:** `NOT_RUN`

**Full source record:**
[`../references/PROTOCOL-SPLIT-CLARIFY-001-citations.md`](../references/PROTOCOL-SPLIT-CLARIFY-001-citations.md)

This targeted review answers only the split/grouping questions needed to
unblock `SPLIT-001`. External protocols are not copied wholesale. A source can
support one rule and conflict with another because dataset variants,
supervision, preprocessing, and evaluation goals differ.

## 1. Evidence classification

| SeqLogAD rule | Classification | Supporting source(s) | Exact support | Caveat |
|---|---|---|---|---|
| HDFS block/session grouping | `LITERATURE_SUPPORTED` | S1, S3, S6 | HDFS messages are grouped by `block_id`/session | Does not establish SeqLogAD connected components |
| HDFS session atomicity | `LITERATURE_SUPPORTED` | S1 | HDFS partitioning is performed at session level and no session is split | S1 uses label-stratified allocation, which SeqLogAD rejects |
| HDFS chronology-first, label-independent allocation | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | S2, S4, S5; conflicts S1/S3 | Recent work supports chronological/sequential evaluation to reduce future leakage | No retained source specifies SeqLogAD's exact eligible-line algorithm for HDFS |
| HDFS META-001 connected component | `SEQLOGAD_PROTOCOL_DECISION` | None required | Handles transitive block co-occurrence without splitting a shared raw line | Not claimed as a standard benchmark method |
| HDFS whole-component `PURGED_BOUNDARY` | `SEQLOGAD_PROTOCOL_DECISION` | None required | Deterministic way to preserve atomicity when a component occupies multiple nominal ranges | Literature supports atomicity, not this purge algorithm |
| HDFS explicit `NO_BLOCK_ID` / malformed / decode exclusions | `SEQLOGAD_PROTOCOL_DECISION` | None required | Prevents silent loss and fake session identities | Accepted HDFS bytes currently have no observed no-block line; implementation must still handle it |
| BGL source chronology | `LITERATURE_SUPPORTED` | S1, S3, S4, S5 | Chronological/sequential allocation is used and motivated by leakage/real-world ordering | S5 also evaluates shuffled folds, showing protocol sensitivity |
| BGL raw split before windows | `LITERATURE_SUPPORTED` | S1 | Raw messages are chronologically partitioned before 100-message windows to prevent boundary crossing/future leakage | S1 uses three partitions, not SeqLogAD's five |
| BGL fixed-entry windows | `LITERATURE_SUPPORTED` | S1, S3 | Both use fixed-entry grouping for BGL | Other valid grouping strategies exist (S6) |
| BGL non-overlapping windows | `LITERATURE_SUPPORTED` | S1; informed by S3 | S1 explicitly uses fixed non-overlapping windows and stride equal to length | Non-overlap is not universally used |
| BGL 100-event parents | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | S1, S3 | 100 is a directly evaluated, established choice | S1 tests 50/100/200; S3 tests 20/60/100; no universal optimum |
| Incomplete-window exclusion | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | S1 | S1 discards incomplete trailing fixed windows | Exact per-partition residual accounting across five partitions is SeqLogAD-specific; S6 retains short groups |
| `60/10/10/10/10` partition family | `SEQLOGAD_PROTOCOL_DECISION` | None required | Separates base, expert validation, reserved fusion development, and final TEST | Recent sources use 60/20/20, 80/20, 60/5/30/5, or cross-validation |
| Cumulative-floor boundaries | `SEQLOGAD_PROTOCOL_DECISION` | None required | One pre-registered deterministic rounding algorithm | No retained source mandates it |
| Label-independent assignment | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | S2, S4; conflicts S1 | Leakage-aware evaluation motivates outcome-independent partitioning | Some studies stratify HDFS or filter/balance using labels; SeqLogAD intentionally does not |
| No post-hoc ratio repair | `SEQLOGAD_PROTOCOL_DECISION` | None required | Prevents composition-driven changes after atomicity purge | Not a literature-universal algorithm |
| Canonical split payload and layered hashes | `SEQLOGAD_PROTOCOL_DECISION` | None required | Resolves circular identity and separates scientific identity from file integrity | Engineering reproducibility contract, not a scientific novelty claim |
| Physical TEST sealing | `SEQLOGAD_PROTOCOL_DECISION` | None required | Enforces the already frozen human-only final-TEST policy | No retained log-anomaly paper establishes this exact mechanism |

No major rule is classified `INSUFFICIENT_EVIDENCE`: rules without direct
literature backing are explicitly owned as pre-registered project decisions
rather than disguised as external claims.

## 2. Required literature questions

### Q-LIT-1 — HDFS grouping

- **Supported:** HDFS block/session grouping remains common in 2024–2026 work.
- **Supported:** at least one recent peer-reviewed study partitions at session
  level and explicitly avoids splitting sessions.
- **Conflict:** S1 uses label-stratified 60/20/20 session allocation; S3 uses a
  random 80/20 sequence split; S4 uses sequential ordering. There is no
  universal HDFS allocation rule.
- **SeqLogAD decision:** chronology over eligible raw-line ranks, followed by
  whole connected-component assignment/purge, without labels.

### Q-LIT-2 — BGL chronology

- **Supported:** S1 directly splits raw BGL messages chronologically before
  window construction and states that this prevents boundary crossing and
  future-message leakage.
- **Corroborated:** S3 uses initial 80% messages for training and later 20% for
  testing; S4 uses sequential ordering for dataset sequences.
- **Conflict/sensitivity:** S5 evaluates both shuffled and time-contiguous
  sequential folds and reports materially different behavior. This confirms
  that exact allocation remains an experimental protocol choice.

### Q-LIT-3 — BGL windows

- Fixed-entry grouping and 100-message windows are established choices in S1
  and S3.
- S1 explicitly uses non-overlapping windows and discards an incomplete tail.
- Size 100 is not universal: S1 includes 50 and 200 sensitivity conditions;
  S3 includes 20, 60, and 100; S6 groups BGL by node rather than by 100-line
  windows and retains short groups for other datasets.
- Therefore 100 and the five-partition residual contract are frozen SeqLogAD
  instantiations, not optimality claims.

### Q-LIT-4 — Ratios

Retained recent protocols include 60/20/20 (S1), 80/20 (S3), 60/5/30/5 (S4),
and shuffled 10-fold cross-validation (S5). Literature supports separating
development and evaluation data, but it does not establish SeqLogAD's
60/10/10/10/10 family or cumulative-floor rounding as a universal standard.

### Q-LIT-5 — Leakage control

- S1 provides the strongest direct support for BGL raw split-before-window and
  no cross-boundary windows.
- S3 and S4 explicitly motivate chronological/sequential allocation as leakage
  control or a closer real-world simulation.
- HDFS session non-crossing is directly supported by S1, but its label-based
  stratification is incompatible with SeqLogAD.
- The broader dataset critique S2 supports careful sequence-dataset and
  protocol selection; it does not prescribe SeqLogAD's exact boundaries.

## 3. Source conflict matrix

| Topic | Source | Year | Method observed | Compatibility with SeqLogAD |
|---|---|---:|---|---|
| HDFS grouping | S1 — Alzahrani | 2026 | one sequence per `block_id` session | Compatible grouping |
| HDFS split | S1 — Alzahrani | 2026 | 60/20/20 at session level, label-stratified | Atomicity compatible; label stratification and ratios incompatible |
| HDFS grouping/split | S3 — LogSD | 2024 | BlockId sessions; random 80/20 sequence allocation | Grouping compatible; random split incompatible |
| HDFS split | S4 — ContraLog | 2026 | sequential 60/5/30/5; oldest train/newest test; label filtering/balancing | Chronology informative; ratios/label operations incompatible |
| BGL split/window | S1 — Alzahrani | 2026 | raw chronological 60/20/20, then non-overlapping 100-message windows; incomplete tail discarded | Principle directly compatible; exact ratios differ |
| BGL split/window | S3 — LogSD | 2024 | initial 80% vs later 20%; fixed 20/60/100-entry groups after removing consecutive duplicates | Chronology/window family informative; ratios and preprocessing differ |
| HDFS/BGL evaluation | S5 — Sedláček et al. | 2025 | shuffled evaluation plus separate time-contiguous sequential folds | Supports explicit chronology sensitivity; also shows random protocols remain in use |
| BGL grouping | S6 — Logs2Graphs | 2026 | BGL grouped by node; other streams use per-user 100-consecutive groups and retain short groups | Demonstrates grouping/residual alternatives; not copied |
| Dataset suitability | S2 — Landauer et al. | 2024 | critical sequence-dataset analysis and simple baselines | Supports cautious claims and negative controls, not exact allocation |

## 4. Decision rationale after conflicts

SeqLogAD chooses chronology-first allocation because its core RQ asks for
sequence value under leakage-controlled temporal evaluation, not because every
paper uses chronology. It chooses label independence because partition identity
must be frozen before outcome inspection. HDFS atomic connected components
protect raw-line/session integrity; purging avoids arbitrary boundary moves.
BGL is split before windows so no parent can bridge scientific partitions.

These choices trade exact target proportions and maximum sample retention for
pre-registration, temporal integrity, and falsifiability. Target/realized ratios
and exclusions must therefore be reported separately.

## 5. Source freshness

- Newest directly relevant source found: **2026** (S1, S4, S6).
- Newest peer-reviewed directly relevant source: **2026** (S1 and S6).
- Newest HDFS-specific/method-relevant source retained: **2026** (S1; S6
  corroborates current block grouping, while S4 is a preprint).
- Newest BGL-specific/method-relevant source retained: **2026** (S1 directly
  specifies raw chronological split-before-window; S6 documents a conflicting
  grouping alternative).

Recency did not override compatibility: the 2024 LogSD paper is retained for
corroboration, and the 2024 critical review remains methodologically important
for dataset-suitability and claim restraint.
