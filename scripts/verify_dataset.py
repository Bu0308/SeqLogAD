"""Report dataset presence and, when available, verify its manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.ingestion.dataset_config import load_dataset_config, resolve_repository_path
from src.ingestion.dataset_manifest import verify_dataset_manifest
from src.ingestion.dataset_validation import validate_dataset_presence
from src.ingestion.errors import DatasetError


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("hdfs", "bgl"), required=True)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main() -> int:
    """Validate required files, then verify bytes if a manifest exists."""

    args = _parser().parse_args()
    try:
        config = load_dataset_config(
            args.dataset,
            config_dir=PROJECT_ROOT / "configs/datasets",
        )
        presence = validate_dataset_presence(config, project_root=PROJECT_ROOT)
        manifest_path = resolve_repository_path(PROJECT_ROOT, config.manifest_path)
        payload: dict[str, object] = {
            "dataset_id": config.dataset_id,
            "status": presence.status.value,
            "required_files": {
                "present": presence.required_present,
                "total": presence.required_count,
                "missing": presence.missing_required_files,
            },
            "manifest": "PRESENT" if manifest_path.is_file() else "MISSING",
            "checksums": "NOT_GENERATED",
            "fingerprint": None,
        }
        exit_code = 0 if presence.status.value == "PRESENT" else 1
        if manifest_path.is_file():
            verification = verify_dataset_manifest(
                config,
                project_root=PROJECT_ROOT,
                manifest_path=manifest_path,
            )
            payload["checksums"] = "VALID" if verification.valid else "INVALID"
            payload["fingerprint"] = verification.expected_fingerprint
            exit_code = 0 if verification.valid else 1

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            required = payload["required_files"]
            assert isinstance(required, dict)
            print(f"Dataset: {payload['dataset_id']}")
            print(f"Status: {payload['status']}")
            print(f"Required files: {required['present']}/{required['total']}")
            print(f"Missing files: {', '.join(required['missing']) or 'none'}")
            print(f"Manifest: {payload['manifest']}")
            print(f"Checksums: {payload['checksums']}")
            print(f"Fingerprint: {payload['fingerprint'] or 'not generated'}")
        return exit_code
    except (DatasetError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
