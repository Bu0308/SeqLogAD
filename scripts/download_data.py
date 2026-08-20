"""Repository wrapper for the installed SeqLogAD dataset-download CLI."""

from pathlib import Path

from seqlogad.cli.download_data import main


if __name__ == "__main__":
    raise SystemExit(main(default_project_root=Path(__file__).resolve().parents[1]))
