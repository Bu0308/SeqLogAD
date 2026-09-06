# SeqLogAD — Master Plan v2: Domain-Adaptive Fusion

**Status:** PLANNED — user-directed strategy, 2026-08-28  
**Empirical status:** NOT_RUN  
**Purpose:** replace the former single-benchmark forward plan with a zero-label, cross-architecture research programme. Historical v1.1 HDFS/BGL assets remain preserved as source-domain provenance only.

## 1. Objective

Build and evaluate a **Domain-Adaptive Fusion** model that transfers knowledge from heterogeneous source architectures, then learns the normal behaviour of an unseen target architecture from an unlabeled burn-in buffer. The output is an anomaly score, calibrated confidence, contributing expert(s), anomalous log/event location, and an `unknown / review` state when confidence is insufficient.

The claim is deliberately bounded: the model is evaluated on held-out architectures available in the study. It must not claim universal detection for every possible architecture, or immediate detection before observing enough target normal behaviour.

## 2. System architecture

```text
raw target logs (timestamp, level, service, component, message)
  -> field normalisation + dynamic-value masking + optional Drain3 template
  -> pretrained semantic encoder + domain-invariant representation
  -> semantic expert | sequence expert | structural/time expert
  -> target-normal calibration + drift and uncertainty estimation
  -> adaptive fusion gate
  -> score, confidence, evidence, localised log/event, abstain/review flag
```

The parser is not an anomaly model. It is one optional structural view; raw-text semantics must be retained for unseen templates and log formats.

## 3. Learning contract

### Source learning

- Use multiple heterogeneous source systems, not only HDFS/BGL.
- Train representation and fusion-gate behaviour with episodic leave-one-architecture-out folds.
- Learn domain-invariant features through self-supervised masked/next-event objectives, contrastive alignment and, if justified, domain-adversarial training.
- Preserve each source dataset's chronology and prevent target labels from entering adaptation or score calibration.

### Target adaptation

- Accept an unlabeled target burn-in buffer that is expected to be predominantly normal; record buffer length, assumed contamination bound and readiness checks.
- Build local prototypes, sequence transition statistics, score quantiles and drift baselines from that buffer only.
- Do not use target anomaly labels to select experts, tune thresholds or train fusion weights.
- Recalibrate after approved drift checks; version each target baseline and retain its provenance.

## 4. Experts and fusion

| Expert | Input | Role |
|---|---|---|
| Semantic expert | masked raw message + template | **Llama-3.1-8B + LoRA-Semantic** detects novel/error semantics |
| Sequence expert | time-ordered log embeddings | **Llama-3.1-8B + separate LoRA-Sequence** scores improbable next-log context |
| Structural/time expert | event, service, component and time graph | **Temporal Graph Transformer (GTAT)** detects anomalous topology, bursts and time patterns |

Llama-3.1-8B is shared as the frozen base model but its two adapters are
independent trainable artifacts: `LoRA-Semantic` is trained for message-level
semantic anomaly scoring and `LoRA-Sequence` for next-log prediction. They
must never share adapter weights or adaptation checkpoints. GTAT is a separate
graph model. Every expert emits `score`, `uncertainty`, `coverage`, `evidence`
and `localisation`. Raw scores are transformed using target-normal quantiles
before fusion. The gate derives weights from calibrated scores, uncertainty,
coverage, target drift and sequence context:

`S_fusion = sum_i w_i(x, drift, uncertainty) * calibrated_score_i(x)`.

Weights are trained only in source-domain episodic folds; the target receives unlabeled adaptation, never label-based target tuning. A fixed equal-weight ensemble is the mandatory comparator. The gate must demonstrate improvement, stability and non-trivial expert diversity before it replaces that comparator.

## 5. Evaluation protocol

1. Hold one full architecture out as target; never create random mixed-system splits.
2. Train on the remaining source architectures and adapt only from the target's unlabeled normal buffer.
3. Test chronologically on later target logs; preserve labels exclusively for final evaluation.
4. Report per-target PR-AUC/AP, AUROC, false-alert rate on normal periods, time-to-detect, latency, calibration/abstention rate and bootstrap uncertainty.
5. Run ablations: remove each expert, replace adaptive gate with equal weighting, remove target adaptation, and remove semantic/sequence/structural views.
6. Stress-test cold start, new templates, log-volume drift and contaminated burn-in buffers. Freeze source data, target buffer, thresholds and gate configuration before final held-out evaluation.

## 6. Four-phase roadmap

1. **Data and protocol foundation:** multi-source acquisition, canonical schema, target-buffer/adaptation contract, chronological leave-one-architecture-out split and leakage guards.
2. **Universal representation and experts:** semantic, sequence and structural/time experts plus a common evidence/uncertainty schema.
3. **Target adaptation and adaptive fusion:** local normal memory, calibration, drift estimator, gate meta-training and explanation contract.
4. **Cross-architecture validation and report:** held-out architecture evaluation, ablation, robustness, final freeze and reproducible report.

## 7. Decision gates

- **G0 — Protocol ready:** at least three source architectures and one independent target architecture; target-label isolation and chronology audit pass.
- **G1 — Adaptation ready:** target burn-in contract, contamination guard and local calibration pass without labels.
- **G2 — Expert diversity:** each selected expert adds evidence beyond the best single expert on source-held-out validation.
- **G3 — Fusion justified:** adaptive gate is more stable than equal-weight fusion across held-out architectures and does not worsen false-alert control.
- **G4 — Final evaluation:** data/model/gate/threshold artifacts frozen before one final untouched held-out evaluation.

## 8. Literature anchors

- LogDLR (IEEE TDSC, 2025): domain-invariant representations with universal sentence embeddings, Transformer autoencoder and adversarial adaptation.
- ZeroLog (2025): zero-label cross-system anomaly detection using meta-learning and unsupervised domain adaptation.
- LogLLaMA (2025): LLaMA-based next-log modelling; informs the two-adapter Llama design, without copying its label/RL branch.
- LogGT (2024): graph Transformer with time and component information; informs GTAT when target topology fields exist.
- FusionLog (2025): zero-label cross-system fusion of general and target-specific knowledge; informs target-adaptation boundaries.

## 9. Ownership and limits

AI/Codex prepares reproducible schemas, implementations, tests, builders and reports. The researcher approves dataset eligibility, target burn-in assumptions, model selection policy, empirical runs and final conclusions. No metric, threshold or claim is recorded without traceable immutable artifacts.
