"""Generate, validate, or compare the read-only PURGE-AUDIT-001 artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from seqlogad.evaluation.purge_audit import (
    PurgeAuditError,
    build_real_audit_payload,
    compare_audit_artifacts,
    validate_audit_artifact,
    wrap_audit_artifact,
    write_audit_artifact,
)


def _parser(default_project_root: Path | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=default_project_root or Path.cwd(),
        help="Repository root containing frozen HDFS artifacts",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="Run the aggregate PURGED-vs-RETAINED audit")
    generate.add_argument("--output", type=Path, required=True)
    generate.add_argument(
        "--classification",
        choices=(
            "PURGE_REPRESENTATIVENESS_CONCERN",
            "PURGE_REPRESENTATIVENESS_INCONCLUSIVE",
        ),
        required=True,
        help="Evidence interpretation recorded after inspecting the aggregate audit only",
    )
    generate.add_argument("--json", action="store_true")

    validate = commands.add_parser("validate", help="Validate one persisted audit artifact")
    validate.add_argument("--artifact", type=Path, required=True)
    validate.add_argument("--json", action="store_true")

    compare = commands.add_parser("compare", help="Compare canonical scientific payload identities")
    compare.add_argument("--first", type=Path, required=True)
    compare.add_argument("--second", type=Path, required=True)
    compare.add_argument("--json", action="store_true")
    return parser


def _display(payload: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(" ".join(f"{key}={value}" for key, value in payload.items()))


def main(*, default_project_root: Path | None = None) -> int:
    args = _parser(default_project_root).parse_args()
    try:
        root = args.project_root.resolve()
        if args.command == "generate":
            def progress(message: str) -> None:
                print(f"PURGE-AUDIT-001 phase={message}", file=sys.stderr, flush=True)

            payload = build_real_audit_payload(
                root,
                final_classification=args.classification,
                progress=progress,
            )
            artifact = wrap_audit_artifact(payload, project_root=root)
            write_audit_artifact(args.output, artifact)
            result = validate_audit_artifact(args.output)
        elif args.command == "validate":
            result = validate_audit_artifact(args.artifact)
        else:
            result = compare_audit_artifacts(args.first, args.second)
            if not result["deterministic"]:
                _display(result, as_json=args.json)
                return 3
        _display(result, as_json=args.json)
        return 0
    except (OSError, ValueError, PurgeAuditError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
