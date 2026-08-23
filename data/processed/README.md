# Processed data

Ignored, reproducible derived artifacts. `splits/hdfs/` and `splits/bgl/` now
contain the local SPLIT-001 manifests, memberships, exclusions, canonical
payloads, and TEST seals. Do not commit these bulk files; regenerate and verify
them using the frozen dataset fingerprints and `seqlogad-split-dataset`.

`parsers/hdfs/` and `parsers/bgl/` contain the local PARSE-001 frozen Drain3
state, template registry, normal-pool summary, parser manifest, and manifest
hash sidecar. These artifacts are derived, non-overwriting, and ignored by
Git. Verify them with `seqlogad-fit-parser ... validate`; do not replace an
accepted parser state in place.
