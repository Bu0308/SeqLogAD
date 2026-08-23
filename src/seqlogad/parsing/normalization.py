"""Label-isolating raw-message extraction for the frozen PARSE-001 contract.

These helpers separate structured source metadata from the free-text content
fed to Drain3.  They do not assign templates, build canonical events, or read
scientific partitions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


NORMALIZATION_VERSION = "seqlogad-message-v1"
BGL_EMPTY_CONTENT_SENTINEL = "SEQLOGAD_EMPTY_CONTENT"


class MessageExtractionError(ValueError):
    """Raised when an accepted raw line violates the frozen source format."""


_HDFS_LINE = re.compile(
    r"^(?P<date>\d{6})\s+"
    r"(?P<time>\d{6})\s+"
    r"(?P<pid>\d+)\s+"
    r"(?P<level>[A-Za-z]+)\s+"
    r"(?P<component>\S+):\s"
    r"(?P<content>.*)$"
)


@dataclass(frozen=True, slots=True)
class BglSourceRecord:
    """Minimum isolated BGL fields needed by PARSE-001."""

    label_marker: str
    message: str


def _decode_line(raw_line: bytes) -> str:
    """Decode UTF-8 strictly and remove only a source line terminator."""

    payload = raw_line
    if payload.endswith(b"\n"):
        payload = payload[:-1]
    if payload.endswith(b"\r"):
        payload = payload[:-1]
    try:
        return payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise MessageExtractionError("raw log line is not valid UTF-8") from exc


def extract_hdfs_message(raw_line: bytes) -> str:
    """Return only HDFS ``Content`` under the frozen Loghub field contract."""

    text = _decode_line(raw_line)
    match = _HDFS_LINE.fullmatch(text)
    if match is None:
        raise MessageExtractionError("HDFS line does not match the frozen raw format")
    message = match.group("content")
    if not message:
        raise MessageExtractionError("HDFS content must not be empty")
    return message


def extract_bgl_record(raw_line: bytes) -> BglSourceRecord:
    """Separate the inline BGL label from the free-text ``Content`` field."""

    text = _decode_line(raw_line)
    fields = text.split(maxsplit=9)
    if len(fields) not in {9, 10}:
        raise MessageExtractionError("BGL line does not match the frozen source format")
    label_marker = fields[0]
    message = fields[9] if len(fields) == 10 else BGL_EMPTY_CONTENT_SENTINEL
    if not label_marker:
        raise MessageExtractionError("BGL label marker must be non-empty")
    return BglSourceRecord(label_marker=label_marker, message=message)


__all__ = [
    "BglSourceRecord",
    "BGL_EMPTY_CONTENT_SENTINEL",
    "MessageExtractionError",
    "NORMALIZATION_VERSION",
    "extract_bgl_record",
    "extract_hdfs_message",
]
