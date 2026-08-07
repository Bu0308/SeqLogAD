"""Safely download configured source archives without extracting them."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.ingestion.dataset_acquisition import download_dataset_archive
from src.ingestion.dataset_config import load_dataset_config
from src.ingestion.errors import DatasetError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_KEYS = ("hdfs", "bgl")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=(*DATASET_KEYS, "all"), required=True)
    parser.add_argument("--dry-run", action="store_true", help="Show destination without downloading")
    parser.add_argument("--force", action="store_true", help="Explicitly replace an existing archive")
    parser.add_argument("--timeout", type=float, default=60.0, help="Network timeout in seconds")
    return parser


def main() -> int:
    """Run safe archive acquisition for one or all core datasets."""

    args = _parser().parse_args()
    keys = DATASET_KEYS if args.dataset == "all" else (args.dataset,)
    try:
        for key in keys:
            config = load_dataset_config(key, config_dir=PROJECT_ROOT / "configs/datasets")
            result = download_dataset_archive(
                config,
                project_root=PROJECT_ROOT,
                dry_run=args.dry_run,
                force=args.force,
                timeout_seconds=args.timeout,
            )
            print(
                f"Dataset={result.dataset_id} status={result.status} "
                f"destination={result.destination} size_bytes={result.size_bytes}"
            )
    except (DatasetError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
