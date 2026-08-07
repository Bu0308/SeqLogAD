# Ingestion

Day 2 implements only the dataset acquisition boundary, not log parsing.

- `dataset_config.py`: strict Pydantic contracts for per-dataset YAML.
- `dataset_acquisition.py`: safe archive download with dry-run, timeout, temporary file and checksum gate; no extraction.
- `dataset_validation.py`: `PRESENT` / `PARTIAL` / `MISSING` required-file report.
- `dataset_manifest.py`: deterministic manifest build, content fingerprint and non-mutating verification.
- `errors.py`: small domain error hierarchy for expected failures.

Input: version-controlled dataset config plus optional local raw bytes.

Output: presence reports, archive acquisition result, manifest or verification report.

Dependencies: `src/common/checksum.py`, Pydantic and PyYAML. Network is used only when the operator explicitly runs a non-dry-run download command; tests are offline.

Not implemented: archive extraction, canonical event schema, Drain3, transformation, sequencing or dataset analysis.
