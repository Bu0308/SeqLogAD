# PARSE-001 — Normal-only parser fit and freeze

Status: `COMPLETE / DERIVED ARTIFACTS VERIFIED`  
Date: 2026-08-23  
Scientific outcome status: `NOT_RUN`  
Scientific TEST: `SEALED / NEVER_OPENED`

## Scope and access contract

PARSE-001 consumes only structural `BASE_TRAIN` membership and the labels
needed to select the permitted normal fitting pool. It fits one separate
Drain3 state for HDFS and BGL, persists it, restores it independently, and
exposes an immutable `match`-only transform. It does not generate the full
canonical event corpus, build sequences, fit anomaly detectors, or compute
anomaly metrics.

The pre-fit gate binds every parser state to:

- accepted dataset fingerprint and source-file SHA-256;
- Protocol v1.1 and frozen EFFECT-001 status;
- split payload and `BASE_TRAIN` partition hashes;
- active unopened TEST seal (`open_count=0`, `unlock_records=0`);
- pre-registered parser/normalization/masking configuration.

## Normal-selection contracts

### HDFS

1. Read ordinary `BASE_TRAIN` component membership only.
2. Derive the allowed block-ID set before consulting the separate label file.
3. Because the canonical CSV is a single physical file, scan it at storage
   level but expose/retain only labels whose block IDs are in that allowed set.
4. Retain an entire connected component only when every member block/session
   has the exact `Normal` label; fail closed on missing or unknown labels.
5. Persist only selected source indices and aggregate structural provenance,
   never raw labels or copied messages.

### BGL

1. Read labels only from source lines belonging to complete ordinary
   `BASE_TRAIN` parent windows.
2. Select normal events at the source's event-level label granularity (`-`).
3. Do not read one source line beyond the `BASE_TRAIN` upper boundary.
4. A valid 9-field source record with no free-text Content is deterministically
   mapped to `SEQLOGAD_EMPTY_CONTENT`; this rule was frozen before the first
   successful real fit.
5. Persist no inline label or copied message.

## Frozen configuration

The complete contract is
[`../configs/parsing/drain3-v1.yaml`](../configs/parsing/drain3-v1.yaml).
Drain3 is pinned to `0.9.11`. The official defaults retained are similarity
threshold `0.4`, depth `4`, max children `100`, no cluster cap, no extra
delimiters, and numeric-token parameterization. These settings were not tuned
against anomaly labels or metrics and are not claimed optimal.

Masks are frozen for HDFS block IDs, IPv4 endpoints (optional port), and
hexadecimal literals. A block ID is a session/grouping identity rather than an
event type and would otherwise fragment templates by block instance. Endpoint
addresses/ports and hexadecimal literals are treated as volatile runtime
parameters. Severity, component, generic paths, and arbitrary integers are
intentionally not blanket-masked because they may carry event semantics; this
is a conservative pre-outcome choice, not a claim that every retained token is
useful. “Not blanket-masked” refers to custom regex masks; Drain3's frozen
official default `parametrize_numeric_tokens=true` still applies during its
template mining. Exact rationale and evidence classification are recorded in
[`references/PARSE-001-citations.md`](references/PARSE-001-citations.md).

## Real normal-pool provenance

| Dataset | Candidate BASE records | Selected normal records | Selection units selected/excluded | Normal-pool SHA-256 |
|---|---:|---:|---:|---|
| HDFS | 5,782,072 | 5,606,995 | 252,576 / 10,113 connected components | `bce127f5c98b120d4ce77be63359b413443ee652980a4846febc7e1c222dad71` |
| BGL | 2,848,700 | 2,616,821 | 2,616,821 / 231,879 events inside 28,487 complete parents | `37654dd24804d561442a79a7fd67cb02379efd7bd9b50573ddac4bbd62058e72` |

These are fitting-provenance counts from an authorized non-TEST partition,
not anomaly prevalence or model-performance results.

## Frozen parser identities

Both datasets share parser config SHA-256
`c5bb4fd25ecc98667700cbb3095fb561ba4b6651b2815400adc91e5efba0d65c`.

| Dataset | Fit records | Clusters/templates | Scientific state SHA-256 | Serialized state SHA-256 | Registry SHA-256 |
|---|---:|---:|---|---|---|
| HDFS | 5,606,995 | 18 / 18 | `7d9bd8041d00ee3a1ce6c32d8e19efd8764108d8695f559ec91b4381ecda8d91` | `a2cf8f022069765262d4cfaf5290ccba6f5c5a42cb4aa43dd87c61311be4c10e` | `054c93635dc5427cc01d23dce7ba1df850e28db13a4087c8629e42a1ed421ccb` |
| BGL | 2,616,821 | 477 / 477 | `e44649d24afbd4bc335e2d38d54cea9338c211c600baef185cd7a0dee6aee4f6` | `6ee0189715a31f59117a02d498adf7b8916832951c9516b83692a6a776952c69` | `bc4ac9e2c6ea51e712ed06c0648372d6ed800f2788d135cd5cc89d7d1047d17f` |

Separate cluster-state and exact manifest-file hashes are stored in each local
manifest. The exact manifest hashes are HDFS
`35400de68ede9907a4f2d3445125bdc27ae434c61dcf2f93c48b825b4000a025`
and BGL
`bc2fd7df13ee231c0e9e63597e3237cd48ebb1658c4609524f04087cf49cfd66`.
Timestamps do not participate in scientific parser-state identity.

## Frozen transform and unknown handling

- Fit uses `TemplateMiner.add_log_message` only inside the fit routine.
- The public restored parser exposes no mutating add method.
- Transform rejects scientific `TEST` before calling Drain3.
- Legal later transforms call `TemplateMiner.match(...,
  full_search_strategy="fallback")` only.
- Canonical cluster-state SHA-256 is checked before and after every transform.
- A message with no perfect frozen match maps to the single schema-supported
  ID `EVT_UNSEEN`; it never creates a cluster.

PARSE-001 smoke tests use synthetic non-TEST messages. It does not transform a
real later partition and does not produce a canonical event corpus.

## Derived artifacts and Git policy

Local non-overwriting artifacts live under:

```text
data/processed/parsers/hdfs/
data/processed/parsers/bgl/
```

Each directory contains `drain3-state.bin`, `template-registry.json`,
`normal-pool-summary.json`, `parser-manifest.json`, and
`parser-manifest.json.sha256`. They are reproducible derived data and remain
ignored by Git. Source, tests, the frozen YAML contract, and this provenance
note are version-controlled.

## Safe commands

```bash
seqlogad-fit-parser --project-root . gate --dataset hdfs --json
seqlogad-fit-parser --project-root . gate --dataset bgl --json
seqlogad-fit-parser --project-root . pool --dataset hdfs --json
seqlogad-fit-parser --project-root . pool --dataset bgl --json
seqlogad-fit-parser --project-root . validate --dataset hdfs --json
seqlogad-fit-parser --project-root . validate --dataset bgl --json
```

`fit` is deliberately non-overwriting. Reproduction must target a new empty
derived directory and compare deterministic identities; it must never replace
an accepted parser artifact in place.
