"""Thin command line used by the Colab orchestration notebook."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['environment', 'auth', 'validate', 'train', 'evaluate'])
    parser.add_argument('--repo-root', default='.')
    parser.add_argument('--data-root', default='/content/phase2')
    parser.add_argument('--output-root', default='/content/seqlogad_outputs')
    parser.add_argument('--fold-id', default='FOLD-TARGET-ARCH-BGL')
    parser.add_argument('--run-id', default='EXP-20260910-001')
    parser.add_argument('--config-json')
    parser.add_argument('--resume-from')
    parser.add_argument('--expected-bundle-sha256')
    parser.add_argument('--run-mode', choices=['pilot', 'final'], default='pilot')
    parser.add_argument('--run-directory')
    parser.add_argument('--checkpoint-name', default='step-300')
    args = parser.parse_args()
    from .config import load_config
    cfg, base = load_config(args.repo_root, run_mode=args.run_mode)
    if args.action == 'environment':
        from .runtime import environment
        result = environment()
    elif args.action == 'auth':
        from .model import verify_access
        result = verify_access(base)
    elif args.action == 'validate':
        from .contracts import validate_bundle
        result = validate_bundle(args.data_root, args.fold_id, args.expected_bundle_sha256)
    elif args.action == 'evaluate':
        if not args.run_directory:
            raise ValueError('--run-directory is required for evaluation')
        from .train import run_engineering_evaluation
        result = run_engineering_evaluation(args.repo_root, args.data_root, args.fold_id,
            args.run_directory, args.checkpoint_name, args.expected_bundle_sha256)
    else:
        from .train import run_training
        overrides = json.loads(Path(args.config_json).read_text()) if args.config_json else None
        directory = Path(args.output_root) / args.fold_id / 'SEMANTIC_LLAMA' / args.run_id
        if directory.exists():
            raise ValueError('run directory exists; use a new run_id')
        try:
            result = run_training(args.repo_root, args.data_root, args.output_root, args.fold_id,
                args.run_id, overrides, args.resume_from, args.expected_bundle_sha256, args.run_mode)
        except Exception as exc:
            from .contracts import dump
            directory = Path(args.output_root) / args.fold_id / 'SEMANTIC_LLAMA' / args.run_id
            if directory.exists():
                dump(directory / 'failure.json', {'type': type(exc).__name__, 'message': str(exc),
                                                  'training_completed': False})
            raise
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
