"""Build the chronological stream index for every registered architecture (P1.3/P1.5)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import yaml

from seqlogad.protocol.architectures import ARCHITECTURES
from seqlogad.protocol.chronology import (
    SegmentFractions,
    scan_architecture,
    write_stream_index,
)
from seqlogad.protocol.normalizer import load_normalizer


def load_fractions(project_root: Path) -> SegmentFractions:
    document = yaml.safe_load(
        (project_root / "configs/protocols/cross-system-split-v1.yaml").read_text(
            encoding="utf-8"
        )
    )
    spec = document["cross_system_split"]["segment_fractions"]
    return SegmentFractions(spec["early_end"], spec["guard_end"], spec["mid_end"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--architecture", action="append", default=None)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    normalizer = load_normalizer(root)
    fractions = load_fractions(root)
    targets = args.architecture or list(ARCHITECTURES)

    for architecture_id in targets:
        spec = ARCHITECTURES[architecture_id]
        started = time.time()
        print(f"[scan] {architecture_id} ...", flush=True)
        frame, diagnostics = scan_architecture(root, spec, normalizer, fractions)
        diagnostics["normalizer"] = normalizer.identity()
        diagnostics["scan_seconds"] = round(time.time() - started, 2)
        diagnostics = write_stream_index(root, architecture_id, frame, diagnostics)
        print(
            f"[done] {architecture_id} records={diagnostics['record_count']:,} "
            f"seconds={diagnostics['scan_seconds']} "
            f"segments={json.dumps(diagnostics['segment_counts'])}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
