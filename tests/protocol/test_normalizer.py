"""NORM-CS-001 golden cases, determinism and versioning (Excel P1.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from seqlogad.protocol.normalizer import NormalizerError, load_normalizer


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def normalizer():
    return load_normalizer(PROJECT_ROOT)


GOLDEN_CASES = [
    (
        "Receiving block blk_-1608999687919862906 src: /10.251.31.5:56682 dest: /10.251.31.5:50010",
        "Receiving block <BLK> src: /<IP>:<PORT> dest: /<IP>:<PORT>",
    ),
    (
        "2015-10-17 21:47:48,288 INFO Created MRAppMaster for application "
        "appattempt_1445087491445_0005_000001",
        "<TS> INFO Created MRAppMaster for application <YARNID>",
    ),
    (
        "instance 544fd51c-4edc-4780-baae-ba1d80a0acfc spawned",
        "instance <UUID> spawned",
    ),
    (
        "ciod: LOGIN chdir(/p/gb1/stella/RAPTOR) failed on R02-M1-N0-C:J12-U11",
        "ciod: LOGIN chdir(/p/gb1/stella/RAPTOR) failed on <NODE>",
    ),
    (
        "checksum deadbeefcafe1234 over IPv4 TCP on x86_64 using SHA-256",
        "checksum <HEX> over IPv4 TCP on x86_64 using SHA-256",
    ),
    ('"GET /v2/servers/detail HTTP/1.1" status: 200 len: 1893', '"GET /v2/servers/detail HTTP/1.1" status: <NUM> len: <NUM>'),
]


@pytest.mark.parametrize(("raw", "expected"), GOLDEN_CASES)
def test_golden_masking_cases(normalizer, raw: str, expected: str) -> None:
    assert normalizer.normalize(raw) == expected


@pytest.mark.parametrize(("raw", "_expected"), GOLDEN_CASES)
def test_transform_is_deterministic(normalizer, raw: str, _expected: str) -> None:
    assert normalizer.normalize(raw) == normalizer.normalize(raw)


def test_business_tokens_survive_the_numeric_rule(normalizer) -> None:
    """The preserve list exists so masking does not erase meaningful vocabulary."""

    for token in ("HTTP/1.1", "IPv4", "IPv6", "SHA-256", "MD5", "x86_64", "TCP"):
        assert token in normalizer.normalize(f"protocol {token} negotiated")


def test_raw_message_is_never_mutated(normalizer) -> None:
    raw = "block blk_123 at 10.0.0.1"
    before = raw
    normalizer.normalize(raw)
    assert raw == before


def test_rule_file_hash_is_bound_to_the_version(normalizer) -> None:
    identity = normalizer.identity()
    assert identity["normalizer_version"] == "seqlogad-normalizer-cs-v1"
    assert len(identity["rule_file_sha256"]) == 64
    assert identity["mask_rule_count"] > 0


def test_rule_file_declares_independence_from_labels_and_partitions() -> None:
    spec = yaml.safe_load(
        (PROJECT_ROOT / "configs/parsing/normalizer-cs-v1.yaml").read_text(encoding="utf-8")
    )["normalizer"]
    assert spec["label_dependent"] is False
    assert spec["partition_dependent"] is False
    assert spec["architecture_dependent"] is False
    assert spec["raw_message_mutated"] is False


def test_a_label_dependent_rule_file_is_refused(tmp_path: Path) -> None:
    source = (PROJECT_ROOT / "configs/parsing/normalizer-cs-v1.yaml").read_text(encoding="utf-8")
    (tmp_path / "configs/parsing").mkdir(parents=True)
    (tmp_path / "configs/parsing/normalizer-cs-v1.yaml").write_text(
        source.replace("label_dependent: false", "label_dependent: true"), encoding="utf-8"
    )
    with pytest.raises(NormalizerError):
        load_normalizer(tmp_path)


def test_control_characters_are_masked_not_dropped(normalizer) -> None:
    assert normalizer.normalize("before\x0fafter") == "before<CTRL>after"
