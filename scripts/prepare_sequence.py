"""Build the portable P2.2 ordered sequence view from verified local lineage."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from seqlogad.sequence.prepare import build_bundle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--semantic-root", default="data/phase2")
    parser.add_argument("--output-root", default="data/phase2-sequence")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    result = build_bundle(
        root,
        root / args.semantic_root,
        root / args.output_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
