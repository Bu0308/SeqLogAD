# META-001 — Source and Method Provenance

| Field | Value |
|---|---|
| Task | META-001 |
| Date | 2026-08-22 |
| Status | COMPLETE |
| Scientific results | NOT_RUN |
| Scientific TEST accessed | false |

## Repository contracts actually used

1. docs/research-protocol-v1.1.md and the machine protocol — active ordering,
   atomicity, label, parser, split-before-window, and TEST boundaries.
2. The EFFECT-001 documents — future HDFS block/session and BGL 100-event
   evaluation units; no metric was executed here.
3. Canonical schema docs and SCHEMA-COMPAT-001 provenance — record identity and
   separation of raw metadata, parsed events, partitions, and sequences.
4. HDFS/BGL configs, dataset cards, and manifests — exact paths, file roles,
   dataset fingerprints, and source-file hashes.

## External sources retained for dataset context

### META-CITE-001 — Loghub source and archive identity

- Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, Michael R. Lyu.
  *Loghub: A Large Collection of System Log Datasets for AI-Driven Log
  Analytics*. ISSRE 2023.
- DOI: https://doi.org/10.1109/ISSRE59848.2023.00071
- Canonical archive: https://doi.org/10.5281/zenodo.8196385
- Use: dataset/source context only. Local identity remains manifest-defined.

### META-CITE-002 — HDFS block/execution context

- Wei Xu, Ling Huang, Armando Fox, David Patterson, Michael I. Jordan.
  *Detecting Large-Scale System Problems by Mining Console Logs*. SOSP 2009.
- DOI: https://doi.org/10.1145/1629575.1629587
- Use: historical HDFS execution/block context only.
- Boundary: paper artifacts are not assumed byte-identical to accepted Loghub
  bytes and no reported performance is transferred.

### META-CITE-003 — BGL operational origin

- Adam Oliner, Jon Stearley. *What Supercomputers Say: A Study of Five System
  Logs*. DSN 2007.
- DOI: https://doi.org/10.1109/DSN.2007.103
- Use: BGL line-oriented operational context only.
- Boundary: this does not define SeqLogAD partition/window protocol, and no
  external metric is treated as a SeqLogAD result.

## Implementation provenance

The block matcher, two-pass streaming extractor, deterministic component hash,
source-order BGL rank, non-overwrite JSONL writer, and invariants are SeqLogAD
engineering decisions implementing frozen contracts. No external extraction
code was copied. Union-find/disjoint-set is standard infrastructure, not a
research contribution or novelty claim.

## Scope assurance

No raw byte or manifest was modified. No anomaly label file was opened by the
extractor. No split, TEST identity, Drain3 state, template, event, sequence,
window, baseline, model, score, metric, or scientific result was generated.
