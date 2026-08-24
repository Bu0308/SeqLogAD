# Original evaluation remediation audit

> Baseline: external `SEQLOGAD_EVAL.md`, evaluated at repository commit
> `16036ddd65f1d1b116efbcda5227cf0ae6fdff94` on 2026-08-21.  
> Current state: `a1e0b8d4197d8942c36d3118be6e5015601daead`
> (`PARSE-001`) on 2026-08-23.  
> Audit verdict: **PARTIALLY ALIGNED — CORRECTIONS REQUIRED**.

> **Post-audit note (2026-08-23):** ALIGN-FIX-001 subsequently synchronized the
> active status/config findings without changing this point-in-time remediation
> record. Current execution truth is in
> [`PROJECT-CONTEXT-POST-PARSE-001.md`](PROJECT-CONTEXT-POST-PARSE-001.md) and
> `configs/active-state.yaml`. Source license remains owner-controlled.

The original evaluator reported 49/100 and recommended scientific redirection.
That historical score is not recomputed here. This audit asks whether its causes
were actually addressed using current code, tests, contracts, artifacts, hashes,
and Git history—not status prose alone.

## 1. Status vocabulary

- `RESOLVED`
- `PARTIALLY_RESOLVED`
- `MITIGATED_NOT_RESOLVED`
- `STILL_OPEN`
- `SUPERSEDED_BY_REDIRECT`
- `INTENTIONALLY_REMOVED_FROM_SCOPE`
- `NO_LONGER_APPLICABLE`
- `REGRESSION`

## 2. Full original-finding remediation matrix

| # | Original finding | Original severity/evidence | Remediation and responsible tasks | Current evidence | Status / remaining risk |
|---:|---|---|---|---|---|
| 1 | The mandatory heterogeneous-expert/fusion core conflicted with prior evidence that common log anomalies are often not sequence manifestations | High; Landauer et al. 2024 and repository V3 architecture | Research Freeze v1.1/ADR redirect replaced the core proposition with an order-added-value question; Transformer/localization/fusion became conditional | Active README, scope, RQs, protocol and backlog use `HYBRID_B_PLUS_C`; no expert/fusion implementation or result exists | `SUPERSEDED_BY_REDIRECT`; empirical sequence value remains unknown |
| 2 | HDFS/BGL risk trivial-baseline saturation: unseen-event/count-vector signals may dominate | High; external benchmark/dataset review | LIT-001 dataset-suitability matrix; mandatory orderless controls; KT-1 ceiling, KT-2 orderless explanatory value, KT-3 count-preserving sequence destruction; null result accepted | Active protocol and statistical contract pre-register the controls; HDFS/BGL are `TO_BE_TESTED` | `MITIGATED_NOT_RESOLVED`; only KT-1–KT-3 can resolve suitability on frozen bytes |
| 3 | LIT-001 was `NOT_STARTED` after architecture/fusion had already been frozen | High; old backlog/plan ordering | LIT-001 completed before model work; search log, screening/disposition ledger, prior-art, baseline, dataset and novelty-risk matrices added | Literature artifacts exist and are linked; Git commit `d28e1dc`; no model experiment has run | `RESOLVED`; focused 2026 delta adds no protocol-changing evidence |
| 4 | Scope was infeasible for a 3-credit/<3-month project: four experts, many models, F0–F8, localization and downstream platform | High; old V3 backlog/architecture | Research Freeze v1.1 cut core to orderless controls, Markov and KT-1–KT-3; Transformer/localization/simple fusion gated; RAG/Agent/UI/Elastic future | Active scope/backlog/roadmap show MUST/SHOULD/CONDITIONAL/FUTURE/REMOVED; future modules remain placeholders only | `RESOLVED`; conditional branches must remain closed until gates pass |
| 5 | Synthetic-mutation/localization plan lacked construct-validity, placebo and negative controls | Medium-high; old mutation/fusion design | Core synthetic-localization benchmark removed; KT-3 order destruction made core; localization randomization/counterfactual checks and corrupted-expert control retained only conditionally | Protocol, test plan, kill criteria and schemas describe controls; no mutation/localization experiment run | `PARTIALLY_RESOLVED`; controls are frozen, but their future implementation/validity remains untested |
| 6 | `Plan/` was ignored although ADR said plans were versioned; GitHub links broke | Technical high; `.gitignore` and 11 broken links | Repository consistency repair exposed/versioned plan artifacts and repaired links | 11 `Plan/` files tracked; 127 repository-local Markdown links checked with zero broken | `RESOLVED` |
| 7 | Docker used Python 3.11 while project contract required 3.12 | Technical medium | Environment repair changed Docker base to Python 3.12 and froze local Python/dependency contract | `Dockerfile` uses `python:3.12-slim`; project environment is Python 3.12.6 | `RESOLVED` |
| 8 | No CI, no LICENSE, and seed placeholders remained | Technical medium | CI and locked environment added; EFFECT-001 froze three-seed policy | GitHub Actions CI exists; lock/pip checks pass; one active baseline config still says `seed: TODO`; no LICENSE exists | `PARTIALLY_RESOLVED`; seed config synchronization and LICENSE decision remain |
| 9 | Held-out discipline existed only in prose; no split artifacts; split came after parser | Scientific high (P1); old task ordering | META-001 → split clarification → real SPLIT-001 before parser; deterministic partition hashes; physical human-only TEST seal | Real split manifests/hashes; ordinary loader denial; both TEST seals `SEALED/NEVER_OPENED`; PARSE manifests bind BASE only | `RESOLVED`; final TEST must still follow the future one-time human workflow |
| 10 | README sequence example could be mistaken for evidence that HDFS/BGL contain the illustrated anomaly | Claim-hygiene medium | README now labels the example conceptual and explicitly separates it from dataset evidence | Current README caveat and `TO_BE_TESTED` suitability language | `RESOLVED` |
| 11 | Stale test counts and schema/task statuses made repository state unreliable | Technical medium | Active docs stopped presenting old counts as current; tests and task chain updated through PARSE-001 | Current suite has 157 passing tests; historical files are marked superseded | `PARTIALLY_RESOLVED`; several active post-PARSE status/config pointers remain stale |
| 12 | Scientific pipeline modules were missing despite ambitious architecture | Technical/tractability; no M1 penalty at original stage | Environment, metadata, split/seal, normal-pool and parser/freeze foundations implemented in dependency order; future architecture explicitly labeled planned | Source/tests/artifacts verify foundation; canonical events, sequences and models remain honestly not implemented | `PARTIALLY_RESOLVED`; expected work remains, but no implementation status is exaggerated |

## 3. P1–P8 reassessment

| Penalty | Original state | Current state | Evidence and interpretation |
|---|---|---|---|
| P1 — held-out leakage risk | Applied/major risk: no physical split or seal | `RESOLVED` | Split precedes parser; deterministic partition identities; ordinary TEST denial; open/unlock counters zero; no TEST metrics |
| P2 — metric misuse | Not applied; metric plan already sound | `RESOLVED / STRONGER` | EFFECT-001 freezes AP difference, strongest-orderless comparator, paired uncertainty, practical margins and interpretation before results |
| P3 — benchmark saturation | Applied | `MITIGATED_NOT_RESOLVED` | The risk is now the core falsifiable question; KT-1–KT-3 are mandatory and Transformer remains closed; no result yet |
| P4 — unfalsifiable contribution | Not applied, but no project-level kill criteria | `RESOLVED` | KC1–KC6 permit sequence, Transformer, localization, fusion, and novelty claims to fail/close |
| P5 — weak hypothesis discipline | Not applied | `RESOLVED` | Negative/equivalent/harmful/inconclusive outcomes are valid; claims map to explicit tests and gates |
| P6 — missing recent literature map | Applied | `RESOLVED` | Reproducible 2024–2026 search log, screening rules, retained/rejected ledger and prior-art matrices exist; current delta check found no redirect-changing source |
| P7 — core bet contradicted by evidence | Applied | `SUPERSEDED_BY_REDIRECT` | Mandatory fusion proposition was replaced by controlled order-added-value RQ; no active artifact restores four experts as core |
| P8 — reproducibility/transparency | Partially applied | `PARTIALLY_RESOLVED` | Clean Python 3.12 environment, lock, CI, hashes, split/seal/parser artifacts and tests exist; one seed TODO, stale status pointers and missing LICENSE remain |

## 4. Original high-severity findings

### P3 — benchmark saturation and suitability

LIT-001 did not “prove” HDFS/BGL suitable. It established that suitability is
contested and dataset variants/protocols cannot be conflated. The project now uses
HDFS/BGL to test whether order adds value beyond strong orderless controls. KT-1,
KT-2 and KT-3 precede any Transformer gate. Sequence advantage is a hypothesis,
not an assumption. Status: `MITIGATED_NOT_RESOLVED` until those experiments run.

### P6 — recent literature map

The repository contains a dated search log, 36 query records, inclusion/exclusion
criteria, duplicate/snowballing procedure, retained/rejected dispositions, a
prior-art matrix, dataset-suitability matrix, baseline matrix, and citation notes.
A focused 2026-08-23 check found newer representation, MoE, calibration, and
localization work, but none supplies a result on the exact SeqLogAD bytes/protocol
that displaces KT-1–KT-3. Status: `RESOLVED`; prior-art monitoring continues.

### P7 — contradicted core bet

Original proposition: heterogeneous experts plus structured fusion are the central
contribution. Current question: measure how much order adds beyond strong
order-insensitive baselines. Retrieval/RAG/Agent are future consumers; Transformer,
localization and simple fusion are conditional. Status:
`SUPERSEDED_BY_REDIRECT`, with no detected regression.

## 5. Original scorecard dimensions — qualitative reassessment

No new numeric score is assigned.

| Dimension | Original → current | Why |
|---|---|---|
| T1 — problem/reason | Weakly justified architecture → precise falsifiable order-value question | The question now targets the dataset-ceiling criticism directly |
| T2 — world positioning | Major prior-art gap → materially improved | LIT-001 and the current delta map prior evidence without novelty claims |
| T3 — claim hygiene | Strong but occasionally ambiguous → strong | Current docs separate implemented, planned, hypothesis, protocol decision and result; minor stale statuses remain |
| T4 — experimental design | Ambitious but poorly gated → strong pre-registered design | Negative controls, kill criteria, equal legal scope, physical TEST seal and effect margins now exist |
| T5 — measurement validity | Threatened by dataset suitability → improved but unresolved | Validity is now measured by KT-1–KT-3; no empirical evidence yet |
| T7 — reproducibility/transparency | Partial → materially improved | Environment lock, CI, manifests, hashes, split/parser identities and 157 tests; LICENSE/status/seed cleanup remains |
| T12 — tractability/opportunity cost | Infeasible → substantially improved | Core scope is small and conditional branches have explicit opening gates |

## 6. Original technical/repository defects

| Defect | Current state | Evidence / remaining action |
|---|---|---|
| Plan ignored vs ADR | Resolved | 11 tracked Plan files |
| Broken Plan links | Resolved | 127 local links checked; zero broken |
| Docker Python mismatch | Resolved | Docker and project require Python 3.12 |
| CI absent | Resolved | GitHub Actions workflow exists |
| LICENSE absent | Still open | No LICENSE file; human must choose a license |
| Stale test counts | Resolved in active docs | 157 tests currently pass; old counts remain only in historical provenance |
| Stale task/status text | Partially resolved | Current backlog chain is correct, but plan/data/config pointers listed in the context snapshot are stale |
| Seed TODOs | Partially resolved | EFFECT-001 freezes three seeds; active baseline YAML still contains one TODO |
| Split only on paper | Resolved | Real manifests, partition hashes and validation artifacts exist |
| TEST not physically sealed | Resolved | Seal bound to TEST hash; ordinary loader denial; no grants/audit records |
| Parser placeholder | Resolved | Frozen Drain3 states, registries, manifests, restore/match tests exist |
| Pipeline order contradiction | Resolved | Metadata → split/seal → BASE normal filter → parser fit/freeze |
| Negative controls absent | Resolved at contract level | KT-3 and conditional localization/fusion controls frozen; not yet run |
| Scope explosion | Resolved | Mandatory multi-expert/fusion/downstream work removed or gated |
| Stale future placeholders | No core regression | Placeholders remain labeled future; Isolation Forest status in model README needs synchronization |

## 7. Redirect task chain and evidence classes

| Stage | Blocker addressed | Evidence class 1 | Evidence class 2 | Intentionally not done |
|---|---|---|---|---|
| Research Freeze v1.1 | Invalid central bet/scope | Active protocol/RQs/ADR | Backlog/roadmap/config | No experiment or model |
| LIT-001 | Missing recent prior art | Search log/citation ledger | Prior-art and suitability matrices/Git commit | No novelty conclusion |
| EFFECT-001 | Undefined practical relevance | Statistical contract/config | Tests/ADR/human-approval record | No result-informed tuning |
| SCHEMA-COMPAT-001 | Protocol/schema ambiguity | Compatibility records/config | Schema tests/source | No scientific corpus |
| META-001 | Missing parser-free split identities | Metadata source/tests | Dataset contracts/Git commit | No labels/parser/templates |
| Split initial block | Ambiguous allocation semantics | Blocked status/history | Clarification issue evidence | No real split until clarified |
| Split clarification | HDFS/BGL boundary ambiguity | Binding contract/YAML | Tests/citation note | No class balancing |
| SPLIT-001 | Held-out only on paper | Real artifacts/hashes | Validator/seal tests/Git commit | No TEST labels/metrics |
| PARSE-001 | Parser fit leakage/state ambiguity | Parser source/tests | Real manifests/hashes/Git commit | No canonical corpus/baseline/model |

## 8. Current literature delta and source discipline

- `LITERATURE_SUPPORTED`: common benchmark suitability remains contested
  ([Landauer et al.](https://doi.org/10.1145/3660768)).
- `LITERATURE_SUPPORTED`: chronological/preprocessing choices can materially alter
  comparative conclusions
  ([CNSM 2025 official paper](https://dl.ifip.org/db/conf/cnsm/cnsm2025/1571164872.pdf)).
- `LITERATURE_INFORMED_SEQLOGAD_DECISION`: a 2026 embedding comparison supports
  controlled representation studies but does not test count-preserving order
  destruction ([DOI](https://doi.org/10.3390/info17030228)).
- `LITERATURE_SUPPORTED` as novelty risk: LogMoE, FAME and FaithLog occupy nearby
  expert-mixture/localization territory; those branches must remain conditional
  and cannot be sold as generic novelty
  ([LogMoE](https://conf.researchr.org/details/ase-2025/ase-2025-papers/13/LogMoE-Lightweight-Expert-Mixture-for-Cross-System-Log-Anomaly-Detection),
  [FAME](https://arxiv.org/abs/2605.22779),
  [FaithLog](https://conf.researchr.org/details/ase-2025/ase-2025-nier-track/1/Walk-the-Talk-Is-Your-Log-based-Software-Reliability-Maintenance-System-Really-Relia)).
- `INSUFFICIENT_EVIDENCE`: no source found proves sequence value on the exact
  SeqLogAD dataset bytes and frozen pipeline.

## 9. Final determination

SeqLogAD is still implementing the corrected plan created in response to the
original evaluation. It has **not** drifted back to mandatory four-expert fusion,
Transformer, localization, or downstream RAG/Agent scope.

The verdict is only `PARTIALLY ALIGNED` because active status/config artifacts
contain post-PARSE drift and repository hygiene still has an unresolved LICENSE
decision and baseline seed placeholder. These are correction tasks, not a
scientific-direction regression.

The next single task is `ALIGN-FIX-001`: synchronize active post-PARSE status and
machine-readable config pointers without changing frozen scientific contracts.
Canonical event generation using the frozen parser follows only after that small
consistency checkpoint.
