"""Enforce the human-only scientific TEST access contract for SPLIT-001.

The real split generator creates a sealed binding but never authorizes or opens
TEST.  Destructive state transitions are exercised only with synthetic test
directories.  No environment variable or casual boolean can bypass the seal.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


TEST_SEAL_SCHEMA_VERSION = "1.0"
TEST_ACCESS_CONFIRMATION_PHRASE = (
    "I_ACKNOWLEDGE_FINAL_TEST_IS_SINGLE_USE_AND_HUMAN_AUTHORIZED"
)
FINAL_TEST_ACCESS_SCOPE = "FINAL_CONFIRMATORY_EVALUATION"

_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_SEAL_ID_PATTERN = r"^TEST-SEAL-[0-9a-f]{64}$"
_UNLOCK_ID_PATTERN = r"^TEST-UNLOCK-[0-9a-f]{64}$"
_GRANT_ID_PATTERN = r"^TEST-GRANT-[0-9a-f]{64}$"


class TestSealError(RuntimeError):
    """Raised when TEST-seal state is missing, stale, or inconsistent."""


class TestAccessDeniedError(TestSealError):
    """Raised before any TEST membership record is opened."""

    __test__ = False


def canonical_json(value: object) -> str:
    """Serialize deterministic identity-bearing JSON."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def sha256_canonical(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _normalized_relative_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or "\x00" in value
        or candidate.is_absolute()
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or candidate.as_posix() != value
    ):
        raise ValueError("path must be normalized repository-relative POSIX")
    return value


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _atomic_json_write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise TestSealError(f"stale temporary file exists: {temporary}")
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    try:
        with temporary.open("xb") as handle:
            handle.write(serialized.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


class SealBinding(BaseModel):
    """The immutable four-part identity required by the frozen protocol."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_key: Literal["hdfs", "bgl"]
    dataset_fingerprint: str = Field(pattern=_SHA256_PATTERN)
    protocol_id: Literal["PROTOCOL-001"] = "PROTOCOL-001"
    protocol_version: Literal["1.1"] = "1.1"
    split_payload_hash: str = Field(pattern=_SHA256_PATTERN)
    test_partition_hash: str = Field(pattern=_SHA256_PATTERN)


def build_seal_id(binding: SealBinding) -> str:
    return f"TEST-SEAL-{sha256_canonical(binding.model_dump(mode='json'))}"


class TestSeal(BaseModel):
    """Persisted deny-by-default state for one real or synthetic split."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = TEST_SEAL_SCHEMA_VERSION
    seal_id: str = Field(pattern=_SEAL_ID_PATTERN)
    binding: SealBinding
    status: Literal["SEALED", "UNLOCKED", "OPENED"]
    access_policy: Literal["DENY_BY_DEFAULT"] = "DENY_BY_DEFAULT"
    test_membership_path: str
    audit_log_path: str
    grant_path: str
    created_at_utc: str = Field(min_length=20)
    never_opened: bool
    open_count: int = Field(ge=0)
    unlock_records: int = Field(ge=0)

    @field_validator("test_membership_path", "audit_log_path", "grant_path")
    @classmethod
    def validate_relative_paths(cls, value: str) -> str:
        return _normalized_relative_path(value)

    @model_validator(mode="after")
    def validate_state(self) -> "TestSeal":
        if self.seal_id != build_seal_id(self.binding):
            raise ValueError("seal_id does not match the immutable TEST binding")
        if self.never_opened != (self.open_count == 0):
            raise ValueError("never_opened and open_count disagree")
        if self.status == "SEALED":
            if self.open_count != 0 or self.unlock_records != 0:
                raise ValueError("a sealed TEST must have no opens or unlock records")
        elif self.status == "UNLOCKED":
            if self.open_count != 0 or self.unlock_records != 1:
                raise ValueError("unlocked TEST requires one authorization and no open")
        elif self.open_count != 1 or self.unlock_records != 1:
            raise ValueError("opened TEST must be the single authorized access")
        return self


class HumanTestUnlockRequest(BaseModel):
    """Explicit future human authorization request; never generated implicitly."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    actor_source: Literal["HUMAN"]
    confirmation_phrase: Literal[
        "I_ACKNOWLEDGE_FINAL_TEST_IS_SINGLE_USE_AND_HUMAN_AUTHORIZED"
    ]
    reason: str = Field(min_length=20, max_length=1000)
    access_scope: Literal["FINAL_CONFIRMATORY_EVALUATION"]
    protocol_id: Literal["PROTOCOL-001"] = "PROTOCOL-001"
    protocol_version: Literal["1.1"] = "1.1"
    dataset_key: Literal["hdfs", "bgl"]
    expected_split_payload_hash: str = Field(pattern=_SHA256_PATTERN)
    expected_test_partition_hash: str = Field(pattern=_SHA256_PATTERN)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        if value != value.strip() or "\x00" in value:
            raise ValueError("reason must be trimmed and NUL-free")
        return value


class TestAccessGrant(BaseModel):
    """One-use grant created only by the dedicated human authorization path."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = TEST_SEAL_SCHEMA_VERSION
    grant_id: str = Field(pattern=_GRANT_ID_PATTERN)
    unlock_id: str = Field(pattern=_UNLOCK_ID_PATTERN)
    seal_id: str = Field(pattern=_SEAL_ID_PATTERN)
    binding: SealBinding
    actor_source: Literal["HUMAN"]
    reason: str = Field(min_length=20)
    access_scope: Literal["FINAL_CONFIRMATORY_EVALUATION"]
    authorized_at_utc: str = Field(min_length=20)
    consumed: bool = False


class TestAccessAuditRecord(BaseModel):
    """Append-only linkage for future authorization or first access."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = TEST_SEAL_SCHEMA_VERSION
    event: Literal["UNLOCK_AUTHORIZED", "TEST_OPENED"]
    unlock_id: str = Field(pattern=_UNLOCK_ID_PATTERN)
    grant_id: str = Field(pattern=_GRANT_ID_PATTERN)
    seal_id: str = Field(pattern=_SEAL_ID_PATTERN)
    binding: SealBinding
    actor_source: Literal["HUMAN"]
    reason: str = Field(min_length=20)
    access_scope: Literal["FINAL_CONFIRMATORY_EVALUATION"]
    timestamp_utc: str = Field(min_length=20)
    previous_record_sha256: str | None = Field(default=None, pattern=_SHA256_PATTERN)
    record_sha256: str = Field(pattern=_SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_record_hash(self) -> "TestAccessAuditRecord":
        payload = self.model_dump(mode="json", exclude={"record_sha256"})
        if self.record_sha256 != sha256_canonical(payload):
            raise ValueError("audit record hash does not match its canonical payload")
        return self


def create_sealed_test_state(
    split_directory: str | Path,
    *,
    binding: SealBinding,
    test_membership_path: str = "sealed/TEST.jsonl",
    created_at_utc: str | None = None,
) -> TestSeal:
    """Create a real/synthetic seal only when no previous access state exists."""

    root = Path(split_directory)
    seal_path = root / "test-seal.json"
    audit_path = root / "test-access-audit.jsonl"
    grant_path = root / "test-access-grant.json"
    if seal_path.exists() or audit_path.exists() or grant_path.exists():
        raise TestSealError("refusing to overwrite existing TEST access state")
    member_path = root / _normalized_relative_path(test_membership_path)
    if not member_path.is_file():
        raise TestSealError("TEST membership must exist inside the unpublished staging tree")
    audit_path.touch(exist_ok=False)
    seal = TestSeal(
        seal_id=build_seal_id(binding),
        binding=binding,
        status="SEALED",
        test_membership_path=test_membership_path,
        audit_log_path="test-access-audit.jsonl",
        grant_path="test-access-grant.json",
        created_at_utc=created_at_utc or _utc_now(),
        never_opened=True,
        open_count=0,
        unlock_records=0,
    )
    _atomic_json_write(seal_path, seal.model_dump(mode="json"))
    return seal


def load_test_seal(split_directory: str | Path) -> TestSeal:
    root = Path(split_directory)
    try:
        payload = json.loads((root / "test-seal.json").read_text(encoding="utf-8"))
        seal = TestSeal.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise TestSealError(f"invalid TEST seal: {exc}") from exc
    member_path = root / seal.test_membership_path
    audit_path = root / seal.audit_log_path
    if not member_path.is_file() or not audit_path.is_file():
        raise TestSealError("seal references a missing membership or audit artifact")
    audit_lines = sum(1 for line in audit_path.open("rb") if line.strip())
    if seal.status == "SEALED" and audit_lines != 0:
        raise TestSealError("sealed TEST has unexpected audit records")
    if seal.status == "UNLOCKED" and audit_lines != 1:
        raise TestSealError("unlocked TEST audit count is inconsistent")
    if seal.status == "OPENED" and audit_lines != 2:
        raise TestSealError("opened TEST audit count is inconsistent")
    return seal


def assert_test_access_denied(split_directory: str | Path) -> TestSeal:
    """Verify the real default state without opening TEST membership."""

    seal = load_test_seal(split_directory)
    if seal.status != "SEALED" or not seal.never_opened:
        raise TestSealError("TEST is not in SEALED / NEVER_OPENED state")
    grant_path = Path(split_directory) / seal.grant_path
    if grant_path.exists():
        raise TestSealError("sealed TEST must not have an access grant")
    return seal


def deny_ordinary_test_access() -> None:
    """Fail before an ordinary loader resolves or opens any TEST record file."""

    raise TestAccessDeniedError(
        "scientific TEST access is denied; use the dedicated human final-TEST workflow"
    )


def _audit_record(
    *,
    event: Literal["UNLOCK_AUTHORIZED", "TEST_OPENED"],
    unlock_id: str,
    grant_id: str,
    seal: TestSeal,
    request: HumanTestUnlockRequest,
    timestamp_utc: str,
    previous_record_sha256: str | None,
) -> TestAccessAuditRecord:
    payload = {
        "schema_version": TEST_SEAL_SCHEMA_VERSION,
        "event": event,
        "unlock_id": unlock_id,
        "grant_id": grant_id,
        "seal_id": seal.seal_id,
        "binding": seal.binding.model_dump(mode="json"),
        "actor_source": "HUMAN",
        "reason": request.reason,
        "access_scope": request.access_scope,
        "timestamp_utc": timestamp_utc,
        "previous_record_sha256": previous_record_sha256,
    }
    return TestAccessAuditRecord(
        **payload,
        record_sha256=sha256_canonical(payload),
    )


def authorize_human_test_access(
    split_directory: str | Path,
    request: HumanTestUnlockRequest,
    *,
    timestamp_utc: str | None = None,
) -> TestAccessGrant:
    """Future dedicated unlock path; it never reads TEST membership."""

    root = Path(split_directory)
    seal = assert_test_access_denied(root)
    binding = seal.binding
    if (
        request.dataset_key != binding.dataset_key
        or request.protocol_id != binding.protocol_id
        or request.protocol_version != binding.protocol_version
        or request.expected_split_payload_hash != binding.split_payload_hash
        or request.expected_test_partition_hash != binding.test_partition_hash
    ):
        raise TestAccessDeniedError("human unlock request does not match sealed identity")
    timestamp = timestamp_utc or _utc_now()
    request_identity = {
        **request.model_dump(mode="json"),
        "seal_id": seal.seal_id,
        "timestamp_utc": timestamp,
    }
    unlock_id = f"TEST-UNLOCK-{sha256_canonical(request_identity)}"
    grant_payload = {
        "unlock_id": unlock_id,
        "seal_id": seal.seal_id,
        "binding": binding.model_dump(mode="json"),
        "actor_source": "HUMAN",
        "reason": request.reason,
        "access_scope": request.access_scope,
        "authorized_at_utc": timestamp,
    }
    grant_id = f"TEST-GRANT-{sha256_canonical(grant_payload)}"
    grant = TestAccessGrant(
        grant_id=grant_id,
        **grant_payload,
        consumed=False,
    )
    audit = _audit_record(
        event="UNLOCK_AUTHORIZED",
        unlock_id=unlock_id,
        grant_id=grant_id,
        seal=seal,
        request=request,
        timestamp_utc=timestamp,
        previous_record_sha256=None,
    )
    _atomic_json_write(root / seal.grant_path, grant.model_dump(mode="json"))
    with (root / seal.audit_log_path).open("ab") as handle:
        handle.write((audit.model_dump_json() + "\n").encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    unlocked = seal.model_copy(
        update={"status": "UNLOCKED", "unlock_records": 1}
    )
    _atomic_json_write(root / "test-seal.json", unlocked.model_dump(mode="json"))
    return grant


def validate_unconsumed_grant(
    split_directory: str | Path,
    grant: TestAccessGrant,
) -> tuple[TestSeal, Path]:
    """Validate a future grant without opening TEST membership."""

    root = Path(split_directory)
    seal = load_test_seal(root)
    if seal.status != "UNLOCKED" or seal.open_count != 0:
        raise TestAccessDeniedError("TEST is not in the authorized unopened state")
    if grant.consumed or grant.seal_id != seal.seal_id or grant.binding != seal.binding:
        raise TestAccessDeniedError("grant does not match the active TEST seal")
    persisted_path = root / seal.grant_path
    try:
        persisted = TestAccessGrant.model_validate_json(
            persisted_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        raise TestAccessDeniedError("persisted TEST grant is missing or invalid") from exc
    if persisted != grant:
        raise TestAccessDeniedError("provided TEST grant differs from persisted grant")
    return seal, root / seal.test_membership_path


def consume_human_test_grant(
    split_directory: str | Path,
    grant: TestAccessGrant,
    *,
    timestamp_utc: str | None = None,
) -> Path:
    """Consume one synthetic/future grant before returning the TEST file path.

    State is durably changed to ``OPENED`` before the caller can open the
    membership file.  SPLIT-001 never invokes this function for real data.
    """

    root = Path(split_directory)
    seal, membership_path = validate_unconsumed_grant(root, grant)
    timestamp = timestamp_utc or _utc_now()
    request = HumanTestUnlockRequest(
        actor_source="HUMAN",
        confirmation_phrase=TEST_ACCESS_CONFIRMATION_PHRASE,
        reason=grant.reason,
        access_scope=grant.access_scope,
        protocol_id=grant.binding.protocol_id,
        protocol_version=grant.binding.protocol_version,
        dataset_key=grant.binding.dataset_key,
        expected_split_payload_hash=grant.binding.split_payload_hash,
        expected_test_partition_hash=grant.binding.test_partition_hash,
    )
    audit_path = root / seal.audit_log_path
    try:
        first_payload = json.loads(
            next(line for line in audit_path.read_text(encoding="utf-8").splitlines() if line)
        )
        first_record = TestAccessAuditRecord.model_validate(first_payload)
    except (OSError, StopIteration, json.JSONDecodeError, ValueError) as exc:
        raise TestAccessDeniedError("authorization audit record is invalid") from exc
    opened_record = _audit_record(
        event="TEST_OPENED",
        unlock_id=grant.unlock_id,
        grant_id=grant.grant_id,
        seal=seal,
        request=request,
        timestamp_utc=timestamp,
        previous_record_sha256=first_record.record_sha256,
    )
    consumed = grant.model_copy(update={"consumed": True})
    _atomic_json_write(root / seal.grant_path, consumed.model_dump(mode="json"))
    with audit_path.open("ab") as handle:
        handle.write((opened_record.model_dump_json() + "\n").encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    opened = seal.model_copy(
        update={"status": "OPENED", "never_opened": False, "open_count": 1}
    )
    _atomic_json_write(root / "test-seal.json", opened.model_dump(mode="json"))
    return membership_path


__all__ = [
    "FINAL_TEST_ACCESS_SCOPE",
    "HumanTestUnlockRequest",
    "SealBinding",
    "TEST_ACCESS_CONFIRMATION_PHRASE",
    "TEST_SEAL_SCHEMA_VERSION",
    "TestAccessDeniedError",
    "TestAccessGrant",
    "TestAccessAuditRecord",
    "TestSeal",
    "TestSealError",
    "assert_test_access_denied",
    "authorize_human_test_access",
    "build_seal_id",
    "canonical_json",
    "consume_human_test_grant",
    "create_sealed_test_state",
    "deny_ordinary_test_access",
    "load_test_seal",
    "sha256_canonical",
    "validate_unconsumed_grant",
]
