<div align="center">

# SeqLogAD

### Multi-Model Sequence Anomaly Localization for System Logs

A research project studying heterogeneous sequence-anomaly experts, structured evidence fusion, and evidence-grounded regression-test recommendation for large-scale system logs.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
![Tests](https://img.shields.io/badge/tests-73%20passed-brightgreen)
![Stage](https://img.shields.io/badge/stage-canonical%20schema-orange)
![Type](https://img.shields.io/badge/type-research%20prototype-8A2BE2)

</div>

> [!IMPORTANT]
> Dataset integrity/provenance, the reproducible environment, the frozen scientific protocol, and canonical event/template schemas are implemented. Sequence, partition, localization, and mutation schema contracts are implemented and awaiting human audit. No real canonical event or sequence artifact has been generated. Drain3 parsing, split/sequence/mutation generation, models, complementarity analysis, fusion, retrieval, investigation, API, and UI remain planned. No model has been trained and no empirical model result is reported.

## Research direction

SeqLogAD studies:

> **Multi-Model Sequence Anomaly Localization with Structured Evidence Fusion and Evidence-Grounded Regression-Test Recommendation.**

Central research question:

> Do heterogeneous log-anomaly experts provide measurably complementary evidence, and can a scientifically justified fusion mechanism exploit that complementarity without double-counting redundant evidence or becoming less reliable under expert disagreement?

The four-expert design is provisional. An expert remains in the final fusion only if complementarity analysis demonstrates measurable incremental value.

Novelty status: **UNVERIFIED / PRIOR-ART VALIDATION REQUIRED**. “Structured Evidence Consensus Fusion” is a working name, not a novelty claim.

## Why sequence anomalies matter

Operational failures can occur even when every individual event is common and no `ERROR` line appears:

```text
Expected: LOGIN_REQUEST → TOKEN_VALIDATE → USER_LOOKUP → SESSION_CREATE → LOGIN_SUCCESS
Observed: LOGIN_REQUEST →                  USER_LOOKUP → SESSION_CREATE → LOGIN_SUCCESS
```

The missing validation step is a behavioral sequence anomaly. SeqLogAD targets missing, extra, reordered, repeated, unexpected-transition, timing, and contextual anomalies.

Localization uses separate coordinate systems:

- **Token positions:** extra, replacement, or repeated observed events.
- **Gap positions:** missing events; for `E1 E2 E3`, the gaps are `G0 E1 G1 E2 G2 E3 G3`.
- **Transition positions:** unexpected transitions and reorder-related evidence.

## Product positioning

SeqLogAD is a **sequence-aware AI investigation and QA layer on top of observability infrastructure**.

It is not an ELK, Elasticsearch, or Kibana replacement; it is not a generic RAG chatbot or generic multi-agent platform. Elasticsearch may later provide P1/P2 storage and search adapters, but it is not the research contribution.

The LLM/agent is not an anomaly detector. It is a downstream, read-only consumer of frozen expert/fusion outputs and evidence IDs.

## Research architecture

```text
Raw System Logs
      ↓
Dataset Integrity / Provenance                 [IMPLEMENTED]
      ↓
Canonical Event/Template Schema                [IMPLEMENTED CONTRACT]
      ↓
Drain3 Parsing / Templates                     [PLANNED]
      ↓
Event Sequence Construction                    [PLANNED; SCHEMA CONTRACT IMPLEMENTED]
      ↓
Leakage-Safe Dataset Splits                    [PLANNED]
      ↓
┌──────────────────────────────────────────────────────────┐
│ HETEROGENEOUS EXPERTS                          [PLANNED] │
│ A — SeqLogAD-T lightweight causal Transformer           │
│ B — Markov / N-gram transition expert                   │
│ C — Isolation Forest quantitative expert                │
│ D — normal-reference structural retrieval expert        │
└───────────────────────────┬──────────────────────────────┘
                            ↓
Complementarity Analysis                       [PLANNED]
                            ↓
Structured Evidence Fusion                     [PLANNED]
                            ↓
Anomaly + Localization + Reliability           [PLANNED]
                            ↓
Evidence-Grounded Investigation                [PLANNED]
                            ↓
Regression-Test Recommendation                 [PLANNED]
```

## Expert overview

| Expert | Primary inductive bias | Expected evidence | Status |
|---|---|---|---|
| A — SeqLogAD-T | Long-range context and order | Missing/reordered/contextually inconsistent events | Planned |
| B — Markov/N-gram | Short local transition probability | Rare or unexpected transitions | Planned |
| C — Isolation Forest | Quantitative/statistical behavior | Length, frequency, repetition, entropy, rarity | Planned |
| D — Normal-reference retrieval | Deviation from historical normal execution | Nearest-normal IDs and structural differences | Planned |

Dense semantic retrieval is P1. Expert D starts with edit distance, LCS, event n-gram overlap, and transition overlap.

## Complementarity and fusion gates

Before proposed fusion training, the project must measure score correlation, prediction disagreement, error overlap, oracle ensemble gain, anomaly-family conditional performance, localization overlap, and marginal contribution. Redundant experts may be removed or demoted.

Required fusion ladder:

| ID | Baseline |
|---|---|
| F0 | Strongest single expert |
| F1 | Normalized mean |
| F2 | Validation-weighted average |
| F3 | Voting/rank voting |
| F4 | Logistic stacking |
| F5 | MLP stacking |
| F6 | Standard gating/MoE |
| F7 | Evidential/Dempster-Shafer, if technically applicable |
| F8 | Proposed structured fusion |

The minimal fusion-loss candidate is detection loss plus fused-localization loss. A redundancy term is only potential work pending prior-art and ablation evidence. Conflict is currently an input, verifier signal, abstention signal, and evaluation variable—not the rejected `confidence × conflict` core penalty.

## Current implementation status

| Capability | Status | Evidence today |
|---|---|---|
| Dataset contracts | Implemented | Strict HDFS/BGL Pydantic/YAML contracts |
| Safe acquisition | Implemented | Canonical source, `.part`, timeout, checksum, non-overwrite policy |
| Checksums | Implemented | Streaming source MD5 and local SHA-256 |
| Manifests/fingerprints | Implemented | Deterministic version-controlled JSON manifests |
| Manifest verification | Implemented | Independent file-size/hash/fingerprint checks |
| Reproducible Python environment | Implemented | Python 3.12, editable `seqlogad` package, tested dependency lock |
| Scientific protocol | Frozen | Human-approved `PROTOCOL-001` plus machine-readable regression guard |
| Canonical event/template schemas | Implemented and approved | Frozen immutable `SCHEMA-001` contract; no real event artifact generated |
| Sequence/localization/mutation schemas | Implemented; awaiting audit | Strict `SCHEMA-002` contracts; no real sequence or mutation artifact generated |
| Drain3 parsing/templates | Planned | No logs parsed by the project pipeline |
| Split/sequence/mutation generators | Planned | No processed sequence artifacts |
| Experts A–D | Planned | No model implementation, fit, training, or checkpoints |
| Complementarity/calibration/fusion | Planned | No experiment has run |
| Retrieval/RAG/agent/API/UI | Planned downstream | Placeholder modules only |

## Dataset provenance

Raw benchmarks are excluded from Git. The manifests identify the exact extracted bytes accepted locally.

| Dataset | Manifested files | Bytes | Source archive | Manifest | Fingerprint |
|---|---:|---:|---|---|---|
| HDFS_v1 | 6 | 1,828,041,800 | Verified | Verified | `0103c63b...4013` |
| BGL | 1 | 743,185,031 | Verified | Verified | `c9ee7a8d...e861` |

Full fingerprints and source checksums are recorded in the [HDFS dataset card](docs/datasets/hdfs.md), [BGL dataset card](docs/datasets/bgl.md), and [acquisition documentation](docs/dataset-acquisition.md). Downloadability does not imply unrestricted redistribution; raw data and archives are not distributed in this repository.

## Quick start: verify the implemented foundation

```bash
git clone https://github.com/Bu0308/SeqLogAD.git
cd SeqLogAD
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e ".[dev]"
python -m pip check
python -m pytest -q
```

After acquiring datasets according to [docs/dataset-acquisition.md](docs/dataset-acquisition.md):

```bash
seqlogad-verify-dataset --project-root . --dataset hdfs --json
seqlogad-verify-dataset --project-root . --dataset bgl --json
```

The canonical import namespace is `seqlogad.*`; imports do not require `PYTHONPATH` or execution from the repository root. The repository-local `scripts.*` wrappers remain available for compatibility.

No parser, model-training, fusion-training, or final-test command exists yet.

## Research questions

All questions are **HYPOTHESIS — TO BE TESTED**:

1. **Expert value:** How well do individually optimized heterogeneous experts capture different behavioral anomaly mechanisms?
2. **Complementarity:** Do heterogeneous experts exhibit measurable complementary error and localization patterns?
3. **Fusion:** Can structured evidence fusion outperform the strongest individual expert and standard fusion baselines?
4. **Reliability/redundancy:** Does explicit handling of expert dependency improve reliability and false-positive control without sacrificing detection performance?
5. **Downstream value:** Does fused structured evidence improve evidence-grounded investigation and regression-test recommendation compared with score-only context?

See [research questions](docs/research-questions.md) and [project scope](docs/project-scope.md).

## Human and AI research workflow

### AI/Codex prepares

- source code, preprocessing, models, losses, fusion, configs;
- training/evaluation scripts and commands;
- tests, documentation, and reproducibility checks.

### Human researcher executes and decides

- actual model/fusion training and hyperparameter tuning;
- checkpoint selection and ablation experiments;
- locked final-test execution;
- empirical conclusions and research decisions.

AI must never fabricate metrics or imply that a planned experiment ran.

## Frozen data and training protocol

The preferred terminology is:

> **Normal-only self-supervised sequential anomaly detection with synthetic supervision for localization and fusion.**

The human-approved split is chronological `60/10/10/10/10` across `BASE_TRAIN`, `FUSION_TRAIN`, `VAL_EXPERT`, `VAL_FUSION`, and locked `TEST`. Labels may filter authorized normal pools and support validation, but they never enter model inputs or base self-supervised losses. TEST labels remain sealed until one human-executed final command.

HDFS preserves block/session atomicity and purges boundary-spanning components. BGL uses non-overlapping 100-event parent windows. Drain3 is fitted on normal `BASE_TRAIN` messages and then frozen. The complete source-of-truth contract is [PROTOCOL-001](docs/research-protocol.md); its literature and method provenance are recorded in the [task citation note](docs/references/PROTOCOL-001-citations.md).

Training is staged: freeze data artifacts, fit experts independently, freeze experts, generate fusion-development evidence, calibrate, measure complementarity, train fusion, select thresholds/abstention, and finally execute locked TEST. Human execution is required for all empirical stages.

## Repository map

```text
configs/          Version-controlled dataset and future experiment contracts
data/manifests/   Exact accepted raw-dataset identities
docs/             Active public scope, research, data, and reproducibility docs
Plan/             Version-controlled historical and V3 research plans
scripts/                  Compatibility wrappers for installed CLIs
src/seqlogad/ingestion/   Implemented dataset integrity/provenance foundation
src/seqlogad/*            Canonical package namespace and planned module boundaries
tests/                    73 active foundation/environment/protocol/schema tests plus future placeholders
outputs/          Ignored experiment artifacts grouped by experiment ID
```

## Scientific integrity

- No novelty or superiority claim precedes `LIT-001` and controlled experiments.
- No training metric is entered as a result without a traceable run artifact.
- Parser, expert, calibrator, fusion, threshold, and retrieval fit scopes exclude TEST.
- Raw datasets are immutable and excluded from Git.
- Configuration, manifests, research decisions, and experiment status are version-controlled.
- Downstream hypotheses require evidence IDs and may return `INSUFFICIENT_EVIDENCE`.

## Documentation

- [V3 master implementation plan](Plan/master-implementation-plan-v3.md)
- [Architecture](Plan/01_ARCHITECTURE.md)
- [Research plan](Plan/02_RESEARCH_PLAN.md)
- [Task backlog](Plan/03_TASK_BACKLOG.md)
- [Test plan](Plan/04_TEST_PLAN.md)
- [Relative 8-week roadmap](Plan/05_8_WEEK_ROADMAP.md)
- [Decision log](Plan/06_DECISIONS.md)
- [Experiment tracker](Plan/07_EXPERIMENT_TRACKER.md)
- [Reproducibility](docs/reproducibility.md)
- [Frozen scientific protocol](docs/research-protocol.md)
- [PROTOCOL-001 citations and method provenance](docs/references/PROTOCOL-001-citations.md)
- [Canonical event/template schema](docs/schemas/canonical-events.md)
- [SCHEMA-001 citations and method provenance](docs/references/SCHEMA-001-citations.md)
- [Sequence/localization/mutation schema](docs/schemas/event-sequences-and-localization.md)
- [SCHEMA-002 citations and method provenance](docs/references/SCHEMA-002-citations.md)

## License and data notice

Project source licensing has not yet been declared in this repository. HDFS and BGL come from the canonical [LogPAI Loghub](https://github.com/logpai/loghub) / [Zenodo record 8196385](https://doi.org/10.5281/zenodo.8196385). Review and retain source terms and citations; this repository contains configs, manifests, documentation, source, and synthetic fixtures—not benchmark raw logs.
