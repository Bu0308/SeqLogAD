"""The reference registry is the authoritative source list and must stay consistent.

These tests enforce the invariants the consolidation established: the registry is
regenerable, its workbook mappings come from the workbook, every active source is
verified and used, and no citation is quietly upgraded past what it supports.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = PROJECT_ROOT / "docs/references/reference_registry.yaml"

CLASSIFICATIONS = {
    "LITERATURE_SUPPORTED",
    "LITERATURE_INFORMED_SEQLOGAD_DECISION",
    "SEQLOGAD_PROTOCOL_DECISION",
    "ENGINEERING_DECISION",
}


@pytest.fixture(scope="module")
def registry() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["reference_registry"]


@pytest.fixture(scope="module")
def active(registry: dict) -> list[dict]:
    return [s for s in registry["sources"] if s["active_status"] == "ACTIVE"]


def test_registry_is_not_stale() -> None:
    """Regenerating must be a no-op, or the registry has drifted from its generator."""

    result = subprocess.run(
        [sys.executable, "scripts/build_reference_registry.py", "--check"],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_registry_declares_itself_authoritative(registry: dict) -> None:
    assert registry["status"] == "AUTHORITATIVE"
    assert registry["plan"] == "Bang_ke_hoach_SeqLogAD.xlsx"


def test_every_active_source_is_verified(active: list[dict]) -> None:
    for source in active:
        assert source["verified_on"], source["id"]
        assert source["verification"], source["id"]
        assert source["publication_status"], source["id"]
        assert source["title"].strip()
        assert source["authors"]
        assert source["official_url"].startswith("http")


def test_no_active_source_is_orphaned(active: list[dict]) -> None:
    """ACTIVE_SOURCE_WITHOUT_USED_BY must be zero."""

    for source in active:
        used = source["used_by"]
        assert used["workbook_tasks"] or used["repository"], f"{source['id']} has no used_by"


def test_no_duplicate_dois(registry: dict) -> None:
    dois = [s["doi"] for s in registry["sources"] if s.get("doi")]
    duplicates = [doi for doi, count in Counter(dois).items() if count > 1]
    assert duplicates == []


def test_no_duplicate_ids(registry: dict) -> None:
    ids = [s["id"] for s in registry["sources"]]
    assert len(ids) == len(set(ids))


def test_workbook_source_ids_are_preserved_and_mapped(registry: dict, active: list[dict]) -> None:
    """S1-S11 are the workbook's own IDs; they may not be renumbered or unmapped."""

    roadmap = yaml.safe_load(
        (PROJECT_ROOT / "configs/plan/excel-roadmap-v1.yaml").read_text(encoding="utf-8")
    )["roadmap"]
    workbook_ids = {s["key"] for s in roadmap["research_sources"]}
    registry_ids = {s["id"] for s in registry["sources"]}
    assert workbook_ids <= registry_ids, workbook_ids - registry_ids

    by_id = {s["id"]: s for s in active}
    for key in workbook_ids:
        assert by_id[key]["used_by"]["workbook_tasks"], f"{key} maps to no workbook task"


def test_workbook_task_mapping_matches_the_workbook(registry: dict) -> None:
    """The mapping is derived, so it must equal what the workbook playbooks say."""

    roadmap = yaml.safe_load(
        (PROJECT_ROOT / "configs/plan/excel-roadmap-v1.yaml").read_text(encoding="utf-8")
    )["roadmap"]
    expected: dict[str, set[str]] = {}
    for task in roadmap["tasks"]:
        for key in task.get("playbook", {}).get("citations", []):
            expected.setdefault(key, set()).add(task["task_id"])
    for source in registry["sources"]:
        if source["id"] in expected:
            assert set(source["used_by"]["workbook_tasks"]) == expected[source["id"]], source["id"]


def test_every_claim_carries_a_valid_classification(registry: dict) -> None:
    for source in registry["sources"]:
        for claim in source.get("claims", []):
            assert claim["classification"] in CLASSIFICATIONS, source["id"]
            assert claim["claim"].strip()


def test_preprints_are_not_presented_as_peer_reviewed(active: list[dict]) -> None:
    """A preprint must say so, and must not carry a LITERATURE_SUPPORTED design claim
    without a use boundary."""

    for source in active:
        if source["publication_status"] == "PREPRINT_NOT_PEER_REVIEWED":
            assert source.get("use_boundary"), f"{source['id']} is a preprint with no use boundary"


def test_reference_support_gaps_are_recorded_not_hidden(registry: dict) -> None:
    for gap in registry["reference_support_gaps"]:
        assert gap["claim"] and gap["problem"] and gap["recommended_action"]
        assert gap["methodology_changed"] is False
        assert gap["affected_tasks"]


def test_active_references_markdown_covers_every_active_source(active: list[dict]) -> None:
    text = (PROJECT_ROOT / "docs/references/ACTIVE_REFERENCES.md").read_text(encoding="utf-8")
    for source in active:
        assert f"`{source['id']}`" in text, source["id"]


def test_deleted_reference_files_are_not_referenced_anywhere() -> None:
    deleted = (
        "ALIGN-FIX-001-citations",
        "SCHEMA-COMPAT-001-citations",
        "EXCEL-PLAN-citation-verification",
        "day02-log-anomaly-survey",
    )
    skip = (".venv", "_agent_workspace_pack", ".git/", "__pycache__")
    offenders = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".yaml", ".yml", ".py", ".json"}:
            continue
        if any(k in str(path) for k in skip):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for name in deleted:
            # The cleanup report names them by design; so does this test.
            if name in text and path.name not in {
                "REFERENCE_CLEANUP_REPORT.md",
                "test_reference_registry.py",
            }:
                offenders.append((str(path.relative_to(PROJECT_ROOT)), name))
    assert offenders == []


def test_no_broken_relative_markdown_links() -> None:
    link = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    skip = (".venv", "_agent_workspace_pack", ".git/", "__pycache__")
    broken = []
    for path in PROJECT_ROOT.rglob("*.md"):
        if any(k in str(path) for k in skip):
            continue
        for target in link.findall(path.read_text(encoding="utf-8", errors="replace")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            cleaned = target.split("#")[0].strip()
            if cleaned and not (path.parent / cleaned).exists():
                broken.append((str(path.relative_to(PROJECT_ROOT)), target))
    assert broken == []


def test_historical_packs_are_marked() -> None:
    """A retired-plan citation pack must announce itself when opened directly."""

    active_files = {
        "README.md", "ACTIVE_REFERENCES.md", "REFERENCE_CLEANUP_REPORT.md",
    }
    unmarked = []
    for path in (PROJECT_ROOT / "docs/references").glob("*.md"):
        if path.name in active_files:
            continue
        if "**HISTORICAL / SUPERSEDED.**" not in path.read_text(encoding="utf-8")[:600]:
            unmarked.append(path.name)
    assert unmarked == []
