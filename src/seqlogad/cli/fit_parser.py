"""Gate, select, fit, or validate the frozen PARSE-001 Drain3 artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from seqlogad.parsing.drain_parser import (
    ParserContractError,
    fit_and_freeze_parser,
    validate_parser_artifact,
)
from seqlogad.parsing.normal_pool import (
    NormalPoolError,
    build_real_normal_pool,
    validate_parser_prefit_gate,
)


def _parser(default_project_root: Path | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=default_project_root or Path.cwd(),
        help="Repository root containing frozen configs, splits, and raw data",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("gate", "Verify all prerequisites without opening source labels"),
        ("pool", "Build and report the permitted normal-only BASE_TRAIN identity"),
        ("fit", "Fit and atomically freeze a real Drain3 parser state"),
        ("validate", "Independently verify an existing frozen parser artifact"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--dataset", choices=("hdfs", "bgl"), required=True)
        command.add_argument("--json", action="store_true")
        if name in {"fit", "validate"}:
            command.add_argument("--output-dir", type=Path)
    return parser


def _default_output(root: Path, dataset: str) -> Path:
    return root / f"data/processed/parsers/{dataset}"


def _display(payload: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for key, value in payload.items():
            if not isinstance(value, (dict, list)):
                print(f"{key}={value}")


def main(*, default_project_root: Path | None = None) -> int:
    args = _parser(default_project_root).parse_args()
    try:
        root = args.project_root.resolve()
        if args.command == "gate":
            result = validate_parser_prefit_gate(root, args.dataset)
        elif args.command == "pool":
            result = build_real_normal_pool(root, args.dataset).summary()
        elif args.command == "validate":
            output = args.output_dir or _default_output(root, args.dataset)
            result = validate_parser_artifact(output)
            if result["dataset"] != args.dataset:
                raise ParserContractError("parser artifact dataset does not match CLI input")
        else:
            output = args.output_dir or _default_output(root, args.dataset)
            pool = build_real_normal_pool(root, args.dataset)

            def progress(count: int) -> None:
                print(
                    f"PARSE-001 dataset={args.dataset} fitted_records={count}",
                    file=sys.stderr,
                    flush=True,
                )

            result = fit_and_freeze_parser(
                pool=pool,
                contract_path=root / "configs/parsing/drain3-v1.yaml",
                output_directory=output,
                progress=progress,
            )
        _display(result, as_json=args.json)
        return 0
    except (OSError, ValueError, NormalPoolError, ParserContractError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
