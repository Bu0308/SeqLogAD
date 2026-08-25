# Primary context: nine required answers

## 1. What is the objective?
Measure how much anomaly-detection value sequence order adds beyond strong order-insensitive baselines under a leakage-controlled, chronological, equal-budget protocol. Null/negative results are valid.

## 2. What is authoritative?
The read-only stack is [`../docs/research-protocol-v1.1.md`](../docs/research-protocol-v1.1.md) + [`../configs/protocols/protocol-v1.1.yaml`](../configs/protocols/protocol-v1.1.yaml), with [`../configs/protocols/effect-001.yaml`](../configs/protocols/effect-001.yaml), [`../configs/protocols/split-clarification-v1.yaml`](../configs/protocols/split-clarification-v1.yaml), and [`../configs/protocols/purge-decision-v1.yaml`](../configs/protocols/purge-decision-v1.yaml). [`../configs/active-state.yaml`](../configs/active-state.yaml) is the operational pointer registry, not an amendment mechanism.

## 3. Who owns decisions?
No agent, including Primary, owns or may amend the frozen scientific plan. Primary orchestrates, accepts/rejects work against the contract, and routes scientific decisions to the human owner. Sub-agents act only within an explicit task.

## 4. What is active versus historical?
Active planning: [`../Plan/00_MASTER_PLAN.md`](../Plan/00_MASTER_PLAN.md) and [`../Plan/master-implementation-plan-v1.1.md`](../Plan/master-implementation-plan-v1.1.md). Protocol v1.0 and V1/V2/V3 plans are historical provenance only and cannot override v1.1/ADR-025.

## 5. What is complete and what is next?
SPLIT-001 and PURGE-AUDIT-001 are complete; PARSE-001 is complete/frozen; PURGE-DECISION-001 is frozen/human-approved. Scientific results remain `NOT_RUN`; no canonical event corpus exists. `CANONICAL-EVENT-001` is the one next authorized scientific task, but only a separate assignment may start it.

## 6. What identities are authoritative?
HDFS fingerprint `0103c63b...a34013`, split payload `21ec061a...fc4295c`, TEST partition `fa0c7436...3175d`, parser state `7d9bd804...da8d91`; BGL fingerprint `c9ee7a8d...afbe861`, split payload `0c1bb1b9...ebd05`, TEST partition `7ecf43ab...96a876d`, parser state `e44649d2...e4f6`. Full hashes and artifact pointers are authoritative only in [`../configs/active-state.yaml`](../configs/active-state.yaml).

## 7. What are the TEST and label/leakage boundaries?
Both TEST partitions are `SEALED / NEVER_OPENED`, with zero opens/unlock records. Deny TEST labels, counts, previews, metrics, membership, and model comparisons. Labels may be used only in contract-authorized scopes; never as parser/model features or base self-supervised loss. Escalate any leakage signal.

## 8. What human gates remain?
Human ownership remains for empirical execution/training/tuning, validation-only selections/freezes, KT-1→KT-3 gate decisions, conditional Transformer/localization/fusion openings, any protocol amendment, one final TEST run after artifact/claim freeze, and scientific conclusions. The purge sensitivity stays secondary, non-selection, and `NOT_RUN` until its registered timing.

## 9. How is work routed and accepted?
All roles use `gpt-5.6-sol`: Primary `xhigh`; T1/T3/T4/T5/T6-R/T6-I/T7 `high`; T2/T8/T9 `medium`. T6-R is closed before the CANONICAL QA pass and limited to research/contract preparation during explicitly authorized `THEORY-COMPLETE-001`; T6-I Transformer implementation/training remains closed. Use the narrowest context pack; implementer hands to T8 QA & Reproducibility, then Primary accepts/rejects or routes a human decision. Conflicts follow [`escalation.md`](escalation.md).
