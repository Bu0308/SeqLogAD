# Agent roles and model assignments

All roles use `gpt-5.6-sol`. Roles advise or implement only within an explicitly assigned task; none owns the scientific plan.

| Role | Assignment | Effort |
|---|---|---|
| Primary | Orchestration, contract-based acceptance/rejection, human-decision routing | `xhigh` |
| T1 Governance | Contract/boundary review and conflict detection | `high` |
| T2 Literature | Verified source retrieval and claim classification | `medium` |
| T3 Data provenance | Dataset, split, parser, artifact identity, leakage boundary | `high` |
| T4 Statistics | EFFECT-001 interpretation and statistical implementation review | `high` |
| T5 Baselines | Order-insensitive and Markov/N-gram implementation tasks | `high` |
| T6-R Transformer Research | Closed before the CANONICAL QA pass; research/contract preparation only during explicitly authorized `THEORY-COMPLETE-001` | `high` |
| T6-I Transformer Implementation | Execution gate closed; implementation/execution requires a recorded human gate opening | `high` |
| T7 Localization/Fusion | Conditional localization/fusion only after recorded human gate opening | `high` |
| T8 QA & Reproducibility | Contract tests, determinism, leakage, TEST seal, reproducibility review | `medium` |
| T9 Documentation | Pointer docs, handoffs, status-neutral reporting | `medium` |

No agent, including Primary, owns or may amend the frozen scientific plan. T1–T9 escalate instead of changing methodology or active state. T6-R is closed before the CANONICAL QA pass and limited to research/contract preparation during explicitly authorized `THEORY-COMPLETE-001`; T6-I Transformer implementation/training and T7 conditional implementation remain closed until their respective gates open. T9 never promotes task or empirical status.
