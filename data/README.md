# Dataset Policy

This directory separates immutable source bytes from every derived artifact. HDFS and BGL are the P0 benchmark datasets, but neither dataset is stored in this repository or present locally as of Day 2.

## Directory layout

| Path | Purpose | Git policy |
|---|---|---|
| `raw/hdfs/` | Locally acquired HDFS source files | Contents ignored; `.gitkeep` only |
| `raw/bgl/` | Locally acquired BGL source files | Contents ignored; `.gitkeep` only |
| `manifests/` | Versioned JSON identity and integrity records | Committed after real bytes are verified |
| `parsed/` | Future canonical events and templates | Generated data ignored |
| `processed/` | Future sequences, splits and features | Generated data ignored |
| `knowledge_base/` | Future normal sequences, incidents, docs and tests | Generated data ignored |

## Raw-data immutability

After an archive or extracted raw file passes verification, it is read-only input. Code must not normalize, rewrite, rename or silently replace it. Corrections produce a separately identified dataset snapshot and manifest. A `.part` file is never considered dataset content.

## Acquisition

Version-controlled contracts are in `configs/datasets/hdfs.yaml` and `configs/datasets/bgl.yaml`. The safe downloader stores the configured archive only; it never extracts or transforms it. See `docs/dataset-acquisition.md` for verified sources and the manual fallback.

## Manifest, checksums and identity

Each raw file is recorded with repository-relative path, byte size, SHA-256, role, extension, compression and encoding status. The dataset fingerprint is SHA-256 over the sorted `relative_path:file_sha256` list. Modification time is excluded because it can change without a content change. Source-published MD5 values are used only to validate downloaded archives; scientific identity uses SHA-256.

`schema_version` describes the manifest format. `dataset_version` identifies the source snapshot. They are independent and must not be conflated.

## Git, licensing and privacy

- Do not commit benchmark archives, raw logs, private logs or derived bulk data.
- Do not commit passwords, tokens, personal identifiers or proprietary host/service details.
- Loghub provides custom research/academic usage terms, not an assumed SPDX license. Review the source terms before redistribution and retain the required notice/citations with any dataset copy.
- Prefer acquisition instructions and checksums over copying public benchmark data into Git.

## Reproducing a dataset state

1. Review `docs/dataset-acquisition.md` and the relevant dataset card.
2. Dry-run the configured acquisition command.
3. Acquire the archive from the configured source and verify its published source checksum.
4. Extract manually without overwriting existing files and preserve the source notice.
5. Confirm required file presence.
6. Build a manifest and commit the manifest, config and documentation—not the raw bytes.
7. Re-run manifest verification before parsing or experiments.

Future parsing and sequence tasks may read `raw/`, but must write only to `parsed/`, `processed/` or experiment-specific output directories.
