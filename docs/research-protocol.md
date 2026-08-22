# SeqLogAD Scientific Protocol — Current Entry Point

The active scientific contract is:

- human-readable: [`research-protocol-v1.1.md`](research-protocol-v1.1.md);
- machine-readable: [`../configs/protocols/protocol-v1.1.yaml`](../configs/protocols/protocol-v1.1.yaml);
- citation and method provenance: [`references/RESEARCH-FREEZE-v1.1-citations.md`](references/RESEARCH-FREEZE-v1.1-citations.md).

Its required statistical addendum is:

- human-readable: [`statistical-decision-contract.md`](statistical-decision-contract.md);
- machine-readable: [`../configs/protocols/effect-001.yaml`](../configs/protocols/effect-001.yaml);
- method provenance: [`references/EFFECT-001-citations.md`](references/EFFECT-001-citations.md).

`EFFECT-001` has frozen the estimand, comparison family, bootstrap, confidence level, equal-budget rule, seed aggregation, and KT-3 decision logic. It remains `PARTIALLY_FROZEN — HUMAN DECISION REQUIRED` because `delta_HDFS` and `delta_BGL` are null. No scientific run is authorized until the human researcher supplies and approves both margins without consulting KT/TEST outcomes.

Historical protocol v1.0 is preserved at [`research-protocol-v1.0.md`](research-protocol-v1.0.md), with its original machine-readable contract at [`../configs/protocols/protocol-v1.yaml`](../configs/protocols/protocol-v1.yaml).

Protocol v1.1 supersedes v1.0 for future scientific work. It preserves the verified datasets, chronological `60/10/10/10/10` partition contract, normal-only parser fit, label isolation, three-seed policy, PR-AUC primary metric, and human-only final TEST. It changes the primary research question, reduces core scope, adds cheap falsification experiments and negative controls, and makes Transformer, localization, and fusion conditional.

No scientific experiment has run. TEST is contractually sealed but is not yet physically sealed because no split artifact, partition hashes, or access guard exists. Versioned Protocol v1.1 remains preserved; EFFECT-001 is the anticipated statistical addendum rather than a silent rewrite of the approved file.
