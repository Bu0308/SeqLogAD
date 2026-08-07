# Scripts

Day 2 command wrappers:

- `python3 -m scripts.download_data --dataset hdfs --dry-run`: resolve and display archive destination without network access.
- `python3 -m scripts.verify_dataset --dataset hdfs`: report required-file presence and verify an existing manifest.
- `python3 -m scripts.build_dataset_manifest --dataset hdfs`: build a deterministic manifest only when required files exist.

The downloader does not extract archives. The manifest verifier does not repair data. All commands return non-zero for expected invalid/incomplete states. Training, parsing, indexing and experiment scripts are intentionally absent.
