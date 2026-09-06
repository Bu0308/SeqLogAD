"""CLI for initializing and validating process-evidence records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from seqlogad.collection.models import RECORD_FILES
from seqlogad.collection.store import CollectionError, append_record, initialize_collection, validate_collection


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seqlogad-collect")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="create empty append-only research_records files")
    sub.add_parser("validate", help="validate every collection JSONL file")
    record = sub.add_parser("record", help="validate and append one JSON record")
    record.add_argument("record_type", choices=sorted(RECORD_FILES))
    record.add_argument("--json", dest="json_path", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            result = initialize_collection(args.project_root)
        elif args.command == "validate":
            result = validate_collection(args.project_root)
        else:
            _, model = RECORD_FILES[args.record_type]
            record = model.model_validate_json(args.json_path.read_text(encoding="utf-8"))
            result = append_record(args.project_root, args.record_type, record)
    except (CollectionError, ValidationError, OSError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") in {"PASS", "READY", "APPENDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
