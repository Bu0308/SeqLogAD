# Scripts

Implemented dataset-integrity command wrappers:

- `python3 -m scripts.download_data --dataset hdfs --dry-run`: resolve and display archive destination without network access.
- `python3 -m scripts.verify_dataset --dataset hdfs`: report required-file presence and verify an existing manifest.
- `python3 -m scripts.build_dataset_manifest --dataset hdfs`: build a deterministic manifest only when required files exist.

META-001 bounded validation is available without writing an artifact:

    python3 -m scripts.extract_raw_metadata --dataset hdfs --dry-run --max-lines 1000

The metadata wrapper has no split, TEST, parser, window, model, or experiment
option. Training, parsing, indexing and experiment scripts remain absent.
