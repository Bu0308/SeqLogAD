# Data-collection gap matrix for v2

This matrix applies the supplied process-capture guide **after** the v2
research protocol was frozen. It changes observation and audit mechanics only;
it does not change datasets, experts, folds, metrics or scientific decisions.

| Guide requirement | Repo status before collection layer | Disposition | Priority |
|---|---|---|---|
| Immutable source/manifests/checksums | Implemented for HDFS/BGL | Reuse; bind records to existing fingerprints | Existing |
| Unified v2 architecture registry (≥3 sources, held-out targets) | Missing; only HDFS/BGL v1.1 dataset contracts | Create manifest record; dataset selection remains P1.2 | Immediate |
| Raw-message/event schema and missingness | v1.1 event schemas exist; no v2 registry record | Create versioned collection record; retain raw message reference, never copy raw logs | Immediate |
| Dataset snapshot and data-quality profile | Partial: manifests and parser/split summaries exist | Add snapshot/profile fields and artifact references | Immediate |
| Transform/split provenance | v1.1 split/parser identities exist; v2 LOAO folds missing | Record v1.1 foundation and require v2 fold records before model work | Immediate |
| Architecture/variant IDs | Missing | Implement append-only JSONL records | Immediate |
| Run bridge and technical/scientific status separation | Missing | Implement required run bridge record and validation | Immediate |
| Artifact manifest + availability | Partial exact hashes in existing artifacts; no per-run inventory | Implement hash/size/archive-status records | Immediate |
| Incident, ground-truth G0–G4, causal C0–C4 | Missing | Implement explicit records; correctness only G3/G4 and causal claims only C3/C4 | Immediate |
| Lineage edges and source badges | Missing | Implement direct-evidence edges; never label manifests as native evidence | Immediate |
| Protocol deviations / late backfill | Missing | Implement append-only deviation record with `recorded_late` | Immediate |
| Seal/access records | v1.1 TEST seal exists; no v2 target holdout collection seal | Reuse v1.1 seal evidence; add v2 seal/access record schema | Immediate |
| Toolchain and Projmem-native capture | Python lock exists; Projmem not installed/integrated | Record toolchain explicitly; native source remains `not_available` until supplied | Immediate |
| Capture coverage, random trace, leakage/privacy QA | Partial historical audits; no collection coverage | Implement validator/report schema; weekly execution remains operational | Immediate |
| Restricted/public sanitized handoff | Directory policy exists; no package builder | Prepare package-control schemas/templates; build only at handoff milestone | Future-prep |
| Aletheia adapter/export/graph | No integration | Keep as future read-only import boundary | Future-prep |
| Continuous filesystem/process monitoring | Not present and not required | Do not add; guide specifies explicit commands/records, not surveillance | Not needed |
| Scientific direction/model/experimental protocol changes | Must remain v2-owned | Collection layer cannot modify these | Forbidden |
