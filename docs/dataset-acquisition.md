# Dataset Acquisition Plan

## 1. Purpose

DATA-001 establishes a reproducible, inspectable boundary between external benchmark data and the project. It records where bytes came from, what files are required, how integrity is checked, and what remains outside the acquisition gate. Acquisition never parses or transforms scientific log content.

## 2. Core datasets

### HDFS

- **Purpose:** P0 block/session-oriented benchmark for sequence anomaly detection.
- **Canonical project source:** [LogPAI Loghub HDFS](https://github.com/logpai/loghub/tree/master/HDFS).
- **Archive record:** [Zenodo record 8196385](https://doi.org/10.5281/zenodo.8196385), file `HDFS_v1.zip`.
- **Expected required files:** `HDFS.log` and `preprocessed/anomaly_label.csv`; archive retention is optional after a verified, documented extraction.
- **Known label structure:** Loghub documents normal/anomalous labels at block-trace level and grouping by block ID. Detailed parsing and distribution analysis are deferred.
- **Acquisition:** archive-only safe downloader or manual download from the same Zenodo record; extraction is manual and must not overwrite files.
- **Local location:** `data/raw/hdfs/HDFS_v1/`.
- **Permission status:** `VERIFIED_LOGHUB_TERMS`; custom research/academic terms, citation/notice obligations and human review before redistribution.
- **Verification:** source MD5 for the archive, then SHA-256 per local file and a content fingerprint in the generated manifest.
- **Historical Day 2 state:** source contract was verified before raw acquisition. **Current state:** canonical archive, extracted bytes, and real manifest are verified; see Section 11 and the HDFS dataset card.

### BGL

- **Purpose:** P0 large system-log benchmark with line-level alert markers and a chronology different from HDFS.
- **Canonical project source:** [LogPAI Loghub BGL](https://github.com/logpai/loghub/tree/master/BGL).
- **Archive record:** [Zenodo record 8196385](https://doi.org/10.5281/zenodo.8196385), file `BGL.zip`.
- **Expected extracted file:** `BGL.log`; the first field is documented as `-` for non-alert records and another category for alerts.
- **Acquisition:** archive-only safe downloader or manual download from the same Zenodo record; extraction is manual and non-overwriting.
- **Local location:** `data/raw/bgl/BGL/`.
- **Permission status:** `VERIFIED_LOGHUB_TERMS`; custom research/academic terms, citation/notice obligations and human review before redistribution.
- **Verification:** source MD5 for the archive, then SHA-256 and a generated content fingerprint.
- **Historical Day 2 state:** source contract was verified before raw acquisition. **Current state:** canonical archive, extracted bytes, and real manifest are verified; see Section 11 and the BGL dataset card.

Dataset sizes and line counts reported by Loghub are source metadata only until local files are acquired and measured. They are not copied into a generated manifest as observed facts.

## 3. Integrity policy

- Downloads use `<archive>.part`, a timeout and atomic rename after checksum success.
- Existing archives are preserved by default and checked when a source checksum is available.
- Source MD5 is accepted solely because Zenodo publishes it for these archives.
- Every local manifest file identity uses SHA-256.
- Raw files are immutable after verification.
- Verification reports mismatches; it never repairs files or edits a manifest.

## 4. Manifest format

Manifest schema `1.0` records dataset ID/name/version, source provenance, repository-relative raw root, file metadata, basic aggregate statistics, integrity flags and dataset fingerprint. It contains no parsed events, templates, sequences, labels analysis or split metadata.

`schema_version` versions this JSON contract. `dataset_version` identifies the external dataset snapshot. A schema migration does not imply different dataset bytes.

## 5. Dataset fingerprint

For each included raw file, compute SHA-256, form `path:sha256`, sort the lines and hash the joined list with SHA-256. Therefore the identity is deterministic, independent of discovery order, content-sensitive and relative-path-sensitive. File modification time and machine-specific absolute paths are excluded.

## 6. Failure modes

| Failure | Safe behavior |
|---|---|
| Source unavailable/rate-limited | Stop with an error; retain no `.part`; use documented manual fallback |
| Interrupted transfer | Delete partial file; do not create final archive |
| Source checksum mismatch | Reject bytes and delete partial file |
| Destination already exists | Verify known checksum and preserve it unless `--force` is explicit |
| Missing required extracted file | Report `MISSING` or `PARTIAL`; refuse normal manifest build |
| Malformed config/manifest | Return a domain error and non-zero CLI status |
| Raw bytes changed after manifest | Verification fails on size/checksum/fingerprint; no automatic repair |
| License/permission unclear | Mark unverified/review-required; do not invent a license |

## 7. Offline/manual acquisition fallback

If automated acquisition is unsuitable, download the named archive directly from Zenodo record 8196385, verify the source-published checksum from the version-controlled config, place it under the configured raw directory, and extract without replacing existing files. Record acquisition time in the config only after acquisition actually occurs. All tests use synthetic fixtures and require no network.

## 8. Raw-data immutability

The raw directory is an input boundary. Parsing will read from it later but must write elsewhere. A changed source snapshot receives a new `dataset_version`/manifest; an old experiment continues to reference its original fingerprint.

## 9. Security and privacy

No secrets, private logs, access tokens or machine-specific absolute paths belong in configs or manifests. URLs must be reviewed before use. Archives are not executed. Private datasets remain outside Git and require separate privacy classification.

## 10. Historical Day 2 commands

Run from repository root:

```bash
python3 -m scripts.download_data --dataset all --dry-run
python3 -m scripts.verify_dataset --dataset hdfs
python3 -m scripts.verify_dataset --dataset bgl
python3 -m scripts.build_dataset_manifest --dataset hdfs
python3 -m pytest tests/unit/test_checksum.py tests/unit/test_dataset_validation.py tests/unit/test_dataset_manifest.py tests/unit/test_dataset_acquisition.py
python3 -m pytest tests/integration/test_dataset_manifest_workflow.py
```

The first command performs no network I/O. These commands remain useful for acquisition-tool regression tests; the current real-data status is recorded below.

## 11. Day 2.5 real-data registration

Day 2.5 found manually extracted datasets below wrapper directories. The version-controlled contracts were aligned to the observed extracted roots without moving or modifying raw bytes:

- HDFS: `data/raw/hdfs/HDFS_v1/`, with label file at `preprocessed/anomaly_label.csv`.
- BGL: `data/raw/bgl/BGL/`.

BGL's canonical archive was found outside the repository and passed exact source MD5, local SHA-256, ZIP safety/CRC and member-to-extracted-file SHA-256 comparison. Its manifest is `data/manifests/bgl_manifest.json`.

HDFS extracted files are present, hashed and reproducibly manifested at `data/manifests/hdfs_manifest.json`. The subsequently acquired canonical `HDFS_v1.zip` is 186,645,559 bytes, matches source MD5 `76a24b4d9a6164d543fb275f89773260`, and has local SHA-256 `04f919f2185821f23f045dca611a7586429bdabc601bd7b43f30005f8e289b01`. ZIP structure, full CRC and path-safety checks passed. Every archive file matches the existing extracted tree byte-for-byte; the raw tree was not re-extracted or modified.

Both HDFS and BGL now have complete source-archive-to-extracted-file integrity chains. Their manifests rebuild deterministically and pass independent repeated verification. This acceptance establishes immutable input identity only; it does not imply that parsing, event templates, sequences, splits, or models exist.

Acquisition timestamps remain unknown. Filesystem modification times are not promoted to acquisition provenance. License status remains custom Loghub research/academic terms with redistribution review required.
