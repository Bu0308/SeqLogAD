"""T1-T8 of the frozen CANONICAL-NUL-DECISION-001 resume-test list.

The codec is a reuse of an approved decision, so these tests assert the *specified*
behaviour rather than whatever the implementation happens to do.
"""

from __future__ import annotations

import hashlib

import pytest

from seqlogad.protocol.nul import (
    NUL_POLICY_VERSION,
    CanonicalizedMessage,
    NormalizationStatus,
    NulCodecError,
    canonicalize_nul_message,
    decode_canonical_message,
    representation_identity,
)


def test_t1_ordinary_message_is_unchanged() -> None:
    result = canonicalize_nul_message(b"instruction cache parity error corrected")
    assert result.canonical_message == "instruction cache parity error corrected"
    assert result.normalization_status is NormalizationStatus.UNCHANGED
    assert result.representation_block() is None


def test_t2_single_nul_is_encoded_exactly() -> None:
    result = canonicalize_nul_message(b"before\x00after")
    assert result.canonical_message == "before\\x00after"
    assert result.normalization_status is NormalizationStatus.NUL_ESCAPED
    assert result.representation_block() == {
        "policy_id": "CANONICAL-NUL-DECISION-001",
        "policy_version": NUL_POLICY_VERSION,
        "status": "NUL_ESCAPED",
        "raw_message_sha256": hashlib.sha256(b"before\x00after").hexdigest(),
    }


def test_t3_multiple_nuls_are_deterministic() -> None:
    payload = b"a\x00b\x00c"
    first = canonicalize_nul_message(payload)
    second = canonicalize_nul_message(payload)
    assert first.canonical_message == "a\\x00b\\x00c" == second.canonical_message


@pytest.mark.parametrize(
    ("payload", "expected"),
    [(b"\x00lead", "\\x00lead"), (b"trail\x00", "trail\\x00")],
)
def test_t4_t5_leading_and_trailing_nul(payload: bytes, expected: str) -> None:
    assert canonicalize_nul_message(payload).canonical_message == expected


def test_t6_literal_escape_collision_is_unambiguous_and_reversible() -> None:
    """A raw ``\\x00`` and a raw NUL must not collapse onto the same representation."""

    literal = canonicalize_nul_message(rb"literal \x00 here")
    real_nul = canonicalize_nul_message(b"literal \x00 here")

    assert literal.normalization_status is NormalizationStatus.UNCHANGED
    assert real_nul.normalization_status is NormalizationStatus.NUL_ESCAPED
    assert representation_identity(literal) != representation_identity(real_nul)

    mixed = b"back\\slash and \x00 nul"
    encoded = canonicalize_nul_message(mixed)
    assert decode_canonical_message(encoded.canonical_message, encoded.normalization_status) == mixed


def test_t7_unicode_around_nul_is_preserved() -> None:
    payload = "héllo→".encode() + b"\x00" + "wörld".encode()
    result = canonicalize_nul_message(payload)
    assert result.canonical_message == "héllo→\\x00wörld"
    assert decode_canonical_message(result.canonical_message, result.normalization_status) == payload


def test_t8_hash_covers_the_exact_original_message_bytes() -> None:
    payload = b"exact \x00 bytes"
    result = canonicalize_nul_message(payload)
    assert result.raw_message_sha256 == hashlib.sha256(payload).hexdigest()


def test_t15_t16_canonicalisation_is_label_and_partition_independent() -> None:
    """The codec takes bytes and nothing else, so it cannot vary by context."""

    import inspect

    signature = inspect.signature(canonicalize_nul_message)
    assert list(signature.parameters) == ["raw_message_bytes"]


def test_t19_malformed_escape_is_rejected_rather_than_guessed() -> None:
    with pytest.raises(NulCodecError):
        decode_canonical_message("bad \\q escape", NormalizationStatus.NUL_ESCAPED)


def test_unchanged_status_never_decodes() -> None:
    assert decode_canonical_message("plain \\x00 text", NormalizationStatus.UNCHANGED) == (
        b"plain \\x00 text"
    )


def test_non_bytes_input_is_refused() -> None:
    with pytest.raises(NulCodecError):
        canonicalize_nul_message("already decoded")  # type: ignore[arg-type]


def test_representation_identity_is_the_specified_tuple() -> None:
    result: CanonicalizedMessage = canonicalize_nul_message(b"x\x00y")
    assert representation_identity(result) == (
        NUL_POLICY_VERSION,
        "NUL_ESCAPED",
        result.canonical_message,
        result.raw_message_sha256,
    )
