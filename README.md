<div align="center">

# SeqLogAD

### Domain-Adaptive Fusion for Zero-Label Cross-System Log Anomaly Detection

A research project testing **whether knowledge transfers across heterogeneous log architectures and adapts to an unseen target using only an unlabeled normal buffer**.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
![Plan](https://img.shields.io/badge/plan-Bang__ke__hoach__SeqLogAD.xlsx-informational)
![Phase](https://img.shields.io/badge/phase-P1%20complete-success)
![Gate](https://img.shields.io/badge/G0-PASSED%20%C2%B7%20signed%202026--09--06-success)
![Results](https://img.shields.io/badge/scientific%20results-NOT__RUN-lightgrey)
![Type](https://img.shields.io/badge/type-research%20prototype-8A2BE2)

</div>

> [!IMPORTANT]
> The authoritative scientific plan is **`Bang_ke_hoach_SeqLogAD.xlsx`**. Phase 1 (Data & Protocol) is **complete and signed**: gate **G0 = `PROTOCOL_READY`**, 19 of 19 criteria pass, signed by the researcher on 2026-09-06. `NEXT_AUTHORIZED_TASK = P2.PRE` (Base Model / Tokenizer / Revision Freeze), metadata-only, authorised and not started. P2.1 Semantic Expert remains blocked until P2.PRE passes. G1–G4 remain closed, and `EXC-003` blocks G1 for the ARCH-HADOOP fold. No model has been trained: SeqLogAD reports **no scientific performance result**.

## The question

> **Can fusion transfer knowledge across heterogeneous source architectures, adapt to an unseen target using only an unlabelled normal-log buffer, and detect anomalies with calibrated, explainable evidence?**

Deliberately falsifiable and bounded to evaluated architectures. SeqLogAD does not assume that target adaptation works before a sufficient burn-in buffer, that every target has complete service/component topology, that adaptive fusion must beat equal-weight fusion, or that results generalise beyond held-out architectures. Negative or null findings are valid outcomes.

## Plan and authority

| Layer | Artifact |
| --- | --- |
| Authoritative plan | [`Bang_ke_hoach_SeqLogAD.xlsx`](Bang_ke_hoach_SeqLogAD.xlsx) — 4 phases, 32 micro-tasks, 5 gates, 11 verified sources |
| Machine-readable projection | [`configs/plan/excel-roadmap-v1.yaml`](configs/plan/excel-roadmap-v1.yaml) (`python scripts/extract_excel_roadmap.py`) |
| Implementation contract | [`DOMAIN-ADAPTIVE-FUSION-001`](docs/research-protocol-v2-domain-adaptive-fusion.md) · [machine contract](configs/protocols/protocol-v2-domain-adaptive-fusion.yaml) |
| Execution registry | [`configs/active-state.yaml`](configs/active-state.yaml) |
| Migration record | [`docs/migration/EXCEL-PLAN-MIGRATION-001.md`](docs/migration/EXCEL-PLAN-MIGRATION-001.md) · [relevance audit](docs/migration/EXCEL-RELEVANCE-AUDIT.md) |

Where the workbook and any other document disagree, the workbook wins.

## Phase 1 — Data & Protocol (complete)

| Task | Deliverable | Record |
| --- | --- | --- |
| P1.1 | Research scope | [`docs/protocol/P1.1-research-scope.md`](docs/protocol/P1.1-research-scope.md) |
| P1.2 | Dataset registry `DATA-REG-001` | [`data/registry/dataset_registry.csv`](data/registry/dataset_registry.csv) |
| P1.3 | Canonical schema `LOG-UNIFY-001` | [`src/seqlogad/protocol/schema.py`](src/seqlogad/protocol/schema.py) |
| P1.4 | Normaliser `NORM-CS-001` | [`docs/protocol/P1.4-normalisation.md`](docs/protocol/P1.4-normalisation.md) |
| P1.5 | LOAO folds `CS-SPLIT-001` | [`data/processed/protocol/folds/`](data/processed/protocol/folds) |
| P1.6 | Target buffer `ADAPT-INPUT-001` | [`data/processed/protocol/buffers/`](data/processed/protocol/buffers) |
| P1.7 | Isolation audit `LEAK-CS-001` | [`data/processed/protocol/audits/`](data/processed/protocol/audits) |
| P1.8 | G0 receipt | [`data/processed/protocol/G0-receipt.json`](data/processed/protocol/G0-receipt.json) |

All eight tasks are `DONE`. Four researcher signatures were required and supplied;
they are recorded in [`configs/protocols/g0-signatures.yaml`](configs/protocols/g0-signatures.yaml)
and re-verified by exact payload match on every build, so the gate fails closed if a
payload is altered. Accepted exceptions are registered in
[`configs/protocols/leak-cs-001-exceptions.yaml`](configs/protocols/leak-cs-001-exceptions.yaml)
— approval acknowledges them, it does not resolve them.

Full numbers: [`docs/protocol/PHASE-1-RECORD.md`](docs/protocol/PHASE-1-RECORD.md).

### Active architectures

Four log-producing systems, 16,525,722 records, all from Loghub
([Zenodo `10.5281/zenodo.8196385`](https://doi.org/10.5281/zenodo.8196385), CC-BY-4.0):

| Architecture | System | Domain | Records | Role |
| --- | --- | --- | ---: | --- |
| `ARCH-HDFS` | HDFS v1 | distributed storage | 11,175,629 | source + target |
| `ARCH-BGL` | Blue Gene/L | HPC supercomputer | 4,747,963 | source + target |
| `ARCH-HADOOP` | Hadoop YARN / MapReduce | batch compute | 394,310 | source + target |
| `ARCH-OPENSTACK` | OpenStack Nova | cloud IaaS control plane | 207,820 | source only |

Three leave-one-architecture-out folds, each with three source architectures.
OpenStack is source-only because the only label-blind ordering of its three capture
sessions places every anomaly before both normal captures — the reasoning is in
[P1.1](docs/protocol/P1.1-research-scope.md).

### Target-label isolation

Target anomaly labels are forbidden in training, adaptation, calibration, routing,
fusion fitting, model selection, normaliser fitting and parser fitting. This is
enforced structurally, not by convention:

- the canonical record has **no label field**, and a label-shaped field is rejected;
- adapters strip inline ground truth (BGL's alert marker) before a record exists;
- [`labels.py`](src/seqlogad/protocol/labels.py) is the only module that may open
  ground truth, refuses every forbidden scope, and records each access;
- no adaptation-path module imports it — audit check `L09` re-derives this from the
  import graph on every run, and a test asserts it.

## Reproduce

```bash
python scripts/extract_excel_roadmap.py   # workbook -> machine-readable plan
python scripts/build_streams.py           # scan raw corpora  (~11 min)
python scripts/build_protocol.py          # registry, folds, buffers, audits, G0
python -m pytest -q
```

---

# Historical context — the retired v1.1 study

> Everything below documents the **superseded** v1.1 sequence-added-value study. It
> is retained so the frozen HDFS/BGL artifacts, decisions and TEST seals stay
> explicable and verifiable. **None of it routes work, gates anything, or defines a
> definition of done under the workbook.** See
> [`docs/migration/EXCEL-PLAN-MIGRATION-001.md`](docs/migration/EXCEL-PLAN-MIGRATION-001.md).

## Why test sequence information explicitly?


A true behavioral anomaly may be invisible to per-event frequency:

```text
Expected: LOGIN_REQUEST → TOKEN_VALIDATE → USER_LOOKUP → SESSION_CREATE
Observed: LOGIN_REQUEST →                  USER_LOOKUP → SESSION_CREATE
```

However, a benchmark label may also be predictable from unseen event types, sequence length, or event counts. SeqLogAD therefore tests cheap order-insensitive explanations before attributing performance to sequence order.

## Preserved v1.1 foundation

The former approved direction was `HYBRID_B_PLUS_C`; it is retained as historical provenance:

- **Core (Option B):** keep the exact verified HDFS/BGL datasets and measure sequence added value over strong order-insensitive controls.
- **Conditional (Option C):** study localization faithfulness only if sequence signal and localization sanity gates pass.
- **Fallback (Option A):** consider a different/expanded dataset only after the current datasets fail pre-registered suitability gates and literature supports a candidate.

`LIT-001` is complete as a targeted review. It found strong prior art for generic sequence models, multi-pattern fusion, mixture-of-experts, localization, and synthetic log generation. SeqLogAD therefore makes **no component-level algorithmic novelty claim**; its active contribution is a controlled empirical study whose outcome remains `NOT_RUN`. Any future novelty claim requires a new claim-specific systematic search.

`EFFECT-001` is **FROZEN — HUMAN APPROVED**. It fixes `delta_HDFS = delta_BGL = 0.01 AP` under `RESOURCE_FEASIBILITY_MARGIN`, together with the estimand, comparison family, equal-budget rule, paired bootstrap, 95% interval, seed aggregation, and KT-3 decision logic. Approval occurred before any scientific baseline, KT, parser-derived experiment, or TEST result. This completes the statistical gate but does not automatically authorize pipeline execution.

`PROTOCOL-SPLIT-CLARIFY-001` is **FROZEN — HUMAN APPROVED**. It resolves the exact HDFS eligible-line/connected-component boundary policy, BGL raw split-before-window/residual policy, reconciliation equations, and layered split identities. SPLIT-001 has now instantiated that frozen contract: both real manifests reproduce, and both TEST partitions remain `SEALED / NEVER_OPENED`.

## Historical v1.1 gated architecture

```text
Verified immutable HDFS/BGL bytes                    [IMPLEMENTED]
        ↓
Metadata/group-key extraction without fitted parser  [IMPLEMENTED]
        ↓
Raw chronological 60/10/10/10/10 partition           [IMPLEMENTED / VERIFIED]
        ↓
Normal BASE_TRAIN → fit/freeze Drain3                 [IMPLEMENTED / VERIFIED]
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

## Current implementation status and v2 boundary

| Capability | Status |
|---|---|
| HDFS/BGL acquisition, checksums, manifests, fingerprints, verification | **Implemented and verified** |
| Python 3.12 environment, editable `seqlogad` package, dependency lock, CLIs | **Implemented and verified** |
| Canonical event/template schemas | **Implemented and tested** |
| Sequence/localization/mutation schema contracts | **Implemented and tested; no real artifact generated** |
| HDFS group/BGL chronology metadata extraction | **Implemented and tested; no full real metadata artifact generated** |
| Research protocol v1.1 and negative-control contract | **Frozen; empirical status `NOT_RUN`** |
| EFFECT-001 statistical contract | **Frozen and human-approved; both margins `0.01 AP`; empirical status `NOT_RUN`** |
| Exact split-semantics addendum | **Frozen and contract-tested** |
| Raw split manifests and physical TEST guards | **Implemented and verified; TEST `SEALED / NEVER_OPENED`; open count `0`** |
| Drain3 normal-only fit/freeze, persistence, restore, and unknown policy | **Implemented and verified; no canonical event corpus generated** |
| HDFS purge representativeness audit | **Completed; `PURGE_REPRESENTATIVENESS_CONCERN` retained as a limitation** |
| HDFS purge methodological decision | **Option B frozen and human-approved; primary unchanged; secondary sensitivity pre-registered / `NOT_RUN`** |
| Canonical parsed event corpus | **Not generated** |
| Sequence builder and killer-experiment pipeline | **Not implemented** |
| Baselines/models/localization/fusion | **Not implemented or fitted** |
| RAG/Agent/API/UI | **Future placeholders only** |

The v2 forward model stack and target-adaptation workflow are planned only:
Llama-3.1-8B with independent LoRA-Semantic/LoRA-Sequence adapters, GTAT,
unlabeled target-buffer calibration and adaptive fusion. No v2 model,
checkpoint, target fold or metric exists.

`PURGE-DECISION-001` is **FROZEN — HUMAN APPROVED**. The original HDFS split
remains primary, while a separate non-confirmatory purge-sensitivity analysis
is pre-registered and `NOT_RUN`. `CANONICAL-EVENT-001` is now the one
authorized next task; no split repair, parser refit, scientific experiment, or
TEST access is authorized by this decision.

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
- The HDFS purge removed 2,541,053 eligible lines (22.737449498368278%) under
  the frozen whole-component rule. PURGE-AUDIT-001 found aggregate anomaly
  prevalence 2.6745% in purged versus 3.0045% in retained components
  (difference −0.32996 percentage points; Newcombe-Wilson 95% CI −0.42921 to
  −0.22877; prevalence ratio 0.8902). This is
  `PURGE_REPRESENTATIVENESS_CONCERN`, not a causal or model-performance result.
  Option B keeps the frozen primary split and pre-registers a separate
  robustness-only sensitivity cohort from whole `PURGED_BOUNDARY` components;
  it cannot tune/select methods or replace the primary result.
- BGL uses non-overlapping 100-event parent windows created after partitioning.
- Labels may filter authorized normal pools and support validation/evaluation, but never enter model inputs or base loss.
- Drain3 fits normal `BASE_TRAIN` only and then freezes.
- TEST is physically sealed for both datasets. Ordinary loaders fail before reading TEST records; future access requires a dedicated human-only, hash-bound, audited workflow.
- Final TEST runs once, by the human researcher, after all artifacts and claims are frozen.

The forward source of truth is [Protocol v2](docs/research-protocol-v2-domain-adaptive-fusion.md), its [machine contract](configs/protocols/protocol-v2-domain-adaptive-fusion.yaml), and the [migration record](docs/plan-migration-v1.1-to-v2.md). The v1.1 protocol, exact split addendum and EFFECT-001 remain frozen historical foundation contracts.

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
seqlogad-split-dataset --project-root . generate --dataset hdfs --json
seqlogad-split-dataset --project-root . generate --dataset bgl --json
seqlogad-split-dataset --project-root . validate --dataset hdfs --json
seqlogad-split-dataset --project-root . validate --dataset bgl --json
seqlogad-split-dataset --project-root . status --dataset hdfs --json
seqlogad-split-dataset --project-root . status --dataset bgl --json
seqlogad-fit-parser --project-root . gate --dataset hdfs --json
seqlogad-fit-parser --project-root . gate --dataset bgl --json
seqlogad-fit-parser --project-root . validate --dataset hdfs --json
seqlogad-fit-parser --project-root . validate --dataset bgl --json
```

The metadata commands are bounded, label-independent dry-runs. Split generation
is structural and non-overwriting; generated bulk artifacts remain ignored by
Git. Parser commands above only gate or validate existing frozen states. No
canonical-event generation, baseline experiment, model training, or final-TEST
execution command is run by this quick start.

## Preserved v1.1 research questions (historical)

All are **HYPOTHESIS — TO BE TESTED**:

1. **Dataset suitability:** Do the exact HDFS/BGL artifacts contain enough non-trivial sequential information for a sequence-based claim?
2. **Sequence added value:** How much does sequence modeling add over strong order-insensitive baselines?
3. **Order sensitivity:** Does destroying order materially reduce sequential-detector performance while preserving counts and length?
4. **Conditional localization faithfulness:** If sequence signal exists, can anomaly-causing positions/transitions be localized beyond sanity controls?

These questions are not the v2 RQs. See [v2 research questions](docs/research-questions.md).

## Human and AI ownership

AI/Codex prepares implementation, deterministic builders, tests, configs, and commands. The human researcher approved `delta_HDFS = delta_BGL = 0.01 AP` pre-experiment, executes empirical runs/training/tuning, selects validation-only configurations, opens TEST once, and owns conclusions. AI must never fabricate metrics or mark `NOT_RUN` work complete.

## Repository map

```text
configs/          Dataset and protocol contracts; future configs clearly gated
data/manifests/   Version-controlled identities of accepted raw bytes
docs/             Active protocol, RQs, dataset cards, literature, citations
Plan/             Version-controlled v2 plan, migration record, and historical v1.1/ADR records
src/seqlogad/     Installable package; data foundation/schemas implemented
tests/            Active foundation/schema/protocol tests plus labeled placeholders
outputs/          Ignored experiment-specific artifacts
```

## Key documents

- [Forward master plan v2](Plan/master-implementation-plan-v2-domain-adaptive-fusion.md)
- [v1.1 historical master plan](Plan/master-implementation-plan-v1.1.md)
- [Architecture](Plan/01_ARCHITECTURE.md)
- [Research plan](Plan/02_RESEARCH_PLAN.md)
- [Task backlog](Plan/03_TASK_BACKLOG.md)
- [Test plan](Plan/04_TEST_PLAN.md)
- [Roadmap](Plan/05_8_WEEK_ROADMAP.md)
- [Decision log](Plan/06_DECISIONS.md)
- [Experiment tracker](Plan/07_EXPERIMENT_TRACKER.md)
- [Active post-PARSE execution state](configs/active-state.yaml)
- [Canonical post-PARSE context](docs/audits/PROJECT-CONTEXT-POST-PARSE-001.md)
- [Original evaluation remediation matrix](docs/audits/ORIGINAL-EVALUATION-REMEDIATION.md)
- [Protocol v1.1](docs/research-protocol-v1.1.md)
- [Exact split-semantics addendum](docs/split-clarification-contract.md)
- [PARSE-001 fit/freeze provenance](docs/parser-fit-and-freeze.md)
- [PARSE-001 literature and citation record](docs/references/PARSE-001-citations.md)
- [Reference registry](docs/references/reference_registry.yaml) · [active references](docs/references/ACTIVE_REFERENCES.md)
- [PURGE-AUDIT-001 report](docs/audits/PURGE-AUDIT-001.md)
- [PURGE-AUDIT-001 citations and method provenance](docs/references/PURGE-AUDIT-001-citations.md)
- [Split literature evidence matrix](docs/literature/split-protocol-evidence-matrix.md)
- [Split citations and search record](docs/references/PROTOCOL-SPLIT-CLARIFY-001-citations.md)
- [Real split artifacts and TEST seal](docs/split-artifacts-and-test-seal.md)
- [SPLIT-001 citations and method provenance](docs/references/SPLIT-001-citations.md)
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
