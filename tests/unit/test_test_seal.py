"""Synthetic-only tests for the future human final-TEST workflow."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from seqlogad.evaluation.test_seal import (
    FINAL_TEST_ACCESS_SCOPE,
    TEST_ACCESS_CONFIRMATION_PHRASE,
    HumanTestUnlockRequest,
    SealBinding,
    TestAccessDeniedError,
    authorize_human_test_access,
    consume_human_test_grant,
    create_sealed_test_state,
    load_test_seal,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _sealed(tmp_path: Path, *, split_hash: str = HASH_B) -> tuple[Path, SealBinding]:
    root = tmp_path / f"split-{split_hash[:4]}"
    (root / "sealed").mkdir(parents=True)
    (root / "sealed/TEST.jsonl").write_text('{"synthetic":true}\n', encoding="utf-8")
    binding = SealBinding(
        dataset_key="hdfs",
        dataset_fingerprint=HASH_A,
        protocol_version="1.1",
        split_payload_hash=split_hash,
        test_partition_hash=HASH_C,
    )
    create_sealed_test_state(
        root,
        binding=binding,
        created_at_utc="2026-08-23T00:00:00Z",
    )
    return root, binding


def _request(binding: SealBinding, **changes: str) -> HumanTestUnlockRequest:
    payload = {
        "actor_source": "HUMAN",
        "confirmation_phrase": TEST_ACCESS_CONFIRMATION_PHRASE,
        "reason": "Human-approved final confirmatory evaluation only.",
        "access_scope": FINAL_TEST_ACCESS_SCOPE,
        "protocol_version": "1.1",
        "dataset_key": binding.dataset_key,
        "expected_split_payload_hash": binding.split_payload_hash,
        "expected_test_partition_hash": binding.test_partition_hash,
    }
    payload.update(changes)
    return HumanTestUnlockRequest.model_validate(payload)


def test_default_state_is_sealed_never_opened_and_has_no_record(tmp_path: Path) -> None:
    root, _ = _sealed(tmp_path)
    seal = load_test_seal(root)
    assert (seal.status, seal.never_opened, seal.open_count, seal.unlock_records) == (
        "SEALED",
        True,
        0,
        0,
    )
    assert (root / "test-access-audit.jsonl").read_bytes() == b""
    assert not (root / "test-access-grant.json").exists()


def test_unlock_requires_exact_confirmation_phrase() -> None:
    with pytest.raises(ValidationError):
        HumanTestUnlockRequest(
            actor_source="HUMAN",
            confirmation_phrase="yes",
            reason="Human-approved final confirmatory evaluation only.",
            access_scope=FINAL_TEST_ACCESS_SCOPE,
            protocol_version="1.1",
            dataset_key="hdfs",
            expected_split_payload_hash=HASH_B,
            expected_test_partition_hash=HASH_C,
        )


@pytest.mark.parametrize(
    "change",
    [
        {"expected_split_payload_hash": "d" * 64},
        {"expected_test_partition_hash": "e" * 64},
        {"dataset_key": "bgl"},
    ],
)
def test_wrong_binding_cannot_unlock(tmp_path: Path, change: dict[str, str]) -> None:
    root, binding = _sealed(tmp_path)
    with pytest.raises(TestAccessDeniedError):
        authorize_human_test_access(root, _request(binding, **change))
    assert load_test_seal(root).status == "SEALED"


def test_explicit_human_flow_is_single_use_and_audited(tmp_path: Path) -> None:
    root, binding = _sealed(tmp_path)
    grant = authorize_human_test_access(
        root,
        _request(binding),
        timestamp_utc="2026-08-23T00:01:00Z",
    )
    unlocked = load_test_seal(root)
    assert unlocked.status == "UNLOCKED"
    assert unlocked.open_count == 0
    membership = consume_human_test_grant(
        root, grant, timestamp_utc="2026-08-23T00:02:00Z"
    )
    assert membership == root / "sealed/TEST.jsonl"
    opened = load_test_seal(root)
    assert (opened.status, opened.open_count, opened.unlock_records) == ("OPENED", 1, 1)
    assert len((root / "test-access-audit.jsonl").read_text().splitlines()) == 2
    with pytest.raises(TestAccessDeniedError):
        consume_human_test_grant(root, grant)


def test_seal_binding_cannot_be_reused_for_another_split(tmp_path: Path) -> None:
    first, binding = _sealed(tmp_path, split_hash=HASH_B)
    second, _ = _sealed(tmp_path, split_hash="d" * 64)
    grant = authorize_human_test_access(first, _request(binding))
    with pytest.raises(TestAccessDeniedError):
        consume_human_test_grant(second, grant)


def test_regeneration_creates_no_unlock_state(tmp_path: Path) -> None:
    first, _ = _sealed(tmp_path / "first")
    second, _ = _sealed(tmp_path / "second")
    for root in (first, second):
        seal = load_test_seal(root)
        assert seal.status == "SEALED"
        assert seal.open_count == seal.unlock_records == 0


def test_unsupported_protocol_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SealBinding(
            dataset_key="hdfs",
            dataset_fingerprint=HASH_A,
            protocol_version="1.0",
            split_payload_hash=HASH_B,
            test_partition_hash=HASH_C,
        )
