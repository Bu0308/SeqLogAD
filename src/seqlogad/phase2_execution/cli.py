"""Platform-neutral CLI entry point used by thin GPU notebooks."""
import argparse
import json

from .runner import run_all_targets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True, choices=["P2.1", "P2.2", "P2.3", "P2.4"])
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--output-root", required=True)
    persistence = parser.add_mutually_exclusive_group(required=True)
    persistence.add_argument("--persistent-root", dest="persistent_root")
    persistence.add_argument("--drive-root", dest="persistent_root")
    parser.add_argument("--expected-bundle-sha256", required=True)
    args = parser.parse_args()
    result = run_all_targets(
        task_id=args.task_id,
        repo_root=args.repo_root,
        data_root=args.data_root,
        output_root=args.output_root,
        drive_root=args.persistent_root,
        expected_bundle_sha256=args.expected_bundle_sha256,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
