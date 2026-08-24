# SeqLogAD context snapshot — post PARSE-001

> Canonical handoff snapshot for `PROJECT-ALIGNMENT-AUDIT-001`  
> Audit date: 2026-08-23  
> Repository state audited: `a1e0b8d4197d8942c36d3118be6e5015601daead` (`PARSE-001`)  
> Audit verdict at creation: **PARTIALLY ALIGNED — CORRECTIONS REQUIRED**  
> Post-audit status: **ALIGN-FIX-001 COMPLETE — ACTIVE STATE SYNCHRONIZED**  
> Active state registry: `configs/active-state.yaml`

This snapshot records the current scientific contract. It does not report model
performance and does not authorize the next pipeline stage. Historical V1/V2/V3
plans remain provenance only; active Protocol v1.1 and later binding addenda take
precedence.

## 1. Current research question

> **How much additional anomaly-detection value does sequence order provide
> beyond strong order-insensitive baselines under a leakage-controlled,
> chronological, and equal-budget evaluation protocol?**

The current direction is `HYBRID_B_PLUS_C`:

- **Core (Option B):** controlled measurement of the added value of order.
- **Conditional (Option C):** localization faithfulness only if the detection and
  order-information gates justify it.
- HDFS and BGL are suitability/negative-result benchmarks, not assumed proof that
  sequence modeling is useful.
- A null, equivalent, harmful, or inconclusive result is scientifically valid.

## 2. Current contribution framing

The safe pre-experiment framing is:

> A leakage-controlled empirical evaluation framework for measuring the
> additional value of sequence order beyond strong order-insensitive baselines
> on large-scale event logs.

This is an evaluation design and research hypothesis. It is **not** a claim of a
novel Transformer, fusion method, localization method, synthetic mutation method,
or anomaly-detection algorithm.

## 3. Source-of-truth order

1. Verified immutable bytes and generated identity-bearing artifacts.
2. Active Protocol v1.1.
3. Binding addenda and contracts: EFFECT-001, SCHEMA-COMPAT-001,
   PROTOCOL-SPLIT-CLARIFY-001, SPLIT-001, and PARSE-001.
4. Latest ADRs, especially the redirect decision that supersedes the former V3
   multi-expert/fusion core.
5. Active plan/backlog/configuration.
6. Historical plans only for provenance.

Where a base protocol file and a later binding addendum differ, the addendum wins.
The machine-readable base now points explicitly to EFFECT-001 and split
clarification, while current execution status is kept separately so frozen
scientific history is not rewritten.

## 4. Frozen dataset identities

| Dataset | Canonical local identity | Current role |
|---|---|---|
| HDFS | `0103c63b2847ba98b0b309a9e06eebb80ac8030e2f92d1f62320742537a34013` | Core suitability and sequence-value evaluation; block/session atomicity |
| BGL | `c9ee7a8db13d37c88f896e305ed12dc7a66b586cdae4e388db4949f78afbe861` | Core suitability and sequence-value evaluation; chronological raw-line construction |

Dataset suitability is `TO_BE_TESTED`. Existing literature warns that both data
sets may expose strong order-insensitive signals. That warning motivated the
current question; it is not a SeqLogAD result.

## 5. Frozen protocol and statistical contract

- Partition family: `BASE_TRAIN / FUSION_TRAIN / VAL_EXPERT / VAL_FUSION / TEST`.
- Target split: `60 / 10 / 10 / 10 / 10`, chronological and label-independent.
- HDFS: raw line rank boundaries; connected block/session components remain
  atomic; boundary-spanning components are purged deterministically.
- BGL: split raw source-line chronology first; then form independent,
  non-overlapping 100-event parent windows inside each partition; residual lines
  are explicit exclusions.
- Drain3: fit only on permitted normal `BASE_TRAIN` records, then freeze.
- No Loghub preprocessed HDFS templates/traces are scientific input.
- Primary metric/estimand: Average Precision (`AP`) difference between an eligible
  sequential candidate and the strongest eligible order-insensitive candidate.
- Practical-effect margins, human-approved before results:
  `delta_HDFS = 0.01 AP`, `delta_BGL = 0.01 AP`.
- Decision family using the paired 95% interval:
  - entirely above `+0.01`: meaningful gain;
  - entirely inside `[-0.01, +0.01]`: practical equivalence;
  - entirely below `-0.01`: meaningful harm;
  - otherwise: inconclusive.
- KT-3 sequence destruction uses the same practical-effect margin.
- Stochastic core methods use three predeclared seeds: `42`, `43`, and `44`.
  Deterministic baselines are explicitly marked seed-not-applicable and do not
  receive fabricated repeated runs.
- Scientific TEST is opened once by the human researcher after all choices are
  frozen. No scientific TEST run has occurred.

## 6. Split identities and TEST state

| Dataset | Split payload hash | TEST partition hash | TEST state |
|---|---|---|---|
| HDFS | `21ec061a7717cd03e7648e3d89200d486bce81eb7dd1bf4114272dd90fc4295c` | `fa0c743619f8e2f7ef82a3cb2057eb99891515d56b0aa87f168c60bec093175d` | `SEALED / NEVER_OPENED / open_count=0 / unlock_records=0` |
| BGL | `0c1bb1b9b755aa2aa50238771cf5bf34649e1ca33c7964e061766b659aeebd05` | `7ecf43ab27d6519b7af4ae4e8f7be5cd9d5351c8c11d18b3bd11b4ff896a876d` | `SEALED / NEVER_OPENED / open_count=0 / unlock_records=0` |

The ordinary partition loader rejects `TEST` before resolving its membership
file. A dedicated, human-only final-TEST workflow would require a bound partition
hash, reason, confirmation, and audit record. No grant exists.

Structural split facts, not anomaly-label statistics:

- HDFS: 11,175,629 eligible raw lines; 2,541,053 lines in 133,184
  boundary-spanning components were explicitly purged; 8,634,576 lines assigned.
- The HDFS purge ratio is 22.737449498368278% and remains
  `METHODOLOGICAL_RISK_TO_BE_ASSESSED`; representativeness/sensitivity has not
  been evaluated, no anomaly labels were inspected for this assessment, and the
  frozen split is not repaired.
- BGL: 4,747,963 raw lines; 47,475 complete parent windows; 463 residual lines
  explicitly excluded.

## 7. Frozen parser identities

Shared Drain3 package/config:

- Drain3 version: `0.9.11`.
- Parser config hash:
  `c5bb4fd25ecc98667700cbb3095fb561ba4b6651b2815400adc91e5efba0d65c`.
- Fit scope: normal-only `BASE_TRAIN`.
- Later partitions: frozen read-only matching; no cluster creation/update.
- Unknown template contract: reserved `EVT_UNSEEN`.

| Field | HDFS | BGL |
|---|---|---|
| Status | `FIT_COMPLETED_FROZEN` | `FIT_COMPLETED_FROZEN` |
| Normal-pool records | 5,606,995 | 2,616,821 |
| Normal-pool SHA-256 | `bce127f5c98b120d4ce77be63359b413443ee652980a4846febc7e1c222dad71` | `37654dd24804d561442a79a7fd67cb02379efd7bd9b50573ddac4bbd62058e72` |
| Parser-state SHA-256 | `7d9bd8041d00ee3a1ce6c32d8e19efd8764108d8695f559ec91b4381ecda8d91` | `e44649d24afbd4bc335e2d38d54cea9338c211c600baef185cd7a0dee6aee4f6` |
| Serialized-state SHA-256 | `a2cf8f022069765262d4cfaf5290ccba6f5c5a42cb4aa43dd87c61311be4c10e` | `6ee0189715a31f59117a02d498adf7b8916832951c9516b83692a6a776952c69` |
| Template-registry SHA-256 | `054c93635dc5427cc01d23dce7ba1df850e28db13a4087c8629e42a1ed421ccb` | `bc4ac9e2c6ea51e712ed06c0648372d6ed800f2788d135cd5cc89d7d1047d17f` |
| Parser-manifest SHA-256 | `35400de68ede9907a4f2d3445125bdc27ae434c61dcf2f93c48b825b4000a025` | `bc2fd7df13ee231c0e9e63597e3237cd48ebb1658c4609524f04087cf49cfd66` |

Parser manifests record `test_accessed=false`, `validation_accessed=false`, and
`scientific_metrics_computed=false`. Canonical event corpora have **not** been
generated.

## 8. Completed task chain

| Stage | Purpose and verified outcome | Scientific direction changed? |
|---|---|---|
| Research Freeze v1.1 | Redirected from mandatory multi-expert fusion to measuring sequence added value; froze falsification and kill criteria | Yes |
| LIT-001 | Added reproducible 2024–2026 search log, screening ledger, prior-art and dataset-suitability matrices | No; supported the redirect |
| EFFECT-001 | Froze AP estimand, paired uncertainty framework, strongest-orderless comparator, and human margins | No |
| SCHEMA-COMPAT-001 | Verified that protocol concepts can be represented without collapsing sequence/gap/transition semantics | No |
| META-001 | Implemented parser/label-independent HDFS grouping and BGL chronology metadata contracts | No |
| SPLIT-001 initial block | Refused real generation while allocation semantics were ambiguous | No; protected protocol |
| PROTOCOL-SPLIT-CLARIFY-001 | Froze cumulative-floor boundaries, HDFS component purge, BGL split-before-window semantics, exclusions, and identities | No |
| SPLIT-001 complete | Generated/validated real split identities and activated physical TEST seals | No |
| PARSE-001 | Selected permitted normal BASE pools, fit/froze Drain3, and verified immutable restore/match behavior | No |

Each completed stage is supported by at least two of: source/tests, config/contract,
generated identity-bearing artifacts, and Git history.

## 9. Current scope

### MUST

- Frozen data identities, leakage-safe splits, and physical TEST seal.
- Frozen parser, canonical events, and deterministic sequence construction.
- Strong order-insensitive controls: unseen-event, length, total count, event-count
  vector, and required Isolation Forest comparator under the binding EFFECT-001
  addendum.
- Markov/N-gram sequential comparator.
- KT-1 ceiling, KT-2 orderless explanatory value, and KT-3 sequence destruction.
- AP, paired uncertainty, practical-effect classification, reproducibility, and
  one human final TEST.

### SHOULD

- Count/label-dependence, duplicate/collision, and robustness diagnostics.
- Secondary metrics and resource measurements after the primary contract.

### CONDITIONAL

- Transformer only if cheaper tests show meaningful long-range order signal.
- Localization and KT-4/KT-5 only after detection/order gates and prior-art checks.
- At most simple F0/F1 fusion after measurable complementarity and a corrupted
  expert control.

### FUTURE / OUTSIDE CORE

- Retrieval, RAG, Agent, regression-test recommendation, API/UI, Elasticsearch,
  broad fusion, and deployment work.

### Intentionally removed from core

- Mandatory LSTM.
- Fixed four-expert architecture.
- Normal-reference retrieval expert.
- F2–F8 fusion ladder and structured-fusion contribution claim.
- Multi-agent and observability-product expansion.

## 10. Experiments not yet run

- No unseen-event, length, count, count-vector, Isolation Forest, or Markov result.
- No KT-1, KT-2, KT-3, Transformer, localization, or fusion result.
- No AP/F1/PR curve, confidence interval, checkpoint, threshold tuning, or
  scientific TEST evaluation.
- Dataset suitability and sequence advantage remain hypotheses.

## 11. Current literature delta

Focused re-check on 2026-08-23 found no result that invalidates Protocol v1.1:

- **LITERATURE_SUPPORTED:** Landauer et al. continue to justify treating common
  log benchmarks as possible ceiling/trivial-signal cases rather than assumed
  sequence evidence ([DOI](https://doi.org/10.1145/3660768)).
- **LITERATURE_SUPPORTED:** a 2025 controlled comparative study reports that
  conclusions can change under time-ordered evaluation and preprocessing choices,
  supporting chronology and equal-pipeline controls
  ([official PDF](https://dl.ifip.org/db/conf/cnsm/cnsm2025/1571164872.pdf)).
- **LITERATURE_INFORMED_SEQLOGAD_DECISION:** a 2026 embedding study uses HDFS,
  BGL, and Thunderbird under a controlled representation comparison, but does not
  supply the count-preserving order-destruction test required by SeqLogAD; it does
  not replace KT-3 ([DOI](https://doi.org/10.3390/info17030228)).
- **LITERATURE_SUPPORTED, novelty-risk only:** LogMoE and FAME strengthen prior-art
  overlap for expert fusion/MoE and message-level localization; keeping those
  branches conditional and non-novel remains appropriate
  ([LogMoE](https://conf.researchr.org/details/ase-2025/ase-2025-papers/13/LogMoE-Lightweight-Expert-Mixture-for-Cross-System-Log-Anomaly-Detection),
  [FAME](https://arxiv.org/abs/2605.22779)).
- **INSUFFICIENT_EVIDENCE:** no newly found source establishes sequence advantage
  on the exact frozen SeqLogAD bytes and protocol. That remains an empirical
  question for KT-1–KT-3.

## 12. Claims currently allowed and forbidden

Allowed before experiments:

- The project implements verified data provenance, deterministic split identities,
  physical TEST sealing, and normal-only frozen parser artifacts.
- The project studies whether order adds practical anomaly-detection value beyond
  strong order-insensitive controls.
- Transformer/localization/fusion are conditional hypotheses, not deliverables.

Forbidden before evidence:

- “Sequence models outperform order-insensitive methods.”
- “HDFS/BGL prove behavioral sequence anomalies.”
- “SeqLogAD is novel/state of the art.”
- “SeqLogAD has a novel Transformer, fusion, localization, or mutation method.”
- Any model metric, TEST result, root-cause accuracy, or downstream performance.

## 13. ALIGN-FIX-001 remediation status

All confirmed active drift from the audit has been synchronized:

1. Active plans record SPLIT-001/PARSE-001 complete and canonical events absent.
2. `data/README.md` records real ignored split/parser artifact trees.
3. META-001 downstream status no longer points to PARSE-001 as current work.
4. `configs/default.yaml` points to frozen parser artifacts through the active
   registry.
5. Baseline config points to real split identities instead of a split TODO.
6. Isolation Forest is required by EFFECT-001 and uses seeds `42/43/44`; all
   deterministic controls are seed-not-applicable.
7. Protocol v1.1 explicitly declares EFFECT-001 and split clarification as
   binding addenda.
8. The split config explicitly labels `parser_fitted: false` and PARSE-001 as the
   historical pre-fit authorization snapshot; current completion lives in the
   active-state registry.
9. The model README matches current method scope.
10. Source license remains deliberately `OWNER_DECISION_REQUIRED`; no LICENSE was
    selected for the owner.

## 14. Next dependency-correct task

`CANONICAL-EVENT-001 — Generate canonical event artifacts using frozen Drain3
states with strict no-update semantics`.

It must remain partition-scoped, reject TEST through the ordinary path, preserve
parser state identity, isolate labels from canonical event content, and produce
no baseline/model metric. It has not started.

## 15. Validation at snapshot time

- Clean-environment dependency check: pass.
- Full test suite: 163 passed; one non-scientific pytest-cache permission warning.
- HDFS/BGL dataset verification: pass with frozen fingerprints.
- HDFS/BGL split validation and TEST status: pass; both sealed/unopened.
- HDFS/BGL parser validation/restore/frozen transform: pass.
- Ordinary TEST loader denial: pass for both datasets.
- YAML parse: 17 files valid.
- Repository-local Markdown links: 137 checked, zero broken.
- No tracked raw HDFS/BGL archive/log, checkpoint, secret pattern, or absolute
  personal path detected.
