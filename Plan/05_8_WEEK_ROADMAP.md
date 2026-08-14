# 05 — Relative 8-Week Roadmap V3

This is a **relative implementation-week plan**, not a claim about elapsed calendar time.

| Week | Primary work | Human execution | Expected artifacts | Exit criteria |
|---|---|---|---|---|
| 1 | LIT-001, ADR/ENV, canonical event/evidence contracts | Approve novelty framing and contracts | Prior-art matrix, packaging decision, schemas | Scope stable; environment and contracts pass tests |
| 2 | Drain3 lifecycle, HDFS/BGL adapters, sequences, five-way split, mutations | Review split/mutation policy | Frozen parser/sequence/split/mutation artifacts | Deterministic artifacts and leakage audit pass |
| 3 | Frequency/Markov/IF/LSTM sources and training handoff | Run B0–B3 baselines | Baseline checkpoints/predictions/reports | Traceable baseline runs; no TEST tuning |
| 4 | SeqLogAD-T source, A0–A3 losses, training handoff | Run A0–A3 experiments | Expert A checkpoints/evidence/ablation report | Strongest expert candidates identified on validation only |
| 5 | Expert D, calibration, complementarity, F0–F6 | Review keep/remove/demote gate | Calibrated ExpertEvidence and complementarity report | Retained experts scientifically justified; fusion baselines ready |
| 6 | F7 applicability, F8 structured fusion, optional gated redundancy | Run fusion experiments | F0–F8 result bundle and ablations | Proposed fusion compared against strongest standard baselines |
| 7 | Structural retrieval evidence, verifier, downstream test recommendation | Run curated downstream review if ready | RQ5 evidence/test artifacts | Downstream uses frozen outputs; unsupported claims handled |
| 8 | Locked TEST, statistics, limitations, report/demo | Execute final TEST and approve conclusions | Immutable final metrics, CIs, report, demo | Claims mapped to evidence; negative results retained |

## Weekly operating rule

Every week ends with inspectable artifacts and a cut decision. Dense retrieval, Elasticsearch, API/UI polish, partial unfreezing, executable test sandboxing, and agent features never delay the detector/complementarity/fusion critical path.

## Stage ownership

```text
Stage 0  Freeze data artifacts                         AI prepares / HUMAN approves
Stage 1  Fit/train each expert independently          HUMAN EXECUTES
Stage 2  Freeze expert checkpoints                    HUMAN
Stage 3  Generate fusion-development evidence         HUMAN EXECUTES
Stage 4  Calibrate experts                            AI prepares / HUMAN EXECUTES
Stage 5  Measure complementarity/redundancy           AI prepares / HUMAN decides
Stage 6  Train fusion                                  HUMAN EXECUTES
Stage 7  Tune validation thresholds/abstention        HUMAN EXECUTES
Stage 8  Locked final TEST                            HUMAN EXECUTES
```

End-to-end joint training is not the default.
