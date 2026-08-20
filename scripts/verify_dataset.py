"""Repository wrapper for the installed SeqLogAD dataset-verification CLI."""

from pathlib import Path

from seqlogad.cli.verify_dataset import main


if __name__ == "__main__":
    raise SystemExit(main(default_project_root=Path(__file__).resolve().parents[1]))
