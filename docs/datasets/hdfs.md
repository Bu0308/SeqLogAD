# Dataset Card v0.1 — HDFS

- **Name:** HDFS Log Dataset v1 (`HDFS_v1`).
- **Purpose in project:** P0 benchmark for leakage-safe, sequence-aware anomaly detection and retrieval evaluation.
- **Source:** [LogPAI Loghub HDFS](https://github.com/logpai/loghub/tree/master/HDFS); canonical archive record [Zenodo 8196385](https://doi.org/10.5281/zenodo.8196385).
- **Reference:** Loghub repository/readme and its linked HDFS/Loghub publications; exact literature citations remain part of LIT-001.
- **Extracted root:** `data/raw/hdfs/HDFS_v1/`.
- **Required files:** `HDFS.log` and `preprocessed/anomaly_label.csv`, both locally present and non-empty.
- **Labels:** CSV at block-trace level with header `BlockId,Label`. Distribution analysis and joins are not part of Day 2.5.
- **Experiment role:** Primary dataset for future parser, block/session sequence construction, statistical baselines and LSTM comparison.
- **Sequence grouping assumption:** **PRELIMINARY** — group events by HDFS block identifier. A later SEQ task must formalize boundary, ordering and malformed-ID handling.
- **Known limitations:** Private-cloud benchmark and handcrafted labeling rules; source-specific block IDs may limit generalization. Parser/split leakage remains a later audit concern.
- **License/permission:** `VERIFIED_LOGHUB_TERMS`, custom research/academic usage conditions. Retain source notice/citations; redistribution still requires review.
- **Acquisition status:** `EXTRACTED_PRESENT`; canonical `HDFS_v1.zip` was not discoverable during Day 2.5, so source-archive acceptance is incomplete and acquisition timestamp remains unknown.
- **Local integrity:** Six source-delivered scientific files, 1,828,041,800 bytes, SHA-256 recorded in `data/manifests/hdfs_manifest.json`.
- **Dataset fingerprint:** `0103c63b2847ba98b0b309a9e06eebb80ac8030e2f92d1f62320742537a34013`; deterministic rebuild and two manifest verifications passed.
- **Encoding/basic sanity:** `HDFS.log` and CSV files are ASCII/UTF-8 compatible; `HDFS.log` has 11,175,629 newline-terminated records. `HDFS.npz` is binary and correctly classified non-text.
- **Acceptance status:** `FAIL_SOURCE_ARCHIVE_GATE` until the canonical archive is found/reacquired and its MD5, ZIP safety and extracted-member equivalence are verified.
- **TODO:** Reacquire only from canonical Zenodo if necessary; expected MD5 is `76a24b4d9a6164d543fb275f89773260`. Do not parse before the archive gate is closed.
