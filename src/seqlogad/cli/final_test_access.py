"""Dedicated human-only authorization workflow for the final scientific TEST.

SPLIT-001 installs this workflow but never invokes ``unlock`` on real data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from seqlogad.evaluation.split import validate_split_artifact
from seqlogad.evaluation.test_seal import (
    FINAL_TEST_ACCESS_SCOPE,
    TEST_ACCESS_CONFIRMATION_PHRASE,
    HumanTestUnlockRequest,
    TestSealError,
    authorize_human_test_access,
    load_test_seal,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    status = subparsers.add_parser("status", help="Inspect seal metadata without TEST access")
    status.add_argument("--split-dir", type=Path, required=True)
    status.add_argument("--json", action="store_true")

    unlock = subparsers.add_parser(
        "unlock",
        help="Human-only one-use authorization; does not itself read TEST records",
    )
    unlock.add_argument("--split-dir", type=Path, required=True)
    unlock.add_argument("--dataset", choices=("hdfs", "bgl"), required=True)
    unlock.add_argument("--reason", required=True)
    unlock.add_argument("--confirmation-phrase", required=True)
    unlock.add_argument("--expected-split-payload-hash", required=True)
    unlock.add_argument("--expected-test-partition-hash", required=True)
    unlock.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "status":
            seal = load_test_seal(args.split_dir)
            payload = {
                "seal_id": seal.seal_id,
                "status": seal.status,
                "never_opened": seal.never_opened,
                "open_count": seal.open_count,
                "unlock_records": seal.unlock_records,
            }
        else:
            # Structural integrity is checked while TEST is still SEALED. This
            # verifier does not inspect anomaly labels or outcomes.
            validate_split_artifact(args.split_dir)
            request = HumanTestUnlockRequest(
                actor_source="HUMAN",
                confirmation_phrase=args.confirmation_phrase,
                reason=args.reason,
                access_scope=FINAL_TEST_ACCESS_SCOPE,
                protocol_version="1.1",
                dataset_key=args.dataset,
                expected_split_payload_hash=args.expected_split_payload_hash,
                expected_test_partition_hash=args.expected_test_partition_hash,
            )
            grant = authorize_human_test_access(args.split_dir, request)
            payload = {
                "grant_id": grant.grant_id,
                "unlock_id": grant.unlock_id,
                "status": "UNLOCKED_NOT_OPENED",
                "warning": "Final TEST is now authorized; use only the frozen human evaluation workflow.",
            }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(" ".join(f"{key}={value}" for key, value in payload.items()))
        return 0
    except (OSError, TestSealError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
