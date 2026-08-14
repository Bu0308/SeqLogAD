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
