# SeqLogAD Scientific Protocol — Current Entry Point

The active scientific contract is:

- human-readable: [`research-protocol-v1.1.md`](research-protocol-v1.1.md);
- machine-readable: [`../configs/protocols/protocol-v1.1.yaml`](../configs/protocols/protocol-v1.1.yaml);
- citation and method provenance: [`references/RESEARCH-FREEZE-v1.1-citations.md`](references/RESEARCH-FREEZE-v1.1-citations.md).

Its required statistical addendum is:

- human-readable: [`statistical-decision-contract.md`](statistical-decision-contract.md);
- machine-readable: [`../configs/protocols/effect-001.yaml`](../configs/protocols/effect-001.yaml);
- method provenance: [`references/EFFECT-001-citations.md`](references/EFFECT-001-citations.md).

`EFFECT-001` is `FROZEN_HUMAN_APPROVED`: `delta_HDFS = delta_BGL = 0.01 AP`, framework `RESOURCE_FEASIBILITY_MARGIN`, approval timing `PRE_EXPERIMENT`, and `result_informed = false`. Its estimand, comparison family, bootstrap, confidence level, equal-budget rule, seed aggregation, and KT-3 logic remain unchanged. This completes the statistical prerequisite but does not authorize downstream execution by itself.

Its required exact-split addendum is:

- human-readable: [`split-clarification-contract.md`](split-clarification-contract.md);
- machine-readable: [`../configs/protocols/split-clarification-v1.yaml`](../configs/protocols/split-clarification-v1.yaml);
- evidence matrix: [`literature/split-protocol-evidence-matrix.md`](literature/split-protocol-evidence-matrix.md);
- source record: [`references/PROTOCOL-SPLIT-CLARIFY-001-citations.md`](references/PROTOCOL-SPLIT-CLARIFY-001-citations.md).

`PROTOCOL-SPLIT-CLARIFY-001` is `FROZEN_HUMAN_APPROVED`. It binds Protocol v1.1 to exact cumulative-floor allocation, HDFS eligible-line/connected-component purge accounting, BGL split-before-window/per-partition residual behavior, and non-circular layered identities. It was frozen with `real_split_created=false` and `scientific_test_created=false`; execution still requires separately authorized `SPLIT-001`.

Historical protocol v1.0 is preserved at [`research-protocol-v1.0.md`](research-protocol-v1.0.md), with its original machine-readable contract at [`../configs/protocols/protocol-v1.yaml`](../configs/protocols/protocol-v1.yaml).

Protocol v1.1 supersedes v1.0 for future scientific work. It preserves the verified datasets, chronological `60/10/10/10/10` partition contract, normal-only parser fit, label isolation, three-seed policy, PR-AUC primary metric, and human-only final TEST. It changes the primary research question, reduces core scope, adds cheap falsification experiments and negative controls, and makes Transformer, localization, and fusion conditional.

No scientific experiment has run. TEST is contractually sealed but is not yet physically sealed because no split artifact, partition hashes, or access guard exists. Versioned Protocol v1.1 remains preserved; EFFECT-001 and PROTOCOL-SPLIT-CLARIFY-001 are binding addenda rather than silent rewrites of the approved file.
