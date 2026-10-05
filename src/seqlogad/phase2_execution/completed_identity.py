"""Verify completed Sequence runs before reusing a persisted target ZIP."""
import json
import zipfile

from seqlogad.sequence.config import identity, load_config
from seqlogad.sequence.implementation import implementation_digest


def verify_completed_sequence(archive, repo_root, run_id, fold_id, candidate,
                              bundle_sha256, sidecar_sha256):
    cfg, _ = load_config(repo_root, candidate=candidate)
    expected = {"config_sha256": identity(cfg), "fold_id": fold_id,
                "bundle_sha256": bundle_sha256,
                "implementation_sha256": implementation_digest(repo_root),
                "source_development_manifest_sha256": sidecar_sha256}
    with zipfile.ZipFile(archive) as handle:
        manifest = json.loads(handle.read(f"{run_id}/manifest.json"))
    if manifest.get("run_id") != run_id or manifest.get("real_training_completed") is not True:
        raise ValueError("completed Sequence run identity mismatch")
    if any(manifest.get("identity", {}).get(key) != value for key, value in expected.items()):
        raise ValueError("completed Sequence config/data/code/labels identity mismatch")
