# SPLIT-001 — Citations and Method Provenance

This note records the verified sources reused for SPLIT-001. The implementation
does not add a scientific claim or a SeqLogAD model result. Full search details
and source caveats remain in
[`PROTOCOL-SPLIT-CLARIFY-001-citations.md`](PROTOCOL-SPLIT-CLARIFY-001-citations.md).

Bibliographic identities and publisher/official-proceedings records were
rechecked on 2026-08-23 before this task was closed.

## Retained external sources

1. Musaad Alzahrani, “Investigating the Impact of Log-Sequence Embeddings on
   Anomaly Detection: A Systematic Study,” *Information* 17(3), 2026.
   DOI: [10.3390/info17030228](https://doi.org/10.3390/info17030228).
   Peer-reviewed. Supports HDFS block/session grouping and session atomicity;
   supports chronological BGL raw split before non-overlapping fixed-entry
   windows and explicit incomplete-tail exclusion. It does not support
   SeqLogAD's exact ratios, connected-component purge, hashing, or seal.

2. Max Landauer, Florian Skopik, and Markus Wurzenberger, “A Critical Review of
   Common Log Data Sets Used for Evaluation of Sequence-Based Anomaly Detection
   Techniques,” *Proceedings of the ACM on Software Engineering* (FSE), 2024.
   DOI: [10.1145/3660768](https://doi.org/10.1145/3660768).
   Peer-reviewed. Supports explicit dataset construction/provenance and warns
   that preprocessing/grouping can dominate conclusions. It does not prescribe
   SeqLogAD's split algorithm.

3. Yongzheng Xie, Hongyu Zhang, and Muhammad Ali Babar, “LogSD: Detecting
   Anomalies from System Logs through Self-Supervised Learning and
   Frequency-Based Masking,” *Proceedings of the ACM on Software Engineering*
   (FSE), 2024. DOI:
   [10.1145/3660800](https://doi.org/10.1145/3660800).
   Peer-reviewed. Corroborates HDFS block grouping, chronological BGL
   allocation, and fixed-entry windows, while using different ratios and
   preprocessing.

4. Ondřej Sedláček, Martin Žádník, and Václav Bartoš, “Anomaly Detection in Log
   Data: A Comparative Study,” CNSM 2025. DOI:
   [10.23919/CNSM67658.2025.11297503](https://doi.org/10.23919/CNSM67658.2025.11297503).
   Peer-reviewed. Supports treating chronological versus shuffled evaluation
   and grouping as explicit protocol variables; it does not define SeqLogAD's
   exact five-way split.

## Rule classification

| Rule | Classification | Source |
|---|---|---|
| HDFS block/session grouping and atomicity | `LITERATURE_SUPPORTED` | Alzahrani 2026; Xie et al. 2024 |
| BGL chronological allocation | `LITERATURE_SUPPORTED` | Alzahrani 2026; Xie et al. 2024; Sedláček et al. 2025 |
| BGL split before windows | `LITERATURE_SUPPORTED` | Alzahrani 2026 |
| BGL fixed non-overlapping windows | `LITERATURE_SUPPORTED` | Alzahrani 2026 |
| Label-independent chronology-first allocation | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | Landauer et al. 2024; chronological sources above |
| BGL 100-line parent and residual exclusion | `LITERATURE_INFORMED_SEQLOGAD_DECISION` | Alzahrani 2026; Xie et al. 2024 |
| `60/10/10/10/10` and cumulative floor | `SEQLOGAD_PROTOCOL_DECISION` | No external standard claimed |
| HDFS connected-component purge | `SEQLOGAD_PROTOCOL_DECISION` | No external standard claimed |
| Layered hashes and assignment IDs | `SEQLOGAD_PROTOCOL_DECISION` | Engineering reproducibility rule |
| Physical TEST seal and human unlock workflow | `SEQLOGAD_PROTOCOL_DECISION` | Project governance rule |

External methods remain external evidence. The real structural counts and
hashes in SeqLogAD are repository artifacts, not literature results. No paper
is cited as evidence that SeqLogAD's exact split is optimal or novel.
