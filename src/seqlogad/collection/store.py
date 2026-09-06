"""Append-only JSONL storage and cross-record validation."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from seqlogad.collection.models import CollectionRecord, RECORD_FILES


class CollectionError(RuntimeError):
    """Raised when a process-evidence record violates its contract."""


RecordT = TypeVar("RecordT", bound=CollectionRecord)


def _relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise CollectionError("collection paths must be non-empty relative POSIX paths")
    return value


def _record_id(record: BaseModel) -> str | None:
    data = record.model_dump(mode="json")
    for key in ("architecture_id", "variant_id", "dataset_id", "event_schema_id", "transform_id", "split_id", "run_alias", "artifact_manifest_id", "incident_id", "edge_id", "deviation_id", "seal_id", "access_id", "toolchain_id"):
        if key in data:
            return str(data[key])
    return None


_PATH_FIELDS = {
    "raw_manifest_path",
    "processed_manifest_path",
    "config_path",
    "metrics_path",
    "leakage_audit_path",
    "path",
    "evidence_paths",
    "decision_evidence",
    "bundle_path",
    "inventory_path",
    "protocol_path",
}


def _check_project_relative_paths(record: BaseModel) -> None:
    """Reject absolute/parent-traversing paths in portable evidence records."""

    for field, value in record.model_dump(mode="python").items():
        if field not in _PATH_FIELDS or value is None:
            continue
        values = value if isinstance(value, (tuple, list)) else (value,)
        for item in values:
            if isinstance(item, str):
                _relative_path(item)


def initialize_collection(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve() / "research_records"
    root.mkdir(parents=True, exist_ok=True)
    (root / "run_inputs").mkdir(exist_ok=True)
    (root / "run_metrics").mkdir(exist_ok=True)
    (root / "qa").mkdir(exist_ok=True)
    (root / "private").mkdir(exist_ok=True)
    created: list[str] = []
    for filename, _model in RECORD_FILES.values():
        path = root / filename
        if not path.exists():
            path.touch()
            created.append(filename)
    return {"root": "research_records", "created_files": created, "status": "READY"}


def append_record(project_root: str | Path, record_type: str, record: RecordT) -> dict[str, Any]:
    if record_type not in RECORD_FILES:
        raise CollectionError(f"unsupported record type: {record_type}")
    filename, expected_model = RECORD_FILES[record_type]
    if not isinstance(record, expected_model):
        raise CollectionError(f"record type {record_type} requires {expected_model.__name__}")
    _check_project_relative_paths(record)
    root = Path(project_root).resolve() / "research_records"
    root.mkdir(parents=True, exist_ok=True)
    path = root / _relative_path(filename)
    existing_ids: set[str] = set()
    if path.exists():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                old = expected_model.model_validate_json(line)
            except ValidationError as exc:
                raise CollectionError(f"existing record invalid at {filename}:{line_number}") from exc
            old_id = _record_id(old)
            if old_id:
                existing_ids.add(old_id)
    new_id = _record_id(record)
    if new_id and new_id in existing_ids:
        raise CollectionError(f"duplicate record id: {new_id}")
    payload = json.dumps(record.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(payload + "\n")
    return {"status": "APPENDED", "record_type": record_type, "path": f"research_records/{filename}", "record_id": new_id}


def validate_collection(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve() / "research_records"
    errors: list[str] = []
    counts: dict[str, int] = {}
    seen: dict[str, str] = {}
    records: dict[str, list[CollectionRecord]] = {record_type: [] for record_type in RECORD_FILES}
    for record_type, (filename, model) in RECORD_FILES.items():
        path = root / filename
        count = 0
        if path.exists():
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                count += 1
                try:
                    parsed = model.model_validate_json(line)
                except ValidationError as exc:
                    errors.append(f"{filename}:{line_number}: {exc.errors()[0]['msg']}")
                    continue
                try:
                    _check_project_relative_paths(parsed)
                except CollectionError as exc:
                    errors.append(f"{filename}:{line_number}: {exc}")
                records[record_type].append(parsed)
                identity = _record_id(parsed)
                if identity and identity in seen:
                    errors.append(f"duplicate id {identity} in {filename} and {seen[identity]}")
                elif identity:
                    seen[identity] = filename
        counts[record_type] = count

    # Resolve references only across records that are already present. This is
    # intentionally a package-level check: append order may be arbitrary, but
    # an export cannot contain dangling core references.
    ids_by_type = {
        record_type: {_record_id(record) for record in values if _record_id(record)}
        for record_type, values in records.items()
    }

    def require(record_type: str, field: str, target_type: str) -> None:
        for record in records[record_type]:
            value = getattr(record, field, None)
            if value is None:
                continue
            values = value if isinstance(value, tuple) else (value,)
            for item in values:
                if item and item not in ids_by_type[target_type]:
                    errors.append(
                        f"orphan reference {record_type}.{field}={item!r}"
                    )

    require("variant", "architecture_id", "architecture")
    require("variant", "parent_variant_id", "variant")
    require("dataset", "event_schema_id", "event_schema")
    require("dataset", "transform_id", "transform")
    require("transform", "input_dataset_id", "dataset")
    require("split", "dataset_id", "dataset")
    for field, target in (
        ("architecture_id", "architecture"),
        ("variant_id", "variant"),
        ("dataset_id", "dataset"),
        ("event_schema_id", "event_schema"),
        ("transform_id", "transform"),
        ("split_id", "split"),
    ):
        require("run_bridge", field, target)
    require("run_bridge", "artifact_manifest_id", "artifact_manifest")
    require("incident", "linked_run_ids", "run_bridge")
    require("protocol_deviation", "affected_run_ids", "run_bridge")
    require("seal", "split_id", "split")
    require("access", "seal_id", "seal")
    return {"status": "PASS" if not errors else "FAIL", "records_checked": sum(counts.values()), "counts": counts, "duplicate_or_parse_errors": errors}
