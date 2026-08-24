# PURGE-DECISION-001 — HDFS Boundary-Purge Decision

| Field | Frozen value |
|---|---|
| Decision ID | `PURGE-DECISION-001` |
| Version | `1.0` |
| Status | `FROZEN_HUMAN_APPROVED` |
| Approval source | `HUMAN_RESEARCHER` |
| Approval timing | `PRE_SCIENTIFIC_EXPERIMENT` |
| Result informed | `false` |
| Selected option | **Option B — keep frozen primary + pre-register secondary sensitivity** |
| Scientific results | `NOT_RUN` |
| Next authorized task | `CANONICAL-EVENT-001` |

`result_informed=false` means that no baseline, model, killer-experiment, or
scientific TEST performance informed this decision. The aggregate prevalence
facts produced by PURGE-AUDIT-001 are permitted pre-model data-validity
evidence.

## 1. Evidence identities

- HDFS fingerprint: `0103c63b2847ba98b0b309a9e06eebb80ac8030e2f92d1f62320742537a34013`
- HDFS split payload: `21ec061a7717cd03e7648e3d89200d486bce81eb7dd1bf4114272dd90fc4295c`
- HDFS TEST partition: `fa0c743619f8e2f7ef82a3cb2057eb99891515d56b0aa87f168c60bec093175d`
- HDFS parser state: `7d9bd8041d00ee3a1ce6c32d8e19efd8764108d8695f559ec91b4381ecda8d91`
- PURGE-AUDIT payload: `274b62f3a7a6b072aec9e142b3e7e97c1548c08984ebe5240f4dc753ed27eabb`

All identities were independently verified immediately before this decision.
Both dataset TEST seals remained `SEALED / NEVER_OPENED`, with zero opens and
zero unlock records.

## 2. Evidence interpretation

**SeqLogAD audit fact — not a model result.** The frozen boundary rule removes
133,184 connected components and 2,541,053 eligible lines (22.7374%). Purged
component anomaly prevalence is 2.6745%, retained prevalence is 3.0045%, and
the difference is about -0.32996 percentage points with the recorded 95%
interval excluding zero. This establishes a representativeness concern; it
does not establish that the primary split is invalid or that model performance
will change.

**`LITERATURE_SUPPORTED`.** Recent log-anomaly studies show that dataset
construction, grouping, parsing, windowing, and split choices can affect what
anomaly performance means. Group/session integrity and chronology therefore
remain consequential design variables.

**`LITERATURE_INFORMED_SEQLOGAD_DECISION`.** General methods guidance supports
pre-specifying a focused robustness/sensitivity analysis after a diagnostic
concern is found but before inferential outcomes are inspected. The retained
guidance is not specific to log anomaly detection, so it informs rather than
dictates this project decision.

**`SEQLOGAD_PROTOCOL_DECISION`.** No reviewed source validates this exact
connected-component purge or requires replacing it. SeqLogAD therefore keeps
the already frozen, pre-result primary analysis and registers one secondary
robustness analysis instead of silently changing the primary population.

See [the task-specific citation note](../references/PURGE-DECISION-001-citations.md)
for source-level claims, publication status, limitations, and search record.

## 3. Alternatives and decision matrix

| Criterion | A — primary + limitation only | B — primary + secondary sensitivity | C — amend primary split |
|---|---|---|---|
| Scientific validity | Defensible but leaves magnitude of construction sensitivity unknown | **Strongest balance: preserves confirmatory design and measures robustness** | Potentially improves coverage, but benefit is unproven |
| Selection-bias handling | Documents concern only | Explicitly evaluates the excluded construction | Changes selection mechanism, but introduces a new design choice |
| Preserves frozen primary | Yes | **Yes** | No |
| Preserves TEST identity | Yes | **Yes** | No |
| Measures robustness | No | **Yes** | Not against the original primary unless both are retained |
| Researcher degrees of freedom | Low | Low when fixed before outcomes and non-selection rules are enforced | High due to redesign choices |
| Implementation/time cost | Lowest | **Moderate and bounded** | Highest; invalidates split/parser provenance |
| Reproducibility | High | **High with separate hashed artifacts** | Possible, but requires new protocol/artifact family |
| Reviewer defensibility | Concern remains unquantified | **Best: primary/secondary distinction is explicit** | Weak without evidence that current primary is indefensible |
| Decision | Not selected | **Selected and human-approved** | Not authorized |

### Option A assessment

Option A would preserve all frozen identities and is scientifically reportable,
but it cannot answer whether the HDFS conclusion is sensitive to the 22.7%
structural exclusion. Its remaining reviewer risk is avoidable with one bounded
secondary analysis.

### Option B assessment

Option B preserves pre-registration, TEST identity, parser identity, and the
primary estimand while quantifying the exact concern discovered before model
results. Its main risk—turning a secondary result into a second chance to pick
a favorable conclusion—is controlled by the non-confirmatory, non-selection,
post-primary execution contract below.

### Option C assessment

Option C would require a new split identity, TEST identity, normal-pool
identity, parser fit, protocol amendment, and downstream provenance. The audit
shows a detectable population difference but no model-performance distortion
or fatal invalidity. That evidence is insufficient to justify replacing the
primary analysis.

## 4. Frozen primary HDFS protocol

The primary HDFS protocol is unchanged:

1. The existing retained-component SPLIT-001 population remains confirmatory.
2. Split payload and TEST partition hashes remain canonical.
3. Drain3 0.9.11 state remains frozen and is never refit for this decision.
4. EFFECT-001 remains unchanged; `delta_HDFS = 0.01 AP`.
5. Only the original frozen HDFS analysis can support the primary HDFS claim.
6. TEST remains human-only, sealed, and single-use under the existing policy.

## 5. Secondary HDFS purge-sensitivity contract

Status: `PRE_REGISTERED_SECONDARY_NOT_RUN`.

Purpose: assess whether the qualitative conclusion about sequence-order value
is robust to the HDFS boundary-purge construction.

### Population and construction

- The sensitivity cohort is all and only complete META-001 components already
  recorded as public `PURGED_BOUNDARY` exclusions by SPLIT-001.
- Membership is structural and label-independent; no component is split.
- Events within each component retain original source-line chronology.
- Raw bytes and primary memberships are never modified.
- The frozen primary HDFS parser is reused in read-only match mode; unknowns
  follow `EVT_UNSEEN`. No sensitivity parser is fit.

### Execution boundary

- Human execution only, after the primary HDFS final-result bundle is
  immutable.
- Reuse the exact frozen primary orderless comparator, sequential comparator,
  configs, seeds, event mapping, metric implementation, and paired component
  uncertainty method.
- Do not tune, select, open Transformer/fusion gates, change thresholds, or
  rewrite the primary result from this cohort.
- Do not access scientific TEST membership. This excluded cohort is stored and
  reported under a separate sensitivity namespace.

### Interpretation

- **Robust:** primary and sensitivity analyses occupy the same
  non-inconclusive EFFECT-001 decision region.
- **Sensitive:** they occupy incompatible non-inconclusive regions; report
  `HDFS_RESULT_SENSITIVE_TO_SPLIT_CONSTRUCTION`.
- **Limitation required:** the sensitivity result is inconclusive,
  unclassifiable, or disagrees with the primary.
- In every case, the original primary result remains controlling.

The existing `0.01 AP` margin is reused only as the secondary interpretive
framework for the same Delta-AP estimand. This decision does not modify
EFFECT-001 and does not compare anomaly-prevalence percentage points with AP.

## 6. Effects and limitations

- **Primary protocol effect:** none; identities and memberships are unchanged.
- **TEST effect:** none; no access, grant, unlock, or identity change.
- **Parser effect:** none; frozen state remains read-only.
- **Known limitation:** the primary HDFS conclusion formally targets the
  retained-component population. The secondary cohort helps assess robustness
  but cannot erase the non-random exclusion mechanism.
- **Known limitation:** the methods guidance used to motivate pre-specified
  sensitivity analysis includes clinical/observational domains; it is applied
  as a general planning principle, not as log-specific proof.

## 7. Authorization and stop point

`PURGE-DECISION-001` closes the human stop gate. It authorizes only
`CANONICAL-EVENT-001` as the next task. It does not execute the sensitivity
analysis, generate canonical events, build sequences, run baselines/models,
or open TEST.
