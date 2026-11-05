"""Build the label-free TV-001 target-fold views (docs/fusion/TARGET_VIEW_DESIGN.md).

    PYTHONPATH=src python scripts/build_target_view.py --project . \
        --out data/processed/target-views/TV-001

No label file is opened. Output refuses to overwrite an existing fold directory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from seqlogad.target.view import build_view, load_config

CONFIG = "configs/fusion/target-view-v1.yaml"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fold", action="append", help="default: every fold in the config")
    args = parser.parse_args()
    root = args.project.resolve()
    folds = args.fold or load_config(root, CONFIG)[0]["folds"]
    for fold_id in folds:
        manifest = build_view(root, CONFIG, fold_id, args.out)
        print(json.dumps({"fold": fold_id, "evaluation": manifest["evaluation"],
                          "calibration": manifest["calibration"]}, indent=1), flush=True)
    print("TARGET_VIEW_BUILT=" + str(args.out))


if __name__ == "__main__":
    main()
