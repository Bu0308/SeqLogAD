"""Build a deterministic raw-dataset manifest from configured local files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from seqlogad.ingestion.dataset_config import load_dataset_config, resolve_repository_path
from seqlogad.ingestion.dataset_manifest import build_dataset_manifest, write_dataset_manifest
from seqlogad.ingestion.errors import DatasetError, MissingRequiredFileError


def _parser(default_project_root: Path | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("hdfs", "bgl"), required=True)
    parser.add_argument("--output", type=Path, help="Optional manifest output path")
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--force", action="store_true", help="Explicitly replace an existing manifest")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=default_project_root or Path.cwd(),
        help="Repository root containing configs/ and data/ (default: current directory)",
    )
    return parser


def main(*, default_project_root: Path | None = None) -> int:
    """Generate a manifest only after validating dataset completeness policy."""

    args = _parser(default_project_root).parse_args()
    try:
        project_root = args.project_root.resolve()
        config = load_dataset_config(
            args.dataset,
            config_dir=project_root / "configs/datasets",
        )
        manifest = build_dataset_manifest(config, project_root=project_root)
        if not manifest.integrity.all_required_files_present and not args.allow_incomplete:
            raise MissingRequiredFileError(
                "Required raw files are missing; use --allow-incomplete only for diagnostic manifests"
            )
        output = (
            args.output
            if args.output is not None
            else resolve_repository_path(project_root, config.manifest_path)
        )
        written = write_dataset_manifest(manifest, output, overwrite=args.force)
        print(
            f"Dataset={manifest.dataset_id} files={manifest.statistics.file_count} "
            f"bytes={manifest.statistics.total_bytes} "
            f"fingerprint={manifest.dataset_fingerprint} manifest={written}"
        )
    except (DatasetError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
