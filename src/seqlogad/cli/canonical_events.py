"""Generate, validate, or deterministically compare CANONICAL-EVENT-001."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from seqlogad.parsing.canonical_events import (
    CanonicalEventError,
    compare_canonical_regeneration,
    generate_canonical_corpus,
    validate_canonical_corpus,
    validate_canonical_prerequisites,
)
from seqlogad.parsing.drain_parser import ParserContractError


def _parser(default_project_root: Path | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=default_project_root or Path.cwd(),
        help="Repository root containing frozen raw/split/parser artifacts",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("gate", "Verify frozen prerequisites without transforming raw logs"),
        ("generate", "Generate one non-TEST canonical corpus atomically"),
        ("validate", "Independently reload and verify an existing corpus"),
        ("compare", "Regenerate into a hash sink and compare scientific identity"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--dataset", choices=("hdfs", "bgl"), required=True)
        command.add_argument("--output-dir", type=Path)
        command.add_argument("--json", action="store_true")
    return parser


def _default_output(root: Path, dataset: str) -> Path:
    return root / f"data/processed/canonical-events/{dataset}"


def _display(payload: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        for key, value in payload.items():
            if not isinstance(value, (dict, list)):
                print(f"{key}={value}")


def main(*, default_project_root: Path | None = None) -> int:
    args = _parser(default_project_root).parse_args()
    try:
        root = args.project_root.resolve()
        output = args.output_dir or _default_output(root, args.dataset)
        if args.command == "gate":
            gate = validate_canonical_prerequisites(root, args.dataset)
            result = {
                "dataset": args.dataset,
                "status": "READY",
                "dataset_fingerprint": gate["dataset_fingerprint"],
                "split_payload_hash": gate["split_payload_hash"],
                "parser_state_sha256": gate["parser_validation"][
                    "parser_state_sha256"
                ],
                "test_status": gate["test_status"]["test_status"],
                "never_opened": gate["test_status"]["never_opened"],
            }
        elif args.command == "generate":
            result = generate_canonical_corpus(
                project_root=root,
                dataset_key=args.dataset,
                output_directory=output,
            )
        elif args.command == "validate":
            result = validate_canonical_corpus(output)
            if result["dataset"] != args.dataset:
                raise CanonicalEventError("canonical corpus dataset mismatch")
        else:
            result = compare_canonical_regeneration(
                project_root=root,
                dataset_key=args.dataset,
                output_directory=output,
            )
            if result["deterministic"] is not True:
                raise CanonicalEventError("canonical regeneration is nondeterministic")
        _display(result, as_json=args.json)
        return 0
    except (CanonicalEventError, ParserContractError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
