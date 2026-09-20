# Notebooks

Phase-2 training notebooks are mandatory reproducible entry points under
[the P2.0 contract](../docs/protocol/P2.0-phase2-architecture-contract.md#8-mandatory-notebook-first-deliverables-and-artifact-map).
Reusable Python modules remain authoritative; notebooks orchestrate them.

The active seed-42 development amendment provides these thin GPU orchestrators:

- `P2.1_run_all_semantic_s42.ipynb` — READY for a RunPod NVIDIA A40; registers
  the verified BGL-S42 run, then trains/resumes HDFS-S42 and Hadoop-S42
  sequentially with bounded recovery on the `/workspace` Network Volume.
- `P2.2_run_all_sequence_lora_s42.ipynb` — READY for the same RunPod A40 class;
  trains/resumes the independent Sequence-LoRA reference on the materialized
  sequence view and persists recovery/final artifacts under `/workspace/SeqLogAD/P2.2`.
- `P2.3_run_all_lightweight_sequence_s42.ipynb` — BLOCKED fail-closed until the
  lightweight architecture/resource criterion, sequence view and trainer exist.
- `P2.4_run_all_gtat_s42.ipynb` — BLOCKED fail-closed until the exact GTAT
  graph/temporal specification, graph view and trainer exist.

All four lock `SEED=42` and target order `BGL → HDFS → HADOOP`. P2.3–P2.4 remain
explicit blocker notebooks rather than non-authoritative placeholder trainers.
The controlling contract is
`configs/protocols/phase2-development-s42-v1.yaml`. Multi-seed confirmation is
deferred and no scientific-stability claim is made.

These names use P2_ARCH_V1; workbook migration completed in P2.0.1. P2.0 does
not authorize training. Future notebooks take explicit DATA_ROOT and OUTPUT_ROOT,
verify the portable `data/phase2/` bundle and record environment/seed/revisions.
Exploration notebooks remain allowed but are never the only pipeline implementation.

P2.PRE addendum: every future Phase-2 real-training task must provide a portable
GPU notebook. P2.1 and P2.2 use RunPod as their primary runtime, ephemeral active
output under `/tmp`, and verified persistent recovery under
`/workspace/SeqLogAD`. Their extracted data roots are respectively
`/workspace/.../phase2` and `/workspace/.../phase2_sequence`; repository sources
remain `data/phase2/` and `data/phase2-sequence/`.
Load frozen model/runtime policy from `configs/models/base-freeze-v1.yaml`; expose
OUTPUT_ROOT, HF_TOKEN secret mechanism, SEED, training mode and resume checkpoint.
