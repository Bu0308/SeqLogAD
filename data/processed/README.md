# Processed data

Ignored, reproducible derived artifacts. `splits/hdfs/` and `splits/bgl/` now
contain the local SPLIT-001 manifests, memberships, exclusions, canonical
payloads, and TEST seals. Do not commit these bulk files; regenerate and verify
them using the frozen dataset fingerprints and `seqlogad-split-dataset`.
