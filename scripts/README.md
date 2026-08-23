# Scripts

Implemented dataset-integrity command wrappers:

- `python3 -m scripts.download_data --dataset hdfs --dry-run`: resolve and display archive destination without network access.
- `python3 -m scripts.verify_dataset --dataset hdfs`: report required-file presence and verify an existing manifest.
- `python3 -m scripts.build_dataset_manifest --dataset hdfs`: build a deterministic manifest only when required files exist.

META-001 bounded validation is available without writing an artifact:

    python3 -m scripts.extract_raw_metadata --dataset hdfs --dry-run --max-lines 1000

The metadata wrapper has no split, TEST, parser, window, model, or experiment
option.

SPLIT-001 structural generation/validation is available through:

    python3 -m scripts.split_dataset generate --dataset hdfs --json
    python3 -m scripts.split_dataset validate --dataset hdfs --json
    python3 -m scripts.split_dataset status --dataset hdfs --json

Generation is non-overwriting and publishes TEST only with its seal. The
ordinary split CLI deliberately has no TEST-unlock operation. Training,
parsing, indexing and experiment scripts remain absent.
