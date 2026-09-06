"""Build every Phase 1 protocol artifact from the stream indices (Excel P1.2-P1.8).

Run ``scripts/build_streams.py`` first; this driver never rescans raw logs, so the
artifacts it emits are a pure function of the stream indices plus the versioned
contract files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from seqlogad.protocol.audit import audit_fold, write_audit
from seqlogad.protocol.buffer import build_buffer, write_buffer
from seqlogad.protocol.folds import build_all_folds, write_fold
from seqlogad.protocol.freeze import build_g0_receipt, write_g0_receipt
from seqlogad.protocol.labels import LabelAccessScope, label_inventory
from seqlogad.protocol.registry import build_registry, write_registry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    from seqlogad.protocol.architectures import ARCHITECTURES

    active = list(ARCHITECTURES)

    # P1.2 -- registry. Label *inventories* are aggregate counts opened through the
    # evaluation boundary under an explicit, recorded scope; no per-record label is
    # materialised anywhere in Phase 1.
    inventories = {
        architecture: label_inventory(
            root,
            architecture,
            scope=LabelAccessScope.PROTOCOL_LABEL_INVENTORY,
            reason="P1.2 dataset registry: record that ground truth exists and at what granularity",
        )
        for architecture in active
    }
    registry_summary = write_registry(root, build_registry(root, label_inventories=inventories))
    print("[P1.2] registry:", json.dumps(registry_summary))

    # P1.5 -- leave-one-architecture-out folds
    folds = build_all_folds(root, active)
    for fold in folds:
        digest = write_fold(root, fold)
        print(
            f"[P1.5] {fold['fold_id']} target={fold['target_architecture']} "
            f"sources={fold['source_architecture_count']} sha256={digest[:16]}"
        )

    # P1.6 -- target burn-in buffers
    for fold in folds:
        manifest = build_buffer(root, fold["fold_id"])
        write_buffer(root, manifest)
        print(
            f"[P1.6] {manifest['buffer_id']} records={manifest['records']:,} "
            f"readiness={manifest['readiness']}"
        )

    # P1.7 -- isolation / leakage audit
    for fold in folds:
        report = audit_fold(root, fold["fold_id"])
        write_audit(root, report)
        print(
            f"[P1.7] {report['fold_id']} verdict={report['verdict']} "
            f"{json.dumps(report['counts'])}"
        )

    # P1.8 -- freeze and G0 receipt
    receipt = build_g0_receipt(root)
    write_g0_receipt(root, receipt)
    print(f"[P1.8] G0 gate_state={receipt['gate_state']} {json.dumps(receipt['counts'])}")
    for criterion in receipt["criteria"]:
        if criterion["verdict"] != "PASS":
            print(f"        {criterion['verdict']}: {criterion['id']} {criterion['description']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
