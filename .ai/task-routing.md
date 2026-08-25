# Frozen task routing

Primary supplies task ID, exact scope, allowed files, and stop condition. Route governance→T1, literature→T2, provenance→T3, statistics→T4, baselines/Markov→T5, explicitly authorized `THEORY-COMPLETE-001` Transformer research/contract preparation→T6-R, gated Transformer implementation/training→T6-I, gated localization/fusion→T7, QA/reproducibility→T8, and documentation/handoff→T9. T6-R is closed before the CANONICAL QA pass. Use the matching [`context-packs/`](context-packs/) file.

## Frozen dependency graph

```text
[AUTHORIZED NEXT] CANONICAL-EVENT-001
→ SEQ-001
→ LEAK-001
→ BASE-001
→ BASE-002
→ BASE-003
→ KT-1
→ KT-2
→ KT-3
→ GATE-SEQ-001
→ conditional
→ FINAL-FREEZE-001
→ FINAL HUMAN TEST
→ REPORT-001
```

## Delivery flow

```text
Primary assignment → implementer → T8 QA & Reproducibility → Primary accept/reject
                                                         → human decision if required
```

Do not infer authorization from the graph, start a successor, use historical plans as requirements, open TEST, or execute a conditional branch without its recorded human gate. Any code from [`escalation.md`](escalation.md) stops normal routing.
