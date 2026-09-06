# CANONICAL-NUL-DECISION-001

## Status

| Field | Value |
| --- | --- |
| Decision status | `FROZEN_HUMAN_REVIEW_READY` |
| Human approval | `PENDING` |
| Prepared | 2026-09-06 |
| Parent protocol | Protocol v1.1 |
| Scope | Maintenance amendment to the frozen v1.1 data foundation |
| Scientific results | `NOT_RUN` |
| Real canonical corpus | `NOT_CREATED` |
| TEST | `SEALED / NEVER_OPENED` |

This record is a proposal, not a binding protocol addendum. It becomes binding
only after the human researcher explicitly approves the payload in
[Human approval payload](#human-approval-payload). It does not reactivate or
replace any broader research plan.

## Exact conflict

Four retained, non-TEST BGL source lines contain one literal `0x00` byte in
their message content. The current contracts cannot carry those observations
through the pipeline:

```text
retained raw BGL line containing 0x00
→ source extraction preserves U+0000
→ frozen parser input validator rejects NUL
→ EventObservation.message rejects NUL
→ no canonical event can be emitted
→ silently dropping the line would break one-line-one-event
   and a retained BGL parent would contain 99 rather than 100 events
```

This is a narrow canonical-observation representation gap. It is not evidence
of corruption, a reason to refit Drain3, or a reason to change the split,
scientific population, central RQ, EFFECT-001, or TEST policy.

## Verified raw findings

The verification scanned only assignment records from `BASE_TRAIN`,
`FUSION_TRAIN`, `VAL_EXPERT`, and `VAL_FUSION`. It did not open the sealed TEST
membership file and did not invoke the TEST membership loader.

| Source line | Chronological index | Partition | Parent position | NUL bytes | Source-line SHA-256 |
| ---: | ---: | --- | ---: | ---: | --- |
| 4,223,248 | 4,223,247 | `VAL_FUSION` | 77 | 1 | `e40a4614942300fd6d750d8678fc9a7faec2182008d65d5d2a44a9624a35ba56` |
| 4,223,278 | 4,223,277 | `VAL_FUSION` | 7 | 1 | `9de58b31c6b153aa9f3f990c786b3c985484c6547ecbe934bf9ec4271c152964` |
| 4,224,013 | 4,224,012 | `VAL_FUSION` | 42 | 1 | `9bf7b4a5fc88eaafc7cbd54967037a8f948bef5fb734d9e84e74c52b00af7a3b` |
| 4,224,014 | 4,224,013 | `VAL_FUSION` | 43 | 1 | `68e10db19a9af57e6af24414226f7a9700fb59b731c0b80fc27c06f169e9709d` |

The four lines occupy three retained 100-event parents. Each message has one
NUL at zero-based message byte offset 200. Their exact extracted message bytes
share SHA-256
`6f301ecb31188e412b425e639181dd5a9890eecb83bf24c5c85742e53b261b93`.
Bytes surrounding the NUL decode as UTF-8 normally.

Eight additional non-TEST source lines—3,865,490; 3,865,492; 3,875,813;
3,875,814; and 3,884,944–3,884,947—contain sixteen `0x0f` bytes and two
`0x10` bytes in source metadata fields, not in parser-facing message content.
Existing validators do not reject those fields. They are an informational
finding and are deliberately outside this NUL-specific amendment.

## Representation-layer boundary

The following identities remain distinct:

| Layer | Meaning |
| --- | --- |
| `RAW_BYTES` | Exact immutable full source-line bytes. |
| `CANONICAL_PARSER_INPUT` | Deterministic, parser-safe text derived from the raw message bytes. |
| `CANONICAL_EVENT_MESSAGE` | The same NUL-free text persisted in `EventObservation.message`. |
| `EVENT_TEMPLATE_ID` | Existing frozen template mapping, or `EVT_UNSEEN` when no template matches. |

`CANONICAL_PARSER_INPUT` never replaces raw provenance. The existing
`source_line_sha256` continues to bind the exact source line. A separate
`raw_message_sha256` binds the exact bytes of the extracted `Content` field.

## Evidence classification

| Statement | Classification |
| --- | --- |
| Syslog message content can contain NUL and NUL requires careful handling. | `LITERATURE_SUPPORTED` |
| Silent character dropping is poor interoperability practice. | `LITERATURE_SUPPORTED` |
| Original and normalized log representations should be traceably distinct. | `LITERATURE_INFORMED_SEQLOGAD_DECISION` |
| A transformation should have source→activity→derived provenance. | `LITERATURE_INFORMED_SEQLOGAD_DECISION` |
| Drain3 v0.9.11 `match()` is the read-only inference path. | `LITERATURE_SUPPORTED` by official tagged source |
| SeqLogAD will use the exact codec below. | `SEQLOGAD_PROTOCOL_DECISION` |
| The codec implementation, validation, and envelope wiring are implementation details. | `ENGINEERING_DECISION` |

No reviewed source prescribes a Drain3-specific NUL codec. The selected codec
is therefore a versioned SeqLogAD decision informed by standards and
provenance principles, not a literature-proven universal policy.

## Candidate-policy assessment

### Option A — versioned deterministic NUL escaping

Convert NUL-bearing raw message bytes to a collision-safe textual
representation before frozen Drain3 matching. Preserve both raw hashes and add
typed representation metadata outside model attributes.

Assessment: preserves population, chronology, cardinality, parser state, and
raw provenance. It requires only a canonical artifact-envelope amendment and a
small deterministic codec. **Recommended.**

### Option B — allow literal NUL

Widen `EventObservation`, parser-input, parameter, template, and downstream
compatibility contracts to accept literal NUL.

Assessment: Python strings can carry NUL, but Drain3 publishes no NUL-specific
compatibility guarantee, RFC 5424 warns about NUL handling risks, and this
option changes more frozen boundaries than necessary. **Rejected.**

### Option C — dedicated malformed/control-character event

Emit a dedicated event rather than matching a parser-safe message.

Assessment: a bypass or special event ID introduces artificial event semantics
and touches the frozen registry contract. If it first maps the message to safe
text and then calls Drain3, it is merely a weaker form of Option A. **Fallback
only; not selected.**

### Option D — exclude lines or parents

Drop the four lines or their three parent windows.

Assessment: dropping a line violates one-line-one-event and produces a
99-event parent; dropping a parent changes the frozen evaluation universe.
Neither is necessary because Option A is feasible. **Rejected.**

## Decision matrix

| Policy | Scientific population changed? | One line → one event? | Lossless raw provenance? | Drain3 compatible? | Parser refit? | Schema change? | Deterministic? | Collision risk | Reproducible? | Complexity | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A — versioned escape | No | Yes | Yes | Yes | No | Artifact envelope only | Yes | Controlled by typed status + grammar | Yes | Low–moderate | **Select** |
| B — literal NUL | No | Yes | Yes | Unverified/risky | No expected, but broad validators change | Multiple contracts | Potentially | N/A | Uncertain across tools | Moderate–high | Reject |
| C — dedicated malformed event | No | Yes | Yes | Bypass or degenerates to A | No | Event semantics/registry risk | Yes | Low | Yes | Moderate | Fallback only |
| D — exclude | Yes, or parent cardinality changes | No | Source remains but observation removed | N/A | No | Exclusion contract | Yes | N/A | Yes | Low | Strongly reject |

## Recommended policy

Select **Option A: `seqlogad-nul-escape-v1`** after human approval.

### Deterministic codec

The function contract for the resumed implementation is:

```text
canonicalize_nul_message(raw_message_bytes: bytes) -> CanonicalizedMessage
```

Returned fields:

```text
canonical_message: str
normalization_status: UNCHANGED | NUL_ESCAPED
raw_message_sha256: lowercase SHA-256
policy_version: seqlogad-nul-escape-v1
```

Rules:

1. Compute `raw_message_sha256` over the exact extracted `Content` bytes,
   after source metadata separation, before UTF-8 decoding, and excluding the
   source line terminator.
2. If no `0x00` exists, strict UTF-8 decode the original bytes. Return the
   decoded text unchanged with status `UNCHANGED`.
3. If `0x00` exists, replace every original `0x5c` byte (backslash) with two
   `0x5c` bytes, then replace every `0x00` with the visible four-byte ASCII
   sequence `0x5c 0x78 0x30 0x30` (`\x00`). Strict UTF-8 decode the result and
   return status `NUL_ESCAPED`.
4. A decoder is selected only when status is `NUL_ESCAPED`: `\\` decodes to an
   original backslash and `\x00` decodes to NUL. Any other escape is invalid.
5. The transform receives no label, partition, parent, TEST, or model-result
   input.

The status-conditioned grammar resolves collisions. A raw literal `\x00` is
escaped as `\\x00` within a `NUL_ESCAPED` message; a raw NUL becomes `\x00`.
An ordinary raw literal `\x00` remains unchanged with status `UNCHANGED`.
Canonical text alone is not a provenance identity.

## Exact proposed amendment

For a transformed record, add an envelope-level block:

```json
{
  "message_representation": {
    "policy_id": "CANONICAL-NUL-DECISION-001",
    "policy_version": "seqlogad-nul-escape-v1",
    "status": "NUL_ESCAPED",
    "raw_message_sha256": "<sha256 of exact original Content bytes>"
  }
}
```

`EventObservation.message` stores `canonical_message`. The block is outside
`EventObservation.attributes`, so normalization status cannot become a model
feature through the existing model-input conversion.

For an unchanged record, omit `message_representation`; the corpus manifest
binds the policy and defines omission as `UNCHANGED`. The implementation-level
return object still exposes status and raw hash for validation. This minimizes
artifact overhead without making transformed records ambiguous.

The corpus manifest must bind:

- policy ID and version;
- omission semantics;
- artifact envelope version;
- implementation version;
- existing split, partition, dataset, parser-state, registry, and config
  identities.

The label-independent canonical record identity includes the representation
block when present. The representation identity is the tuple:

```text
(policy_version, normalization_status, canonical_message, raw_message_sha256)
```

## Schema and versioning impact

| Contract | Proposed state after approval |
| --- | --- |
| Protocol v1.1 | Unchanged |
| `EventTemplate` schema | `1.0`, unchanged |
| `LogEvent` / `EventObservation` schema | `1.0`, unchanged |
| Frozen parser normalization | `seqlogad-message-v1`, unchanged |
| Drain3 config/state/registry | Unchanged |
| Canonical artifact envelope | `1.0` → `1.1` for newly generated corpus |
| Canonical implementation | `seqlogad-canonical-event-001-v1` → `v2` |
| NUL policy | New `seqlogad-nul-escape-v1` |

Historical schema/envelope 1.0 records remain interpretable through a separate
validator branch and must never be rewritten. No real canonical corpus exists,
so this proposal does not migrate scientific artifacts.

## Frozen parser impact

Drain3 remains version `0.9.11`, `RESTORE_ONLY`, with updates forbidden. The
codec executes after field/label isolation and before `TemplateMiner.match()`.
It cannot fit clusters, update templates, change the parser config, or learn
from `VAL_FUSION`.

A read-only feasibility check passed the four transformed messages through the
existing frozen BGL parser. All four deterministically returned `EVT_UNSEEN`,
which is the existing fallback. Parser state, parser manifest, and template
registry hashes were identical before and after. This is an engineering
compatibility check, not a scientific result.

## Provenance and hash contract

- `source_line_sha256`: existing exact full raw-line identity; unchanged.
- `raw_message_sha256`: exact extracted raw `Content` bytes before decode;
  added only to the transformed record envelope.
- `canonical_message`: parser-safe derived text; never described as raw text.
- `canonical_event_sha256`: label-independent canonical payload identity; must
  include representation metadata when present.
- Corpus identity: binds the policy plus all frozen dataset/split/parser
  identities.
- Raw data, source-line hashes, split membership, and parent identities are not
  regenerated or mutated.

## Leakage analysis

The policy is valid only under this dependency:

```text
RAW CONTENT → deterministic representation
```

The following dependencies are forbidden and testable:

```text
ANOMALY LABEL ─╳→ representation
PARTITION ID  ─╳→ representation
TEST OUTCOME  ─╳→ representation
MODEL RESULT  ─╳→ representation
```

The same byte sequence must receive the same representation in every dataset,
partition, parent, and label context. Future application to TEST requires the
existing human TEST authorization but requires no fitting or policy learning.

## Required resumed-implementation tests

The following tests are frozen before implementation:

| ID | Requirement |
| --- | --- |
| T1 | Ordinary message remains unchanged. |
| T2 | One NUL is encoded exactly under `seqlogad-nul-escape-v1`. |
| T3 | Multiple NULs are encoded deterministically. |
| T4 | Leading NUL is supported. |
| T5 | Trailing NUL is supported. |
| T6 | Literal escape/sentinel collision is unambiguous and reversible. |
| T7 | Unicode surrounding NUL is preserved. |
| T8 | `raw_message_sha256` hashes exact original message bytes. |
| T9 | One retained raw line produces one observation and one event. |
| T10 | A retained BGL parent remains exactly 100 events. |
| T11 | Frozen Drain3 state hash is unchanged before/after inference. |
| T12 | Template registry hash is unchanged. |
| T13 | `EVT_UNSEEN` fallback is deterministic. |
| T14 | Repeated generation is byte/hash identical. |
| T15 | Canonicalization is label-independent. |
| T16 | Canonicalization is partition-independent. |
| T17 | TEST loader remains denied. |
| T18 | No TEST artifact is generated. |
| T19 | Validator rejects non-canonical status/escape/hash combinations. |
| T20 | Historical schema/envelope 1.0 remains independently valid. |

Acceptance coverage must include a synthetic, non-TEST 100-event BGL parent:

```text
raw line
→ canonicalization
→ frozen Drain3 match
→ EventObservation
→ canonical event serialization
→ parent reconciliation
```

One synthetic event contains NUL. The assertion is exactly 100 inputs → 100
outputs, with no silent drop and no parser mutation.

## Frozen identity verification

| Identity | Value |
| --- | --- |
| BGL dataset fingerprint | `c9ee7a8db13d37c88f896e305ed12dc7a66b586cdae4e388db4949f78afbe861` |
| BGL split payload | `0c1bb1b9b755aa2aa50238771cf5bf34649e1ca33c7964e061766b659aeebd05` |
| BGL `VAL_FUSION` partition | `3f035c038bc8c8acacc475fc69cf811214ec247d8891022495adf5d7636da3f7` |
| BGL TEST partition | `7ecf43ab27d6519b7af4ae4e8f7be5cd9d5351c8c11d18b3bd11b4ff896a876d` |
| BGL parser manifest | `bc2fd7df13ee231c0e9e63597e3237cd48ebb1658c4609524f04087cf49cfd66` |
| BGL parser state | `e44649d24afbd4bc335e2d38d54cea9338c211c600baef185cd7a0dee6aee4f6` |
| BGL template registry | `bc4ac9e2c6ea51e712ed06c0648372d6ed800f2788d135cd5cc89d7d1047d17f` |

The machine-readable proposal identity is
`72c1e03ceae625ab719c51fd552706912d55a06daddb5c280c445afe37696192`.

## TEST integrity

```text
HDFS_TEST_STATUS = SEALED / NEVER_OPENED
BGL_TEST_STATUS  = SEALED / NEVER_OPENED
OPEN_COUNT       = 0
UNLOCK_RECORDS   = 0
```

No TEST content was searched, canonicalized, previewed, or generated during
this decision task.

## Plan lock

The execution order remains:

```text
CANONICAL-NUL-DECISION-001
→ HUMAN APPROVAL
→ resume CANONICAL-EVENT-001
→ T8 QA
→ THEORY-COMPLETE-001
→ HUMAN THEORY FREEZE
→ SEQ-001
→ LEAK-001
→ BASELINES
→ MARKOV/N-GRAM
→ KT-1 → KT-2 → KT-3
→ HUMAN SCIENTIFIC GATE
→ conditional methods
→ final one-time HUMAN TEST
```

No successor is authorized by this proposal.

## Human approval payload

To approve the proposal exactly as written, the human researcher must send:

```text
APPROVE CANONICAL-NUL-DECISION-001 OPTION A — seqlogad-nul-escape-v1
```

Until that explicit approval:

```text
CANONICAL-NUL-DECISION-001 = FROZEN_HUMAN_REVIEW_READY
CANONICAL-EVENT-001 = BLOCKED_PENDING_HUMAN_APPROVAL
```

## References

The reproducible search log and claim-level source mapping are in
[`../references/CANONICAL-NUL-DECISION-001-citations.md`](../references/CANONICAL-NUL-DECISION-001-citations.md).
The exact proposal payload is in
[`../../configs/protocols/canonical-nul-decision-v1.yaml`](../../configs/protocols/canonical-nul-decision-v1.yaml).
