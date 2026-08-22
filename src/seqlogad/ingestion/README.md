# Ingestion

This module implements dataset integrity plus parser-independent raw metadata,
not log-template parsing or scientific partitioning.

META-001 adds raw_metadata.py for deterministic HDFS block/component and BGL
chronology metadata, bounded dry-runs, and non-overwrite generated artifacts.

- `dataset_config.py`: strict Pydantic contracts for per-dataset YAML.
- `dataset_acquisition.py`: safe archive download with dry-run, timeout, temporary file and checksum gate; no extraction.
- `dataset_validation.py`: `PRESENT` / `PARTIAL` / `MISSING` required-file report.
- `dataset_manifest.py`: deterministic manifest build, content fingerprint and non-mutating verification.
- `errors.py`: small domain error hierarchy for expected failures.

Input: version-controlled dataset config plus optional local raw bytes.

Output: presence reports, archive acquisition result, manifest/verification
report, or label-free raw metadata.

Dependencies: `seqlogad.common.checksum`, Pydantic and PyYAML. Network is used only when the operator explicitly runs a non-dry-run download command; tests are offline.

Not implemented here: archive extraction, Drain3 fitting/templates, scientific
partition assignment, canonical event generation, sequencing, models, or
dataset analysis.
