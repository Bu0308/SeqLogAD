"""Repository wrapper for the installed SeqLogAD manifest-build CLI."""

from pathlib import Path

from seqlogad.cli.build_dataset_manifest import main


if __name__ == "__main__":
    raise SystemExit(main(default_project_root=Path(__file__).resolve().parents[1]))
