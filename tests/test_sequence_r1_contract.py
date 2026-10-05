"""R1 must bind executable code, complete source cohorts and completed outputs."""
import json
from pathlib import Path
import zipfile

import pytest

from seqlogad.common.checksum import sha256_file
from seqlogad.sequence.config import load_config, identity, development_run_id
from seqlogad.sequence.implementation import implementation_digest
from seqlogad.sequence.objective import select_windows
from seqlogad.sequence.source_development import load_source_development
from seqlogad.phase2_execution.completed_identity import verify_completed_sequence

ROOT = Path(__file__).resolve().parents[1]


def test_r1_real_source_cohort_and_original_entries_retained():
    cfg, _ = load_config(ROOT, candidate='v13r1')
    sidecar = ROOT / 'data/phase2-source-dev-v13r1'
    old = ROOT / 'data/phase2-source-dev-v13'
    if not sidecar.exists():
        pytest.skip('local sealed source sidecar unavailable')
    manifest = json.loads((sidecar / 'manifest.json').read_text())
    assert manifest['target_labels_used_for_selection'] is False
    assert 'target_labels_read' not in manifest
    for fold in cfg['target_folds']:
        assert sha256_file(sidecar / (fold + '.json')) == sha256_file(old / (fold + '.json'))
        rows = select_windows(ROOT / 'data/phase2-sequence', fold, 'val', 512, 42, replacement=False)
        selected = load_source_development(sidecar, ROOT / 'data/phase2-sequence', fold, rows)
        for arch in {entry['architecture_id'] for entry in selected.values()}:
            units = {entry['unit_id']: entry['anomaly'] for entry in selected.values()
                     if entry['architecture_id'] == arch}
            assert sum(units.values()) == {'ARCH-BGL': 16, 'ARCH-HDFS': 10}[arch]


def test_legacy_v13_sidecar_remains_readable():
    sidecar = ROOT / 'data/phase2-source-dev-v13'
    if not sidecar.exists():
        pytest.skip('local sealed source sidecar unavailable')
    fold = 'FOLD-TARGET-ARCH-BGL'
    rows = select_windows(ROOT / 'data/phase2-sequence', fold, 'val', 512, 42, replacement=False)
    assert load_source_development(sidecar, ROOT / 'data/phase2-sequence', fold, rows)


def test_completed_archive_cannot_skip_changed_implementation(tmp_path):
    cfg, _ = load_config(ROOT, candidate='v13r1')
    fold = 'FOLD-TARGET-ARCH-BGL'
    run = development_run_id(fold, candidate='v13r1')
    manifest = {'run_id': run, 'real_training_completed': True, 'identity': {
        'config_sha256': identity(cfg), 'fold_id': fold, 'bundle_sha256': 'data',
        'source_development_manifest_sha256': 'labels',
        'implementation_sha256': implementation_digest(ROOT)}}
    archive = tmp_path / 'target.zip'
    def write():
        with zipfile.ZipFile(archive, 'w') as handle:
            handle.writestr(f'{run}/manifest.json', json.dumps(manifest))
    write()
    verify_completed_sequence(archive, ROOT, run, fold, 'v13r1', 'data', 'labels')
    manifest['identity']['implementation_sha256'] = 'different-code'
    write()
    with pytest.raises(ValueError, match='code/labels identity'):
        verify_completed_sequence(archive, ROOT, run, fold, 'v13r1', 'data', 'labels')
