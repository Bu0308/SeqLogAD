# 03 — Task Backlog v1.1

Statuses: `NOT_STARTED`, `IN_PROGRESS`, `HUMAN_DECISION_REQUIRED`, `BLOCKED`, `DONE`, `CONDITIONAL`, `FUTURE`, `SUPERSEDED`. Owners: `AI`, `HUMAN`, `AI_PREP/HUMAN_EXECUTE`.

## Governance and verified foundation

| Task ID | Scope | Owner | Dependencies | Status | Definition of Done |
|---|---|---|---|---|---|
| DATA-001 | MUST | AI_PREP/HUMAN_EXECUTE | — | DONE | HDFS/BGL archive/raw identities, manifests, fingerprints, and repeated verification pass |
| ENV-001 | MUST | AI | — | DONE | Python 3.12 local environment, editable package, lock, imports, CLIs, and `pip check` pass |
| SCHEMA-001 | MUST | AI | DATA-001, ENV-001 | DONE | Canonical `EventTemplate`/`LogEvent` contracts and active tests pass |
| SCHEMA-002 | MUST | AI | SCHEMA-001 | DONE | Sequence/mutation/partition/localization contracts and active tests pass; no real artifact claimed |
| PROTOCOL-001-v1.0 | HISTORICAL | AI_PREP/HUMAN_EXECUTE | — | SUPERSEDED | Preserved as approved historical protocol |
| FREEZE-v1.1 | MUST | AI_PREP/HUMAN_EXECUTE | audit approval | DONE | Protocol/config/ADR/RQs/scope/roadmap/citations are consistent and validated |
| LIT-001 | MUST | AI_PREP/HUMAN_EXECUTE | FREEZE-v1.1 | DONE | Targeted matrix, reproducible search log, citation note, dataset/baseline matrices, and conservative prior-art states completed; no novelty claim established |
| EFFECT-001 | MUST | HUMAN | LIT-001 | DONE | `delta_HDFS = delta_BGL = 0.01 AP`, `RESOURCE_FEASIBILITY_MARGIN`, pre-experiment/non-result-informed approval, estimand/comparison/bootstrap/baseline/equal-budget/KT-3 contracts frozen and tested |
| SCHEMA-COMPAT-001 | MUST | AI | FREEZE-v1.1 | DONE | Historical v1.0 and active v1.1 identities, current-artifact factory, HDFS/BGL parent provenance, KT-3 control provenance, round-trip, and TEST-label safeguards pass |

## Raw partition, parser, and sequences

| Task ID | Scope | Owner | Dependencies | Status | Definition of Done |
|---|---|---|---|---|---|
| META-001 | MUST | AI | SCHEMA-COMPAT-001 | NOT_STARTED | Minimal HDFS group/BGL chronology metadata extracted deterministically without fitted parser or label leakage |
| SPLIT-001 | MUST | AI | META-001 | NOT_STARTED | Chronological five-way partition manifest, HDFS purge report, target/realized ratios, and hashes are reproducible |
| TESTLOCK-001 | MUST | AI_PREP/HUMAN_EXECUTE | SPLIT-001 | NOT_STARTED | Routine commands cannot reveal TEST supervision/metrics; human unlock contract tested |
| PARSE-001 | MUST | AI | SPLIT-001, TESTLOCK-001 | NOT_STARTED | Drain3 fits normal `BASE_TRAIN`, freezes/restores deterministically, and transforms later legal partitions read-only |
| PARSE-002 | MUST | AI | PARSE-001 | NOT_STARTED | HDFS/BGL adapters isolate labels and emit canonical events without using source preprocessed scientific inputs |
| SEQ-001 | MUST | AI | PARSE-002 | NOT_STARTED | HDFS block sequences and BGL 100-event parents are deterministic and partition-contained |
| LEAK-001 | MUST | AI | SEQ-001 | NOT_STARTED | Group/time/duplicate/window/parser/normalization/label/TEST leakage audit passes |

## Minimal baselines and killer experiments

| Task ID | Scope | Owner | Dependencies | Status | Definition of Done |
|---|---|---|---|---|---|
| BASE-001 | MUST | AI | SEQ-001 | NOT_STARTED | Unseen-event, length, total-count, and count-vector controls have deterministic configs/tests |
| BASE-002 | MUST | AI | BASE-001, EFFECT-001 | NOT_STARTED | Isolation Forest order-insensitive feature pipeline is deterministic, normal-BASE fitted, validation-only selected, and eligible in the required primary comparator family |
| BASE-003 | MUST | AI | SEQ-001 | NOT_STARTED | Markov/N-gram smoothing/scoring and transition evidence pass tests |
| KT-1-PREP | MUST | AI | BASE-001, BASE-003, LEAK-001 | NOT_STARTED | Equal-budget ceiling experiment command/config/report schema is frozen without TEST |
| KT-1-RUN | MUST | HUMAN | KT-1-PREP, EFFECT-001 | NOT_STARTED | Human run produces immutable validation artifacts; no metric entered manually |
| KT-2-PREP | MUST | AI | BASE-001, LEAK-001 | NOT_STARTED | HDFS collision/dependence/out-of-sample analysis code and fixtures pass |
| KT-2-RUN | MUST | HUMAN | KT-2-PREP, EFFECT-001 | NOT_STARTED | Human run produces traceable validation report |
| NC-SEQ-001 | MUST | AI | SEQ-001 | NOT_STARTED | Deterministic order destruction preserves multiset/count/length/label/partition and never mutates raw data |
| KT-3-RUN | MUST | HUMAN | NC-SEQ-001, BASE-003, EFFECT-001 | NOT_STARTED | Paired original/shuffled validation report and provenance produced |
| GATE-SEQ-001 | MUST | HUMAN | KT-1-RUN, KT-2-RUN, KT-3-RUN | NOT_STARTED | Human records claim states and KEEP/REMOVE decisions for sequence/Transformer/localization branches |

## Conditional branches

| Task ID | Scope | Owner | Dependencies | Status | Definition of Done |
|---|---|---|---|---|---|
| MODEL-T-001 | CONDITIONAL | AI_PREP/HUMAN_EXECUTE | GATE-SEQ-001=OPEN_TRANSFORMER | CONDITIONAL | Lightweight Transformer answers registered long-range question; otherwise not implemented |
| LOC-001 | CONDITIONAL | AI | GATE-SEQ-001=OPEN_LOCALIZATION | CONDITIONAL | Deterministic mutation/localization pipeline and separate coordinate metrics pass |
| KT-4/5-RUN | CONDITIONAL | HUMAN | LOC-001 | CONDITIONAL | Randomization and counterfactual faithfulness controls produce immutable reports |
| COMP-001 | CONDITIONAL | AI_PREP/HUMAN_EXECUTE | at least two eligible experts | CONDITIONAL | Correlation, disagreement, overlap, oracle gain, and marginal contribution are measured |
| FUSION-F0/F1 | CONDITIONAL | AI_PREP/HUMAN_EXECUTE | COMP-001 demonstrates value | CONDITIONAL | Strongest single and simple mean are compared; no trainable fusion implied |
| KT-6-RUN | CONDITIONAL | HUMAN | FUSION-F0/F1 | CONDITIONAL | Random/corrupted expert control is evaluated |
| FUSION-F2/F8 | REMOVED_FROM_CORE | AI_PREP/HUMAN_EXECUTE | new protocol amendment | BLOCKED | Cannot start under v1.1 |

## Evaluation, report, and future work

| Task ID | Scope | Owner | Dependencies | Status | Definition of Done |
|---|---|---|---|---|---|
| EVAL-001 | MUST | AI | EFFECT-001, KT contracts | NOT_STARTED | Non-interpolated AP, paired cluster bootstrap, degenerate-resample handling, seed separation, decision regions, provenance, and report schemas pass fixture tests |
| FINAL-FREEZE-001 | MUST | HUMAN | GATE-SEQ-001, EVAL-001 | NOT_STARTED | Artifacts/configs/thresholds/claims/Git state frozen before TEST |
| FINAL-TEST-001 | MUST | HUMAN | FINAL-FREEZE-001, TESTLOCK-001 | NOT_STARTED | TEST opened once; immutable result bundle produced |
| REPORT-001 | MUST | AI_PREP/HUMAN_EXECUTE | FINAL-TEST-001 | NOT_STARTED | Claims map to run artifacts; null results and limitations retained |
| RETR/RAG/AGENT | FUTURE | AI_PREP/HUMAN_EXECUTE | completed scientific core | FUTURE | Requires separate scope/protocol |
| API/UI/ELK | FUTURE | AI | completed scientific core | FUTURE | Delivery work cannot delay core research |
