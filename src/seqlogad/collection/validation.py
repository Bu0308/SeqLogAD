"""Record identities and portable evidence integrity; no handoff certification."""
from pathlib import Path, PurePosixPath, PureWindowsPath
import re

from seqlogad.common.checksum import sha256_file
from .models import RECORD_FILES


class CollectionError(RuntimeError):
    """A process-evidence record violates its contract."""


ID_FIELDS = {
    "architecture": "architecture_id", "variant": "variant_id",
    "dataset": "dataset_id", "event_schema": "event_schema_id",
    "transform": "transform_id", "split": "split_id", "run_bridge": "run_alias",
    "artifact_manifest": "artifact_manifest_id", "incident": "incident_id",
    "lineage_edge": "edge_id", "protocol_deviation": "deviation_id",
    "seal": "seal_id", "access": "access_id", "toolchain": "toolchain_id",
}
PATH_FIELDS = {
    "raw_manifest_path", "processed_manifest_path", "config_path", "metrics_path",
    "leakage_audit_path", "path", "evidence_paths", "decision_evidence",
    "bundle_path", "inventory_path", "protocol_path",
}
HASH_FIELDS = {"sha256", "extraction_query_hash", "template_dictionary_hash",
               "runtime_packages_hash", "evidence_hashes"}


def record_id(record):
    for kind, (_, model) in RECORD_FILES.items():
        if isinstance(record, model):
            return getattr(record, ID_FIELDS[kind])
    raise CollectionError("unregistered record type")


def relative_path(value):
    if not isinstance(value, str):
        raise CollectionError("collection paths must be non-empty relative POSIX paths")
    path = PurePosixPath(value)
    if (not value or value.strip() != value or value == "." or path.is_absolute()
            or ".." in path.parts or "\\" in value or PureWindowsPath(value).drive
            or ":" in value or any(ord(c) < 32 for c in value)):
        raise CollectionError("collection paths must be non-empty relative POSIX paths")
    return value


def _walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            yield from _walk(child)


def check_record(record):
    identity = record_id(record)
    if not identity or identity.strip() != identity:
        raise CollectionError("record identity must be non-empty without outer whitespace")
    for key, value in _walk(record.model_dump(mode="python")):
        if value is None:
            continue
        items = value if isinstance(value, (list, tuple)) else (value,)
        for item in items:
            if key in PATH_FIELDS:
                # Explicit native decision references are IDs, not filesystem paths.
                if key == "decision_evidence" and isinstance(item, str) and re.fullmatch(r"projmem:decision:[\w-]+", item):
                    continue
                relative_path(item)
            if key in HASH_FIELDS or key.endswith("_sha256"):
                if not isinstance(item, str) or not re.fullmatch(r"[0-9a-f]{64}", item):
                    raise CollectionError(f"invalid SHA-256: {key}")
    if hasattr(record, "evidence_hashes"):
        if len(record.evidence_hashes) != len(record.evidence_paths):
            raise CollectionError("lineage requires one hash per evidence path")
    if getattr(record, "causal_claim", None) and record.causal_tier not in {"C3", "C4"}:
        raise CollectionError("causal claim requires C3/C4 evidence")


def _verify(root, path, digest=None, size=None):
    relative_path(path)
    candidate = root / path
    if not candidate.resolve().is_relative_to(root):
        raise CollectionError(f"evidence escapes project root: {path}")
    if any(p.is_symlink() for p in (candidate, *candidate.parents) if p != root.parent):
        raise CollectionError(f"symlink evidence forbidden: {path}")
    if not candidate.is_file():
        raise CollectionError(f"missing evidence file: {path}")
    if digest is not None and sha256_file(candidate) != digest:
        raise CollectionError(f"checksum mismatch: {path}")
    if size is not None and candidate.stat().st_size != size:
        raise CollectionError(f"size mismatch: {path}")


def verify_files(root, record):
    data = record.model_dump(mode="python")
    for key in PATH_FIELDS - {"path", "decision_evidence", "evidence_paths"}:
        if data.get(key):
            digest = data.get(key.removesuffix("_path") + "_sha256")
            _verify(root, data[key], digest)
    for path in data.get("decision_evidence", ()):
        if not path.startswith("projmem:decision:"):
            _verify(root, path)
    for path, digest in zip(data.get("evidence_paths", ()), data.get("evidence_hashes", ())):
        _verify(root, path, digest)
    for item in data.get("items", ()):
        # Missing/restricted bytes must remain in the inventory, not silently vanish.
        if item["availability_status"] == "included":
            _verify(root, item["path"], item["sha256"], item["size_bytes"])
