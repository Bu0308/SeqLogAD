<div align="center">

# SeqLogAD

### Sequence-Based Unsupervised Anomaly Detection for Large-Scale Event Logs

A research project testing **whether and when event order adds measurable anomaly-detection value beyond strong order-insensitive baselines**.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
![Protocol](https://img.shields.io/badge/protocol-v1.1%20frozen-blue)
![Results](https://img.shields.io/badge/scientific%20results-NOT__RUN-lightgrey)
![Type](https://img.shields.io/badge/type-research%20prototype-8A2BE2)

</div>

> [!IMPORTANT]
> The data-integrity foundation, reproducible Python environment, schema contracts, and parser-independent raw metadata extractor are implemented and tested. The scientific pipeline is not complete: no split artifact, project parser run, baseline/model fit, training, tuning, or final TEST evaluation has occurred. SeqLogAD reports no scientific performance result yet.

## Current scientific question

The active question is:

> **How much additional anomaly-detection value does sequence order provide beyond strong order-insensitive baselines under a leakage-controlled, chronological, and equal-budget evaluation protocol?**

This is deliberately falsifiable. SeqLogAD does not assume that:

- HDFS or BGL necessarily contains useful non-trivial sequence signal;
- a sequence model must beat a count-based baseline;
- a Transformer is needed;
- localization or fusion will be scientifically justified.

Negative or null findings are valid outcomes.

## Why test sequence information explicitly?

A true behavioral anomaly may be invisible to per-event frequency:

```text
Expected: LOGIN_REQUEST → TOKEN_VALIDATE → USER_LOOKUP → SESSION_CREATE
Observed: LOGIN_REQUEST →                  USER_LOOKUP → SESSION_CREATE
```

However, a benchmark label may also be predictable from unseen event types, sequence length, or event counts. SeqLogAD therefore tests cheap order-insensitive explanations before attributing performance to sequence order.

## Research Freeze v1.1

The approved direction is `HYBRID_B_PLUS_C`:

- **Core (Option B):** keep the exact verified HDFS/BGL datasets and measure sequence added value over strong order-insensitive controls.
- **Conditional (Option C):** study localization faithfulness only if sequence signal and localization sanity gates pass.
- **Fallback (Option A):** consider a different/expanded dataset only after the current datasets fail pre-registered suitability gates and literature supports a candidate.

`LIT-001` is complete as a targeted review. It found strong prior art for generic sequence models, multi-pattern fusion, mixture-of-experts, localization, and synthetic log generation. SeqLogAD therefore makes **no component-level algorithmic novelty claim**; its active contribution is a controlled empirical study whose outcome remains `NOT_RUN`. Any future novelty claim requires a new claim-specific systematic search.

`EFFECT-001` is **FROZEN — HUMAN APPROVED**. It fixes `delta_HDFS = delta_BGL = 0.01 AP` under `RESOURCE_FEASIBILITY_MARGIN`, together with the estimand, comparison family, equal-budget rule, paired bootstrap, 95% interval, seed aggregation, and KT-3 decision logic. Approval occurred before any scientific baseline, KT, parser-derived experiment, or TEST result. This completes the statistical gate but does not automatically authorize pipeline execution.

## Minimal gated architecture

```text
Verified immutable HDFS/BGL bytes                    [IMPLEMENTED]
        ↓
Metadata/group-key extraction without fitted parser  [IMPLEMENTED]
        ↓
Raw chronological 60/10/10/10/10 partition           [PLANNED]
        ↓
Normal BASE_TRAIN → fit/freeze Drain3                 [PLANNED]
        ↓
Read-only transform → canonical events/sequences      [SCHEMAS IMPLEMENTED;
                                                       GENERATION PLANNED]
        ↓
Order-insensitive controls                            [PLANNED / MUST]
  unseen-event · length · count/count-vector
  Isolation Forest                                   [PLANNED / MUST]
        ↓
Markov/N-gram sequential baseline                     [PLANNED / MUST]
        ↓
Sequence-destruction negative control                 [PLANNED / MUST]
  preserve multiset · counts · length · label
        ↓
Human scientific gate
        ├── insufficient sequence value → report/reframe; stop complexity
        └── meaningful sequence value
              ├── lightweight Transformer             [CONDITIONAL]
              ├── localization faithfulness           [CONDITIONAL]
              └── simple/complementarity fusion       [CONDITIONAL]
        ↓
One human-executed locked final TEST                   [PLANNED]

RAG / Agent / API / UI / Elasticsearch                [FUTURE, NOT CORE]
```

The old fixed four-expert and F0–F8 fusion architecture is preserved as historical V3 planning, not active scope.

## Pre-registered killer experiments

| ID | Question | Status |
|---|---|---|
| KT-1 | Do unseen-event, length, count/count-vector, or Isolation Forest already reach the practical ceiling? | `NOT_RUN` |
| KT-2 | How much of HDFS label behavior is explainable without event order? | `NOT_RUN` |
| KT-3 | Does destroying order while preserving counts and length reduce sequential performance? | `NOT_RUN` |
| KT-4 | Does localization beat randomized-position controls? | `NOT_RUN / CONDITIONAL` |
| KT-5 | Do counterfactual repair/deletion tests support localization faithfulness? | `NOT_RUN / CONDITIONAL` |
| KT-6 | Does conditional fusion ignore random/corrupted expert evidence? | `NOT_RUN / CONDITIONAL` |

The statistical method family and practical margins are frozen before experiments. A meaningful gain requires the 95% interval to lie entirely above `+0.01`; equivalence lies entirely inside `[-0.01,+0.01]`; meaningful harm lies entirely below `-0.01`; all other cases are inconclusive.

## Scope

| Class | Included work |
|---|---|
| **MUST** | Data/split provenance, TEST guard, frozen normal-only Drain3, canonical events/sequences, unseen-event/length/count/Isolation Forest baselines, Markov/N-gram, KT-1–KT-3, leakage audit, reproducible paired evaluation |
| **SHOULD** | Count-label dependence diagnostics and additional robustness summaries |
| **CONDITIONAL** | Transformer, localization + KT-4/KT-5, strongest-single/simple fusion + KT-6 after complementarity |
| **FUTURE** | Dataset expansion, retrieval/RAG/Agent, test recommendation, Elasticsearch adapter, FastAPI, Streamlit/dashboard |
| **REMOVED FROM CORE** | LSTM, fixed four-expert design, normal-reference expert, F2–F8 trainable fusion ladder, multi-agent platform |

## Current implementation status

| Capability | Status |
|---|---|
| HDFS/BGL acquisition, checksums, manifests, fingerprints, verification | **Implemented and verified** |
| Python 3.12 environment, editable `seqlogad` package, dependency lock, CLIs | **Implemented and verified** |
| Canonical event/template schemas | **Implemented and tested** |
| Sequence/localization/mutation schema contracts | **Implemented and tested; no real artifact generated** |
| HDFS group/BGL chronology metadata extraction | **Implemented and tested; no full real metadata artifact generated** |
| Research protocol v1.1 and negative-control contract | **Frozen; empirical status `NOT_RUN`** |
| EFFECT-001 statistical contract | **Frozen and human-approved; both margins `0.01 AP`; empirical status `NOT_RUN`** |
| Raw split manifest and physical TEST guard | **Not implemented** |
| Drain3 scientific fit/freeze and parsed events | **Not implemented** |
| Sequence builder and killer-experiment pipeline | **Not implemented** |
| Baselines/models/localization/fusion | **Not implemented or fitted** |
| RAG/Agent/API/UI | **Future placeholders only** |

## Dataset provenance

Raw benchmark files are local and excluded from Git. Version-controlled manifests identify the accepted bytes.

| Dataset | Source archive | Manifest | Dataset fingerprint | Scientific suitability |
|---|---|---|---|---|
| HDFS_v1 | Verified | Verified | `0103c63b...4013` | `TO_BE_TESTED` by KT-1–KT-3 |
| BGL | Verified | Verified | `c9ee7a8d...e861` | `TO_BE_TESTED` by KT-1–KT-3 |

See the [HDFS card](docs/datasets/hdfs.md), [BGL card](docs/datasets/bgl.md), and [acquisition guide](docs/dataset-acquisition.md). Public availability does not imply unrestricted redistribution.

## Frozen data and TEST discipline

- Split raw atomic units chronologically: `BASE_TRAIN/FUSION_TRAIN/VAL_EXPERT/VAL_FUSION/TEST = 60/10/10/10/10`.
- HDFS uses block/session atomicity and purges boundary-spanning components.
- BGL uses non-overlapping 100-event parent windows created after partitioning.
- Labels may filter authorized normal pools and support validation/evaluation, but never enter model inputs or base loss.
- Drain3 fits normal `BASE_TRAIN` only and then freezes.
- TEST is contractually sealed now. It becomes physically sealed only when a split manifest, partition hashes, and access guard exist.
- Final TEST runs once, by the human researcher, after all artifacts and claims are frozen.

The source of truth is [Protocol v1.1](docs/research-protocol-v1.1.md), its [machine contract](configs/protocols/protocol-v1.1.yaml), and the [EFFECT-001 statistical addendum](docs/statistical-decision-contract.md).

## Quick start: verify the implemented foundation

```bash
git clone https://github.com/Bu0308/SeqLogAD.git
cd SeqLogAD
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e ".[dev]"
python -m pip check
python -m pytest -q
```

After acquiring raw datasets according to the [acquisition guide](docs/dataset-acquisition.md):

```bash
seqlogad-verify-dataset --project-root . --dataset hdfs --json
seqlogad-verify-dataset --project-root . --dataset bgl --json
seqlogad-extract-raw-metadata --project-root . --dataset hdfs --dry-run --max-lines 1000 --json
seqlogad-extract-raw-metadata --project-root . --dataset bgl --dry-run --max-lines 1000 --json
```

The metadata commands are bounded, label-independent dry-runs. No command for
parser execution, split generation, baseline experiments, model training, or
final TEST is available yet.

## Research questions

All are **HYPOTHESIS — TO BE TESTED**:

1. **Dataset suitability:** Do the exact HDFS/BGL artifacts contain enough non-trivial sequential information for a sequence-based claim?
2. **Sequence added value:** How much does sequence modeling add over strong order-insensitive baselines?
3. **Order sensitivity:** Does destroying order materially reduce sequential-detector performance while preserving counts and length?
4. **Conditional localization faithfulness:** If sequence signal exists, can anomaly-causing positions/transitions be localized beyond sanity controls?

Fusion and downstream investigation are not primary RQs in v1.1.

## Human and AI ownership

AI/Codex prepares implementation, deterministic builders, tests, configs, and commands. The human researcher approved `delta_HDFS = delta_BGL = 0.01 AP` pre-experiment, executes empirical runs/training/tuning, selects validation-only configurations, opens TEST once, and owns conclusions. AI must never fabricate metrics or mark `NOT_RUN` work complete.

## Repository map

```text
configs/          Dataset and protocol contracts; future configs clearly gated
data/manifests/   Version-controlled identities of accepted raw bytes
docs/             Active protocol, RQs, dataset cards, literature, citations
Plan/             Version-controlled active v1.1 and historical plans/ADRs
src/seqlogad/     Installable package; data foundation/schemas implemented
tests/            Active foundation/schema/protocol tests plus labeled placeholders
outputs/          Ignored experiment-specific artifacts
```

## Key documents

- [Active master plan v1.1](Plan/master-implementation-plan-v1.1.md)
- [Architecture](Plan/01_ARCHITECTURE.md)
- [Research plan](Plan/02_RESEARCH_PLAN.md)
- [Task backlog](Plan/03_TASK_BACKLOG.md)
- [Test plan](Plan/04_TEST_PLAN.md)
- [Roadmap](Plan/05_8_WEEK_ROADMAP.md)
- [Decision log](Plan/06_DECISIONS.md)
- [Experiment tracker](Plan/07_EXPERIMENT_TRACKER.md)
- [Protocol v1.1](docs/research-protocol-v1.1.md)
- [EFFECT-001 statistical decision contract](docs/statistical-decision-contract.md)
- [EFFECT-001 citations and method provenance](docs/references/EFFECT-001-citations.md)
- [Targeted prior-art matrix](docs/literature/prior-art-matrix-v1.1.md)
- [LIT-001 reproducible search log](docs/literature/LIT-001-search-log.md)
- [LIT-001 citations and method provenance](docs/references/LIT-001-citations.md)
- [Research Freeze v1.1 citations](docs/references/RESEARCH-FREEZE-v1.1-citations.md)

## Scientific integrity and license

- No fabricated metrics, tables, plots, citations, SOTA claims, or novelty claims.
- No TEST access for fitting, selection, thresholding, calibration, architecture, or claim decisions.
- No raw benchmark bytes, archives, secrets, checkpoints, or generated bulk outputs in Git.
- Historical plans are preserved but labeled superseded.
- **LICENSE DECISION REQUIRED FROM PROJECT OWNER.** No project-source license is implied until the owner selects and adds one.
