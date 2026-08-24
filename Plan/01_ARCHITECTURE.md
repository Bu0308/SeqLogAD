# 01 — Architecture v1.1

Status legend: `IMPLEMENTED`, `PLANNED`, `CONDITIONAL`, `FUTURE`.

## Gated component map

```text
Verified Raw HDFS/BGL + Manifests                     IMPLEMENTED
        ↓
Minimal Metadata / Group-Key Extraction               IMPLEMENTED
        ↓
Exact Split Semantics / Identity Contract             FROZEN / TESTED
        ↓
Raw Chronological Five-Way Split + TEST Guard         IMPLEMENTED / VERIFIED
        ↓
Normal BASE_TRAIN Pool                                IMPLEMENTED / VERIFIED
        ↓
Drain3 Fit → Freeze → Read-Only Transform             IMPLEMENTED / VERIFIED
        ↓
HDFS Purge Representativeness Audit                   IMPLEMENTED / CONCERN
        ↓
PURGE-DECISION-001 — Option B                        FROZEN / HUMAN APPROVED
        ↓
Canonical Events / Partition-Contained Sequences      SCHEMAS IMPLEMENTED;
                                                      EVENTS AUTHORIZED NEXT
        ↓
┌──────────────── ORDER-INSENSITIVE CONTROLS ────────────────┐
│ unseen event · length · count/count-vector          MUST  │
│ Isolation Forest                                   MUST  │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
                 Markov / N-gram                     MUST
                           ↓
      Sequence Destruction (same counts/length/label) MUST
                           ↓
                 Human Scientific Gate
                   ┌───────┴────────┐
        insufficient signal       meaningful signal
                   ↓                 ↓
         report/reframe       Transformer             CONDITIONAL
                              Localization KT-4/5     CONDITIONAL
                              F0/F1 after COMP gate   CONDITIONAL
                                      ↓
                         One Locked Human TEST        PLANNED

Retrieval/RAG/Agent/API/UI/Elasticsearch              FUTURE
```

## Data boundaries

| Artifact | Responsibility | Fit/access boundary |
|---|---|---|
| Raw manifest | Exact accepted bytes | Implemented; immutable |
| Raw metadata/group map | Partition key without fitted parser | Implemented; labels/parser state excluded |
| Split-semantics addendum | Exact allocation, purge, residual, reconciliation, and identity rules | Frozen/tested; instantiated by SPLIT-001 |
| Split manifest | Stable partition/purge/hash identity | Implemented/verified before parser fit; derived bulk files ignored by Git |
| Parser state | Drain3 templates and frozen event mapping | Normal `BASE_TRAIN` only |
| Purge audit | Aggregate `PURGED` versus `RETAINED` data-validity result | Implemented without partition membership; concern retained; stop gate resolved by PURGE-DECISION-001 |
| Purge decision | Primary/secondary disposition of the HDFS boundary concern | Option B frozen: primary unchanged; secondary sensitivity pre-registered / `NOT_RUN` |
| Canonical events | Parsed fields with label isolation | Read-only transform per partition |
| Event sequences | HDFS blocks/BGL parents | Never cross partition boundary |
| Destruction manifest | Deterministic order permutation | Preserve multiset/count/length/label; no raw mutation |
| Predictions/results | Method/version/config/seed identity | Validation-only selection; TEST once |

## Dataset construction

- HDFS: block/session connected components are atomic; boundary-spanning components are purged.
- BGL: raw chronology is partitioned first; non-overlapping 100-event parents are then formed inside partitions.
- HDFS preprocessed templates/traces are excluded from scientific input.

## Method layer

The minimal sequential comparator is Markov/N-gram. A Transformer is not part of the fixed architecture and opens only if the sequence gate identifies a residual long-range question. LSTM and normal-reference retrieval are removed from core.

## Localization contract

Existing schema contracts keep separate token, gap, and transition coordinates. This representation is implemented, but localization research is conditional and has no generated artifact/result.

## Fusion boundary

No trainable fusion is in v1.1 core. If at least two eligible experts later demonstrate score/error complementarity and oracle gain, a new decision may open F0 strongest-single and F1 simple mean. F2–F8 require a protocol amendment.

## Downstream boundary

Future RAG/Agent can only consume frozen evidence, cannot override detector outputs, and cannot access hidden TEST labels. It is not part of the current anomaly-detection contribution.

## Implemented flow today

```text
dataset config → acquisition/integrity checks → deterministic manifest
→ independent verification

schema fixtures → strict validation → deterministic identity/serialization

raw HDFS/BGL fixtures → label/parser-independent META-001 group/chronology metadata

synthetic structural fixtures → exact split-contract arithmetic/identity tests

verified raw bytes + META-001 → deterministic real split artifacts
→ hash-bound TEST seals (`SEALED / NEVER_OPENED`)

ordinary BASE membership → scoped normal-label selection
→ deterministic normal-pool identity → Drain3 fit/freeze
→ independent restore → immutable `match`-only transform

public purge exclusions + reconstructed META component universe
→ aggregate PURGED/RETAINED audit → human stop gate

human-approved Option B → frozen primary unchanged
→ secondary purge sensitivity pre-registered / not run
```

Frozen parser states and template registries now exist as ignored reproducible
derived artifacts. PURGE-AUDIT-001 remains a recorded concern;
PURGE-DECISION-001 keeps the primary split unchanged and authorizes
`CANONICAL-EVENT-001` next. No canonical event corpus, scientific event
sequence, baseline, model, sensitivity run, TEST unlock, or final TEST path
currently executes.
