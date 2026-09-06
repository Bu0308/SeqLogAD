# v2 process-evidence records

This directory is the append-only, project-local evidence layer for the v2
domain-adaptive fusion workflow. It records what the project did; it does not
define the research direction and it never stores raw log events or target
labels used during adaptation.

The machine contract is [`configs/collection/v2.yaml`](../configs/collection/v2.yaml).
Record schemas and the validator live in `src/seqlogad/collection/`. Every
record carries a source badge (`projmem_native`, `research_manifest`, or
`aletheia_derived`) so imported evidence is not misrepresented as native.

Initialize and validate from the repository root:

```bash
seqlogad-collect --project-root . init
seqlogad-collect --project-root . validate
```

Records are JSONL and append-only. Failures and late backfills remain records;
they are not deleted or silently rewritten. Keep private/raw material outside
the tracked manifests under `research_records/private/`.
