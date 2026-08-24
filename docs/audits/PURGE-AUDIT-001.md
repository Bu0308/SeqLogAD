# PURGE-AUDIT-001 — HDFS Purge Representativeness Audit

| Field | Value |
|---|---|
| Status | `PURGE_REPRESENTATIVENESS_CONCERN` |
| Plan state | `PLAN_CONFLICT_DETECTED` — human review required; no split change authorized |
| Dataset fingerprint | `0103c63b2847ba98b0b309a9e06eebb80ac8030e2f92d1f62320742537a34013` |
| Split payload hash | `21ec061a7717cd03e7648e3d89200d486bce81eb7dd1bf4114272dd90fc4295c` |
| Audit payload SHA-256 | `274b62f3a7a6b072aec9e142b3e7e97c1548c08984ebe5240f4dc753ed27eabb` |
| Primary unit | META-001 connected component/session |
| TEST | `SEALED / NEVER_OPENED`; open count `0`; unlock records `0` |
| Scientific experiment | `NOT_RUN` |

Machine-readable source: [`PURGE-AUDIT-001.json`](PURGE-AUDIT-001.json). Method
and source provenance: [`../references/PURGE-AUDIT-001-citations.md`](../references/PURGE-AUDIT-001-citations.md).

## Population and mapping facts

`PURGED` is exactly the public `PURGED_BOUNDARY` component set. `RETAINED` is
the complement of that set in the reconstructed META-001 component universe;
the audit did not open ordinary or sealed partition membership.

The label file contains 575,061 rows and 575,061 unique normalized block IDs.
Mapping found zero duplicates, unknown IDs, missing IDs, multi-block
components, or within-component label conflicts. On these exact bytes, one
label row maps to one connected component, but this was verified rather than
assumed.

| Aggregate population | Components | Unique blocks | Raw lines | Anomalous | Normal | Anomaly prevalence |
|---|---:|---:|---:|---:|---:|---:|
| `PURGED` | 133,184 | 133,184 | 2,541,053 | 3,562 | 129,622 | 0.0267449543 |
| `RETAINED` | 441,877 | 441,877 | 8,634,576 | 13,276 | 428,601 | 0.0300445599 |

These are aggregate dataset-validity audit outcomes, not model metrics and not
partition-specific outcomes.

## Primary contrast

**FACT:**

- `D = p_PURGED - p_RETAINED = -0.0032996056` (−0.32996 percentage points).
- Newcombe hybrid-score Wilson 95% CI: `[-0.0042920586, -0.0022876514]`.
- Prevalence ratio `p_PURGED / p_RETAINED = 0.8901762724`.
- No p-value was used and no practical-equivalence threshold was invented.

The CI treats connected components as independent inferential units. This is
appropriate to the verified component-level binary label mapping but does not
model possible temporal dependence between distinct components. The observed
finite-dataset difference itself is exact; the CI is a superpopulation-style
uncertainty summary.

## Structural diagnostics

| Diagnostic | `PURGED` | `RETAINED` |
|---|---:|---:|
| Raw lines/component, median (IQR) | 19 (0) | 19 (3) |
| Raw lines/component, 5th–95th percentile | 19–20 | 13–29 |
| Source-line span, median (IQR) | 1,467,452.5 (610,006.25) | 597,001 (1,609,397) |
| Source-line span, 5th–95th percentile | 924,516–2,070,643 | 3,736–2,724,301.2 |
| Nominal partitions touched, median | 2 | 1 |
| Nominal partitions touched, maximum | 5 | 1 |
| Nominal boundaries crossed, median | 1 | 0 |

Full robust summaries, including source-line start/end and min/max, are in the
JSON artifact. These variables are raw/META structural quantities; no parser,
template, feature, or model was used.

## Interpretation and decision boundary

**INTERPRETATION:** The frozen purge is demonstrably non-random: it selects
components whose observations span nominal chronological boundaries. It also
removes 22.7374495% of eligible raw lines, while the purged population has
about 11.0% lower anomaly prevalence relative to retained components. This can
change the population represented by future HDFS results and is therefore a
scientifically relevant selection-bias concern.

**PROJECT DECISION:** Record `PURGE_REPRESENTATIVENESS_CONCERN` and
`PLAN_CONFLICT_DETECTED`. This does **not** authorize split repair, ratio
repair, component reassignment, or a claim that HDFS is invalid. A human
researcher must decide how the limitation affects continuation and reporting.
Because no human-approved prevalence-equivalence margin exists,
`PURGE_REPRESENTATIVENESS_ACCEPTABLE` cannot be issued.

The audit cannot establish causality and cannot answer whether sequence order
helps anomaly detection.

## Leakage and TEST boundary

The execution order was frozen structural identities → reconstruct aggregate
populations → read labels for the audit only. Labels did not flow into split,
parser, canonical events, sequences, baseline/model selection, or TEST.
Neither partition-specific outcome statistics nor TEST membership/outcomes
were produced. `purge_representativeness` is now a formal data-validity audit
item.

## Determinism

Two independent full runs produced the same canonical scientific payload
SHA-256:

```text
274b62f3a7a6b072aec9e142b3e7e97c1548c08984ebe5240f4dc753ed27eabb
```

Generation timestamp and Git dirty metadata are the only volatile wrapper
fields and are excluded from scientific identity.
