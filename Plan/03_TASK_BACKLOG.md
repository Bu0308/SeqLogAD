# 03 — Task Backlog V3

Status values: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `SUPERSEDED`. Owners: `AI`, `HUMAN`, `AI_PREP/HUMAN_EXECUTE`.

## Foundation and governance

| Task ID | Priority | Owner | Dependencies | Status | Definition of Done |
|---|---|---|---|---|---|
| PLAN-001 | P0 | AI | — | DONE | Original scope, priorities, and acceptance contract documented |
| REPRO-001 | P0 | AI | PLAN-001 | DONE | Initial config/seed/output/data-integrity conventions documented |
| DATA-001 | P0 | AI_PREP/HUMAN_EXECUTE | PLAN-001 | DONE | HDFS/BGL canonical archives, extracted bytes, manifests, and fingerprints independently verified |
| DOC-V3-001 | P0 | AI | V3 direction | DONE | Active docs/plans synchronized; history preserved; Git-readiness audit executed |
| ADR-V3-001 | P0 | AI | V3 direction | DONE | V3 scope and superseding decisions recorded without deleting old ADRs |
| LIT-001 | P0 | AI_PREP/HUMAN_EXECUTE | ADR-V3-001 | NOT_STARTED | Prior-art matrix completed and every contribution candidate classified |
| ENV-001 | P0 | AI | ADR-V3-001 | NOT_STARTED | PyArrow/package/import/Drain3 issues resolved and editable-install smoke test passes |
| REPRO-V3-001 | P0 | AI | ENV-001 | NOT_STARTED | Five-way split, artifact IDs, package lock, run metadata, and human-run commands validated |

## Data, schemas, parsing, and sequences

| Task ID | Priority | Owner | Dependencies | Status | Definition of Done |
|---|---|---|---|---|---|
| SCHEMA-001 | P0 | AI | DATA-001, ENV-001 | NOT_STARTED | Canonical LogEvent/EventTemplate schemas and tests approved |
| SCHEMA-002 | P0 | AI | SCHEMA-001 | NOT_STARTED | EventSequence, MutationRecord, and partition schemas distinguish token/gap/transition coordinates |
| SCHEMA-003 | P0 | AI | SCHEMA-002 | NOT_STARTED | ExpertEvidence and structured-claim schemas validated with unsupported fields optional |
| PARSE-001 | P0 | AI | SCHEMA-001 | NOT_STARTED | Drain3 lifecycle supports fit/freeze/transform and deterministic state artifact |
| PARSE-002 | P0 | AI | PARSE-001 | NOT_STARTED | HDFS adapter maps raw lines to canonical events without label leakage |
| PARSE-003 | P0 | AI | PARSE-001 | NOT_STARTED | BGL adapter preserves inline labels separately from model inputs |
| SEQ-001 | P0 | AI | PARSE-002, SCHEMA-002 | NOT_STARTED | HDFS block grouping is deterministic and malformed IDs are audited |
| SEQ-002 | P0 | AI | PARSE-003, SCHEMA-002 | NOT_STARTED | BGL chronology/window policy is deterministic and boundary-safe |
| SEQ-003 | P0 | AI | SEQ-001, SEQ-002 | NOT_STARTED | Five-way group-aware chronological split manifest created before overlapping windows |
| LEAK-001 | P0 | AI | SEQ-003 | NOT_STARTED | Parser/template/group/window/padding/threshold/reference leakage audit passes |
| MUT-001 | P0 | AI | SEQ-003, SCHEMA-002 | NOT_STARTED | Missing/extra/reorder/repeat mutations are deterministic and train-only |
| MUT-002 | P0 | AI | MUT-001 | NOT_STARTED | Token, gap, and transition ground truth and provenance tests pass |

## Baselines and heterogeneous experts

| Task ID | Priority | Owner | Dependencies | Status | Definition of Done |
|---|---|---|---|---|---|
| BASE-001 | P0 | AI | SEQ-003 | NOT_STARTED | Frequency baseline and common score interface implemented/tested |
| BASE-002 | P0 | AI | BASE-001 | NOT_STARTED | N-gram/backoff Markov expert produces transition evidence and deterministic scores |
| BASE-003 | P0 | AI | SEQ-003 | NOT_STARTED | Isolation Forest feature families and explicit feature evidence implemented/tested |
| BASE-004 | P0 | AI | SEQ-003 | NOT_STARTED | LSTM neural baseline source, masks, checkpoint format, and training handoff tested |
| MODEL-A-001 | P0 | AI | SCHEMA-003, MUT-002 | NOT_STARTED | Lightweight causal SeqLogAD-T forward path and heads pass shape/mask tests |
| LOSS-A-001 | P0 | AI | MODEL-A-001 | NOT_STARTED | A0–A3 loss variants pass analytical/sanity tests without training |
| RETR-D-001 | P0 | AI | SEQ-003, SCHEMA-003 | NOT_STARTED | Edit/LCS/n-gram/transition normal-reference expert returns IDs and structural diffs |
| RETR-D-002 | P1 | AI | RETR-D-001, LIT-001 | NOT_STARTED | Dense retrieval added only if evidence justifies scope |
| TRAIN-BASE-001 | P0 | HUMAN | BASE-001/002/003/004 | NOT_STARTED | Human runs B0–B3 with traceable artifacts and locked configs |
| TRAIN-A-001 | P0 | HUMAN | MODEL-A-001, LOSS-A-001 | NOT_STARTED | Human runs A0–A3; checkpoints/metrics retained without TEST tuning |

## Calibration, complementarity, and fusion

| Task ID | Priority | Owner | Dependencies | Status | Definition of Done |
|---|---|---|---|---|---|
| CAL-001 | P0 | AI | SCHEMA-003 | NOT_STARTED | Validation-only calibration interfaces and ECE/Brier/NLL metrics tested |
| EVID-001 | P0 | AI | Experts, SCHEMA-003 | NOT_STARTED | Frozen expert predictions serialize/reload with sequence/model/artifact identity |
| COMP-001 | P0 | AI | EVID-001 | NOT_STARTED | Correlation/disagreement/error-overlap/oracle/localization/marginal metrics tested |
| COMP-002 | P0 | HUMAN | COMP-001, human expert runs | NOT_STARTED | Human reviews complementarity report and records keep/remove/demote decision per expert |
| FUSION-001 | P0 | AI | CAL-001, COMP-001 | NOT_STARTED | F0–F3 strongest/simplest fusion baselines implemented/tested |
| FUSION-002 | P0 | AI | FUSION-001 | NOT_STARTED | F4–F6 logistic/MLP/gating baselines implemented/tested |
| FUSION-003 | P0 | AI | LIT-001, FUSION-002 | NOT_STARTED | F7 evidential baseline included or documented technically inapplicable |
| FUSION-004 | P0 | AI | COMP-002, FUSION-002 | NOT_STARTED | F8 structured claim alignment/fusion and minimal loss pass contract tests |
| FUSION-005 | P1/P0-gated | AI | LIT-001, COMP-002, FUSION-004 | BLOCKED | Redundancy-aware term proceeds only after prior-art and measurable-need gates |
| ABSTAIN-001 | P1 | AI | CAL-001, FUSION-004 | NOT_STARTED | Conflict-aware abstention evaluated through risk/coverage without collapse-prone loss |
| TRAIN-FUSION-001 | P0 | HUMAN | FUSION-001–004 | NOT_STARTED | Human runs F0–F8 on frozen evidence and records full artifacts |

## Evaluation and downstream

| Task ID | Priority | Owner | Dependencies | Status | Definition of Done |
|---|---|---|---|---|---|
| EVAL-001 | P0 | AI | MUT-002 | NOT_STARTED | Detection/localization/calibration/latency/statistical metric code tested |
| EVAL-002 | P0 | AI_PREP/HUMAN_EXECUTE | Human runs, EVAL-001 | NOT_STARTED | Paired CIs/significance and RQ1–RQ4 tables generated from real artifacts |
| TESTLOCK-001 | P0 | HUMAN | EVAL-002, frozen protocol | NOT_STARTED | Human executes final TEST once and archives immutable result bundle |
| DOWNSTREAM-001 | P1 | AI | TESTLOCK-001 | NOT_STARTED | Frozen score-only/strongest/fused evidence conditions created |
| DOWNSTREAM-002 | P1 | AI | DOWNSTREAM-001 | NOT_STARTED | Evidence verifier and read-only investigation contracts tested |
| DOWNSTREAM-003 | P1 | AI | DOWNSTREAM-002 | NOT_STARTED | Structured regression-test recommendation and rubric tested |
| DOWNSTREAM-004 | P1 | HUMAN | DOWNSTREAM-003 | NOT_STARTED | Human evaluates grounding/test quality for RQ5 |
| API-001 | P1 | AI | Frozen core artifacts | NOT_STARTED | Thin API exposes versioned read-only artifacts without changing scientific state |
| UI-001 | P1 | AI | API-001 | NOT_STARTED | Demo distinguishes observed results from planned capabilities |
| ELK-001 | P1/P2 | AI | Stable storage interface | NOT_STARTED | Elasticsearch adapter works without expert/fusion rewrites |
| DOC-FINAL-001 | P0 | AI_PREP/HUMAN_EXECUTE | TESTLOCK-001, DOWNSTREAM optional | NOT_STARTED | Final report, README, limitations, negative results, and CV/interview artifacts approved |
