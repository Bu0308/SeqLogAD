"""Generate, validate, compare, or inspect SPLIT-001 structural artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from seqlogad.evaluation.split import (
    SplitError,
    compare_split_artifacts,
    generate_split_artifact,
    split_status,
    validate_split_artifact,
)
from seqlogad.evaluation.test_seal import TestSealError
from seqlogad.ingestion.errors import DatasetError


def _parser(default_project_root: Path | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=default_project_root or Path.cwd(),
        help="Repository root containing configs/ and data/",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate one sealed split")
    generate.add_argument("--dataset", choices=("hdfs", "bgl"), required=True)
    generate.add_argument("--output-dir", type=Path)
    generate.add_argument("--json", action="store_true")

    validate = subparsers.add_parser("validate", help="Independently validate one split")
    validate.add_argument("--dataset", choices=("hdfs", "bgl"), required=True)
    validate.add_argument("--split-dir", type=Path)
    validate.add_argument("--json", action="store_true")

    status = subparsers.add_parser("status", help="Report structural identity and seal state")
    status.add_argument("--dataset", choices=("hdfs", "bgl"), required=True)
    status.add_argument("--split-dir", type=Path)
    status.add_argument("--json", action="store_true")

    compare = subparsers.add_parser("compare", help="Compare deterministic split identities")
    compare.add_argument("--first", type=Path, required=True)
    compare.add_argument("--second", type=Path, required=True)
    compare.add_argument("--json", action="store_true")
    return parser


def _default_split_dir(root: Path, dataset: str) -> Path:
    return root / f"data/processed/splits/{dataset}"


def _display(payload: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(" ".join(f"{key}={value}" for key, value in payload.items() if not isinstance(value, dict)))


def main(*, default_project_root: Path | None = None) -> int:
    args = _parser(default_project_root).parse_args()
    try:
        root = args.project_root.resolve()
        if args.command == "generate":
            output = args.output_dir or _default_split_dir(root, args.dataset)
            result = generate_split_artifact(
                project_root=root,
                dataset_key=args.dataset,
                output_directory=output,
            )
        elif args.command == "validate":
            directory = args.split_dir or _default_split_dir(root, args.dataset)
            result = validate_split_artifact(directory)
        elif args.command == "status":
            directory = args.split_dir or _default_split_dir(root, args.dataset)
            result = split_status(directory)
        else:
            result = compare_split_artifacts(args.first, args.second)
            if not result["deterministic"]:
                _display(result, as_json=args.json)
                return 3
        _display(result, as_json=args.json)
        return 0
    except (DatasetError, OSError, SplitError, TestSealError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
