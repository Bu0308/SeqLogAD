# `.ai/` — agent context

Routing and context material for agents working in this repository.

**Authoritative plan: `Bang_ke_hoach_SeqLogAD.xlsx`.** Everything here is subordinate
to it. If a file in this directory disagrees with the workbook, the workbook is
right and the file is stale.

| File | Purpose |
| --- | --- |
| [`primary-context.md`](primary-context.md) | What is authoritative, active, historical, and forbidden |
| [`task-routing.md`](task-routing.md) | Workbook task graph, gates and retired routing |
| [`agent-roles.md`](agent-roles.md) | Role boundaries |
| [`escalation.md`](escalation.md) | When to stop and ask the researcher |
| [`handoff-template.md`](handoff-template.md) | Handoff format |
| [`context-packs/`](context-packs/) | Topic packs |

## Status of the context packs

`context-packs/` was written for the retired v1.1 study. `governance.md`,
`qa.md`, `literature.md`, `data-provenance.md` and `statistics.md` remain broadly
applicable. `transformer.md`, `baselines.md` and `localization-fusion.md` describe
the retired Transformer gate, the retired Markov/N-gram baseline ladder and the
retired localization/fusion gate; treat them as **historical** and do not route work
from them. The workbook's own `Task Playbooks` sheet is the current per-task method.
