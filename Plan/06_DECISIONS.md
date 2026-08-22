# 06 — Architecture Decision Log

## ADR-001 — Project positioning

- **Date:** 2026-08-07
- **Decision:** Position the system as a sequence-aware AI investigation and QA layer on top of observability infrastructure.
- **Alternatives:** Build an ELK replacement; build an independent log search engine.
- **Reason:** The research contribution is sequence intelligence, evidence verification and QA automation, not storage/search infrastructure.
- **Impact:** Elasticsearch remains an optional backend; detector, retrieval and agent layers remain the primary scope.

## ADR-002 — HDFS and BGL as core datasets

- **Date:** 2026-08-07
- **Decision:** Use HDFS and BGL for the 8-week core evaluation.
- **Alternatives:** Add OpenStack immediately; use only one dataset.
- **Reason:** Two datasets provide cross-dataset evidence while remaining feasible for one developer.
- **Impact:** OpenStack is P2 and does not block the MVP.

## ADR-003 — Drain3 parser with frozen train state

- **Date:** 2026-08-07
- **Decision:** Use Drain3 and freeze parser state after train fitting.
- **Alternatives:** Write a custom parser; let the parser adapt over the full dataset.
- **Reason:** Drain3 is an established baseline and frozen state reduces parser leakage.
- **Impact:** Unseen templates require explicit OOV handling and audit reporting.

## ADR-004 — Parquet/local storage before Elasticsearch

- **Date:** 2026-08-07
- **Decision:** Use Parquet and local files for the initial experiment path.
- **Alternatives:** Require Elasticsearch from day one.
- **Reason:** Local reproducibility and lower setup risk are more important for Phase 1.
- **Impact:** Storage/retrieval interfaces must be backend-agnostic so Elasticsearch can be added later.

## ADR-005 — LangGraph single agent

- **Date:** 2026-08-07
- **Decision:** Use one LangGraph agent with explicit state and read-only tools.
- **Alternatives:** Multi-agent architecture; OpenAI Agents SDK; free-form chatbot loop.
- **Reason:** A graph makes rounds, budgets, tools and termination observable and testable.
- **Impact:** Multi-agent is future work; model provider remains behind an adapter.

## ADR-006 — LSTM P0, Transformer P1

- **Status:** SUPERSEDED by ADR-015 on 2026-08-14; retained as historical context.
- **Date:** 2026-08-07
- **Decision:** Make LSTM the core neural sequence detector and Transformer an optional comparison.
- **Alternatives:** Start with Transformer; implement both before baselines.
- **Reason:** Baselines and a working sequence detector must exist before model expansion.
- **Impact:** RQ1 can be answered with LSTM if time is limited; Transformer results are an enhancement.

## ADR-007 — Evidence IDs and insufficient-evidence status

- **Date:** 2026-08-07
- **Decision:** Every evidence item has a stable ID and hypotheses can return `insufficient_evidence`.
- **Alternatives:** Let the LLM produce free-form citations and always select a root cause.
- **Reason:** Unsupported RCA conclusions are a primary research and safety risk.
- **Impact:** Structured schemas, resolver checks and verifier tests are mandatory.

## ADR-008 — No production actions

- **Date:** 2026-08-07
- **Decision:** MVP agent is read-only and has no arbitrary shell or remediation tools.
- **Alternatives:** Add restart/deployment tools; execute generated code automatically.
- **Reason:** The project is an investigation and QA layer, not an autonomous remediation system.
- **Impact:** Optional test execution is sandbox/staging-only future work.

## ADR-009 — Chronological evaluation is the default

- **Date:** 2026-08-07
- **Decision:** Dataset splits and primary evaluation use chronological train/validation/test partitions.
- **Alternatives:** Random split; mixed temporal cross-validation without a fixed holdout.
- **Reason:** Random splitting can leak future behavior and overstate anomaly performance.
- **Impact:** Parser fitting, vocabulary, thresholds, retrieval tuning and sequence boundaries must respect split scope.

## ADR-010 — Metrics are pipeline-generated

- **Date:** 2026-08-07
- **Decision:** Research metrics must be produced by evaluation scripts and stored with experiment metadata.
- **Alternatives:** Manually copy metrics into reports; use notebooks as the only source of results.
- **Reason:** Manual transcription weakens reproducibility and makes comparison errors harder to detect.
- **Impact:** Future reports reference structured outputs under experiment-specific directories.

## ADR-011 — SHA-256 defines local file integrity

- **Date:** 2026-08-07
- **Decision:** Use streaming SHA-256 for every local raw file and manifest identity; use a source-published MD5 only to check the downloaded archive when that is the source's available digest.
- **Alternatives:** Use MD5 throughout; rely on filename/size; load whole files into memory.
- **Reason:** SHA-256 provides content-sensitive identity with a simple standard-library implementation suitable for large files.
- **Impact:** Manifests store SHA-256; archive config may preserve a separately labeled source MD5.

## ADR-012 — Raw benchmark bytes stay outside Git

- **Date:** 2026-08-07
- **Decision:** Ignore raw archives/logs and generated bulk data while committing acquisition configs, manifests, documentation and synthetic test fixtures.
- **Alternatives:** Commit public benchmark copies; use Git LFS immediately.
- **Reason:** Acquisition provenance, licensing review and repository size are safer and more reproducible than arbitrary copied bytes.
- **Impact:** A fresh checkout needs an explicit acquisition/verification step before data processing.

## ADR-013 — Dataset identity excludes modification time

- **Date:** 2026-08-07
- **Decision:** Compute a dataset fingerprint from sorted repository-relative paths and their SHA-256 values.
- **Alternatives:** Include `mtime`; hash manifest JSON including runtime timestamps; use a manually assigned label only.
- **Reason:** Modification time is machine-dependent and can change without changing scientific content.
- **Impact:** Same paths and bytes reproduce the same identity; changed content or path produces a new fingerprint.

## ADR-014 — V3 multi-model research direction

- **Date:** 2026-08-14
- **Status:** ACCEPTED; supersedes active V1/V2 research priorities for future work.
- **Decision:** Center SeqLogAD on heterogeneous expert value, complementarity, structured evidence fusion, reliability, and downstream regression-test recommendation.
- **Alternatives:** Continue the single-primary-detector roadmap; make RAG/agent the primary contribution.
- **Reason:** V3 creates a measurable research question around complementary inductive biases and evidence reliability.
- **Impact:** RQ1–RQ5 and the V3 critical path replace the old four-layer research priority while preserving downstream goals.

## ADR-015 — Transformer primary contextual expert; LSTM baseline

- **Date:** 2026-08-14
- **Status:** ACCEPTED; supersedes ADR-006.
- **Decision:** Use SeqLogAD-T, a lightweight causal Transformer, as Expert A; retain LSTM as a strong neural baseline.
- **Alternatives:** Keep LSTM as the only P0 neural detector; implement Transformer only after downstream RAG.
- **Reason:** The V3 hypothesis explicitly studies long-range contextual/order evidence while still requiring historical neural comparison.
- **Impact:** Transformer source/loss work is P0 after baselines and data contracts; no result or superiority is assumed.

## ADR-016 — Four-expert architecture is provisional

- **Date:** 2026-08-14
- **Status:** ACCEPTED.
- **Decision:** Begin with Transformer, Markov/N-gram, Isolation Forest, and normal-reference retrieval experts, subject to a mandatory complementarity gate.
- **Alternatives:** Always retain all experts; choose experts only by standalone accuracy.
- **Reason:** Multi-model complexity is justified only by measurable unique signal.
- **Impact:** Redundant experts are removed or demoted before final fusion training.

## ADR-017 — Fusion novelty remains unverified

- **Date:** 2026-08-14
- **Status:** ACCEPTED.
- **Decision:** Treat Structured Evidence Consensus Fusion as a working name and proposed design, not a novel method, until `LIT-001` is complete.
- **Alternatives:** Claim novelty from the combination; defer literature review until after experiments.
- **Reason:** Ensemble, evidential, redundancy, and conflict-aware fusion have substantial prior art.
- **Impact:** Contribution language uses known component, adaptation, potential contribution, or high prior-art risk.

## ADR-018 — Human owns empirical training and final evaluation

- **Date:** 2026-08-14
- **Status:** ACCEPTED.
- **Decision:** AI/Codex prepares implementation/tests/configs/commands; the human researcher executes training, tuning, checkpoint selection, ablations, fusion training, and final TEST.
- **Alternatives:** Allow autonomous training and result selection.
- **Reason:** Human control protects scientific intent, compute use, test isolation, and interpretation.
- **Impact:** Future experiment rows remain `NOT_RUN` until backed by human-executed artifacts; AI cannot fabricate metrics.

## ADR-019 — Accurate supervision terminology

- **Date:** 2026-08-14
- **Status:** ACCEPTED.
- **Decision:** Describe the core as normal-only self-supervised sequential anomaly detection with synthetic supervision for localization and fusion.
- **Alternatives:** Call the entire pipeline pure unsupervised.
- **Reason:** Synthetic mutation positions and fusion labels constitute supervision even when real anomaly labels are withheld from training.
- **Impact:** Real anomaly labels remain evaluation-only unless an experiment explicitly changes and documents the protocol.

## ADR-020 — Separate localization coordinate systems

- **Date:** 2026-08-14
- **Status:** ACCEPTED.
- **Decision:** Represent token, gap, and transition localization separately.
- **Alternatives:** Use one token vector for all anomaly types.
- **Reason:** A missing event has no observed token position and is naturally located at an insertion gap.
- **Impact:** Schemas, masks, losses, metrics, mutations, and fusion claim alignment become coordinate-family aware.

## ADR-021 — Staged training is the default

- **Date:** 2026-08-14
- **Status:** ACCEPTED.
- **Decision:** Fit experts independently, freeze them, generate evidence, calibrate, measure complementarity, and then fit fusion.
- **Alternatives:** End-to-end joint expert/fusion training from the start.
- **Reason:** Staging improves attribution, reproducibility, ablation validity, and compute control.
- **Impact:** Partial unfreezing is a separately justified P1 experiment.

## ADR-022 — Conflict is not an official confidence-collapse loss

- **Date:** 2026-08-14
- **Status:** ACCEPTED.
- **Decision:** Use conflict as a fusion feature, verifier signal, abstention signal, and evaluation variable; exclude the proposed `confidence × conflict` term from the core loss.
- **Alternatives:** Directly penalize confidence by conflict magnitude.
- **Reason:** The simple product admits trivial low-confidence behavior.
- **Impact:** Any trainable conflict objective requires a separate proper selective-risk formulation and ablation.

## ADR-023 — Research plans return to version control

- **Date:** 2026-08-14
- **Status:** ACCEPTED.
- **Decision:** Track `Plan/`, including historical plans and the V3 master plan.
- **Alternatives:** Keep all planning artifacts local-only.
- **Reason:** The current Git-readiness contract requires reviewable research scope, ownership, status, and decision history.
- **Impact:** Raw data remains ignored, while plans are visible for human review and future commits.

## ADR-024 — Freeze PROTOCOL-001 scientific data and evaluation contract

- **Date:** 2026-08-20
- **Status:** ACCEPTED; supersedes the unresolved split ratios and label-use wording in ADR-019 while preserving its supervision terminology.
- **Decision:** Freeze the raw-chronological five-way split as `60/10/10/10/10`; allow labels only for controlled normal-pool filtering and validation/evaluation, never as model inputs or base self-supervised loss; seal TEST until one human-executed final command; preserve HDFS block/session atomicity with boundary purge; use non-overlapping 100-event BGL parent windows; fit Drain3 on normal `BASE_TRAIN` then freeze; separate synthetic localization from real-anomaly evaluation; require partition-separated expert/fusion development, three stochastic seeds, PR-AUC as primary detection metric, complementarity-based `KEEP/DEMOTE/REMOVE`, F0 strongest-single comparison, and downstream-only RAG/Agent.
- **Alternatives:** Leave ratios open; use random/stratified splitting; fit the parser globally; tune from TEST; treat synthetic and real localization as one result; always retain four experts; require F8 to win.
- **Reason:** A frozen access and evaluation contract is required before schema, parsing, sequence, mutation, or model implementation can produce scientifically interpretable artifacts.
- **Impact:** `docs/research-protocol.md` and `configs/protocols/protocol-v1.yaml` are the source of truth. Behavioral changes require a new protocol version, decision entry, and citation/provenance update before affected results are inspected.

## ADR-025 — Scientific redirect, scope reduction, and kill criteria

- **Date:** 2026-08-21
- **Status:** ACCEPTED; supersedes the active research priorities in ADR-014 through ADR-017, ADR-021, and the fusion-specific portions of ADR-022/ADR-024. Historical decisions remain preserved.
- **Context:** The V3 plan made a provisional four-expert architecture, Transformer, localization, and F0–F8 fusion central before proving that the exact HDFS/BGL protocol contains non-trivial sequence signal. Repository audit also found missing negative controls, TEST sealing only at contract level, significant overlap with recent fusion/localization prior art, and a scope incompatible with a 3-credit project under three months.
- **Evidence:** Verified dataset-integrity artifacts are sound. Literature raises dataset-suitability and prior-art risks, but no SeqLogAD killer experiment has run. Therefore risks are confirmed while exact empirical outcomes remain unknown.
- **Decision:** Adopt `HYBRID_B_PLUS_C`: Option B (measure sequence added value beyond strong order-insensitive baselines) is the core; Option C (localization faithfulness) is conditional. Preserve HDFS/BGL, `60/10/10/10/10`, normal-only Drain3 fit, PR-AUC, three seeds, label isolation, and human-only final TEST. Register KT-1–KT-6 and KC-1–KC-6 before experiments.
- **Consequences:** LSTM and normal-reference retrieval leave the core. Transformer requires a sequence-signal/long-range gate. Localization requires sequence and faithfulness gates. Four experts and F2–F8 fusion leave the frozen core; F0/F1 are conditional after measured complementarity. RAG/Agent/API/UI/Elasticsearch become future-only. Negative/null results are accepted.
- **Rejected alternatives:** Blindly retain V3; switch to BGL-only; replace datasets immediately; implement fusion first; infer dataset unsuitability solely from prior work.
- **Revisit conditions:** Dataset expansion (Option A) may open only after KT-1–KT-3 demonstrate insufficient sequence evidence on both verified datasets, LIT-001 identifies a defensible candidate, acquisition/provenance is approved, and a protocol amendment precedes access or experiments.
- **Impact:** Protocol v1.1, active RQs, scope, architecture, backlog, roadmap, and experiment tracker replace V3 as future-work sources of truth. No existing dataset/schema artifact or experimental result is invalidated because no scientific run exists.

## ADR-026 — EFFECT-001 statistical comparison family

- **Date:** 2026-08-22
- **Status:** ACCEPTED — HUMAN APPROVED.
- **Context:** LIT-001 found no transferable universal numerical AP margin. Protocol v1.1 requires the estimand, practical-effect bounds, uncertainty method, comparator selection, multiplicity, and KT-3 rule to be fixed before any baseline/killer experiment or TEST access.
- **Decision:** Freeze separate HDFS/BGL estimands `Delta_AP_d = AP_sequence,d - AP_strongest_orderless,d`; non-interpolated Average Precision; one validation-selected primary contrast per dataset; a required orderless family containing unseen-event, length, total-count, count-vector, and Isolation Forest; equal 12-config family budgets; seeds `42/43/44` for stochastic methods; and a 95% paired cluster-percentile bootstrap with 10,000 valid replicates, seed `42`, HDFS block/session units, BGL 100-event parent-window units, deterministic degenerate-redraw rules, and gain/equivalence/harm/inconclusive outcomes. KT-3 reuses the dataset margin and bootstrap.
- **Human approval:** On 2026-08-22, the researcher fixed `delta_HDFS = delta_BGL = 0.01 AP` under `RESOURCE_FEASIBILITY_MARGIN`. Approval source is `HUMAN_RESEARCHER`, timing is `PRE_EXPERIMENT`, and `result_informed = false`. The common margin simplifies the rule; dataset conclusions remain independent.
- **Multiple comparisons:** No correction for one separately interpreted primary contrast per dataset; no pooled/disjunctive claim. Secondary comparisons remain descriptive and require a pre-result amendment before confirmatory use.
- **Alternatives:** Use zero as the meaningful bound; copy a number from unrelated literature; pool datasets; select the strongest comparator on TEST; event-level IID bootstrap; report only point AP; add baselines after seeing outcomes.
- **Reason:** The selected family is falsifiable, dependency-aware, equal-budget, and prevents outcome-driven margins/comparators while preserving valid negative and inconclusive results.
- **Consequence:** `configs/protocols/effect-001.yaml` is `FROZEN_HUMAN_APPROVED` and the statistical prerequisite is complete. It does not itself authorize split execution, parser fitting, baseline/Markov runs, KT-1/2/3, bootstrap, or TEST access; those remain separately gated. The `0.01 AP` margins cannot change after outcomes. Versioned Protocol v1.1 is preserved; EFFECT-001 is its anticipated statistical addendum.
- **Evidence:** `docs/references/EFFECT-001-citations.md`; all empirical statuses remain `NOT_RUN`.

## ADR-027 — Explicit Protocol-v1.1 schema compatibility and separate KT-3 provenance

- **Date:** 2026-08-22
- **Status:** ACCEPTED.
- **Context:** SCHEMA-002 constrained `PartitionIdentity.protocol_version` to `1.0` even though Protocol v1.1 governs all future artifacts. Its synthetic `MutationRecord` also could not represent EFFECT-001 KT-3 because it requires a normal source, localization targets, and a non-noop anomaly mutation.
- **Decision:** Use explicit-version compatibility: valid historical `1.0` and active `1.1` identities parse, the field has no implicit default, and all new artifacts use a factory pinned to `1.1`. Active BGL parents are exactly 100 events; historical explicit-v1.0 residual records remain readable, while active trailing 1–99 event ranges use an exclusion disposition instead of becoming sequences. Add a separate `SequenceDestructionRecord` for KT-3 that binds source/parent/partition/split identity, seed, ordered and multiset hashes, equal lengths, applied/no-op status, and label-access safeguards.
- **Alternatives:** Globally replace every `1.0`; accept an unrestricted version string; silently default to `1.1`; reuse `MutationRecord`; discard retained no-op controls.
- **Reason:** The chosen patch preserves historical provenance, prevents new artifacts from silently claiming v1.0, matches Protocol v1.1/EFFECT-001, and avoids conflating synthetic anomaly localization with an order-destruction control.
- **Consequence:** SCHEMA-COMPAT-001 is complete at contract/test level. No real split, parser output, event sequence, shuffle, TEST lock, scientific TEST access, or metric was generated. META-001 remains the next dependency-correct task.
- **Evidence:** `docs/references/SCHEMA-COMPAT-001-citations.md`; schema tests use synthetic identities only.

## ADR-028 — Parser-independent raw metadata and chronology contract

- **Date:** 2026-08-22
- **Status:** ACCEPTED.
- **Context:** Protocol v1.1 requires HDFS atomic block/component identity and BGL raw chronology before any fitted parser, scientific partition, or window. Raw labels must not influence those identities.
- **Decision:** Implement META-001 as a separate ingestion-layer contract. HDFS uses normalized block tokens, two-pass union-find for transitive co-occurrence, earliest source-line chronology, and explicit unassigned reasons. BGL preserves source-line rank as authoritative chronology, parses the detailed timestamp for audit/tie evidence, and does not retain the first-field label. BGL 100-event parents remain outside META-001.
- **Alternatives:** Fit Drain3 before grouping; use source labels for ordering/grouping; choose only the first HDFS ID on a shared line; reorder BGL from label/status; create scientific partitions/windows in the metadata task.
- **Reason:** This is the smallest dependency-correct contract that preserves raw atomicity, prevents parser/label leakage, handles malformed observations without silent deletion, and remains scalable.
- **Consequence:** Deterministic metadata source, raw-line, component, and chronology IDs plus a bounded CLI and ignored non-overwrite artifact format now exist. No full real metadata artifact, split, TEST assignment, parser/template, event, sequence, metric, or result was generated. SPLIT-001 is the next task and requires separate approval.
- **Evidence:** `docs/metadata-extraction-contract.md` and `docs/references/META-001-citations.md`.
