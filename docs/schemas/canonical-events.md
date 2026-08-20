# SCHEMA-001 — Canonical Event and Template Contract

| Field | Value |
|---|---|
| Task | `SCHEMA-001` |
| Schema version | `1.0` |
| Status | **IMPLEMENTED — AWAITING HUMAN AUDIT** |
| Source module | `src/seqlogad/common/schemas/events.py` |
| Scientific protocol | `docs/research-protocol.md` |
| Method provenance | `docs/references/SCHEMA-001-citations.md` |

This contract defines canonical `EventTemplate` and `LogEvent` records. It does not parse logs, run Drain3, read raw datasets, assign real partitions, build sequences, or open TEST labels.

## 1. Design goals

The schema must make these properties mechanically checkable:

1. event occurrences remain traceable to immutable dataset bytes and source lines;
2. template/event-type identity does not depend on Drain3 discovery order;
3. HDFS block identity is retained before sequence construction;
4. BGL inline labels are structurally separate from parser/model fields;
5. training partitions contain controlled normal records only;
6. validation labels have validation-only access;
7. canonical TEST events cannot contain supervision;
8. records reject unknown fields and serialize deterministically;
9. no raw absolute machine path enters a scientific artifact.

## 2. Record boundaries

```text
EventTemplate
├── deterministic event_id
├── normalized template
├── parser/normalization versions and config hashes
└── BASE_TRAIN fit ownership

LogEvent
├── EventProvenance       dataset/source/partition/group identity
├── EventObservation      label-isolated message, time, safe attributes
├── parsed identity       event_id, parameters, parser/registry hashes
├── EventSupervision?     controlled non-TEST label boundary
└── to_model_input()      explicit label-free sequence-model view
```

`EventSequence`, mutation coordinates, sequence masks, and split-manifest records belong to `SCHEMA-002` and later tasks.

## 3. EventTemplate

| Field | Contract |
|---|---|
| `schema_version` | Literal `1.0` |
| `event_id` | Deterministic `EVT-<sha256>` identity |
| `normalized_template` | Frozen normalized template text |
| `parser_name` | Literal `drain3` |
| `parser_version` | Exact fitted Drain3 package/version identity |
| `parser_config_sha256` | Content identity of the parser configuration |
| `normalization_version` | Version of normalization rules |
| `normalization_config_sha256` | Content identity of normalization configuration |
| `template_sha256` | SHA-256 of normalized template UTF-8 bytes |
| `fit_partition` | Must be `BASE_TRAIN` |

The deterministic event ID is:

```text
EVT- + SHA256(
  "drain3" + NUL
  + parser_version + NUL
  + normalization_version + NUL
  + normalized_template
)
```

The full 256-bit digest is retained. No numeric discovery-order ID is a scientific identity. `EVT_UNSEEN` is a reserved `LogEvent` value for post-freeze templates that are absent from the frozen registry; it does not fabricate an `EventTemplate` record.

## 4. LogEvent

| Field | Contract |
|---|---|
| `schema_version` | Literal `1.0` |
| `record_id` | Deterministic source-occurrence identity |
| `provenance` | Dataset, source line, chronology, partition and group identity |
| `observation` | Label-isolated message/timestamp/model-safe attributes |
| `event_id` | Frozen template identity or `EVT_UNSEEN` |
| `parameters` | Ordered Drain3 parameters; not part of P0 model input |
| `parser_state_sha256` | Exact frozen parser-state content identity |
| `template_registry_sha256` | Exact frozen registry content identity |
| `supervision` | Controlled real label for authorized non-TEST use, or absent |

The deterministic record ID is:

```text
LOG- + SHA256(
  dataset_fingerprint + NUL
  + repository_relative_source_file + NUL
  + one_based_source_line_number + NUL
  + source_line_sha256
)
```

Dataset ID/version remain metadata, while the verified dataset fingerprint anchors byte identity. Source paths must be normalized repository-relative POSIX paths; absolute paths and traversal are rejected.

## 5. Provenance and grouping

`EventProvenance` contains:

- `dataset_key`, `dataset_id`, `dataset_version`, and 64-character dataset fingerprint;
- repository-relative `source_file`;
- one-based `source_line_number` and zero-based `chronological_index`;
- SHA-256 of the exact source line bytes supplied by the future adapter, including the original line terminator when one exists;
- one of the frozen five scientific partitions;
- grouping kind and group IDs.

HDFS canonical events require `group_kind=hdfs_block` and at least one block ID. Multiple IDs support the protocol's connected-component atomicity rule. BGL events have no pre-window group identity; their 100-event parent-window identity is created later.

This schema validates a supplied partition identity but does not calculate partition boundaries. That responsibility remains with the future split implementation and split manifest. The line-byte convention must be enforced by adapter tests before real artifacts are generated.

## 6. Observation and model-safe attributes

`EventObservation.message` is the message after dataset metadata and source labels have been separated. `label_isolated` is a required literal `true`, making adapter responsibility explicit.

Both source timestamp text and optional normalized UTC time may be retained:

- `source_timestamp` preserves source representation without inventing timezone semantics;
- `timestamp_utc`, when present, must be timezone-aware.

Attributes are immutable key/value records. Their names are unique and sorted for deterministic serialization. Keys resembling label, anomaly, ground-truth, or alert markers are rejected. Severity such as `ERROR` remains ordinary observed log data and is not treated as a ground-truth anomaly label.

## 7. Supervision isolation

`EventSupervision` is physically separate from `EventObservation` and the returned `EventModelInput`.

| Partition | Required state for HDFS/BGL canonical events |
|---|---|
| `BASE_TRAIN` | Label present, `normal`, access=`normal_pool_filtering` |
| `FUSION_TRAIN` | Label present, `normal`, access=`normal_pool_filtering` |
| `VAL_EXPERT` | Label present, access=`validation_evaluation` |
| `VAL_FUSION` | Label present, access=`validation_evaluation` |
| `TEST` | `supervision` must be absent |

HDFS supervision granularity is `block_session`; BGL source supervision granularity is `event`. TEST labels will be joined only by a future human-authorized evaluation boundary; they are intentionally not representable inside a canonical TEST `LogEvent`.

`LogEvent.to_model_input()` returns only:

- `record_id` for traceability;
- `event_id`;
- optional normalized timestamp;
- validated model-safe attributes.

It excludes source message, parameters, provenance partition, and all supervision fields. Future models must consume this explicit view or a versioned derivative, not arbitrary `LogEvent.model_dump()` output.

## 8. Determinism and immutability

All schema models:

- reject extra fields;
- are frozen after validation;
- reject non-finite floating-point attributes;
- canonicalize attribute ordering;
- provide canonical JSON with sorted keys and compact UTF-8 encoding;
- provide SHA-256 over canonical JSON.

Serialization determinism is a record-format guarantee, not a claim that later parser/model outputs are already deterministic.

## 9. Synthetic example only

```json
{
  "schema_version": "1.0",
  "record_id": "LOG-<64 lowercase hex characters>",
  "provenance": {
    "dataset_key": "hdfs",
    "dataset_id": "HDFS_v1",
    "dataset_version": "zenodo-8196385:HDFS_v1",
    "dataset_fingerprint": "<64 lowercase hex characters>",
    "source_file": "data/raw/hdfs/HDFS_v1/HDFS.log",
    "source_line_number": 7,
    "chronological_index": 6,
    "source_line_sha256": "<64 lowercase hex characters>",
    "partition": "BASE_TRAIN",
    "group_kind": "hdfs_block",
    "group_ids": ["blk_-1"]
  },
  "observation": {
    "message": "synthetic label-isolated message",
    "label_isolated": true,
    "source_timestamp": "synthetic timestamp",
    "timestamp_utc": null,
    "attributes": []
  },
  "event_id": "EVT-<64 lowercase hex characters>",
  "parameters": [],
  "parser_state_sha256": "<64 lowercase hex characters>",
  "template_registry_sha256": "<64 lowercase hex characters>",
  "supervision": {
    "label": "normal",
    "granularity": "block_session",
    "access": "normal_pool_filtering",
    "source_kind": "external_file",
    "source_reference": "preprocessed/anomaly_label.csv",
    "category": null
  }
}
```

The placeholder hashes above are explanatory and are not experiment artifacts.

## 10. Explicit non-goals

SCHEMA-001 does not:

- read HDFS/BGL raw files or inspect TEST labels;
- implement Drain3 lifecycle or normalization;
- generate actual event/template IDs from dataset bytes;
- create sequences, windows, split manifests, or mutations;
- define token/gap/transition localization records;
- train or evaluate any detector, retriever, fusion, RAG, or agent component.
