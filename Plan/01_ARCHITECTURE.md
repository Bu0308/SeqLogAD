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
Raw Chronological Five-Way Split + TEST Guard         PLANNED / MUST
        ↓
Normal BASE_TRAIN Pool                                PLANNED / MUST
        ↓
Drain3 Fit → Freeze → Read-Only Transform             PLANNED / MUST
        ↓
Canonical Events / Partition-Contained Sequences      SCHEMAS IMPLEMENTED;
                                                      ARTIFACTS PLANNED
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
| Split-semantics addendum | Exact allocation, purge, residual, reconciliation, and identity rules | Frozen/tested on synthetic fixtures; creates no real split |
| Split manifest | Stable partition/purge/hash identity | Created before parser fit/windows |
| Parser state | Drain3 templates and frozen event mapping | Normal `BASE_TRAIN` only |
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
```

No real scientific split, TEST partition, parser output, sequence, baseline, or
model path currently executes.
