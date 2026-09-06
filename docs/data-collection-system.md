# v2 data-collection system

The collection layer observes the frozen v2 protocol; it cannot modify the
protocol, architecture set, target-buffer rule, split, model stack, metrics,
or evaluation decisions. The research protocol remains the source of truth:
[`docs/research-protocol-v2-domain-adaptive-fusion.md`](research-protocol-v2-domain-adaptive-fusion.md).

## Capture boundary

The layer stores validated, append-only process records in
`research_records/*.jsonl`: architecture and variant identities, dataset/event
and transform/split manifests, a run bridge, artifact availability, incidents,
ground-truth/causal tiers, lineage, deviations, holdout seals/access, and
toolchain metadata. Raw event payloads and target labels used for adaptation
are explicitly excluded. Native Projmem data, manually authored research
manifests, and Aletheia-derived records retain separate provenance badges.

`seqlogad-collect init` creates the portable record files. `record` validates a
single JSON object against its schema and appends it; `validate` checks parsing,
duplicate identities, project-relative paths, and core cross-record references.
Collection may be used at capture levels A/B/C from the supplied guide, but
the repository does not require continuous filesystem or process surveillance.

## Status boundary

Technical execution status and scientific interpretation status are separate
fields. Missing artifacts and denominators remain explicit. Ground-truth
correctness is eligible for claims only at G3/G4, and causal claims only at
C3/C4. A future handoff may build restricted/public packages and an Aletheia
import descriptor, but those are not prerequisites for the current v2 plan.

The requirement-to-repo mapping is recorded in
[`docs/data-collection-gap-matrix.md`](data-collection-gap-matrix.md).
