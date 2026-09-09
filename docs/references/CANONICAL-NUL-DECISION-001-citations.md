# CANONICAL-NUL-DECISION-001 — citations and search log

> **HISTORICAL / SUPERSEDED.** This citation pack belongs to the retired v1.1
> study. It is retained for provenance only and is **not** an active reference
> source. The authoritative registry is
> [`reference_registry.yaml`](reference_registry.yaml).

## Scope and evidence rule

This targeted review supports only the representation decision for NUL-bearing
log messages. It does not establish a universal log-canonicalization standard,
scientific performance, or novelty. Search/access date: **2026-09-06**.

Priority was 2026 → 2025 → 2024, followed by older standards, seminal parser
work, and official tagged source where recent literature did not define a
Drain3-specific NUL policy.

Evidence labels:

- `LITERATURE_SUPPORTED`: the cited source directly supports the stated fact.
- `LITERATURE_INFORMED_SEQLOGAD_DECISION`: the source supplies a principle;
  the exact SeqLogAD policy remains a project decision.
- `SEQLOGAD_PROTOCOL_DECISION`: a pre-implementation project rule not claimed
  as a literature result.
- `ENGINEERING_DECISION`: a repository-specific implementation choice.

## Search log

| Source/search system | Query or navigation | Inclusion outcome |
| --- | --- | --- |
| Crossref/publisher and general scholarly search | `log parsing NUL byte control character malformed log preprocessing 2024 2025 2026` | Retained the 2024 parsing-impact paper; no peer-reviewed Drain3-specific NUL codec found. |
| Scholarly search | `provenance preserving log preprocessing control characters anomaly detection` | Retained general preprocessing-bias evidence; project-specific codec remains unsupported by direct study. |
| IETF Datatracker/RFC Editor | `syslog NUL control characters encoding` | Retained RFC 5424 and RFC 6587. |
| Unicode official standard | `U+0000 C0 control character higher-level protocol` | Retained Unicode 17.0 Chapter 23. |
| OpenTelemetry official specification | `original log record normalized body provenance` | Retained Logs Data Model and `log.record.original`. |
| W3C official specifications | `PROV source entity derivation activity reproducibility` | Retained PROV Primer. |
| Drain3 official tagged GitHub source | `TemplateMiner.match`, `Drain.match`, `v0.9.11` | Retained read-only match semantics; found no NUL-specific guarantee. |
| Drain publication | Original Drain paper and DOI | Retained parser mechanism; paper has no malformed/NUL policy. |

Inclusion criteria:

- official standards/specifications governing log/control-character or
  serialization behavior;
- peer-reviewed work directly relevant to log parsing or preprocessing bias;
- official Drain3 v0.9.11 source for the exact dependency used by SeqLogAD;
- claims that can be scoped precisely to the NUL decision.

Exclusion criteria:

- blogs, Q&A, and vendor posts when an original standard/source was available;
- claims about performance or anomaly-detection benefit without an applicable
  experiment;
- generic sanitization advice that did not preserve raw provenance;
- papers mentioning malformed logs but not supporting the representation
  contract at issue.

Duplicates were merged by canonical DOI/standard/tagged-source identity.
Backward/forward snowballing was limited to the parser paper, its official
implementation, and standards directly referenced by the identified problem.

Search limitation: no retained 2024–2026 peer-reviewed paper prescribed an
exact Drain3 NUL codec. This is a bounded search outcome, not proof that no such
work exists.

## Retained sources and exact claim mapping

### S1 — RFC 5424: The Syslog Protocol

- Title: *The Syslog Protocol*
- Authors: Rainer Gerhards
- Year: 2009
- Venue/source: IETF Standards Track, RFC 5424
- DOI: none
- Official URL: <https://www.rfc-editor.org/rfc/rfc5424.html>
- Accessed: 2026-09-06
- Exact supported claim: the syslog `MSG` and `PARAM-VALUE` domains can contain
  control characters including NUL; NUL requires care because text-processing
  systems may terminate strings or obscure content. The RFC permits receivers
  to encode control characters and advises encoding NUL when writing text
  files.
- Evidence classification: `LITERATURE_SUPPORTED`
- Boundary: it does not prescribe a sentinel, reversible codec, ML schema, or
  SeqLogAD policy.

### S2 — RFC 6587: Transmission of Syslog Messages over TCP

- Title: *Transmission of Syslog Messages over TCP*
- Authors: Rainer Gerhards; Anton Lonvick
- Year: 2012
- Venue/source: IETF Historic, RFC 6587
- DOI: none
- Official URL: <https://www.rfc-editor.org/rfc/rfc6587.html>
- Accessed: 2026-09-06
- Exact supported claim: silently dropping transformed characters while
  repairing an encoding problem is poor practice because it loses source data
  and can damage encoding.
- Evidence classification: `LITERATURE_SUPPORTED`
- Boundary: this is a transport/interoperability document, not a canonical
  event schema or anomaly-detection protocol.

### S3 — The Unicode Standard, Version 17.0, Chapter 23

- Title: *The Unicode Standard, Version 17.0 — Chapter 23: Special Areas and
  Format Characters*
- Authoring body: Unicode Consortium
- Year: 2025
- Venue/source: Unicode Standard 17.0
- DOI: none
- Official URL:
  <https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-23/>
- Accessed: 2026-09-06
- Exact supported claim: U+0000 belongs to the C0 control range; application
  semantics for control codes are governed by the relevant higher-level
  protocol rather than by a single Unicode-mandated handling policy.
- Evidence classification: `LITERATURE_SUPPORTED`
- Boundary: Unicode does not decide whether SeqLogAD should preserve literal
  NUL, escape it, or emit a special event.

### S4 — RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format

- Title: *The JavaScript Object Notation (JSON) Data Interchange Format*
- Author: Tim Bray
- Year: 2017
- Venue/source: IETF Internet Standard STD 90, RFC 8259
- DOI: none
- Official URL: <https://www.rfc-editor.org/rfc/rfc8259.html>
- Accessed: 2026-09-06
- Exact supported claim: JSON strings must escape U+0000–U+001F, and reverse
  solidus itself is escaped in JSON syntax.
- Evidence classification: `LITERATURE_SUPPORTED`
- Boundary: JSON escaping is a serialization rule. After JSON decoding, a
  value can again contain literal NUL; JSON escaping alone is therefore not a
  parser-safe domain-representation policy.

### S5 — OpenTelemetry Logs Data Model and general log conventions

- Title: *Logs Data Model*; *General Logs Attributes*
- Authors: OpenTelemetry project contributors
- Year: living specification, current version accessed 2026
- Venue/source: official OpenTelemetry specification
- DOI: none
- Official URLs:
  - <https://opentelemetry.io/docs/specs/otel/logs/data-model/>
  - <https://opentelemetry.io/docs/specs/semconv/general/logs/>
- Accessed: 2026-09-06
- Exact supported claim: log mappings should avoid ambiguity and preserve
  round-trip semantics where possible; `log.record.original` provides a place
  for an original record when a normalized body differs.
- Evidence classification: `LITERATURE_INFORMED_SEQLOGAD_DECISION`
- Boundary: `log.record.original` is a string attribute, not a guarantee of
  exact arbitrary-byte preservation or a prescribed SHA-256 provenance model.

### S6 — W3C PROV Model Primer

- Title: *PROV Model Primer*
- Editors/authors: Yolanda Gil; Simon Miles, with the W3C Provenance Working
  Group
- Year: 2013
- Venue/source: W3C Working Group Note
- DOI: none
- Official URL: <https://www.w3.org/TR/prov-primer/>
- Accessed: 2026-09-06
- Exact supported claim: provenance can link a source entity, a transformation
  activity, and a derived entity to support trust, verification, and
  reproducibility.
- Evidence classification: `LITERATURE_INFORMED_SEQLOGAD_DECISION`
- Boundary: W3C PROV does not require SHA-256, the proposed field names, or the
  selected escape grammar.

### S7 — Drain: An Online Log Parsing Approach with Fixed Depth Tree

- Title: *Drain: An Online Log Parsing Approach with Fixed Depth Tree*
- Authors: Pinjia He; Jieming Zhu; Zibin Zheng; Michael R. Lyu
- Year: 2017
- Venue/source: IEEE International Conference on Web Services (ICWS)
- DOI: <https://doi.org/10.1109/ICWS.2017.13>
- Official author-hosted paper:
  <https://pinjiahe.github.io/files/pdf/research/ICWS17.pdf>
- Accessed: 2026-09-06
- Exact supported claim: Drain represents a log message as a token sequence
  and uses a fixed-depth tree to mine/match templates.
- Evidence classification: `LITERATURE_SUPPORTED`
- Boundary: the paper does not study NUL, malformed raw bytes, exact-byte
  provenance, or frozen-state inference.

### S8 — Drain3 v0.9.11 official tagged source

- Title: *Drain3 v0.9.11 — TemplateMiner and Drain source*
- Authors: LogPAI/Drain3 maintainers
- Year: tagged software source; version `0.9.11`
- Venue/source: official Drain3 GitHub repository
- DOI: none
- Official URLs:
  - <https://github.com/logpai/Drain3/blob/v0.9.11/drain3/template_miner.py>
  - <https://github.com/logpai/Drain3/blob/v0.9.11/drain3/drain.py>
- Accessed: 2026-09-06
- Exact supported claim: `TemplateMiner.match()` invokes the matching path
  without adding a cluster; `Drain.match()` is documented in source as not
  creating or modifying clusters.
- Evidence classification: `LITERATURE_SUPPORTED` for read-only inference.
- Boundary: the tagged source provides no NUL-specific compatibility contract.
  Therefore literal-NUL support must not be inferred merely from Python string
  behavior.

### S9 — Impact of log parsing on deep learning-based anomaly detection

- Title: *Impact of log parsing on deep learning-based anomaly detection*
- Authors: Zanis Ali Khan; Donghwan Shin; Domenico Bianculli; Lionel C. Briand
- Year: 2024
- Venue/source: *Empirical Software Engineering*, volume 29, article 139
- DOI: <https://doi.org/10.1007/s10664-024-10533-w>
- Official publisher URL:
  <https://link.springer.com/article/10.1007/s10664-024-10533-w>
- Accessed: 2026-09-06
- Exact supported claim: the parsing representation can materially affect
  downstream anomaly-detection distinguishability; parser accuracy alone does
  not guarantee downstream detection quality.
- Evidence classification: `LITERATURE_INFORMED_SEQLOGAD_DECISION`
- Boundary: the study does not evaluate NUL or select among SeqLogAD Options
  A–D.

### S10 — On the Cross-Validation Bias due to Unsupervised Preprocessing

- Title: *On the Cross-Validation Bias due to Unsupervised Preprocessing*
- Authors: Amit Moscovich; Saharon Rosset
- Year: 2022
- Venue/source: *Journal of the Royal Statistical Society: Series B*, 84(4),
  1474–1502
- DOI: <https://doi.org/10.1111/rssb.12537>
- Accessed: 2026-09-06
- Exact supported claim: data-dependent unsupervised preprocessing performed
  using observations outside the appropriate training fold can bias model
  assessment.
- Evidence classification: `LITERATURE_INFORMED_SEQLOGAD_DECISION`
- Boundary: the paper is not log-specific and does not directly test a
  deterministic, content-only, per-record codec. SeqLogAD's prohibition on
  label/partition/TEST-conditioned canonicalization is a conservative project
  decision informed by this broader leakage result.

## Claim-to-source matrix

| SeqLogAD statement | Source(s) | Classification |
| --- | --- | --- |
| Do not silently drop the four retained observations. | S2; frozen one-line-one-event contract | `LITERATURE_INFORMED_SEQLOGAD_DECISION` + `SEQLOGAD_PROTOCOL_DECISION` |
| Keep raw bytes separate from derived parser input. | S5, S6 | `LITERATURE_INFORMED_SEQLOGAD_DECISION` |
| Encoding NUL into a textual representation is defensible. | S1 | `LITERATURE_INFORMED_SEQLOGAD_DECISION` |
| Use a collision-safe backslash grammar and exact raw-message hash. | none prescribes this exact form | `SEQLOGAD_PROTOCOL_DECISION` |
| Apply the codec before frozen read-only `match()`. | S7, S8 plus frozen parser contract | `ENGINEERING_DECISION` |
| Keep the codec content-only and independent of labels/partitions. | S10 plus frozen leakage contract | `LITERATURE_INFORMED_SEQLOGAD_DECISION` + `SEQLOGAD_PROTOCOL_DECISION` |
| Keep `EVT_UNSEEN` when no frozen template matches. | existing SeqLogAD parser contract | `SEQLOGAD_PROTOCOL_DECISION` |
| Bump only the canonical artifact envelope to 1.1. | repository schema analysis | `ENGINEERING_DECISION` |

## Review conclusion

The evidence supports preserving raw bytes, avoiding silent deletion,
separating original and derived representations, recording provenance, and
using Drain3's read-only match path. It does **not** prove an exact NUL codec.

Accordingly, `seqlogad-nul-escape-v1` is classified as a
`LITERATURE_INFORMED_SEQLOGAD_DECISION`. Its exact escape grammar, wrapper
fields, hashes, and version boundary are SeqLogAD protocol/engineering choices
that require human approval and tests before real corpus generation.
