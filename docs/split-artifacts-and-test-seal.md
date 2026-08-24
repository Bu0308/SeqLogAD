# SPLIT-001 — Real Structural Split and TEST Seal

| Field | State |
|---|---|
| Task | `SPLIT-001` |
| Status | **COMPLETE** |
| Protocol | `PROTOCOL-001` v1.1 |
| Split contract | `PROTOCOL-SPLIT-CLARIFY-001` v1.0 |
| Scientific experiment status | `NOT_RUN` |
| HDFS TEST | `SEALED / NEVER_OPENED` |
| BGL TEST | `SEALED / NEVER_OPENED` |
| TEST open count | `0` |
| TEST unlock records | `0` |
| Parser/templates/models/metrics | not used |
| Citation and method note | [`references/SPLIT-001-citations.md`](references/SPLIT-001-citations.md) |

SPLIT-001 generated deterministic structural assignments from the accepted raw
dataset identities. It did not inspect anomaly labels, fit Drain3, create event
templates, build model features, or compute a scientific score. All statistics
below describe structural allocation only.

## HDFS structural result

| Quantity | Value |
|---|---:|
| Raw lines | 11,175,629 |
| Structurally eligible lines | 11,175,629 |
| Structurally ineligible lines | 0 |
| META-001 connected components | 575,061 |
| Purged boundary components | 133,184 |
| Purged eligible lines | 2,541,053 |
| Purge fraction | 0.22737449498368278 |
| Assigned eligible lines | 8,634,576 |

| Partition | Nominal target lines | Assigned lines | Assigned components | Realized assigned-line ratio |
|---|---:|---:|---:|---:|
| `BASE_TRAIN` | 6,705,377 | 5,782,072 | 262,689 | 0.6696416824636207 |
| `FUSION_TRAIN` | 1,117,563 | 307,684 | 23,204 | 0.03563394427242287 |
| `VAL_EXPERT` | 1,117,563 | 710,454 | 37,745 | 0.08228012585678787 |
| `VAL_FUSION` | 1,117,563 | 729,110 | 49,996 | 0.08444074150253585 |
| `TEST` | 1,117,563 | 1,105,256 | 68,243 | 0.12800350590463272 |

Exact reconciliation:

```text
11,175,629 = 0 + 8,634,576 + 2,541,053
8,634,576 = 5,782,072 + 307,684 + 710,454 + 729,110 + 1,105,256
```

The large realized-ratio deviation is retained rather than repaired because
the frozen rule purges every connected component that touches two or more
nominal partitions. This is a protocol consequence, not an anomaly result.

### Post-split representativeness audit

`PURGE-AUDIT-001` subsequently compared only the aggregate purged and retained
component populations. It found anomaly prevalence 0.0267449543 versus
0.0300445599, respectively: difference −0.0032996056 with Newcombe-Wilson 95%
CI [−0.0042920586, −0.0022876514] and prevalence ratio 0.8901762724. Together
with the 22.7374% raw-line removal and deterministic span-based selection, this
is recorded as `PURGE_REPRESENTATIVENESS_CONCERN` / `PLAN_CONFLICT_DETECTED`.
No split repair is authorized; human review is required. See
[`audits/PURGE-AUDIT-001.md`](audits/PURGE-AUDIT-001.md). No partition-specific
outcome, TEST membership, parser update, or model metric was produced.

## BGL structural result

| Partition | Raw lines | Complete 100-line parents | Residual lines | Retained lines |
|---|---:|---:|---:|---:|
| `BASE_TRAIN` | 2,848,777 | 28,487 | 77 | 2,848,700 |
| `FUSION_TRAIN` | 474,797 | 4,747 | 97 | 474,700 |
| `VAL_EXPERT` | 474,796 | 4,747 | 96 | 474,700 |
| `VAL_FUSION` | 474,796 | 4,747 | 96 | 474,700 |
| `TEST` | 474,797 | 4,747 | 97 | 474,700 |

Exact reconciliation:

```text
4,747,963 = 4,747,500 + 463
```

All 47,475 retained parents are consecutive, non-overlapping, exactly 100 raw
lines, and contained in one partition. Each residual is explicit; no line is
padded, borrowed, merged, or silently dropped.

## Scientific identities

### HDFS

- `split_payload_hash`: `21ec061a7717cd03e7648e3d89200d486bce81eb7dd1bf4114272dd90fc4295c`
- `BASE_TRAIN`: `dbdb671e41f5d03377cd2a0b726f7a199af2a7c0dbf48c1c98320a93e41fd77b`
- `FUSION_TRAIN`: `fda089c568ac4673d97eb65228a09132f05d0bc41502939b2b40a958986d5e02`
- `VAL_EXPERT`: `d0c151c945710f331145c342791052cc8022ff7d1fa48297e8e004a7ca4bbbc7`
- `VAL_FUSION`: `d908ba8191bdcdeeeb3e8215fb4eaa05734ce68c1c921b22028393020b786c31`
- `TEST`: `fa0c743619f8e2f7ef82a3cb2057eb99891515d56b0aa87f168c60bec093175d`
- first persisted `manifest_file_hash`: `bcd394c9736dfb147b6dba28a8c5c56a3c77e654ab3b602d80fc47b31537be83`

### BGL

- `split_payload_hash`: `0c1bb1b9b755aa2aa50238771cf5bf34649e1ca33c7964e061766b659aeebd05`
- `BASE_TRAIN`: `08f7830239fb7889cf76ac31921629d34090aba2b471f948422c3869eb845f19`
- `FUSION_TRAIN`: `c39333f450d348150deaa4379ad74b20597124aedd1b1e7e0f42da5a67a04645`
- `VAL_EXPERT`: `d695defa5be177d34e8ee55476951d1d8db22a97f1e3f53180e0a0e38c84172b`
- `VAL_FUSION`: `3f035c038bc8c8acacc475fc69cf811214ec247d8891022495adf5d7636da3f7`
- `TEST`: `7ecf43ab27d6519b7af4ae4e8f7be5cd9d5351c8c11d18b3bd11b4ff896a876d`
- first persisted `manifest_file_hash`: `d5c53442bc9416524767e2f199b8e230ec453b83fd5023eb4092781dacca242f`

The payload and partition hashes reproduced exactly in independent second
generations. Manifest file hashes may differ across generations because the
non-scientific generation timestamp is intentionally volatile.

## Physical TEST enforcement

Each dataset directory separates ordinary and TEST membership:

```text
data/processed/splits/<dataset>/
├── partitions/                 # BASE/FUSION/validation membership
├── sealed/TEST.jsonl           # not exposed by the ordinary loader
├── exclusions.jsonl
├── split-payload.json.gz
├── split-manifest.json
├── split-manifest.json.sha256
├── test-seal.json
└── test-access-audit.jsonl     # empty after SPLIT-001
```

The seal binds dataset fingerprint, Protocol v1.1, split payload hash, and TEST
partition hash. Ordinary loaders reject `TEST` before resolving or opening the
membership file. Future access requires the separate
`seqlogad-final-test-access` workflow, the exact confirmation phrase, a human
reason, expected hashes, and an audit record. SPLIT-001 did not invoke that
workflow and did not create a grant.

## Reproduction and validation

Derived artifacts are ignored by Git and must not be committed. They occupy
about 574 MiB for HDFS and 26 MiB for BGL locally. Regenerate only from the
verified raw fingerprints and the frozen protocol:

```bash
seqlogad-split-dataset --project-root . generate --dataset hdfs --json
seqlogad-split-dataset --project-root . generate --dataset bgl --json
seqlogad-split-dataset --project-root . validate --dataset hdfs --json
seqlogad-split-dataset --project-root . validate --dataset bgl --json
seqlogad-split-dataset --project-root . status --dataset hdfs --json
seqlogad-split-dataset --project-root . status --dataset bgl --json
```

Generation refuses overwrite. Validation is structural and may read sealed
membership solely to recompute hashes/reconciliation; it never reads anomaly
labels or outcomes. Do not run the human unlock workflow until the separate
final-TEST gate is approved.
