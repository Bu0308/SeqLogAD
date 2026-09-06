"""The workbook is the single active scientific plan.

These tests are the guard against the failure mode this repository has already hit
once: two plans coexisting, with stale pointers still routing work.
"""

from __future__ import annotations

import hashlib
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
    assert state["next_authorized_task"] == "P2.1"
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
    first = min(phase_2, key=lambda task: task["task_id"])
    state = _yaml("configs/active-state.yaml")["active_state"]
    assert state["next_authorized_task"] == first["task_id"] == "P2.1"
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
