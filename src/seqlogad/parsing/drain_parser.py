"""Normal-only BASE_TRAIN Drain3 fitting and immutable inference.

PARSE-001 exposes two deliberately separate paths. fit_and_freeze_parser may
use Drain3's mutating online update, but accepts only a NormalPool bound to
BASE_TRAIN. FrozenDrainParser exposes only Drain3's non-mutating match
operation and fails closed for scientific TEST.

This module creates parser state and provenance artifacts only. It does not
generate the full canonical event corpus or calculate anomaly metrics.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

import yaml
from drain3 import TemplateMiner
from drain3.masking import MaskingInstruction
from drain3.memory_buffer_persistence import MemoryBufferPersistence
from drain3.template_miner_config import TemplateMinerConfig

from seqlogad.common.checksum import sha256_file
from seqlogad.common.schemas.events import (
    EventTemplate,
    ScientificPartition,
    UNSEEN_EVENT_ID,
    build_event_id,
)
from seqlogad.parsing.normal_pool import NormalPool
from seqlogad.parsing.normalization import NORMALIZATION_VERSION


PARSER_ARTIFACT_SCHEMA_VERSION = "1.0"
PARSER_IMPLEMENTATION_VERSION = "seqlogad-parse-001-v1"
PARSER_STATE_IDENTITY_ALGORITHM = "SHA256(CANONICAL_SCIENTIFIC_STATE_JSON_UTF8)"


class ParserContractError(RuntimeError):
    """Raised when fitting, persistence, or frozen inference is unsafe."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load_yaml(path: Path) -> dict:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ParserContractError(f"invalid parser contract: {path}") from exc
    if not isinstance(payload, dict):
        raise ParserContractError("parser contract must be a mapping")
    return payload


def _safe_relative_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or "\x00" in value
        or candidate.is_absolute()
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or candidate.as_posix() != value
    ):
        raise ParserContractError("parser artifact path is unsafe")
    return value


def load_frozen_parser_contract(path: str | Path) -> dict:
    """Load and validate the complete pre-fit PARSE-001 configuration."""

    payload = _load_yaml(Path(path))
    metadata = payload.get("parser_contract", {})
    software = payload.get("software", {})
    drain = payload.get("drain", {})
    persistence = payload.get("persistence", {})
    expected_metadata = {
        "id": "PARSE-001",
        "version": "1.0",
        "status": "FROZEN_BEFORE_REAL_FIT",
        "protocol_id": "PROTOCOL-001",
        "protocol_version": "1.1",
        "split_contract_id": "PROTOCOL-SPLIT-CLARIFY-001",
        "split_contract_version": "1.0",
        "fit_partition": "BASE_TRAIN",
        "fit_normal_only": True,
        "later_partition_mode": "FROZEN_READ_ONLY",
        "unknown_event_id": UNSEEN_EVENT_ID,
        "scientific_metrics_allowed": False,
    }
    if metadata != expected_metadata:
        raise ParserContractError("parser metadata is not the frozen PARSE-001 contract")
    if software != {"package": "drain3", "version": "0.9.11"}:
        raise ParserContractError("Drain3 software version is not frozen to 0.9.11")
    if importlib.metadata.version("drain3") != software["version"]:
        raise ParserContractError("installed Drain3 differs from the frozen contract")
    required_drain = {
        "similarity_threshold": 0.4,
        "depth": 4,
        "max_children": 100,
        "max_clusters": None,
        "extra_delimiters": [],
        "parametrize_numeric_tokens": True,
        "frozen_match_full_search_strategy": "fallback",
        "parameter_extraction_cache_capacity": 3000,
        "profiling_enabled": False,
        "snapshot_compress_state": False,
    }
    for key, expected in required_drain.items():
        if drain.get(key) != expected:
            raise ParserContractError(f"Drain3 parameter is not frozen: {key}")
    if persistence.get("overwrite_existing") is not False:
        raise ParserContractError("parser artifacts must use non-overwrite persistence")
    for key in (
        "state_file",
        "template_registry_file",
        "normal_pool_summary_file",
        "parser_manifest_file",
        "parser_manifest_hash_sidecar",
    ):
        _safe_relative_path(str(persistence.get(key, "")))
    return payload


def parser_config_sha256(contract: Mapping[str, object]) -> str:
    """Identity of all frozen parser, masking, normalization, and fit choices."""

    return _canonical_sha256(dict(contract))


def normalization_config_sha256(contract: Mapping[str, object]) -> str:
    normalization = contract.get("normalization")
    if not isinstance(normalization, dict):
        raise ParserContractError("normalization contract is missing")
    return _canonical_sha256(normalization)


def _drain_config(contract: Mapping[str, object]) -> TemplateMinerConfig:
    drain = contract["drain"]
    masking = contract["masking"]
    if not isinstance(drain, dict) or not isinstance(masking, dict):
        raise ParserContractError("Drain3/masking configuration is malformed")
    config = TemplateMinerConfig()
    config.drain_sim_th = float(drain["similarity_threshold"])
    config.drain_depth = int(drain["depth"])
    config.drain_max_children = int(drain["max_children"])
    config.drain_max_clusters = drain["max_clusters"]
    config.drain_extra_delimiters = list(drain["extra_delimiters"])
    config.parametrize_numeric_tokens = bool(drain["parametrize_numeric_tokens"])
    config.parameter_extraction_cache_capacity = int(
        drain["parameter_extraction_cache_capacity"]
    )
    config.profiling_enabled = bool(drain["profiling_enabled"])
    config.snapshot_compress_state = bool(drain["snapshot_compress_state"])
    config.mask_prefix = str(masking["mask_prefix"])
    config.mask_suffix = str(masking["mask_suffix"])
    rules = masking.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ParserContractError("at least one frozen masking instruction is required")
    config.masking_instructions = [
        MaskingInstruction(str(item["regex_pattern"]), str(item["name"]))
        for item in rules
    ]
    return config


def _cluster_records(miner: TemplateMiner) -> list[dict]:
    records = [
        {
            "cluster_id": int(cluster.cluster_id),
            "message_count": int(cluster.size),
            "normalized_template": cluster.get_template(),
            "tokens": list(cluster.log_template_tokens),
        }
        for cluster in miner.drain.clusters
    ]
    return sorted(records, key=lambda item: item["cluster_id"])


def _drain_cluster_state(miner: TemplateMiner) -> dict:
    records = _cluster_records(miner)
    return {
        "clusters_counter": int(miner.drain.clusters_counter),
        "total_message_count": int(miner.drain.get_total_cluster_size()),
        "cluster_count": len(records),
        "clusters": records,
    }


def _scientific_state_payload(
    *,
    miner: TemplateMiner,
    dataset_key: str,
    dataset_fingerprint: str,
    split_payload_hash: str,
    base_train_partition_hash: str,
    normal_pool_hash: str,
    config_hash: str,
) -> dict:
    return {
        "schema_version": PARSER_ARTIFACT_SCHEMA_VERSION,
        "implementation_version": PARSER_IMPLEMENTATION_VERSION,
        "dataset_key": dataset_key,
        "dataset_fingerprint": dataset_fingerprint,
        "protocol": {"id": "PROTOCOL-001", "version": "1.1"},
        "fit_partition": "BASE_TRAIN",
        "split_payload_hash": split_payload_hash,
        "base_train_partition_hash": base_train_partition_hash,
        "normal_pool_hash": normal_pool_hash,
        "parser_config_sha256": config_hash,
        "drain3_version": importlib.metadata.version("drain3"),
        "drain_cluster_state": _drain_cluster_state(miner),
    }


def _serialize_state(miner: TemplateMiner) -> bytes:
    persistence = MemoryBufferPersistence()
    miner.persistence_handler = persistence
    miner.save_state("PARSE-001 final frozen snapshot")
    if not isinstance(persistence.state, bytes) or not persistence.state:
        raise ParserContractError("Drain3 did not produce a serialized state")
    return persistence.state


def _restore_state(state: bytes, contract: Mapping[str, object]) -> TemplateMiner:
    persistence = MemoryBufferPersistence()
    persistence.state = state
    return TemplateMiner(persistence_handler=persistence, config=_drain_config(contract))


def _template_registry(
    *,
    miner: TemplateMiner,
    config_hash: str,
    normalization_hash: str,
    parser_state_hash: str,
) -> dict:
    parser_version = importlib.metadata.version("drain3")
    unique: dict[str, EventTemplate] = {}
    cluster_to_event: dict[str, str] = {}
    for cluster in miner.drain.clusters:
        template = cluster.get_template()
        event_id = build_event_id(
            parser_version=parser_version,
            normalization_version=NORMALIZATION_VERSION,
            normalized_template=template,
        )
        cluster_to_event[str(cluster.cluster_id)] = event_id
        unique.setdefault(
            template,
            EventTemplate(
                event_id=event_id,
                normalized_template=template,
                parser_version=parser_version,
                parser_config_sha256=config_hash,
                normalization_version=NORMALIZATION_VERSION,
                normalization_config_sha256=normalization_hash,
                template_sha256=hashlib.sha256(template.encode("utf-8")).hexdigest(),
            ),
        )
    templates = sorted(unique.values(), key=lambda item: item.event_id)
    return {
        "schema_version": PARSER_ARTIFACT_SCHEMA_VERSION,
        "artifact_type": "FROZEN_DRAIN3_TEMPLATE_REGISTRY",
        "parser_state_sha256": parser_state_hash,
        "unknown_event_id": UNSEEN_EVENT_ID,
        "templates": [item.model_dump(mode="json") for item in templates],
        "cluster_to_event_id": dict(
            sorted(cluster_to_event.items(), key=lambda item: int(item[0]))
        ),
    }


@dataclass(frozen=True, slots=True)
class FrozenTransformResult:
    """Structural frozen-parser result; not a complete canonical LogEvent."""

    event_id: str
    normalized_template: str | None
    parameters: tuple[str, ...]
    matched: bool


class FrozenDrainParser:
    """Read-only Drain3 wrapper bound to a verified frozen state."""

    def __init__(
        self,
        *,
        miner: TemplateMiner,
        contract: Mapping[str, object],
        cluster_to_event_id: Mapping[str, str],
        expected_cluster_state_sha256: str,
    ) -> None:
        self.__miner = miner
        self.__contract = dict(contract)
        self.__cluster_to_event_id = dict(cluster_to_event_id)
        self.__expected_cluster_state_sha256 = expected_cluster_state_sha256
        self._assert_unchanged()

    def _cluster_state_sha256(self) -> str:
        return _canonical_sha256(_drain_cluster_state(self.__miner))

    def _assert_unchanged(self) -> None:
        if self._cluster_state_sha256() != self.__expected_cluster_state_sha256:
            raise ParserContractError("frozen Drain3 cluster state mutated")

    def transform(
        self,
        message: str,
        *,
        partition: ScientificPartition,
    ) -> FrozenTransformResult:
        """Match one message without learning; TEST fails before Drain3 is called."""

        if partition is ScientificPartition.TEST:
            raise ParserContractError("scientific TEST is unavailable to PARSE-001")
        if not isinstance(message, str) or not message or "\x00" in message:
            raise ParserContractError("parser input must be non-empty NUL-free text")
        self._assert_unchanged()
        strategy = str(self.__contract["drain"]["frozen_match_full_search_strategy"])
        cluster = self.__miner.match(message, full_search_strategy=strategy)
        if cluster is None:
            result = FrozenTransformResult(
                event_id=UNSEEN_EVENT_ID,
                normalized_template=None,
                parameters=(),
                matched=False,
            )
        else:
            template = cluster.get_template()
            event_id = self.__cluster_to_event_id.get(str(cluster.cluster_id))
            if event_id is None:
                raise ParserContractError("matched cluster is absent from frozen registry")
            extracted = self.__miner.extract_parameters(
                template, message, exact_matching=True
            )
            parameters = tuple(item.value for item in extracted or ())
            result = FrozenTransformResult(
                event_id=event_id,
                normalized_template=template,
                parameters=parameters,
                matched=True,
            )
        self._assert_unchanged()
        return result


@dataclass(slots=True)
class _FitBundle:
    miner: TemplateMiner
    state_bytes: bytes
    parser_state_sha256: str
    cluster_state_sha256: str
    scientific_state_payload: dict
    registry: dict
    parser_config_sha256: str
    normalization_config_sha256: str


def _fit_pool(
    pool: NormalPool,
    contract: Mapping[str, object],
    *,
    progress: Callable[[int], None] | None = None,
) -> _FitBundle:
    if pool.selected_record_count <= 0:
        raise ParserContractError("normal-only BASE_TRAIN pool is empty")
    if pool.fit_partition is not ScientificPartition.BASE_TRAIN:
        raise ParserContractError("parser fit accepts only BASE_TRAIN input")
    if pool.selection_contract not in {
        "HDFS_ALL_MEMBER_BLOCK_SESSIONS_NORMAL_V1",
        "BGL_NORMAL_EVENT_IN_COMPLETE_BASE_TRAIN_WINDOW_V1",
    }:
        raise ParserContractError("parser fit received an unauthorized pool contract")
    config_hash = parser_config_sha256(contract)
    normalization_hash = normalization_config_sha256(contract)
    miner = TemplateMiner(config=_drain_config(contract))
    count = 0
    for count, (_, message) in enumerate(pool.iter_messages(), start=1):
        miner.add_log_message(message)
        if progress is not None and (
            count % 100_000 == 0 or count == pool.selected_record_count
        ):
            progress(count)
    if count != pool.selected_record_count:
        raise ParserContractError("Drain3 fit count differs from normal-pool identity")
    scientific = _scientific_state_payload(
        miner=miner,
        dataset_key=pool.dataset_key,
        dataset_fingerprint=pool.dataset_fingerprint,
        split_payload_hash=pool.split_payload_hash,
        base_train_partition_hash=pool.base_train_partition_hash,
        normal_pool_hash=pool.normal_pool_hash,
        config_hash=config_hash,
    )
    state_hash = _canonical_sha256(scientific)
    cluster_hash = _canonical_sha256(scientific["drain_cluster_state"])
    state_bytes = _serialize_state(miner)
    restored = _restore_state(state_bytes, contract)
    restored_scientific = _scientific_state_payload(
        miner=restored,
        dataset_key=pool.dataset_key,
        dataset_fingerprint=pool.dataset_fingerprint,
        split_payload_hash=pool.split_payload_hash,
        base_train_partition_hash=pool.base_train_partition_hash,
        normal_pool_hash=pool.normal_pool_hash,
        config_hash=config_hash,
    )
    if _canonical_sha256(restored_scientific) != state_hash:
        raise ParserContractError("independent Drain3 restore changed scientific state")
    registry = _template_registry(
        miner=restored,
        config_hash=config_hash,
        normalization_hash=normalization_hash,
        parser_state_hash=state_hash,
    )
    return _FitBundle(
        miner=restored,
        state_bytes=state_bytes,
        parser_state_sha256=state_hash,
        cluster_state_sha256=cluster_hash,
        scientific_state_payload=scientific,
        registry=registry,
        parser_config_sha256=config_hash,
        normalization_config_sha256=normalization_hash,
    )


def _write_bytes(path: Path, payload: bytes) -> None:
    if path.exists():
        raise ParserContractError(f"refusing to overwrite parser artifact: {path}")
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def fit_and_freeze_parser(
    *,
    pool: NormalPool,
    contract_path: str | Path,
    output_directory: str | Path,
    generated_at_utc: str | None = None,
    progress: Callable[[int], None] | None = None,
) -> dict:
    """Fit, persist atomically, restore independently, and validate frozen match."""

    contract = load_frozen_parser_contract(contract_path)
    destination = Path(output_directory).resolve()
    if destination.exists():
        raise ParserContractError(f"parser output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.tmp"
    if staging.exists():
        raise ParserContractError(f"stale parser staging directory exists: {staging}")
    staging.mkdir()
    try:
        bundle = _fit_pool(pool, contract, progress=progress)
        persistence = contract["persistence"]
        state_name = _safe_relative_path(str(persistence["state_file"]))
        registry_name = _safe_relative_path(str(persistence["template_registry_file"]))
        pool_name = _safe_relative_path(str(persistence["normal_pool_summary_file"]))
        manifest_name = _safe_relative_path(str(persistence["parser_manifest_file"]))
        sidecar_name = _safe_relative_path(
            str(persistence["parser_manifest_hash_sidecar"])
        )
        _write_bytes(staging / state_name, bundle.state_bytes)
        _write_bytes(staging / registry_name, _json_bytes(bundle.registry))
        _write_bytes(staging / pool_name, _json_bytes(pool.summary()))

        artifact_files = []
        for name in (state_name, registry_name, pool_name):
            path = staging / name
            artifact_files.append(
                {
                    "path": name,
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        manifest = {
            "schema_version": PARSER_ARTIFACT_SCHEMA_VERSION,
            "artifact_type": "DERIVED_REPRODUCIBLE_FROZEN_DRAIN3_STATE",
            "status": "FIT_COMPLETED_FROZEN",
            "dataset": {
                "key": pool.dataset_key,
                "dataset_fingerprint": pool.dataset_fingerprint,
                "source_file": pool.source_file,
                "source_file_sha256": pool.source_file_sha256,
            },
            "protocol": {"id": "PROTOCOL-001", "version": "1.1"},
            "fit": {
                "partition": "BASE_TRAIN",
                "normal_only": True,
                "split_payload_hash": pool.split_payload_hash,
                "base_train_partition_hash": pool.base_train_partition_hash,
                "normal_selection_contract": pool.selection_contract,
                "normal_pool_hash": pool.normal_pool_hash,
                "input_record_count": pool.selected_record_count,
            },
            "software": {
                "parser": "drain3",
                "drain3_version": importlib.metadata.version("drain3"),
                "implementation_version": PARSER_IMPLEMENTATION_VERSION,
            },
            "configuration": {
                "parser_config_sha256": bundle.parser_config_sha256,
                "normalization_config_sha256": bundle.normalization_config_sha256,
                "frozen_contract": contract,
            },
            "identity": {
                "normal_pool_sha256": pool.normal_pool_hash,
                "parser_state_sha256": bundle.parser_state_sha256,
                "cluster_state_sha256": bundle.cluster_state_sha256,
                "state_identity_algorithm": PARSER_STATE_IDENTITY_ALGORITHM,
                "serialized_state_sha256": artifact_files[0]["sha256"],
                "template_registry_sha256": artifact_files[1]["sha256"],
            },
            "structural_summary": {
                "input_record_count": pool.selected_record_count,
                "cluster_count": len(bundle.miner.drain.clusters),
                "unique_template_count": len(bundle.registry["templates"]),
                "total_cluster_message_count": bundle.miner.drain.get_total_cluster_size(),
            },
            "frozen_inference": {
                "method": "TemplateMiner.match",
                "full_search_strategy": contract["drain"][
                    "frozen_match_full_search_strategy"
                ],
                "unknown_event_id": UNSEEN_EVENT_ID,
                "mutating_add_log_message_exposed": False,
            },
            "access_audit": {
                "labels_used_only_for_base_train_normal_filtering": True,
                "validation_accessed": False,
                "test_accessed": False,
                "scientific_metrics_computed": False,
            },
            "artifact_files": artifact_files,
            "generation": {
                "generated_at_utc": generated_at_utc or _utc_now(),
                "timestamp_participates_in_identity": False,
            },
        }
        _write_bytes(staging / manifest_name, _json_bytes(manifest))
        manifest_hash = sha256_file(staging / manifest_name)
        _write_bytes(
            staging / sidecar_name,
            f"{manifest_hash}  {manifest_name}\n".encode("ascii"),
        )
        staging.replace(destination)
        validation = validate_parser_artifact(destination)
        return {
            "dataset": pool.dataset_key,
            "output_directory": destination.as_posix(),
            "normal_pool_hash": pool.normal_pool_hash,
            "parser_config_sha256": bundle.parser_config_sha256,
            "parser_state_sha256": bundle.parser_state_sha256,
            "serialized_state_sha256": artifact_files[0]["sha256"],
            "template_registry_sha256": artifact_files[1]["sha256"],
            "input_record_count": pool.selected_record_count,
            "cluster_count": len(bundle.miner.drain.clusters),
            "unique_template_count": len(bundle.registry["templates"]),
            "restore_status": validation["restore_status"],
            "frozen_transform_status": validation["frozen_transform_status"],
            "test_accessed": False,
        }
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ParserContractError(f"invalid parser artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise ParserContractError(f"parser artifact must be an object: {path}")
    return payload


def load_frozen_parser(parser_directory: str | Path) -> FrozenDrainParser:
    """Independently restore the immutable parser using persisted artifacts."""

    root = Path(parser_directory).resolve()
    manifest = _load_json(root / "parser-manifest.json")
    if manifest.get("status") != "FIT_COMPLETED_FROZEN":
        raise ParserContractError("parser state is not marked frozen")
    if manifest.get("access_audit", {}).get("test_accessed") is not False:
        raise ParserContractError("parser manifest reports scientific TEST access")
    contract = manifest.get("configuration", {}).get("frozen_contract")
    if not isinstance(contract, dict):
        raise ParserContractError("frozen parser contract is missing from manifest")
    if parser_config_sha256(contract) != manifest["configuration"]["parser_config_sha256"]:
        raise ParserContractError("embedded parser configuration hash mismatch")
    persistence = contract["persistence"]
    state_path = root / _safe_relative_path(str(persistence["state_file"]))
    registry_path = root / _safe_relative_path(str(persistence["template_registry_file"]))
    state = state_path.read_bytes()
    if sha256_file(state_path) != manifest["identity"]["serialized_state_sha256"]:
        raise ParserContractError("serialized Drain3 state hash mismatch")
    registry = _load_json(registry_path)
    if sha256_file(registry_path) != manifest["identity"]["template_registry_sha256"]:
        raise ParserContractError("template registry hash mismatch")
    miner = _restore_state(state, contract)
    cluster_hash = _canonical_sha256(_drain_cluster_state(miner))
    if cluster_hash != manifest["identity"]["cluster_state_sha256"]:
        raise ParserContractError("restored Drain3 cluster state hash mismatch")
    scientific = _scientific_state_payload(
        miner=miner,
        dataset_key=manifest["dataset"]["key"],
        dataset_fingerprint=manifest["dataset"]["dataset_fingerprint"],
        split_payload_hash=manifest["fit"]["split_payload_hash"],
        base_train_partition_hash=manifest["fit"]["base_train_partition_hash"],
        normal_pool_hash=manifest["fit"]["normal_pool_hash"],
        config_hash=manifest["configuration"]["parser_config_sha256"],
    )
    if _canonical_sha256(scientific) != manifest["identity"]["parser_state_sha256"]:
        raise ParserContractError("restored scientific parser-state identity mismatch")
    if registry.get("parser_state_sha256") != manifest["identity"]["parser_state_sha256"]:
        raise ParserContractError("template registry is bound to another parser state")
    cluster_to_event = registry.get("cluster_to_event_id")
    if not isinstance(cluster_to_event, dict):
        raise ParserContractError("template registry cluster mapping is malformed")
    expected_cluster_ids = {str(item["cluster_id"]) for item in _cluster_records(miner)}
    if set(cluster_to_event) != expected_cluster_ids:
        raise ParserContractError("template registry does not cover exact frozen clusters")
    templates = registry.get("templates")
    if not isinstance(templates, list) or not templates:
        raise ParserContractError("template registry has no canonical templates")
    verified_templates = [EventTemplate.model_validate(item) for item in templates]
    valid_event_ids = {item.event_id for item in verified_templates}
    if set(cluster_to_event.values()).difference(valid_event_ids):
        raise ParserContractError("cluster mapping references an unknown event ID")
    return FrozenDrainParser(
        miner=miner,
        contract=contract,
        cluster_to_event_id=cluster_to_event,
        expected_cluster_state_sha256=cluster_hash,
    )


def validate_parser_artifact(parser_directory: str | Path) -> dict:
    """Verify exact files, identities, restore, and immutable synthetic smoke."""

    root = Path(parser_directory).resolve()
    manifest_path = root / "parser-manifest.json"
    manifest = _load_json(manifest_path)
    sidecar = (root / "parser-manifest.json.sha256").read_text(encoding="ascii").split()
    manifest_hash = sha256_file(manifest_path)
    if sidecar != [manifest_hash, "parser-manifest.json"]:
        raise ParserContractError("parser manifest sidecar is stale")
    if manifest.get("schema_version") != PARSER_ARTIFACT_SCHEMA_VERSION:
        raise ParserContractError("unsupported parser artifact schema")
    if manifest.get("protocol") != {"id": "PROTOCOL-001", "version": "1.1"}:
        raise ParserContractError("parser artifact is bound to another protocol")
    for artifact in manifest.get("artifact_files", []):
        path = root / _safe_relative_path(str(artifact["path"]))
        if (
            not path.is_file()
            or path.stat().st_size != artifact["size_bytes"]
            or sha256_file(path) != artifact["sha256"]
        ):
            raise ParserContractError(
                f"parser artifact integrity mismatch: {path.name}"
            )
    pool_summary = _load_json(root / "normal-pool-summary.json")
    if (
        pool_summary.get("normal_pool_hash")
        != manifest.get("identity", {}).get("normal_pool_sha256")
        or pool_summary.get("test_accessed") is not False
    ):
        raise ParserContractError("normal-pool summary identity/access mismatch")
    parser = load_frozen_parser(root)
    registry = _load_json(root / "template-registry.json")
    if not registry.get("templates"):
        raise ParserContractError("frozen parser has no template")
    max_arity = max(
        len(item["normalized_template"].split()) for item in registry["templates"]
    )
    unknown_message = " ".join(
        f"SEQLOGAD_UNKNOWN_{index}" for index in range(max_arity + 1)
    )
    unknown = parser.transform(
        unknown_message,
        partition=ScientificPartition.VAL_EXPERT,
    )
    if unknown.event_id != UNSEEN_EVENT_ID or unknown.matched:
        raise ParserContractError("frozen unknown-event policy failed")
    return {
        "dataset": manifest["dataset"]["key"],
        "status": "VERIFIED",
        "manifest_file_sha256": manifest_hash,
        "normal_pool_hash": manifest["identity"]["normal_pool_sha256"],
        "parser_config_sha256": manifest["configuration"]["parser_config_sha256"],
        "parser_state_sha256": manifest["identity"]["parser_state_sha256"],
        "serialized_state_sha256": manifest["identity"]["serialized_state_sha256"],
        "template_registry_sha256": manifest["identity"]["template_registry_sha256"],
        "input_record_count": manifest["structural_summary"]["input_record_count"],
        "cluster_count": manifest["structural_summary"]["cluster_count"],
        "unique_template_count": manifest["structural_summary"][
            "unique_template_count"
        ],
        "restore_status": "PASS",
        "frozen_transform_status": "PASS",
        "test_accessed": False,
    }


def compare_fit_identities(
    first: Mapping[str, object], second: Mapping[str, object]
) -> dict:
    """Compare deterministic fit identities, excluding manifest timestamp bytes."""

    keys = (
        "normal_pool_hash",
        "parser_config_sha256",
        "parser_state_sha256",
        "serialized_state_sha256",
        "template_registry_sha256",
        "input_record_count",
        "cluster_count",
        "unique_template_count",
    )
    mismatches = [key for key in keys if first.get(key) != second.get(key)]
    return {"deterministic": not mismatches, "mismatches": mismatches}


__all__ = [
    "PARSER_ARTIFACT_SCHEMA_VERSION",
    "PARSER_IMPLEMENTATION_VERSION",
    "FrozenDrainParser",
    "FrozenTransformResult",
    "ParserContractError",
    "compare_fit_identities",
    "fit_and_freeze_parser",
    "load_frozen_parser",
    "load_frozen_parser_contract",
    "normalization_config_sha256",
    "parser_config_sha256",
    "validate_parser_artifact",
]
