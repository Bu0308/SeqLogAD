"""Materialize P2.1 semantic bundle from existing frozen Phase1 artifacts."""
import argparse
from seqlogad.semantic.prepare import build_bundle

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', default='.')
    parser.add_argument('--output-root', default='data/phase2')
    args = parser.parse_args()
    build_bundle(args.project_root, args.output_root)
