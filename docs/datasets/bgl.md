# Dataset Card v0.1 — BGL

- **Name:** Blue Gene/L System Log (`BGL`).
- **Purpose in project:** P0 second benchmark for chronology-aware detector evaluation and cross-dataset robustness.
- **Source:** [LogPAI Loghub BGL](https://github.com/logpai/loghub/tree/master/BGL); canonical archive record [Zenodo 8196385](https://doi.org/10.5281/zenodo.8196385).
- **Reference:** Loghub repository/readme and its linked BGL/Loghub publications; exact literature citations remain part of LIT-001.
- **Source archive:** `BGL.zip`, 57,489,019 bytes; canonical MD5 `4452953c470f2d95fcb32d5f6e733f7a` matched exactly; local SHA-256 `d67fd82a711aea0157a9b83175892c6ee60e384a2ddf5bc51f39118453816da8`.
- **Archive safety:** Valid ZIP with two members, no duplicate names, traversal, absolute paths, symlinks or nested archives; full ZIP CRC test passed.
- **Extracted root:** `data/raw/bgl/BGL/`. Both extracted members were independently SHA-256 compared with archive members and matched.
- **Required file:** `BGL.log`, locally present and non-empty.
- **Labels:** Inline first field; Loghub documents `-` as non-alert and other values as alert categories. No distribution analysis is part of Day 2.5.
- **Experiment role:** Second P0 dataset for chronology-aware heterogeneous-expert, complementarity, localization, and fusion evaluation; it is not assumed to share HDFS grouping semantics.
- **Sequence grouping assumption:** **PRELIMINARY** — future time/sliding windows, potentially constrained by node/component fields. The SEQ task must validate this.
- **Known limitations:** Line-level alerts are not automatically equivalent to behavioral sequence anomalies; sequence boundaries are not explicit.
- **License/permission:** `VERIFIED_LOGHUB_TERMS`, custom research/academic usage conditions. Retain source notice/citations; redistribution still requires review.
- **Acquisition status:** `ARCHIVE_AND_EXTRACTION_VERIFIED`; acquisition timestamp remains unknown because filesystem time is not treated as acquisition truth.
- **Local integrity:** `BGL.log`, 743,185,031 bytes, SHA-256 `666130b15ef44eb32fd02bd053e6c6e007c37696b5e7e8b9d8e45b729876a5d2`.
- **Dataset fingerprint:** `c9ee7a8db13d37c88f896e305ed12dc7a66b586cdae4e388db4949f78afbe861`; deterministic rebuild and two manifest verifications passed.
- **Encoding/basic sanity:** ASCII/UTF-8 compatible, 4,747,963 newline-terminated records.
- **Acceptance status:** `VERIFIED` for the dataset identity gate. This does not imply parser, sequence, split, or model readiness.
