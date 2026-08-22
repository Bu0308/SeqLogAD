# Experiment documentation

This directory will contain human-executed run reports, result tables, paired statistics, failures, negative results, and threats-to-validity notes. Planned IDs and status live in [`../../Plan/07_EXPERIMENT_TRACKER.md`](../../Plan/07_EXPERIMENT_TRACKER.md).

No model experiment has run. Empty metric fields mean `NOT_RUN`, not zero. Final TEST execution is human-owned.

The active statistical specification is [`../statistical-decision-contract.md`](../statistical-decision-contract.md), now `FROZEN_HUMAN_APPROVED` with both margins at `0.01 AP`. This approval does not make experiment placeholders runnable or bypass their split/parser/TEST-lock dependencies.
