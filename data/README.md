# Dataset Policy

This directory separates immutable source bytes from every derived artifact. HDFS and BGL are present locally for the current researcher, verified against version-controlled manifests, and intentionally excluded from Git.

## Directory layout

| Path | Purpose | Git policy | Current status |
|---|---|---|---|
| `raw/hdfs/` | Local HDFS source files | Contents ignored | Present and verified locally |
| `raw/bgl/` | Local BGL source files | Contents ignored | Present and verified locally |
| `manifests/` | Versioned JSON identity/integrity records | Tracked | HDFS/BGL verified manifests |
| `parsed/` | Future canonical events/templates | Generated contents ignored | Not generated |
| `processed/` | Derived splits, frozen parser states, and future sequences/features | Generated contents ignored | Real split/parser artifacts present and verified locally |
| `knowledge_base/` | Future downstream evidence corpus | Generated contents ignored | Not generated |

## Raw-data immutability

META-001 reserves data/processed/metadata/<dataset>/ for deterministic JSONL
raw metadata. Generated contents stay ignored; source, contracts, and tests
remain version-controlled. No full real metadata artifact has been generated.

Current derived artifacts:

- `processed/splits/<dataset>/`: deterministic structural split manifests,
  partition identities, exclusions, and hash-bound TEST seals. TEST membership is
  not exposed through this documentation.
- `processed/parsers/<dataset>/`: frozen Drain3 state, normal-pool summary,
  template registry, parser manifest, and exact manifest hash.

Both trees are reproducible and ignored by Git. Canonical event and sequence
artifacts have not been generated.

Accepted raw files are read-only scientific inputs. Parsing must write to `parsed/`; sequence, split, mutation, and feature pipelines must write to `processed/` or experiment-specific outputs. Never normalize, rewrite, rename, or corrupt the accepted raw tree.

## Integrity and identity

- Source-published MD5 validates canonical archive transfer.
- Streaming SHA-256 identifies each extracted scientific file.
- Dataset fingerprints hash sorted `relative_path:file_sha256` entries.
- Modification times and machine-specific absolute paths are excluded.
- HDFS and BGL manifests live in `data/manifests/` and are version-controlled.

Recheck local data without mutation:

```bash
python3 -m scripts.verify_dataset --dataset hdfs --json
python3 -m scripts.verify_dataset --dataset bgl --json
```

## Split and label safety for future work

- Assign chronological/group partitions before overlapping window creation.
- Fit parser/baselines and select thresholds without TEST; conditional/future components follow the same rule.
- Real HDFS/BGL labels may filter authorized normal pools and support validation/final evaluation, but never enter parser/model inputs or base loss.
- Conditional synthetic localization labels come only from deterministic mutations of authorized training-derived normal parents.

## Git, licensing, and privacy

- Never commit archives, raw logs, private logs, generated bulk data, credentials, or identifiers.
- Public availability is not redistribution permission; retain Loghub terms and citations.
- Commit configs, manifests, source, tests, documentation, and research plans.
