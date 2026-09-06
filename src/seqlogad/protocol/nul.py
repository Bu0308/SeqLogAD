"""``seqlogad-nul-escape-v1`` — the frozen CANONICAL-NUL-DECISION-001 Option A codec.

This is a *reuse* of an existing, fully specified repository decision, not a new
methodological choice.  The codec, its status vocabulary, its collision grammar and
its hash contract are transcribed from
``configs/protocols/canonical-nul-decision-v1.yaml`` without alteration.

Scope note: the frozen decision covers ``0x00`` only.  Other C0 control bytes are
preserved verbatim here and are handled at the *normalisation* layer
(``NORM-CS-001`` rule ``control_char``), so this codec stays byte-identical to the
approved specification.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum


NUL_POLICY_ID = "CANONICAL-NUL-DECISION-001"
NUL_POLICY_VERSION = "seqlogad-nul-escape-v1"

_NUL = b"\x00"
_BACKSLASH = b"\x5c"
_NUL_ESCAPE = b"\x5c\x78\x30\x30"  # literal ``\x00``


class NormalizationStatus(StrEnum):
    """Typed representation status carried beside the canonical message."""

    UNCHANGED = "UNCHANGED"
    NUL_ESCAPED = "NUL_ESCAPED"


class NulCodecError(ValueError):
    """Raised when bytes cannot be canonicalised or a decode is malformed."""


@dataclass(frozen=True, slots=True)
class CanonicalizedMessage:
    """Deterministic parser-safe text plus the provenance needed to prove it."""

    canonical_message: str
    normalization_status: NormalizationStatus
    raw_message_sha256: str
    policy_version: str = NUL_POLICY_VERSION

    @property
    def escaped(self) -> bool:
        return self.normalization_status is NormalizationStatus.NUL_ESCAPED

    def representation_block(self) -> dict[str, str] | None:
        """Envelope block for a transformed record; ``None`` means ``UNCHANGED``.

        Omission semantics are bound by the corpus/fold manifest, exactly as the
        approved amendment specifies.
        """

        if not self.escaped:
            return None
        return {
            "policy_id": NUL_POLICY_ID,
            "policy_version": self.policy_version,
            "status": str(self.normalization_status),
            "raw_message_sha256": self.raw_message_sha256,
        }


def canonicalize_nul_message(raw_message_bytes: bytes) -> CanonicalizedMessage:
    """Return NUL-free canonical text for the exact extracted ``Content`` bytes.

    The input must already have source metadata and any inline label separated off,
    and must exclude the source line terminator.  The transform receives no label,
    partition, parent, TEST or model-result input.
    """

    if not isinstance(raw_message_bytes, (bytes, bytearray)):
        raise NulCodecError("canonicalisation requires exact raw message bytes")
    payload = bytes(raw_message_bytes)
    raw_message_sha256 = hashlib.sha256(payload).hexdigest()

    if _NUL not in payload:
        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise NulCodecError("raw message bytes are not valid UTF-8") from exc
        return CanonicalizedMessage(
            canonical_message=text,
            normalization_status=NormalizationStatus.UNCHANGED,
            raw_message_sha256=raw_message_sha256,
        )

    transformed = payload.replace(_BACKSLASH, _BACKSLASH * 2).replace(_NUL, _NUL_ESCAPE)
    try:
        text = transformed.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise NulCodecError("escaped message bytes are not valid UTF-8") from exc
    return CanonicalizedMessage(
        canonical_message=text,
        normalization_status=NormalizationStatus.NUL_ESCAPED,
        raw_message_sha256=raw_message_sha256,
    )


def decode_canonical_message(
    canonical_message: str, status: NormalizationStatus | str
) -> bytes:
    """Invert the codec.  A decoder is selected only when status is ``NUL_ESCAPED``."""

    status = NormalizationStatus(str(status))
    if status is NormalizationStatus.UNCHANGED:
        return canonical_message.encode("utf-8")

    source = canonical_message.encode("utf-8")
    out = bytearray()
    index = 0
    length = len(source)
    while index < length:
        byte = source[index]
        if byte != _BACKSLASH[0]:
            out.append(byte)
            index += 1
            continue
        if source[index : index + 2] == _BACKSLASH * 2:
            out += _BACKSLASH
            index += 2
            continue
        if source[index : index + 4] == _NUL_ESCAPE:
            out += _NUL
            index += 4
            continue
        raise NulCodecError("malformed escape in a NUL_ESCAPED canonical message")
    return bytes(out)


def representation_identity(message: CanonicalizedMessage) -> tuple[str, str, str, str]:
    """The label-independent representation identity tuple from the amendment."""

    return (
        message.policy_version,
        str(message.normalization_status),
        message.canonical_message,
        message.raw_message_sha256,
    )


__all__ = [
    "NUL_POLICY_ID",
    "NUL_POLICY_VERSION",
    "CanonicalizedMessage",
    "NormalizationStatus",
    "NulCodecError",
    "canonicalize_nul_message",
    "decode_canonical_message",
    "representation_identity",
]
