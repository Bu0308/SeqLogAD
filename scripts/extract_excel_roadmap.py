"""Deterministically project Bang_ke_hoach_SeqLogAD.xlsx into a machine-readable roadmap.

The workbook is the authoritative scientific plan.  This script never edits it; it
produces ``configs/plan/excel-roadmap-v1.yaml`` so that code, tests and CI can bind
to the same task IDs, dependencies, gates and citations that the researcher signed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import openpyxl
import yaml


WORKBOOK = "Bang_ke_hoach_SeqLogAD.xlsx"
OUTPUT = "configs/plan/excel-roadmap-v1.yaml"
ROADMAP_SCHEMA_VERSION = "1.0"


def _rows(worksheet) -> list[list[str]]:
    table: list[list[str]] = []
    for row in worksheet.iter_rows(values_only=True):
        cells = ["" if cell is None else str(cell).strip() for cell in row]
        if any(cells):
            table.append(cells)
    return table


def _records(table: list[list[str]], header_index: int) -> list[dict[str, str]]:
    header = table[header_index]
    keys = [
        cell.lower().replace(" ", "_").replace("/", "_").replace("-", "_")
        for cell in header
    ]
    out: list[dict[str, str]] = []
    for row in table[header_index + 1 :]:
        record = {}
        for key, value in zip(keys, row, strict=False):
            if key:
                record[key] = value
        out.append(record)
    return out


def _split_dependencies(value: str) -> list[str]:
    if not value or value in {"—", "-"}:
        return []
    return [part.strip() for part in value.replace(",", ";").split(";") if part.strip()]


def build(project_root: Path) -> dict:
    workbook_path = project_root / WORKBOOK
    workbook = openpyxl.load_workbook(workbook_path, data_only=True)
    sheets = {ws.title: _rows(ws) for ws in workbook.worksheets}

    tasks = []
    for record in _records(sheets["Task Register"], 2):
        if not record.get("task_id"):
            continue
        tasks.append(
            {
                "task_id": record["task_id"],
                "phase": record["phase"],
                "workstream": record["workstream"],
                "task_class": record["class"],
                "micro_task": record["micro_task"],
                "output": record["output"],
                "owner": record["owner"],
                "timing": record["timing"],
                "dependencies": _split_dependencies(record.get("dependency", "")),
                "definition_of_done": record["definition_of_done"],
                "workbook_status": record["status"],
            }
        )

    playbooks = {}
    for record in _records(sheets["Task Playbooks"], 2):
        task_id = record.get("task_id")
        if not task_id:
            continue
        playbooks[task_id] = {
            "method": record.get("cách_làm_có_kiểm_soát", ""),
            "required_evidence": record.get("evidence_bắt_buộc", ""),
            "verifiable_dod": record.get("definition_of_done_có_thể_kiểm_chứng", ""),
            "citations": _split_dependencies(record.get("trích_dẫn", "")),
        }

    phases = [
        {
            "phase": record["phase"],
            "timing": record["timing"],
            "objective": record["objective"],
            "micro_task_count": int(record["micro_task_count"]),
            "key_outputs": record["key_outputs"],
            "exit_gate": record["exit_gate"],
            "owner": record["owner"],
        }
        for record in _records(sheets["Roadmap"], 2)
        if record.get("phase")
    ]

    gates = [
        {
            "gate": record["gate"],
            "decision": record["decision"],
            "required_evidence": record["required_evidence"],
            "forbidden_before_pass": record["forbidden_action_before_pass"],
            "owner": record["owner"],
            "depends_on": _split_dependencies(record.get("depends_on", "")),
            "workbook_status": record["status"],
            "evidence_link": record.get("evidence_link___note", ""),
        }
        for record in _records(sheets["Gates"], 2)
        if record.get("gate")
    ]

    research_questions = [
        {
            "rq": record["rq"],
            "question": record["question"],
            "primary_metric": record["primary_metric"],
            "unit_of_evaluation": record["unit_of_evaluation"],
            "task_ids": _split_dependencies(record.get("task_ids", "")),
            "required_evidence": record["required_evidence"],
            "claim_allowed": record["claim_allowed"],
            "claim_forbidden": record["claim_forbidden"],
        }
        for record in _records(sheets["Traceability"], 2)
        if record.get("rq")
    ]

    sources = [
        {
            "key": record["key"],
            "reference": record["paper___year"],
            "type": record["type"],
            "contribution": record["contribution_used_in_plan"],
            "use_boundary": record["use_boundary"],
            "url": record["url___doi"],
            "workbook_status": record["status"],
        }
        for record in _records(sheets["Research Sources"], 2)
        if record.get("key")
    ]

    for task in tasks:
        task["playbook"] = playbooks.get(task["task_id"], {})

    return {
        "roadmap": {
            "schema_version": ROADMAP_SCHEMA_VERSION,
            "authority": "HUMAN_DECLARED_PRIMARY_SCIENTIFIC_ROADMAP",
            "source_workbook": WORKBOOK,
            "source_workbook_sha256": hashlib.sha256(
                workbook_path.read_bytes()
            ).hexdigest(),
            "worksheets": list(sheets),
            "generated_by": "scripts/extract_excel_roadmap.py",
            "note": (
                "Generated projection of the workbook. The workbook wins on any "
                "discrepancy; regenerate rather than hand-editing this file."
            ),
            "phases": phases,
            "gates": gates,
            "research_questions": research_questions,
            "research_sources": sources,
            "tasks": tasks,
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--check", action="store_true", help="Fail if output is stale.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    payload = build(root)
    rendered = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100)
    target = root / OUTPUT

    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != rendered:
            print("STALE: regenerate with scripts/extract_excel_roadmap.py")
            return 1
        print("CURRENT")
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    print(
        json.dumps(
            {
                "output": OUTPUT,
                "tasks": len(payload["roadmap"]["tasks"]),
                "gates": len(payload["roadmap"]["gates"]),
                "sources": len(payload["roadmap"]["research_sources"]),
                "workbook_sha256": payload["roadmap"]["source_workbook_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
