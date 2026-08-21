# Research Questions — Freeze v1.1

All questions are **HYPOTHESIS — TO BE TESTED**. No scientific experiment has run.

## RQ1 — Dataset suitability

**Question:** Do the exact verified HDFS/BGL artifacts contain enough non-trivial sequential information under the SeqLogAD protocol to support sequence-based anomaly-detection claims?

- **Priority:** CORE / MUST
- **Hypothesis:** Dataset suitability may differ by dataset and exact protocol; no positive outcome is assumed.
- **Experiment concept:** KT-1 and KT-2 compare trivial/strong order-insensitive controls and quantify count/label dependence before complex models.
- **Primary metric:** PR-AUC; supplemented by collision/purity/conditional-dependence diagnostics and FPR/latency.
- **Required components:** Frozen split, parser/events/sequences, unseen-event/length/count/count-vector baselines, optional Isolation Forest.
- **Falsification:** If order-insensitive behavior reaches the pre-frozen practical ceiling, that dataset cannot support a sequence-advantage claim by itself.

## RQ2 — Sequence added value

**Question:** How much additional anomaly-detection value does a minimal sequential model provide beyond strong order-insensitive baselines?

- **Priority:** CORE / MUST
- **Hypothesis:** Markov/N-gram may add value when transition structure carries label-relevant information; it may also add no meaningful value.
- **Experiment concept:** Compare Markov/N-gram with the strongest legal order-insensitive comparator under the same partitions, selection budget, thresholds, and metrics.
- **Primary metric:** Paired PR-AUC difference with uncertainty; secondary Precision, Recall, F1, FPR, latency, throughput, memory.
- **Required components:** RQ1 artifacts plus Markov/N-gram.
- **Falsification:** If added value is below the pre-frozen practical margin, do not claim sequence advantage.

## RQ3 — Order sensitivity

**Question:** Does destroying event order materially reduce sequential-detector performance while preserving event counts and length?

- **Priority:** CORE / MUST
- **Hypothesis:** A genuinely order-sensitive detector should degrade under valid sequence destruction; magnitude is unknown.
- **Experiment concept:** KT-3 applies deterministic within-sample permutations preserving event multiset, count vector, length, label, partition, and parent linkage.
- **Primary metric:** Paired PR-AUC/per-sample score change and uncertainty under original versus order-destroyed inputs.
- **Required components:** Frozen sequence artifacts, Markov/N-gram predictions, deterministic destruction manifest.
- **Falsification:** No practically meaningful degradation blocks an order-sensitivity claim on that dataset/protocol.

## Conditional RQ4 — Localization faithfulness

**Question:** If meaningful sequence signal exists, can anomaly-causing token/gap/transition positions be localized more faithfully than sanity controls?

- **Priority:** CONDITIONAL
- **Opening gate:** RQ1–RQ3 support sequence signal, synthetic targets are valid, and KT-4/KT-5 are pre-registered.
- **Hypothesis:** Coordinate-aware localization may identify causal perturbations better than randomized positions; no positive outcome is assumed.
- **Experiment concept:** Separate token/gap/transition metrics, target-position randomization, and counterfactual repair/deletion.
- **Primary metrics:** Coordinate-family precision/recall/ranking plus counterfactual score change against matched controls.
- **Falsification:** Failure against randomization or counterfactual sanity controls removes localization faithfulness from the contribution.

## Non-primary questions

Transformer, complementarity/fusion, RAG/Agent, and regression-test recommendation are not active RQs. They require a later protocol amendment after their gates and cannot substitute for RQ1–RQ3.

## Claim states

Allowed empirical claim states: `PROPOSED`, `HYPOTHESIS`, `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `REJECTED`.

Novelty remains independently `UNVERIFIED` until `LIT-001` is complete. External paper results are prior-work evidence, never SeqLogAD results.
