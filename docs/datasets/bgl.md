# Dataset Card v0.1 — BGL

- **Name:** Blue Gene/L System Log (`BGL`).
- **Purpose in project:** Core candidate benchmark for chronology-aware dataset-suitability, trivial-baseline ceiling, and sequence-added-value evaluation.
- **Source:** [LogPAI Loghub BGL](https://github.com/logpai/loghub/tree/master/BGL); canonical archive record [Zenodo 8196385](https://doi.org/10.5281/zenodo.8196385).
- **Reference:** Loghub repository/readme and its linked BGL/Loghub publications; dataset-suitability evidence is mapped in [`../literature/prior-art-matrix-v1.1.md`](../literature/prior-art-matrix-v1.1.md) and [`../references/LIT-001-citations.md`](../references/LIT-001-citations.md).
- **Source archive:** `BGL.zip`, 57,489,019 bytes; canonical MD5 `4452953c470f2d95fcb32d5f6e733f7a` matched exactly; local SHA-256 `d67fd82a711aea0157a9b83175892c6ee60e384a2ddf5bc51f39118453816da8`.
- **Archive safety:** Valid ZIP with two members, no duplicate names, traversal, absolute paths, symlinks or nested archives; full ZIP CRC test passed.
- **Extracted root:** `data/raw/bgl/BGL/`. Both extracted members were independently SHA-256 compared with archive members and matched.
- **Required file:** `BGL.log`, locally present and non-empty.
- **Labels:** Inline first field; Loghub documents `-` as non-alert and other values as alert categories. No distribution analysis is part of Day 2.5.
- **Experiment role:** KT-1 trivial/strong baselines, Markov/N-gram, and KT-3 order-destruction analysis on non-overlapping chronological parent windows. It is not assumed to share HDFS grouping semantics; Transformer/localization are conditional and fusion is not core.
- **Raw chronology contract:** **IMPLEMENTED** — META-001 preserves zero-based
  source-line rank, parses the detailed timestamp for structural audit, keeps
  malformed/regressing observations explicit, and ignores the inline label
  value. The real structural split and per-partition 100-event parent windows
  are generated and verified; canonical event sequences remain ungenerated.
- **Known limitations:** Line-level alerts are not automatically behavioral sequence anomalies and sequence boundaries are not explicit. Prior work raises trivial/unseen-event ceiling risk, but the exact outcome under these verified bytes and the v1.1 chronological 100-event protocol is `TO_BE_TESTED`.
- **Parser status:** PARSE-001 selected 2,616,821 normal BASE events inside complete parent windows and froze a separate Drain3 state. A valid no-Content source edge case maps to the pre-fit sentinel `SEQLOGAD_EMPTY_CONTENT`. State identity and provenance are in [`../parser-fit-and-freeze.md`](../parser-fit-and-freeze.md); no canonical event corpus or anomaly metric exists.
- **License/permission:** `VERIFIED_LOGHUB_TERMS`, custom research/academic usage conditions. Retain source notice/citations; redistribution still requires review.
- **Acquisition status:** `ARCHIVE_AND_EXTRACTION_VERIFIED`; acquisition timestamp remains unknown because filesystem time is not treated as acquisition truth.
- **Local integrity:** `BGL.log`, 743,185,031 bytes, SHA-256 `666130b15ef44eb32fd02bd053e6c6e007c37696b5e7e8b9d8e45b729876a5d2`.
- **Dataset fingerprint:** `c9ee7a8db13d37c88f896e305ed12dc7a66b586cdae4e388db4949f78afbe861`; deterministic rebuild and two manifest verifications passed.
- **Encoding/basic sanity:** ASCII/UTF-8 compatible, 4,747,963 newline-terminated records.
- **Acceptance status:** dataset identity, real split/TEST seal, and PARSE-001 fit/freeze are `VERIFIED`. This does not imply canonical events, sequences, baselines, models, or scientific results exist.
