"""LOG-UNIFY-001 canonical multi-source record contract (Excel P1.3)."""

from __future__ import annotations

import pytest

from seqlogad.protocol.architectures import ARCHITECTURES, iter_raw_records
from seqlogad.protocol.normalizer import load_normalizer
from seqlogad.protocol.nul import canonicalize_nul_message
from seqlogad.protocol.schema import (
    SOURCE_MAPPINGS,
    CanonicalLogRecord,
    SchemaViolation,
    build_record,
)


def _record(**overrides) -> CanonicalLogRecord:
    payload = dict(
        dataset_id="BGL",
        architecture_id="ARCH-BGL",
        source_file="data/raw/bgl/BGL/BGL.log",
        source_line_number=1,
        source_order=0,
        timestamp_utc="2005-06-03T15:42:50.363779+00:00",
        timestamp_status="PARSED",
        canonical_message="instruction cache parity error corrected",
        raw_message_sha256="a" * 64,
        normalized_message="instruction cache parity error corrected",
        normalizer_version="seqlogad-normalizer-cs-v1",
        parse_status="OK",
    )
    payload.update(overrides)
    return CanonicalLogRecord(**payload)


def test_every_active_architecture_has_a_mapping_contract() -> None:
    assert set(SOURCE_MAPPINGS) == set(ARCHITECTURES)


def test_bgl_mapping_declares_that_the_inline_label_is_stripped() -> None:
    assert SOURCE_MAPPINGS["ARCH-BGL"].label_field_stripped == "field_0_alert_marker"


def test_schema_version_is_pinned() -> None:
    assert _record().schema_version == "1.0"


def test_absolute_source_paths_are_refused() -> None:
    with pytest.raises((SchemaViolation, ValueError)):
        _record(source_file="/Users/someone/data/BGL.log")


def test_nul_in_the_canonical_message_is_refused() -> None:
    with pytest.raises((SchemaViolation, ValueError)):
        _record(canonical_message="bad\x00message")


def test_parsed_status_requires_a_timestamp() -> None:
    with pytest.raises((SchemaViolation, ValueError)):
        _record(timestamp_status="PARSED", timestamp_utc=None)


def test_unparsed_status_must_not_invent_a_timestamp() -> None:
    with pytest.raises((SchemaViolation, ValueError)):
        _record(timestamp_status="CONTINUATION", timestamp_utc="2020-01-01T00:00:00+00:00")


def test_continuation_records_are_representable_rather_than_dropped() -> None:
    record = _record(timestamp_status="CONTINUATION", timestamp_utc=None, parse_status="CONTINUATION")
    assert record.parse_status == "CONTINUATION"


def test_template_id_requires_a_declared_source() -> None:
    with pytest.raises((SchemaViolation, ValueError)):
        _record(template_id="EVT-1")


def test_canonical_identity_is_stable() -> None:
    assert _record().canonical_sha256() == _record().canonical_sha256()


@pytest.mark.parametrize("architecture_id", sorted(ARCHITECTURES))
def test_first_real_record_of_each_architecture_validates(architecture_id: str) -> None:
    """Every active source must actually fit the unified contract, not just in theory."""

    from datetime import datetime, timezone

    spec = ARCHITECTURES[architecture_id]
    normalizer = load_normalizer(".")
    records = list(iter_raw_records(".", spec, max_records=200))
    assert records, f"no records read for {architecture_id}"

    validated = 0
    for order, raw in enumerate(records):
        canonical = canonicalize_nul_message(raw.raw_message_bytes)
        timestamp = (
            datetime.fromtimestamp(raw.timestamp_us / 1_000_000, tz=timezone.utc).isoformat()
            if raw.timestamp_us is not None
            else None
        )
        record = build_record(
            dataset_id=spec.dataset_id,
            architecture_id=architecture_id,
            source_order=order,
            raw_record=raw,
            canonicalized=canonical,
            normalized_message=normalizer.normalize(canonical.canonical_message),
            normalizer_version=normalizer.version,
            timestamp_utc=timestamp,
        )
        assert record.architecture_id == architecture_id
        validated += 1
    assert validated == len(records)
