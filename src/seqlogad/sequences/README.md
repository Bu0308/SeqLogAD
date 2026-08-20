# Sequences

Planned dataset-specific sequence construction:

- HDFS block/session grouping with group-aware chronology;
- BGL chronology-aware windows created only inside partitions;
- deterministic mutation records for missing, extra, reorder, and repeat cases.

Localization uses separate token, gap, and transition coordinates. Inputs are canonical parsed events; outputs carry partition and source-artifact provenance. No sequence data has been generated.
