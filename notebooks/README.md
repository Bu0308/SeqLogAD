# Notebooks

Phase-2 training notebooks are mandatory reproducible entry points under
[the P2.0 contract](../docs/protocol/P2.0-phase2-architecture-contract.md#8-mandatory-notebook-first-deliverables-and-artifact-map).
Reusable Python modules remain authoritative; notebooks orchestrate them.

Planned, NOT CREATED YET:

- `P2.1_train_semantic_expert.ipynb`
- `P2.2_train_sequence_reference.ipynb`
- `P2.3_train_lightweight_sequence_expert.ipynb`
- `P2.4_train_gtat_expert.ipynb`

These names use P2_ARCH_V1; workbook migration completed in P2.0.1. P2.0 does
not authorize training. Future notebooks take explicit DATA_ROOT and OUTPUT_ROOT,
verify the portable `data/phase2/` bundle and record environment/seed/revisions.
Exploration notebooks remain allowed but are never the only pipeline implementation.
