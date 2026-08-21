# 04 — Test Plan v1.1

`ACTIVE` means executable coverage exists. `PLANNED` is a requirement only. Placeholder files never count as implemented tests.

## Active foundation coverage

The current suite must pass for environment/package imports, dataset contracts/acquisition/checksums/manifests/verification, canonical event/template schemas, sequence/localization/mutation schema contracts, and protocol consistency. Test count is reported from each actual run rather than kept as a permanent badge.

## Required future tests

| Area | Required cases | Scope/status |
|---|---|---|
| Protocol identity | v1.1 current, v1.0 preserved, active config pointers consistent | ACTIVE/expanded in freeze |
| Raw metadata | HDFS group extraction, shared-line components, malformed/unassigned IDs, BGL line chronology | MUST / PLANNED |
| Split | deterministic boundaries, atomic HDFS purge, target/realized ratios, hash stability | MUST / PLANNED |
| TEST guard | no routine label/count/preview access; explicit human unlock; access log | MUST / PLANNED |
| Parser | normal BASE fit only, freeze/restore, no updates, unseen mapping, label isolation | MUST / PLANNED |
| Sequence | HDFS grouping, BGL 100-event non-overlap, residual/boundary handling | MUST / PLANNED |
| Orderless controls | unseen event, length, count-vector, empty/unseen/constant cases | MUST / PLANNED |
| Isolation Forest | deterministic features, no order features, validation-only fit/selection | SHOULD / PLANNED |
| Markov/N-gram | count/smoothing/backoff, transition surprise, OOV and short sequence | MUST / PLANNED |
| Sequence destruction | preserve multiset/count/length/label/partition, deterministic seed/hash, reject/record no-op | MUST / PLANNED |
| KT-2 | count-vector collisions, purity/entropy equivalent, out-of-sample fixture | MUST / PLANNED |
| Metrics | PR-AUC fixtures, paired comparison, correct HDFS/BGL unit, no TEST selection | MUST / PLANNED |
| Transformer | causal/mask/shape/checkpoint only after gate | CONDITIONAL |
| Localization | token/gap/transition, randomization, counterfactual repair/deletion | CONDITIONAL |
| Fusion | complementarity and corrupted-expert controls before any fusion | CONDITIONAL |

## Leakage tests

1. Raw split precedes every fitted parser/normalizer/window.
2. HDFS components and BGL parents do not cross partitions.
3. Labels are excluded from parser/model input and base loss.
4. Parser state/vocabulary never updates after normal `BASE_TRAIN` fit.
5. Duplicates/overlapping contexts do not cross partitions.
6. Threshold/model/config selection excludes TEST.
7. Sequence destruction never changes counts, lengths, labels, parents, or raw bytes.
8. Reserved fusion partitions are not silently repurposed.

## Negative-control assertions

- A shuffled sample keeps the same count vector exactly.
- No-op permutations are rejected or explicitly recorded.
- Conditional localization cannot pass solely through target-position leakage.
- Conditional fusion cannot gain confidence from a random/corrupted expert by construction.

## CI acceptance

CI uses canonical Python 3.12, installs with the locked constraint, runs `pip check`, then the full pytest suite. It does not download datasets or execute scientific experiments.

## Gate policy

- Failing tests are diagnosed; they are not weakened to fit implementation.
- No conditional test suite is marked active before its gate/task exists.
- Dataset verifiers must preserve accepted fingerprints.
- Final TEST access requires separate human authorization and is never a normal CI test.

