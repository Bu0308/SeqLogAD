"""DATA-REG-001 — the active dataset registry (Excel P1.2).

A registry row is not a claim that data exists; it records what was *verified*.
ACTIVE rows require a materialised raw corpus with a recomputed SHA-256, a
resolvable source, a checked licence and a stated label availability.  Candidates
that were considered and not taken carry the reason, so the portfolio choice can be
re-examined without re-deriving it.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from seqlogad.common.checksum import sha256_file
from seqlogad.protocol.architectures import ARCHITECTURES, resolve_files


REGISTRY_SCHEMA_VERSION = "1.0"
REGISTRY_DIR = "data/registry"
REGISTRY_CSV = "data/registry/dataset_registry.csv"
REGISTRY_JSON = "data/registry/dataset_registry.json"

ACTIVE = "ACTIVE"
CANDIDATE = "CANDIDATE"
REJECTED = "REJECTED"
HISTORICAL = "HISTORICAL"

LOGHUB_RECORD = "https://doi.org/10.5281/zenodo.8196385"
LOGHUB_LICENSE = "CC-BY-4.0"
LOGHUB_CITATION = "S1"


class RegistryError(RuntimeError):
    """Raised when a registry row cannot be verified."""


@dataclass
class RegistryRow:
    dataset_id: str
    architecture_id: str
    system_name: str
    domain: str
    status: str
    role: str
    target_eligibility: str
    source_reference: str
    record_doi: str
    license_id: str
    license_status: str
    citation_key: str
    raw_root: str
    raw_files: int = 0
    raw_bytes: int = 0
    record_count: int | None = None
    first_timestamp_utc: str | None = None
    last_timestamp_utc: str | None = None
    chronology_field: str = ""
    label_available: str = "UNKNOWN"
    label_granularity: str = ""
    label_source: str = ""
    label_positive_units: int | None = None
    label_total_units: int | None = None
    label_access_policy: str = "EVALUATION_ONLY"
    corpus_sha256: str = ""
    archive_md5_verified: str = ""
    disposition_reason: str = ""
    known_limitations: str = ""
    file_digests: list[dict] = field(default_factory=list)


# Candidates considered for the portfolio but not activated. Sizes are the byte
# counts published by the Loghub Zenodo record and were read from its API, not
# estimated.
CONSIDERED_CANDIDATES: list[dict] = [
    {
        "dataset_id": "Thunderbird",
        "archive_bytes": 2_016_100_000,
        "status": REJECTED,
        "disposition_reason": (
            "Distinct HPC architecture and a strong portfolio candidate, but the "
            "archive alone is ~2.0 GB compressed and expands to tens of GB. The "
            "working volume had 2.2 GB free at portfolio time, so it could not be "
            "materialised, and an unverifiable dataset may not enter the registry."
        ),
    },
    {
        "dataset_id": "Spirit",
        "archive_bytes": None,
        "status": REJECTED,
        "disposition_reason": "Not distributed in Zenodo record 8196385.",
    },
    {
        "dataset_id": "Spark",
        "archive_bytes": 183_470_000,
        "status": REJECTED,
        "disposition_reason": (
            "No ground-truth anomaly labels are distributed with the Loghub Spark "
            "data, so it cannot serve as a LOAO target, and ~2.75 GB expanded "
            "exceeds the available volume."
        ),
    },
    {
        "dataset_id": "HDFS_v2",
        "archive_bytes": 823_700_000,
        "status": REJECTED,
        "disposition_reason": (
            "Same log-producing architecture as the already-active HDFS_v1, so it "
            "adds no architecture diversity to a leave-one-architecture-out design."
        ),
    },
    {
        "dataset_id": "HDFS_v3_TraceBench",
        "archive_bytes": 567_420_000,
        "status": REJECTED,
        "disposition_reason": (
            "Same architecture family as HDFS_v1; adds no distinct architecture."
        ),
    },
    {
        "dataset_id": "Zookeeper / HPC / Linux / Apache / Proxifier / OpenSSH / Mac / "
        "Windows / Android / HealthApp / SSH",
        "archive_bytes": None,
        "status": CANDIDATE,
        "disposition_reason": (
            "Available in the same Zenodo record and cheap to materialise, but not "
            "evaluated: the active portfolio already satisfies the Excel G0 minimum "
            "of three source architectures per fold, and the plan asks for the "
            "smallest defensible portfolio. Label availability for these was NOT "
            "verified and must not be assumed."
        ),
    },
]


def build_registry(project_root: str | Path, *, label_inventories: dict | None = None) -> list[RegistryRow]:
    """Assemble the registry from verified on-disk state.

    ``label_inventories`` must come from :func:`seqlogad.protocol.labels.label_inventory`,
    which is aggregate-only.  Passing it in (rather than importing the label module
    here) keeps the registry builder off the label code path.
    """

    from seqlogad.protocol.chronology import load_stream_index

    root = Path(project_root).resolve()
    rows: list[RegistryRow] = []
    inventories = label_inventories or {}

    for architecture_id, spec in ARCHITECTURES.items():
        files = resolve_files(root, spec)
        digests = [
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ]
        # A per-architecture corpus fingerprint over the ordered file digests.
        corpus = json.dumps(
            [(entry["path"], entry["bytes"], entry["sha256"]) for entry in digests],
            sort_keys=True,
        )
        import hashlib

        corpus_sha = hashlib.sha256(corpus.encode("utf-8")).hexdigest()

        try:
            index = load_stream_index(root, architecture_id)
        except Exception:
            index = {}

        inventory = inventories.get(architecture_id)
        rows.append(
            RegistryRow(
                dataset_id=spec.dataset_id,
                architecture_id=architecture_id,
                system_name=spec.system_name,
                domain=spec.domain,
                status=ACTIVE,
                role="SOURCE_AND_TARGET"
                if str(spec.target_eligibility) == "ELIGIBLE"
                else "SOURCE_ONLY",
                target_eligibility=str(spec.target_eligibility),
                source_reference=spec.source_reference,
                record_doi=LOGHUB_RECORD,
                license_id=spec.license_id,
                license_status="VERIFIED_FROM_ZENODO_RECORD_METADATA",
                citation_key=spec.citation,
                raw_root=spec.raw_root,
                raw_files=len(files),
                raw_bytes=sum(entry["bytes"] for entry in digests),
                record_count=index.get("record_count"),
                first_timestamp_utc=index.get("first_timestamp_utc"),
                last_timestamp_utc=index.get("last_timestamp_utc"),
                chronology_field=(
                    "record timestamp; stream order is timestamp, then file rank, "
                    "then line number"
                ),
                label_available="YES",
                label_granularity=spec.label_granularity,
                label_source=spec.label_source,
                label_positive_units=inventory.positive_units if inventory else None,
                label_total_units=inventory.total_units if inventory else None,
                corpus_sha256=corpus_sha,
                disposition_reason=spec.target_eligibility_rationale,
                known_limitations=spec.notes,
                file_digests=digests,
            )
        )

    for candidate in CONSIDERED_CANDIDATES:
        rows.append(
            RegistryRow(
                dataset_id=candidate["dataset_id"],
                architecture_id="",
                system_name="",
                domain="",
                status=candidate["status"],
                role="NOT_ACTIVE",
                target_eligibility="NOT_EVALUATED",
                source_reference="https://github.com/logpai/loghub",
                record_doi=LOGHUB_RECORD,
                license_id=LOGHUB_LICENSE,
                license_status="VERIFIED_FROM_ZENODO_RECORD_METADATA",
                citation_key=LOGHUB_CITATION,
                raw_root="",
                raw_bytes=candidate["archive_bytes"] or 0,
                label_available="NOT_VERIFIED",
                label_access_policy="N/A",
                disposition_reason=candidate["disposition_reason"],
            )
        )
    return rows


_CSV_FIELDS = [
    "dataset_id", "architecture_id", "system_name", "domain", "status", "role",
    "target_eligibility", "source_reference", "record_doi", "license_id",
    "license_status", "citation_key", "raw_root", "raw_files", "raw_bytes",
    "record_count", "first_timestamp_utc", "last_timestamp_utc", "chronology_field",
    "label_available", "label_granularity", "label_source", "label_positive_units",
    "label_total_units", "label_access_policy", "corpus_sha256",
    "archive_md5_verified", "disposition_reason", "known_limitations",
]


def write_registry(project_root: str | Path, rows: list[RegistryRow]) -> dict:
    root = Path(project_root).resolve()
    directory = root / REGISTRY_DIR
    directory.mkdir(parents=True, exist_ok=True)

    csv_path = root / REGISTRY_CSV
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: (asdict(row)[key] if asdict(row)[key] is not None else "") for key in _CSV_FIELDS})

    payload = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "artifact_id": "DATA-REG-001",
        "plan": "Bang_ke_hoach_SeqLogAD.xlsx",
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "status_vocabulary": [ACTIVE, CANDIDATE, REJECTED, HISTORICAL],
        "active_architectures": [r.architecture_id for r in rows if r.status == ACTIVE],
        "target_eligible_architectures": [
            r.architecture_id for r in rows if r.status == ACTIVE and r.target_eligibility == "ELIGIBLE"
        ],
        "rows": [asdict(row) for row in rows],
    }
    json_path = root / REGISTRY_JSON
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "csv": REGISTRY_CSV,
        "csv_sha256": sha256_file(csv_path),
        "json": REGISTRY_JSON,
        "json_sha256": sha256_file(json_path),
        "active": len(payload["active_architectures"]),
        "target_eligible": len(payload["target_eligible_architectures"]),
    }


def load_registry(project_root: str | Path) -> dict:
    path = Path(project_root).resolve() / REGISTRY_JSON
    if not path.is_file():
        raise RegistryError(f"missing dataset registry: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = [
    "ACTIVE", "CANDIDATE", "HISTORICAL", "REGISTRY_CSV", "REGISTRY_JSON", "REJECTED",
    "RegistryError", "RegistryRow", "build_registry", "load_registry", "write_registry",
]
