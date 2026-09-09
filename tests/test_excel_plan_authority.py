"""The workbook is the single active scientific plan.

These tests are the guard against the failure mode this repository has already hit
once: two plans coexisting, with stale pointers still routing work.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = PROJECT_ROOT / "Bang_ke_hoach_SeqLogAD.xlsx"
ROADMAP = PROJECT_ROOT / "configs/plan/excel-roadmap-v1.yaml"

RETIRED_POINTERS = (
    "SEQ-001",
    "THEORY-COMPLETE-001",
    "KT-1",
    "KT-2",
    "KT-3",
    "EFFECT-001",
)


def _yaml(relative: str) -> dict:
    return yaml.safe_load((PROJECT_ROOT / relative).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def roadmap() -> dict:
    return _yaml("configs/plan/excel-roadmap-v1.yaml")["roadmap"]


def test_workbook_is_present_and_its_hash_is_registered() -> None:
    digest = hashlib.sha256(WORKBOOK.read_bytes()).hexdigest()
    state = _yaml("configs/active-state.yaml")["active_state"]
    assert state["authoritative_plan"]["sha256"] == digest
    assert _yaml("configs/plan/excel-roadmap-v1.yaml")["roadmap"]["source_workbook_sha256"] == digest


def test_roadmap_projection_is_not_stale() -> None:
    """Regenerating the projection must be a no-op, or the plan has drifted."""

    result = subprocess.run(
        [sys.executable, "scripts/extract_excel_roadmap.py", "--check"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_roadmap_carries_the_workbook_structure(roadmap: dict) -> None:
    assert len(roadmap["tasks"]) == 32
    assert len(roadmap["gates"]) == 5
    assert len(roadmap["research_sources"]) == 11
    assert [phase["exit_gate"] for phase in roadmap["phases"]] == [
        "G0: Protocol Ready",
        "G2: Expert Diversity Ready",
        "G3: Fusion Justified",
        "G4: Final Evaluation",
    ]


def test_phase_1_task_ids_and_dependencies_match_the_workbook(roadmap: dict) -> None:
    phase_1 = [task for task in roadmap["tasks"] if task["task_id"].startswith("P1.")]
    assert [task["task_id"] for task in phase_1] == [f"P1.{index}" for index in range(1, 9)]
    dependencies = {task["task_id"]: task["dependencies"] for task in phase_1}
    assert dependencies["P1.2"] == ["P1.1"]
    assert dependencies["P1.7"] == ["P1.4", "P1.5", "P1.6"]
    assert dependencies["P1.8"] == ["P1.7"]


def test_every_phase_1_task_is_a_must(roadmap: dict) -> None:
    for task in roadmap["tasks"]:
        if task["task_id"].startswith("P1."):
            assert task["task_class"] == "Must"


def test_g0_required_evidence_is_recorded_verbatim(roadmap: dict) -> None:
    gate = next(gate for gate in roadmap["gates"] if gate["gate"] == "G0")
    assert gate["decision"] == "Protocol Ready"
    assert "3 source architectures" in gate["required_evidence"]
    assert gate["forbidden_before_pass"] == "Representation or target adaptation training"


def test_active_state_routes_the_workbook_and_nothing_else() -> None:
    state = _yaml("configs/active-state.yaml")["active_state"]
    assert state["authoritative_plan"]["path"] == "Bang_ke_hoach_SeqLogAD.xlsx"
    assert state["next_authorized_task"] == "P2.PRE"
    for pointer in RETIRED_POINTERS:
        assert pointer in state["historical_foundation"]["retired_pointers"]


def test_no_retired_pointer_is_reachable_as_active_routing() -> None:
    """A retired task ID may appear in history, never as a next/active pointer."""

    state = _yaml("configs/active-state.yaml")["active_state"]
    routing_keys = (
        "next_authorized_task",
        "next_scientific_task",
        "current_maintenance_task",
        "next_task",
    )

    def walk(node: object, path: str = "") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in routing_keys and isinstance(value, str):
                    assert value not in RETIRED_POINTERS, f"{path}.{key} still routes {value}"
                if path.startswith("historical") or key.startswith("historical"):
                    continue
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for item in node:
                walk(item, path)

    walk(state)


def test_next_authorized_task_is_the_first_workbook_phase_2_task(roadmap: dict) -> None:
    phase_2 = [task for task in roadmap["tasks"] if task["task_id"].startswith("P2.")]
    first = phase_2[0]  # Workbook order, not lexical order (P2.PRE comes first).
    state = _yaml("configs/active-state.yaml")["active_state"]
    assert state["next_authorized_task"] == first["task_id"] == "P2.PRE"
    assert first["output"] == "LLM-BASE-001"
    assert first["dependencies"] == ["P1.8"]


def test_default_config_does_not_reintroduce_the_retired_ladder() -> None:
    default = _yaml("configs/default.yaml")
    assert default["plan"]["authoritative"] == "Bang_ke_hoach_SeqLogAD.xlsx"
    assert "markov_ngram" not in default["methods"]["must"]
    assert default["methods"]["conditional"] == ["adaptive_gate"]


def test_research_sources_are_recorded_with_use_boundaries(roadmap: dict) -> None:
    for source in roadmap["research_sources"]:
        assert source["url"].startswith("http")
        assert source["use_boundary"], f"{source['key']} has no declared use boundary"
        assert source["workbook_status"] == "Verified"


# --------------------------------------------------------------------------
# Plan amendments after G0 was signed.
#
# The workbook may be re-hashed after signing, but only its bookkeeping may
# move. These tests re-derive that from the archived signed copy rather than
# trusting the ledger's own claim.
# --------------------------------------------------------------------------

SIGNED_WORKBOOK = PROJECT_ROOT / "docs/history/Bang_ke_hoach_SeqLogAD--G0-signed-2026-09-06.xlsx"

# Columns that carry status or evidence bookkeeping, not scientific content.
PRE_MIGRATION_WORKBOOK = PROJECT_ROOT / "docs/history/Bang_ke_hoach_SeqLogAD--pre-P2-ARCH-V1-2026-09-09.xlsx"

BOOKKEEPING_COLUMNS = {
    ("Executive", "H"),
    ("Roadmap", "I"),
    ("Task Register", "K"),
    ("Gates", "G"),
    ("Gates", "H"),
}


def _workbook_cells(path):
    import openpyxl

    workbook = openpyxl.load_workbook(path, data_only=True)
    cells = {}
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is not None:
                    cells[(sheet.title, cell.column_letter, cell.row)] = cell.value
    return cells


@pytest.fixture(scope="module")
def ledger() -> dict:
    return _yaml("configs/protocols/g0-signatures.yaml")["g0_signatures"]


def test_signed_workbook_is_archived(ledger: dict) -> None:
    """The exact bytes the researcher signed must remain recoverable."""

    amendment = ledger["plan_amendments"][0]
    archived = PROJECT_ROOT / amendment["signed_workbook_archived_at"]
    assert archived.is_file(), "the signed workbook snapshot is missing"
    digest = hashlib.sha256(archived.read_bytes()).hexdigest()
    assert digest == amendment["from_sha256"]


def test_amendment_changed_only_bookkeeping_cells(ledger: dict) -> None:
    """Re-derive the status-only claim; fail if any scientific cell moved."""

    amendment = ledger["plan_amendments"][0]
    before = _workbook_cells(PROJECT_ROOT / amendment["signed_workbook_archived_at"])
    after = _workbook_cells(PRE_MIGRATION_WORKBOOK)

    moved = [
        key for key in set(before) | set(after)
        if before.get(key) != after.get(key)
    ]
    offenders = [
        f"{sheet}!{col}{row}"
        for sheet, col, row in moved
        if (sheet, col) not in BOOKKEEPING_COLUMNS
    ]
    assert offenders == [], f"scientific content changed after signing: {offenders}"
    assert amendment["scientific_content_changed"] is False
    assert amendment["scope_of_change"] == "STATUS_AND_EVIDENCE_LINK_CELLS_ONLY"


def test_amendment_declares_every_cell_it_moved(ledger: dict) -> None:
    """The ledger may not under-report what changed."""

    amendment = ledger["plan_amendments"][0]
    before = _workbook_cells(PROJECT_ROOT / amendment["signed_workbook_archived_at"])
    after = _workbook_cells(PRE_MIGRATION_WORKBOOK)
    actually_moved = {
        f"{sheet}!{col}{row}"
        for sheet, col, row in set(before) | set(after)
        if before.get(key := (sheet, col, row)) != after.get(key)
    }
    declared = {
        entry["cell"]
        for group in amendment["changed_cells"].values()
        for entry in group
    }
    assert actually_moved == declared, (
        f"undeclared: {sorted(actually_moved - declared)} | "
        f"declared but unchanged: {sorted(declared - actually_moved)}"
    )


def test_current_workbook_hash_matches_the_amendment(ledger: dict) -> None:
    amendment = ledger["plan_amendments"][0]
    assert hashlib.sha256(PRE_MIGRATION_WORKBOOK.read_bytes()).hexdigest() == amendment["to_sha256"]


def test_passed_gates_name_their_evidence(roadmap: dict) -> None:
    """The Gates sheet's own rule: a gate marked passed must name its evidence."""

    for gate in roadmap["gates"]:
        if gate["workbook_status"].strip().lower() == "passed":
            evidence = gate["evidence_link"].strip()
            assert evidence and evidence != "—", f"{gate['gate']} is passed with no evidence"
            assert (PROJECT_ROOT / evidence).exists(), f"{gate['gate']} evidence missing: {evidence}"


def test_workbook_status_agrees_with_the_receipt(roadmap: dict) -> None:
    """The workbook may not claim a gate the G0 receipt does not support."""

    receipt = json.loads(
        (PROJECT_ROOT / "data/processed/protocol/G0-receipt.json").read_text(encoding="utf-8")
    )
    g0 = next(g for g in roadmap["gates"] if g["gate"] == "G0")
    workbook_passed = g0["workbook_status"].strip().lower() == "passed"
    receipt_passed = receipt["gate_state"] == "PROTOCOL_READY"
    assert workbook_passed == receipt_passed

    phase_1 = [t for t in roadmap["tasks"] if t["task_id"].startswith("P1.")]
    assert all(t["workbook_status"].strip().lower() == "done" for t in phase_1)
    assert all(t["workbook_status"].strip().lower() != "done"
               for t in roadmap["tasks"] if t["task_id"].startswith("P2."))
