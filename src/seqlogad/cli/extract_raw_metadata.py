"""Extract or dry-run parser-independent HDFS/BGL raw metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from seqlogad.ingestion.dataset_config import (
    load_dataset_config,
    resolve_repository_path,
)
from seqlogad.ingestion.errors import DatasetError
from seqlogad.ingestion.raw_metadata import (
    MetadataArtifactSummary,
    resolve_metadata_source,
    summarize_bgl_metadata,
    summarize_hdfs_metadata,
    write_bgl_metadata_artifact,
    write_hdfs_metadata_artifact,
)


def _parser(default_project_root: Path | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("hdfs", "bgl"), required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect a bounded prefix and write no metadata artifact",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=1_000,
        help="Bounded prefix size for --dry-run (default: 1000)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Non-existing generated directory; required without --dry-run",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=default_project_root or Path.cwd(),
        help="Repository root containing configs/ and data/ (default: current directory)",
    )
    return parser


def _display(summary: MetadataArtifactSummary, *, as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                summary.model_dump(mode="json"),
                indent=2,
                sort_keys=True,
            )
        )
        return
    mode = "complete artifact" if summary.complete else "bounded dry-run"
    counts = " ".join(f"{key}={value}" for key, value in summary.counts.items())
    print(
        f"Dataset={summary.source.dataset_id} mode={mode} "
        f"lines={summary.lines_observed} {counts}"
    )
    print(
        "Labels used=false parser used=false split created=false "
        "TEST assigned=false"
    )


def main(*, default_project_root: Path | None = None) -> int:
    """Run META-001 without exposing any scientific partition operation."""

    args = _parser(default_project_root).parse_args()
    try:
        if args.max_lines < 1:
            raise ValueError("--max-lines must be positive")
        if args.dry_run and args.output_dir is not None:
            raise ValueError("--dry-run cannot be combined with --output-dir")
        if not args.dry_run and args.output_dir is None:
            raise ValueError("--output-dir is required unless --dry-run is used")

        project_root = args.project_root.resolve()
        config = load_dataset_config(
            args.dataset,
            config_dir=project_root / "configs/datasets",
        )
        source, log_path = resolve_metadata_source(
            config,
            project_root=project_root,
        )

        if args.dry_run:
            summary = (
                summarize_hdfs_metadata(
                    log_path, source, max_lines=args.max_lines
                )
                if args.dataset == "hdfs"
                else summarize_bgl_metadata(
                    log_path, source, max_lines=args.max_lines
                )
            )
        else:
            assert args.output_dir is not None
            output_dir = resolve_repository_path(
                project_root, args.output_dir.as_posix()
            )
            summary = (
                write_hdfs_metadata_artifact(log_path, source, output_dir)
                if args.dataset == "hdfs"
                else write_bgl_metadata_artifact(log_path, source, output_dir)
            )
        _display(summary, as_json=args.json)
        return 0
    except (DatasetError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
