# Dataset Card v0.1 — HDFS

- **Name:** HDFS Log Dataset v1 (`HDFS_v1`).
- **Purpose in project:** Core candidate benchmark for leakage-safe dataset-suitability, order-insensitive baseline, and sequence-added-value evaluation.
- **Source:** [LogPAI Loghub HDFS](https://github.com/logpai/loghub/tree/master/HDFS); canonical archive record [Zenodo 8196385](https://doi.org/10.5281/zenodo.8196385).
- **Reference:** registry entries [`S12`](../references/ACTIVE_REFERENCES.md) (Xu et al. (2009), SOSP) for the dataset itself, [`S1`](../references/ACTIVE_REFERENCES.md) for the Loghub collection and [`S16`](../references/ACTIVE_REFERENCES.md) for the Zenodo record, licence and published digests. Authoritative registry: [`../references/reference_registry.yaml`](../references/reference_registry.yaml).
- **Extracted root:** `data/raw/hdfs/HDFS_v1/`.
- **Required files:** `HDFS.log` and `preprocessed/anomaly_label.csv`, both locally present and non-empty.
- **Labels:** CSV at block-trace level with header `BlockId,Label`. Distribution analysis and joins are not part of Day 2.5.
- **Experiment role (workbook):** `ARCH-HDFS` is an active source architecture and a target-eligible LOAO fold. The KT-1/KT-2/KT-3 and Markov roles described previously belong to the retired v1.1 study.
- **Raw metadata grouping contract:** **IMPLEMENTED** — META-001 extracts
  normalized block IDs, duplicate/malformed conditions, earliest source-line
  chronology, and transitive connected components without labels or Drain3.
  The real structural split is generated and verified; block-sequence artifacts remain ungenerated.
- **Parser status:** PARSE-001 selected whole all-normal BASE components and froze a separate Drain3 state over 5,606,995 permitted source records. State identity and provenance are in [`../parser-fit-and-freeze.md`](../parser-fit-and-freeze.md); no canonical event corpus or anomaly metric exists.
- **Known limitations:** Prior work raises a material risk that count/event-presence properties explain labels and that dataset variants differ. Applicability to these exact verified bytes and the v1.1 chronological protocol is `TO_BE_TESTED`, not assumed. Source-specific block IDs and labeling rules may limit generalization; downstream canonical-event and sequence leakage checks remain future gates.
- **License/permission:** `VERIFIED_LOGHUB_TERMS`, custom research/academic usage conditions. Retain source notice/citations; redistribution still requires review.
- **Acquisition status:** `CANONICAL_ARCHIVE_VERIFIED`; the canonical `HDFS_v1.zip` was obtained from Zenodo and verified without re-extracting or modifying the existing raw tree. The acquisition timestamp remains unknown.
- **Source archive identity:** 186,645,559 bytes; source-published MD5 `76a24b4d9a6164d543fb275f89773260`; local SHA-256 `04f919f2185821f23f045dca611a7586429bdabc601bd7b43f30005f8e289b01`.
- **Archive safety:** ZIP structure and full CRC passed; no duplicate names, absolute/traversal paths, symlinks or nested archives were found.
- **Archive/extracted equivalence:** All seven archive files match the existing extracted tree byte-for-byte by streaming SHA-256; no archive member is missing and no extra extracted file exists.
- **Local integrity:** Six source-delivered scientific files, 1,828,041,800 bytes, SHA-256 recorded in `data/manifests/hdfs_manifest.json`.
- **Dataset fingerprint:** `0103c63b2847ba98b0b309a9e06eebb80ac8030e2f92d1f62320742537a34013`; deterministic rebuild and two manifest verifications passed.
- **Encoding/basic sanity:** `HDFS.log` and CSV files are ASCII/UTF-8 compatible; `HDFS.log` has 11,175,629 newline-terminated records. `HDFS.npz` is binary and correctly classified non-text.
- **Acceptance status:** dataset identity, real split/TEST seal, and PARSE-001 fit/freeze are `VERIFIED`. This does not imply canonical events, sequences, baselines, models, or scientific results exist.
