"""P2.2 validation/preparation CLI; GPU training is orchestrated by phase2_execution."""
from __future__ import annotations

import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["validate", "auth", "environment"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--data-root")
    parser.add_argument("--fold-id", default="FOLD-TARGET-ARCH-BGL")
    parser.add_argument("--expected-bundle-sha256")
    args = parser.parse_args()
    if args.action == "validate":
        if not args.data_root:
            raise ValueError("--data-root is required")
        from .contracts import validate_bundle
        result = validate_bundle(
            args.data_root, args.fold_id, args.expected_bundle_sha256
        )
    elif args.action == "auth":
        from .config import load_config
        from .model import verify_access
        _, base = load_config(args.repo_root)
        result = verify_access(base)
    else:
        from seqlogad.semantic.runtime import environment
        result = environment()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
