"""Target-label isolation is enforced structurally, not by convention (Excel P1.7)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from seqlogad.protocol.audit import ADAPTATION_PATH_MODULES, LABEL_MODULE
from seqlogad.protocol.labels import (
    FORBIDDEN_SCOPES,
    LabelAccessDeniedError,
    LabelAccessScope,
    label_inventory,
    open_labels,
)
from seqlogad.protocol.schema import CanonicalLogRecord, SchemaViolation


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


@pytest.mark.parametrize("relative", ADAPTATION_PATH_MODULES)
def test_no_adaptation_module_imports_the_label_boundary(relative: str) -> None:
    path = PROJECT_ROOT / relative
    assert path.is_file(), f"adaptation-path module is missing: {relative}"
    assert not any(module.startswith(LABEL_MODULE) for module in _imports(path))


def test_canonical_record_has_no_label_field() -> None:
    for name in CanonicalLogRecord.model_fields:
        assert not any(token in name.lower() for token in ("label", "anomaly", "groundtruth"))


def test_a_label_shaped_field_cannot_be_smuggled_in() -> None:
    with pytest.raises((SchemaViolation, ValueError)):
        CanonicalLogRecord(
            dataset_id="X",
            architecture_id="ARCH-X",
            source_file="data/raw/x/x.log",
            source_line_number=1,
            source_order=0,
            timestamp_status="PARSED",
            timestamp_utc="2020-01-01T00:00:00+00:00",
            canonical_message="m",
            raw_message_sha256="0" * 64,
            normalized_message="m",
            normalizer_version="v",
            parse_status="OK",
            anomaly_label=True,  # type: ignore[call-arg]
        )


@pytest.mark.parametrize("scope", FORBIDDEN_SCOPES)
def test_every_forbidden_scope_is_refused(scope: str, tmp_path: Path) -> None:
    with pytest.raises(LabelAccessDeniedError):
        label_inventory(tmp_path, "ARCH-BGL", scope=scope, reason="attempt")


def test_unknown_scope_is_refused(tmp_path: Path) -> None:
    with pytest.raises(LabelAccessDeniedError):
        label_inventory(tmp_path, "ARCH-BGL", scope="SOMETHING_ELSE", reason="attempt")


def test_access_without_a_reason_is_refused(tmp_path: Path) -> None:
    with pytest.raises(LabelAccessDeniedError):
        label_inventory(
            tmp_path, "ARCH-BGL", scope=LabelAccessScope.PROTOCOL_LABEL_INVENTORY, reason="  "
        )


def test_per_unit_labels_require_the_final_evaluation_scope(tmp_path: Path) -> None:
    with pytest.raises(LabelAccessDeniedError):
        list(
            open_labels(
                tmp_path,
                "ARCH-BGL",
                scope=LabelAccessScope.PROTOCOL_LABEL_INVENTORY,
                reason="inventory only",
            )
        )


def test_inventory_access_is_recorded(tmp_path: Path) -> None:
    from seqlogad.protocol.labels import LABEL_ACCESS_LOG

    with pytest.raises(LabelAccessDeniedError):
        label_inventory(tmp_path, "ARCH-UNKNOWN", scope=LabelAccessScope.PROTOCOL_LABEL_INVENTORY, reason="probe")
    log = tmp_path / LABEL_ACCESS_LOG
    assert log.is_file()
    assert "ARCH-UNKNOWN" in log.read_text(encoding="utf-8")


def test_buffer_module_cannot_reach_a_label_lookup() -> None:
    """The forbidden operation is selecting burn-in records by their label."""

    source = (PROJECT_ROOT / "src/seqlogad/protocol/buffer.py").read_text(encoding="utf-8")
    assert "labels" not in _imports(PROJECT_ROOT / "src/seqlogad/protocol/buffer.py")
    for forbidden in ("anomaly_label", "abnormal_label", "openstack_abnormal", "is_anomalous"):
        assert forbidden not in source
