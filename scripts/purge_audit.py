"""Repository wrapper for the installed PURGE-AUDIT-001 CLI."""

from pathlib import Path

from seqlogad.cli.purge_audit import main


if __name__ == "__main__":
    raise SystemExit(main(default_project_root=Path(__file__).resolve().parents[1]))
