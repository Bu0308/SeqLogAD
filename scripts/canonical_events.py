"""Repository wrapper for the installed CANONICAL-EVENT-001 CLI."""

from pathlib import Path

from seqlogad.cli.canonical_events import main


if __name__ == "__main__":
    raise SystemExit(main(default_project_root=Path(__file__).resolve().parents[1]))
