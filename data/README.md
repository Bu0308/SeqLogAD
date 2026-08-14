# Dataset Policy

This directory separates immutable source bytes from every derived artifact. HDFS and BGL are present locally for the current researcher, verified against version-controlled manifests, and intentionally excluded from Git.

## Directory layout

| Path | Purpose | Git policy | Current status |
|---|---|---|---|
| `raw/hdfs/` | Local HDFS source files | Contents ignored | Present and verified locally |
| `raw/bgl/` | Local BGL source files | Contents ignored | Present and verified locally |
| `manifests/` | Versioned JSON identity/integrity records | Tracked | HDFS/BGL verified manifests |
| `parsed/` | Future canonical events/templates | Generated contents ignored | Not generated |
| `processed/` | Future sequences/splits/features/evidence | Generated contents ignored | Not generated |
| `knowledge_base/` | Future downstream evidence corpus | Generated contents ignored | Not generated |

## Raw-data immutability

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
- Fit parser, experts, normal-reference index, calibrators, fusion, and thresholds without TEST.
- Real HDFS/BGL anomaly labels are evaluation-only unless an approved experiment explicitly states otherwise.
- Synthetic localization/fusion labels come only from training-derived mutations.

## Git, licensing, and privacy

- Never commit archives, raw logs, private logs, generated bulk data, credentials, or identifiers.
- Public availability is not redistribution permission; retain Loghub terms and citations.
- Commit configs, manifests, source, tests, documentation, and research plans.
