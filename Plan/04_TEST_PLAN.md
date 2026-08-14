# 04 — Test Plan V3

## Status convention

- **ACTIVE:** test logic currently exists and runs.
- **PLANNED:** requirement only; no coverage claim.
- Placeholder files do not count as implemented tests.

## Current active foundation tests

The active suite covers streaming checksums, strict dataset config/path validation, dataset presence states, safe acquisition behavior, deterministic manifests/fingerprints, independent verification, corruption detection, and a Python smoke test. Current baseline count before V3 implementation: 27 passing tests.

## Future unit-test requirements

| Area | Required cases | Status |
|---|---|---|
| Canonical schema | Valid/invalid events, sequences, partitions, claims, evidence IDs | PLANNED |
| Parser | Determinism, fit/freeze/restore, malformed lines, unseen templates, label isolation | PLANNED |
| Sequence | HDFS block grouping, BGL ordering, boundaries, no cross-split windows | PLANNED |
| Mutation | Seed determinism, no source mutation, token/gap/transition labels, impossible mutation handling | PLANNED |
| Baselines | Count/smoothing/transition scores, feature determinism, empty/unseen inputs | PLANNED |
| Neural models | Forward shapes, causal mask, padding mask, variable length, device consistency | PLANNED |
| Losses | Zero/positive cases, ranking margin direction, masked localization, finite gradients | PLANNED |
| Checkpoints | Save/load round trip, config/model/schema identity mismatch | PLANNED |
| ExpertEvidence | Optional unsupported fields, serialization, evidence references, fit-split metadata | PLANNED |
| Calibration | No TEST fitting, monotonic mappings, ECE/Brier fixtures, artifact round trip | PLANNED |
| Complementarity | Correlation, disagreement, error overlap, oracle gain, marginal contribution fixtures | PLANNED |
| Fusion | F0–F8 contracts, missing expert, mismatched IDs, masks, deterministic inference | PLANNED |
| Redundancy | Symmetry/diagonal/range, split provenance, leave-one-out behavior | PLANNED |
| Abstention | Coverage/risk accounting, all/none abstain edges, conflict fixtures | PLANNED |

## Integration requirements

1. Raw fixture → parser state → canonical events.
2. Events → grouping → split manifest → non-crossing sequences.
3. Normal sequence → mutation → coordinate-aware labels.
4. Sequence → each expert → ExpertEvidence.
5. Frozen evidence → calibration → complementarity report.
6. Frozen evidence → F0–F8 → evaluation report.
7. Frozen fused evidence → verifier/investigation → test recommendation.

All are **PLANNED** except the existing dataset config → manifest → verification workflow.

## Leakage tests

- Parser state fitted only on authorized partitions.
- Group IDs do not cross partitions.
- Overlapping windows do not cross partition boundaries.
- Mutation sources are training-derived normal sequences only.
- Normal-reference index excludes validation/TEST.
- Calibrator/fusion/threshold/checkpoint selection excludes TEST.
- Padding/sequence length cannot leak class labels through fixture shortcuts.

## Loss and model sanity tests

- Causal outputs cannot use future events.
- Padding never contributes to next-event or localization losses.
- Missing-event localization uses gap targets.
- Isolation Forest does not emit fabricated token positions.
- Ranking direction enforces lower normal than mutated energy.
- Conflict handling cannot minimize an objective by collapsing all confidence.

## Security tests

- Prompt-like log/document text remains data.
- No arbitrary shell or production-write tool.
- Evidence IDs must resolve; fabrication fails verification.
- Poisoned documentation cannot override system/tool policy.
- Generated test artifacts reject unsafe imports/actions before any optional execution.
- Raw paths, secrets, and credentials never enter reports or manifests.

## Performance tests

Future benchmarks report parser throughput, expert latency/throughput/memory, retrieval latency/index size, fusion overhead, and downstream model latency separately. Performance results require controlled hardware metadata and are **NOT_RUN**.

## Acceptance gates

- A module is not implemented until its non-placeholder tests pass.
- Fusion implementation does not start before ExpertEvidence and complementarity metric tests.
- Final TEST execution remains human-owned.
- No test is weakened merely to accommodate a failing implementation.
