import json
from pathlib import Path
import stat
import zipfile

import pytest
import yaml

from seqlogad.semantic.checkpoint import seal, verify_seal
from seqlogad.semantic.config import load_config, final_run_id
from seqlogad.semantic.train import validate_run_id
from scripts.package_semantic_colab import verify_archive


ROOT = Path(__file__).resolve().parents[1]


def test_pilot_closeout_is_registered_without_scientific_claim():
    receipt = json.loads((ROOT / 'docs/reports/P2.1-bgl-pilot-closeout.json').read_text())
    assert receipt['artifact_sha256'] == '2df2bfcc554f32ac7dd2e566952d719dedd4998564007789ad4c37f788961d24'
    assert receipt['best_checkpoint'] == 'step-300'
    assert receipt['best_checkpoint_adapter_sha256'] == 'bc93340c67a0c2a8930456847b4e25fd1f1a643f503071cffdda7840c9661f9d'
    assert receipt['pilot_status'] == 'PASS'
    assert receipt['scientific_status'] == 'NOT_EVALUATED'


def test_final_config_and_exact_matrix_are_frozen():
    raw = yaml.safe_load((ROOT / 'configs/models/semantic-v1.yaml').read_text())['semantic']['final_protocol']
    assert raw['regime'] == 'UNLABELED_POSSIBLY_CONTAMINATED'
    assert raw['target_folds'] == ['FOLD-TARGET-ARCH-HDFS', 'FOLD-TARGET-ARCH-BGL', 'FOLD-TARGET-ARCH-HADOOP']
    assert raw['seeds'] == [42, 3407, 8675309]
    assert raw['train_records_per_source'] == 8192
    assert raw['validation_records_per_source'] == 512
    assert raw['max_steps'] == 1536
    assert raw['early_stopping_patience'] == 3
    cfg, _ = load_config(ROOT, {'seed': 3407}, run_mode='final')
    assert cfg['run_mode'] == 'final' and cfg['rank'] == 16 and cfg['context_length'] == 512
    with pytest.raises(ValueError, match='preregistered'):
        load_config(ROOT, {'seed': 1}, run_mode='final')
    matrix = json.loads((ROOT / 'docs/reports/P2.1-final-run-matrix.json').read_text())['runs']
    assert len(matrix) == 9
    assert len({row['run_id'] for row in matrix}) == 9
    assert {row['fold_id'] for row in matrix} == set(raw['target_folds'])
    assert {row['seed'] for row in matrix} == set(raw['seeds'])
    for row in matrix:
        assert row['run_id'] == final_run_id(row['fold_id'], row['seed'])
        assert validate_run_id(row['run_id']) == row['run_id']


@pytest.mark.parametrize('run_id', [
    'P2.1-FINAL-BGL-S42',
    'PILOT-BGL-20260914-001701',
    'resume_BGL-S42',
])
def test_run_id_validator_accepts_safe_single_path_components(run_id):
    assert validate_run_id(run_id) == run_id


@pytest.mark.parametrize('run_id', [None, '', '.', '..', '../escape', 'nested/run',
                                     '/absolute', '-leading', 'trailing.', 'two--separators'])
def test_run_id_validator_rejects_unsafe_or_ambiguous_values(run_id):
    with pytest.raises(ValueError, match='unsafe run_id'):
        validate_run_id(run_id)


def test_hardened_run_ledger_directly_covers_nested_ledgers(tmp_path):
    checkpoint = tmp_path / 'checkpoints/step-100'
    checkpoint.mkdir(parents=True)
    (checkpoint / 'adapter.bin').write_bytes(b'adapter')
    seal(checkpoint)
    (tmp_path / 'manifest.json').write_text('{}')
    files = seal(tmp_path)
    nested = 'checkpoints/step-100/checksums.sha256'
    assert nested in files
    assert verify_seal(tmp_path, require_nested_ledgers=True)['nested_ledgers'] == [nested]
    lines = (tmp_path / 'checksums.sha256').read_text().splitlines()
    (tmp_path / 'checksums.sha256').write_text('\n'.join(line for line in lines if nested not in line) + '\n')
    with pytest.raises(ValueError, match='incomplete'):
        verify_seal(tmp_path, require_nested_ledgers=True)


def test_status_does_not_unlock_p2_2():
    phase2 = yaml.safe_load((ROOT / 'configs/protocols/phase2-architecture-v1.yaml').read_text())['phase2']
    p21 = phase2['tasks']['P2.1']
    assert p21['pilot_closeout'] == 'PASS'
    assert p21['final_protocol_frozen'] is True
    assert p21['final_training_status'] == 'NOT_STARTED'
    assert p21['scientific_result'] == 'NOT_EVALUATED'
    assert phase2['tasks']['P2.2']['execution_authorized'] is False


def test_notebook_has_explicit_pilot_and_final_modes():
    notebook = json.loads((ROOT / 'notebooks/P2.1_train_semantic_expert.ipynb').read_text())
    code = '\n'.join(''.join(cell['source']) for cell in notebook['cells'] if cell['cell_type'] == 'code')
    assert 'RUN_MODE = "pilot"' in code
    assert '--run-mode' in code
    assert 'P2.1-FINAL-' in code
    assert '/content/phase2' in code and '/content/seqlogad_outputs' in code
    assert 'HF_TOKEN' in code and 'userdata.get("HF_TOKEN")' in code
    for term in ['virtualenv==20.31.2', 'torch==2.9.1', 'https://download.pytorch.org/whl/cu128',
                 'safe_extract_zip', 'Duplicate ZIP member', 'ZIP symlink forbidden',
                 'resolve_uploaded_zip', 'Expected exactly one uploaded code ZIP matching the frozen SHA-256',
                 'PYTHONUNBUFFERED', '[TOKEN_HIDDEN]', 'EXPECTED_CODE_ZIP_SHA256']:
        assert term in code
    assert 'print(os.environ["HF_TOKEN"])' not in code
    assert 'REPO_ROOT = "/content/seqlogad_code"' in code
    assert all(not cell.get('outputs') for cell in notebook['cells'])


def test_kaggle_final_notebook_discovers_read_only_inputs_and_writes_only_to_working():
    path = ROOT / 'notebooks/P2_1_train_semantic_expert_FINAL.ipynb'
    notebook = json.loads(path.read_text())
    code_cells = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
    code = '\n'.join(''.join(cell['source']) for cell in code_cells)
    for index, cell in enumerate(code_cells):
        compile(''.join(cell['source']), f'<kaggle-cell-{index}>', 'exec')
    for term in ['/kaggle/input', '/kaggle/working', 'kaggle_secrets',
                 'rglob("manifests/bundle.json")', 'CODE_PROVENANCE.json',
                 'P2.1-FINAL-', 'EXPECTED_BUNDLE_SHA256', 'PATCHED_IN_WORKING_COPY',
                 'env.pop("PYTHONPATH", None)', 'isolated_subprocess_env()',
                 'wrapt>=1.16,<2']:
        assert term in code
    for forbidden in ['/content/', 'google.colab', 'files.download', 'RUN_MODE = "pilot"']:
        assert forbidden not in code
    assert all(not cell.get('outputs') for cell in notebook['cells'])


def test_final_cannot_fall_back_to_pilot_budget():
    cfg, _ = load_config(ROOT, {'seed': 42}, run_mode='final')
    assert (cfg['train_records_per_source'], cfg['validation_records_per_source']) == (8192, 512)
    assert (cfg['max_steps'], cfg['warmup_steps']) == (1536, 100)
    assert (cfg['validation_steps'], cfg['save_steps']) == (100, 100)
    assert (cfg['early_stopping_patience'], cfg['early_stopping_min_delta']) == (3, 0.001)
    with pytest.raises(ValueError, match='only preregistered'):
        load_config(ROOT, {'seed': 42, 'max_steps': 500}, run_mode='final')


@pytest.mark.parametrize('kind', ['traversal', 'symlink'])
def test_package_verifier_rejects_unsafe_members(tmp_path, kind):
    archive = tmp_path / 'unsafe.zip'
    with zipfile.ZipFile(archive, 'w') as handle:
        if kind == 'traversal':
            handle.writestr('../escape', 'x')
        else:
            info = zipfile.ZipInfo('seqlogad_code/link')
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            handle.writestr(info, '/tmp/target')
    with pytest.raises(ValueError, match='unsafe|symlink'):
        verify_archive(archive, 'seqlogad_code')
