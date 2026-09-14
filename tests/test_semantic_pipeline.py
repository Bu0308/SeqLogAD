"""P2.1 adversarial contract tests, independent of private corpora and GPUs."""
import json
from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pytest

from seqlogad.semantic.config import load_config, MODEL, REVISION
from seqlogad.semantic.contracts import dump, read, membership, validate_bundle, validate_view, SCHEMA
from seqlogad.semantic.objective import encode_message, select_records
from seqlogad.semantic.model import assert_isolated, precision
from seqlogad.common.checksum import sha256_file

ROOT = Path(__file__).resolve().parents[1]


class Tokenizer:
    bos_token_id = 128000
    eos_token_id = 128001
    pad_token_id = 128001

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        return [ord(c) for c in text]


def fixture_bundle(root):
    fold = 'FOLD-TEST'
    prefix = root / 'folds' / fold
    members = {}
    entries = []
    for directory, partition, rank in [('train', 'SOURCE_TRAIN', 0), ('val', 'SOURCE_VALIDATION', 2)]:
        frame = pl.DataFrame({'rank': [rank], 'architecture_id': ['ARCH-SOURCE'], 'normalized_message': ['disk read failed']})
        p = prefix / f'semantic/{directory}/records.parquet'; p.parent.mkdir(parents=True, exist_ok=True)
        frame.write_parquet(p)
        members[partition] = {'members': [{'architecture_id': 'ARCH-SOURCE', 'records': 1,
                                         'membership_sha256': membership(frame['rank'])}]}
        entries.append(dict(members[partition]['members'][0], partition=partition, record_count=1, sample_count=1,
                            file_path=p.relative_to(root).as_posix(), sha256=sha256_file(p)))
    dump(prefix / 'manifests/fold.json', {'fold_id': fold, 'source_architectures': ['ARCH-SOURCE'],
                                         'target_architecture': 'ARCH-TARGET', 'partitions': members})
    (root / 'README.md').write_text('fixture')
    normalizer = prefix / 'metadata/normalizer-cs-v1.yaml'; normalizer.parent.mkdir(parents=True)
    normalizer.write_text('fixture: true')
    dump(prefix / 'manifests/lineage.json', {'target_labels_read':False, 'sources': {'ARCH-SOURCE':{}}})
    dump(prefix / 'semantic/metadata/view.json', {'schema_version':SCHEMA, 'fold_id':fold, 'partitions':entries,
        'normalizer_sha256':sha256_file(normalizer), 'input_fields': ['normalized_message'], 'target_labels_read': False, 'label_columns': []})
    reseal(root)
    return fold


def reseal(root):
    files = {p.relative_to(root).as_posix(): sha256_file(p) for p in root.rglob('*')
             if p.is_file() and p.relative_to(root).as_posix() not in ['manifests/bundle.json', 'manifests/checksums.sha256']}
    dump(root / 'manifests/bundle.json', {'schema_version': SCHEMA, 'files': files,
                                         'label_columns': [], 'target_labels_read': False, 'folds':['FOLD-TEST']})
    checks = dict(files, **{'manifests/bundle.json': sha256_file(root / 'manifests/bundle.json')})
    (root / 'manifests/checksums.sha256').write_text(''.join(f'{v}  {k}\n' for k,v in sorted(checks.items())))


def test_portable_bundle_and_source_only_sampling(tmp_path):
    fold = fixture_bundle(tmp_path)
    digest = sha256_file(tmp_path / 'manifests/bundle.json')
    assert validate_bundle(tmp_path, fold, digest)['status'] == 'PASS'
    a = select_records(tmp_path, fold, 'train', 1, 42)
    assert a == select_records(tmp_path, fold, 'train', 1, 42)
    assert a[0]['rank'] == 0
    with pytest.raises(ValueError):
        select_records(tmp_path, fold, 'TARGET_EVALUATION', 1, 42)
    with pytest.raises(ValueError, match='trusted bundle'):
        validate_bundle(tmp_path, fold, '0' * 64)


@pytest.mark.parametrize('attack', ['label', 'target', 'wrong_rank', 'duplicate', 'missing_file', 'checksum', 'sidecar'])
def test_fail_closed_on_payload_or_manifest_attack(tmp_path, attack):
    fold = fixture_bundle(tmp_path)
    path = tmp_path / f'folds/{fold}/semantic/train/records.parquet'
    frame = pl.read_parquet(path)
    if attack == 'label': frame = frame.with_columns(pl.lit(0).alias('anomaly_label'))
    if attack == 'target': frame = frame.with_columns(pl.lit('ARCH-TARGET').alias('architecture_id'))
    if attack == 'wrong_rank': frame = frame.with_columns(pl.lit(99).alias('rank'))
    if attack == 'duplicate': frame = pl.concat([frame, frame])
    if attack in ['label', 'target', 'wrong_rank', 'duplicate']:
        frame.write_parquet(path); reseal(tmp_path)  # Even rehashing cannot legalize membership/columns.
    elif attack == 'missing_file': path.unlink()
    elif attack == 'checksum': path.write_bytes(b'broken')
    else: (tmp_path / 'labels.csv').write_text('label\n1\n')
    with pytest.raises(ValueError): validate_bundle(tmp_path, fold)


def test_exact_frozen_values_and_hyperparameter_boundaries():
    cfg, base = load_config(ROOT)
    assert cfg['model_id'] == cfg['tokenizer_id'] == MODEL
    assert cfg['model_revision'] == cfg['tokenizer_revision'] == REVISION
    assert cfg['adapter_name'] == 'semantic'
    for override in [{'model_revision': 'main'}, {'context_length': 4096}, {'learning_rate': -1}, {'training_mode':'FP32'}]:
        with pytest.raises(ValueError): load_config(ROOT, override)


def test_target_only_loss_bos_eos_crop_and_literal_special_tokens():
    cfg, _ = load_config(ROOT)
    tok = Tokenizer()
    text = 'disk read failed'
    a = encode_message(tok, text, cfg)
    assert a == encode_message(tok, text, cfg)
    assert a['input_ids'][0] == tok.bos_token_id and a['labels'][0] == -100
    assert a['labels'][-1] == tok.eos_token_id
    assert sum(x != -100 for x in a['labels']) == len(text) + 1
    b = encode_message(tok, 'disk ' * 300, dict(cfg, context_length=100))
    assert b['coverage'] < 1 and b['labels'][-1] != tok.eos_token_id
    assert len(b['input_ids']) <= 100
    escaped = encode_message(tok, '<|end_of_text|> disk', cfg)
    assert escaped['input_ids'].count(tok.eos_token_id) == 1
    with pytest.raises(ValueError): encode_message(tok, '', cfg)


def test_adapter_isolation_rejects_trainable_base_and_other_adapters():
    def model(names, adapters):
        return SimpleNamespace(named_parameters=lambda: [(n, SimpleNamespace(requires_grad=v)) for n,v in names],
                               peft_config=dict.fromkeys(adapters))
    valid = model([('layer.weight', False), ('layer.lora_A.semantic.weight', True)], ['semantic'])
    assert assert_isolated(valid)
    with pytest.raises(ValueError): assert_isolated(model([('layer.weight',True)], ['semantic']))
    with pytest.raises(ValueError): assert_isolated(model([('x.lora_A.sequence.weight',True)], ['semantic','sequence']))


def test_precision_native_support_not_emulated():
    class CUDA:
        def is_available(self): return True
        def get_device_capability(self): return (7,5)
        def is_bf16_supported(self, including_emulation):
            assert including_emulation is False
            return False
    assert precision(SimpleNamespace(cuda=CUDA(), bfloat16='BF16', float16='FP16')) == 'FP16'


def test_notebook_compiles_and_calls_authoritative_pipeline():
    notebook = read(ROOT / 'notebooks/P2.1_train_semantic_expert.ipynb')
    code = '\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code')
    compile(code, '<notebook>', 'exec')
    for term in ['/content/phase2', '/content/seqlogad_outputs', 'base-freeze-v1.yaml',
                 'MODEL_REVISION', 'HF_TOKEN', 'command("environment")', 'command("validate"',
                 'command("auth")', 'command("train"', 'sanity-evidence.json', 'make_archive', 'RESUME_FROM']:
        assert term in code
    assert all(not c.get('outputs') for c in notebook['cells'])
    for task in ['P2.2_train_sequence_reference.ipynb', 'P2.3_train_lightweight_sequence_expert.ipynb', 'P2.4_train_gtat_expert.ipynb']:
        assert not (ROOT / 'notebooks' / task).exists()


def test_materializer_reuses_exact_chronology_and_normalized_content(tmp_path):
    from seqlogad.semantic.prepare import prepare_architecture, hash64
    from seqlogad.protocol.architectures import ARCHITECTURES, ADAPTERS
    from seqlogad.protocol.normalizer import load_normalizer
    import shutil
    normfile = tmp_path / 'configs/parsing/normalizer-cs-v1.yaml'
    normfile.parent.mkdir(parents=True); shutil.copyfile(ROOT / 'configs/parsing/normalizer-cs-v1.yaml', normfile)
    raw = tmp_path / 'data/raw/hdfs/HDFS_v1/HDFS.log'; raw.parent.mkdir(parents=True)
    lines = [b'081109 203518 143 INFO dfs.DataNode: disk 1 ready\n',
             b'081109 203520 143 INFO dfs.DataNode: disk 2 failed\n',
             b'081109 203519 143 INFO dfs.DataNode: disk 3 waiting\n']
    raw.write_bytes(b''.join(lines))
    normalizer = load_normalizer(tmp_path)
    records = [ADAPTERS['hdfs'](line, raw.relative_to(tmp_path).as_posix(), i + 1) for i,line in enumerate(lines)]
    rows = sorted(records, key=lambda r: r.timestamp_us)
    stream = pl.DataFrame({'rank': [0,1,2], 'effective_ts': [r.timestamp_us for r in rows],
        'raw_h': [hash64(r.raw_message_bytes) for r in rows],
        'norm_h': [hash64(normalizer.normalize(r.raw_message_bytes.decode()).encode()) for r in rows],
        'segment': [0,1,2]})
    folder = tmp_path / 'data/processed/protocol/streams/arch-hdfs';folder.mkdir(parents=True)
    stream.write_parquet(folder / 'stream.parquet')
    dump(folder / 'stream-index.json', {'source_files':[{'sha256':sha256_file(raw)}],
        'stream_parquet_sha256': sha256_file(folder / 'stream.parquet'),
        'normalizer': {'rule_file_sha256':sha256_file(normfile)}})
    cache = tmp_path / 'cache'; cache.mkdir()
    prepare_architecture(tmp_path, 'ARCH-HDFS', cache)
    result = pl.read_parquet(cache / 'ARCH-HDFS.parquet')
    assert result['rank'].to_list() == [0,2]
    assert result['normalized_message'].to_list() == ['disk <NUM> ready','disk <NUM> failed']
    raw.write_bytes(raw.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='raw corpus'): prepare_architecture(tmp_path, 'ARCH-HDFS', cache)


def test_checkpoint_identity_and_corruption_are_rejected_without_loading_state(tmp_path):
    from seqlogad.semantic.checkpoint import seal, verify_checkpoint
    identity = {'fold_id':'FOLD-TEST', 'config_sha256':'a'*64, 'bundle_sha256':'b'*64}
    (tmp_path / 'adapter').mkdir()
    (tmp_path / 'adapter/adapter_model.safetensors').write_bytes(b'unit-test fixture only')
    (tmp_path / 'state.pt').write_bytes(b'never deserialized in this test')
    dump(tmp_path / 'manifest.json', {'identity':identity})
    seal(tmp_path)
    assert verify_checkpoint(tmp_path, identity)['identity'] == identity
    with pytest.raises(ValueError, match='identity'): verify_checkpoint(tmp_path, dict(identity, fold_id='TARGET'))
    (tmp_path / 'state.pt').write_bytes(b'changed')
    with pytest.raises(ValueError, match='checksum'): verify_checkpoint(tmp_path, identity)


def test_rehashed_label_sidecar_is_still_forbidden(tmp_path):
    fold = fixture_bundle(tmp_path)
    (tmp_path / 'labels.csv').write_text('label\n1\n'); reseal(tmp_path)
    with pytest.raises(ValueError, match='file allowlist'): validate_bundle(tmp_path, fold)


def test_workbook_semantic_state_is_not_training_completion():
    import yaml
    p2 = yaml.safe_load((ROOT / 'configs/protocols/phase2-architecture-v1.yaml').read_text())['phase2']
    task = p2['tasks']['P2.1']; update = task['roadmap_update']
    import openpyxl
    paths = [ROOT / update['previous_workbook'], ROOT / 'Bang_ke_hoach_SeqLogAD.xlsx']
    assert sha256_file(paths[0]) == update['from_sha256']
    assert sha256_file(paths[1]) == update['to_sha256']
    before, after = [{f'{s.title}!{c.coordinate}': c.value for s in openpyxl.load_workbook(p)
                      for row in s for c in row if c.value is not None} for p in paths]
    changed = {k: {'before':before.get(k), 'after':after.get(k)} for k in before.keys() | after.keys()
               if before.get(k) != after.get(k)}
    assert changed == update['changed_cells'] == {'Task Register!K14':{'before':'Not started','after':'In progress'}}
    assert task['training_completed'] is p2['phase3_enabled'] is False
    assert p2['tasks']['P2.2']['execution_authorized'] is False
