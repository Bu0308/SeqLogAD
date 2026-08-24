# 04 — Test Plan v1.1

`ACTIVE` means executable coverage exists. `PLANNED` is a requirement only. Placeholder files never count as implemented tests.

## Active foundation coverage

The current suite must pass for environment/package imports, dataset contracts/acquisition/checksums/manifests/verification, canonical event/template schemas, sequence/localization/mutation schema contracts, and protocol consistency. Test count is reported from each actual run rather than kept as a permanent badge.

## Required future tests

| Area | Required cases | Scope/status |
|---|---|---|
| Protocol identity | v1.1 current factory, explicit v1.0 preservation, unsupported/missing rejection, EFFECT-001 parent/status/pointers consistent | ACTIVE / SCHEMA-COMPAT-001 frozen |
| Statistical freeze | Approved `0.01 AP` margins plus estimand, candidate family, bootstrap, multiplicity and KT-3 rules remain fixed; no run config may override | ACTIVE contract tests; no statistic executed |
| Raw metadata | HDFS group extraction, shared-line components, malformed/unassigned IDs, BGL chronology/ties/malformed timestamps, label independence, determinism, artifact non-overwrite | ACTIVE / META-001 |
| Split clarification | exact cumulative-floor, HDFS whole-component purge/reconciliation, BGL per-partition 100-line windows/residuals, layered non-circular identities, evidence classifications | ACTIVE |
| Split | deterministic boundaries, atomic HDFS purge, target/realized ratios, universe reconciliation, payload/partition/assignment/file hash stability | ACTIVE / SPLIT-001 |
| TEST guard | default denial, hash substitution rejection, no ordinary bypass, explicit human unlock, linked access log | ACTIVE on synthetic fixtures; real TEST remains sealed/unopened |
| Parser | normal BASE fit only, partition/label-scope rejection, config and pool identity, deterministic fit, freeze/restore, corruption rejection, immutable match, `EVT_UNSEEN`, BGL empty-content policy | ACTIVE / PARSE-001; real fit structurally verified, no event corpus/metric |
| Active state | binding protocol-stack pointers, required Isolation Forest status, stochastic/deterministic seed separation, portable split/parser references, sealed TEST status, current task pointer, owner-controlled license state | ACTIVE / ALIGN-FIX-001 |
| Purge representativeness | frozen identity rejection, deterministic PURGED/RETAINED complement, label normalization/coverage/conflict hard-stop, component-level CI, ratio-zero handling, payload hash, no split/parser/model/TEST dependency | ACTIVE / PURGE-AUDIT-001; human decision pending |
| Sequence | HDFS grouping, BGL 100-event non-overlap, residual/boundary handling | MUST / PLANNED |
| Orderless controls | unseen event, length, count-vector, empty/unseen/constant cases | MUST / PLANNED |
| Isolation Forest | deterministic features, no order features, normal-BASE fit, validation-only selection, required primary eligibility | MUST / PLANNED |
| Markov/N-gram | count/smoothing/backoff, transition surprise, OOV and short sequence | MUST / PLANNED |
| Sequence destruction | preserve multiset/count/length/label/partition, deterministic seed/hash, reject/record no-op | MUST / PLANNED |
| KT-2 | count-vector collisions, purity/entropy equivalent, out-of-sample fixture | MUST / PLANNED |
| Metrics | non-interpolated AP fixtures, paired 10,000-replicate cluster bootstrap, degenerate redraw/failure, seed separation, HDFS/BGL units, four decision regions, no TEST selection | MUST / PLANNED |
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
9. HDFS labels and BGL inline labels cannot alter raw assignment identity.
10. Assignment/partition derived IDs cannot enter the payload that defines their parent split hash.
11. `purge_representativeness` fixes structural populations before label access; labels cannot flow into split, parser, event/sequence generation, models, KT construction, or TEST membership.

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
