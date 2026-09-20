# Scripts

Implemented dataset-integrity command wrappers:

- `python3 -m scripts.download_data --dataset hdfs --dry-run`: resolve and display archive destination without network access.
- `python3 -m scripts.verify_dataset --dataset hdfs`: report required-file presence and verify an existing manifest.
- `python3 -m scripts.build_dataset_manifest --dataset hdfs`: build a deterministic manifest only when required files exist.

META-001 bounded validation is available without writing an artifact:

    python3 -m scripts.extract_raw_metadata --dataset hdfs --dry-run --max-lines 1000

The metadata wrapper has no split, TEST, parser, window, model, or experiment
option.

Phase-2 one-click packaging commands:

    python scripts/package_phase2_all_experts_colab.py --root .
    python scripts/package_p22_runpod.py --root .

The first command rebuilds the shared pinned code archive. The second validates
the materialized P2.2 sequence bundle, creates its RunPod A40 notebook, and emits
the upload directory plus outer ZIP under `outputs/runpod/P2.2-S42-A40*`.
P2.2 runtime orchestration remains in Python modules; the notebook only verifies,
installs, resumes, and exports them.

SPLIT-001 structural generation/validation is available through:

    python3 -m scripts.split_dataset generate --dataset hdfs --json
    python3 -m scripts.split_dataset validate --dataset hdfs --json
    python3 -m scripts.split_dataset status --dataset hdfs --json

Generation is non-overwriting and publishes TEST only with its seal. The
ordinary split CLI deliberately has no TEST-unlock operation. Training,
indexing and experiment scripts remain absent.

PARSE-001 parser lifecycle checks are available through:

    python3 -m scripts.fit_parser gate --dataset hdfs --json
    python3 -m scripts.fit_parser pool --dataset hdfs --json
    python3 -m scripts.fit_parser validate --dataset hdfs --json

The separate `fit` command is non-overwriting and consumes only the permitted
normal `BASE_TRAIN` pool. It does not generate canonical events, sequences, or
scientific metrics, and the ordinary parser CLI cannot open TEST.
