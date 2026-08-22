"""Repository wrapper for the installed SeqLogAD META-001 CLI."""

from pathlib import Path

from seqlogad.cli.extract_raw_metadata import main


if __name__ == "__main__":
    raise SystemExit(main(default_project_root=Path(__file__).resolve().parents[1]))
