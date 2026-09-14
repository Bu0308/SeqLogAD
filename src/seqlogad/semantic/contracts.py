"""Portable semantic-view identities and fail-closed validation (no GPU dependency)."""
import hashlib
import json
from pathlib import Path, PurePosixPath

import polars as pl

from seqlogad.common.checksum import sha256_file

SCHEMA = 'SEMANTIC-VIEW-1'
COLUMNS = {'architecture_id', 'rank', 'normalized_message'}
PARTITIONS = {'train': 'SOURCE_TRAIN', 'val': 'SOURCE_VALIDATION'}


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def read(path):
    return json.loads(Path(path).read_text())


def safe_path(root, relative):
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or '\\' in relative:
        raise ValueError('non-portable path')
    root = Path(root).resolve()
    path = root / relative
    if not path.resolve().is_relative_to(root) or any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
        raise ValueError('external path/symlink forbidden')
    return path


def membership(ranks):
    digest = hashlib.sha256()
    ranks = ranks.sort()
    for start in range(0, len(ranks), 65536):
        digest.update(b''.join(int(v).to_bytes(8, 'big') for v in ranks.slice(start, 65536)))
    return digest.hexdigest()


def validate_view(frame, member, architecture):
    if set(frame.columns) != COLUMNS:
        raise ValueError('payload column allowlist violation (labels/identifiers forbidden)')
    if frame.null_count().row(0) != (0,) * len(frame.columns):
        raise ValueError('null semantic record')
    if frame['architecture_id'].unique().to_list() != [architecture]:
        raise ValueError('source role violation')
    if frame.height != member['records'] or frame['rank'].n_unique() != frame.height:
        raise ValueError('count/duplicate rank violation')
    if membership(frame['rank']) != member['membership_sha256']:
        raise ValueError('Phase1 membership mismatch')
    if frame['normalized_message'].dtype != pl.String:
        raise ValueError('text payload required')


def validate_bundle(data_root, fold_id, expected_bundle_sha256=None):
    root = Path(data_root)
    bundle_path = root / 'manifests/bundle.json'
    if expected_bundle_sha256 and sha256_file(bundle_path) != expected_bundle_sha256:
        raise ValueError('trusted bundle digest mismatch')
    bundle = read(bundle_path)
    if bundle['schema_version'] != SCHEMA or bundle['label_columns'] or bundle['target_labels_read']:
        raise ValueError('bundle policy violation')
    if fold_id not in bundle['folds'] or len(bundle['folds']) != len(set(bundle['folds'])):
        raise ValueError('unknown/duplicate fold')
    shape = {'README.md'}
    for fold in bundle['folds']:
        for name in ['manifests/fold.json', 'manifests/lineage.json', 'metadata/normalizer-cs-v1.yaml',
                     'semantic/metadata/view.json', 'semantic/train/records.parquet', 'semantic/val/records.parquet']:
            shape.add(f'folds/{fold}/{name}')
    if set(bundle['files']) != shape:
        raise ValueError('bundle file allowlist violation')
    allowed = shape | {'manifests/bundle.json', 'manifests/checksums.sha256'}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != allowed:
        raise ValueError('file allowlist violation: unexpected/missing sidecars')
    for name, digest in bundle['files'].items():
        if sha256_file(safe_path(root, name)) != digest:
            raise ValueError(f'checksum mismatch: {name}')
    checks = (root / 'manifests/checksums.sha256').read_text().splitlines()
    expected = dict(bundle['files'], **{'manifests/bundle.json': sha256_file(bundle_path)})
    if checks != [f'{v}  {k}' for k, v in sorted(expected.items())]:
        raise ValueError('checksum ledger mismatch')
    prefix = f'folds/{fold_id}'
    fold = read(safe_path(root, prefix + '/manifests/fold.json'))
    if fold['fold_id'] != fold_id or fold['target_architecture'] in fold['source_architectures']:
        raise ValueError('fold/source identity violation')
    if set(fold['partitions']) != set(PARTITIONS.values()):
        raise ValueError('target partition in training bundle')
    view = read(root / prefix / 'semantic/metadata/view.json')
    lineage = read(root / prefix / 'manifests/lineage.json')
    if view['schema_version'] != SCHEMA or view['fold_id'] != fold_id:
        raise ValueError('semantic view identity mismatch')
    if view['normalizer_sha256'] != sha256_file(root / prefix / 'metadata/normalizer-cs-v1.yaml'):
        raise ValueError('normalizer lineage mismatch')
    if lineage['target_labels_read'] or set(lineage['sources']) != set(fold['source_architectures']):
        raise ValueError('source lineage violation')
    if view['input_fields'] != ['normalized_message'] or view['target_labels_read'] or view['label_columns']:
        raise ValueError('semantic feature policy violation')
    counts = {}
    for directory, partition in PARTITIONS.items():
        frame = pl.read_parquet(root / prefix / f'semantic/{directory}/records.parquet')
        if set(frame.columns) != COLUMNS or set(frame['architecture_id'].unique()) != set(fold['source_architectures']):
            raise ValueError('payload/source allowlist violation')
        counts[partition] = {}
        for member in fold['partitions'][partition]['members']:
            arch = member['architecture_id']
            subset = frame.filter(pl.col('architecture_id') == arch)
            validate_view(subset, member, arch)
            counts[partition][arch] = subset.height
            entries = [e for e in view['partitions'] if e['partition'] == partition and e['architecture_id'] == arch]
            if len(entries) != 1 or entries[0]['membership_sha256'] != member['membership_sha256']:
                raise ValueError('view membership lineage mismatch')
            entry = entries[0]
            if entry['record_count'] != subset.height or entry['sample_count'] != subset.height:
                raise ValueError('view count mismatch')
            name = prefix + f'/semantic/{directory}/records.parquet'
            if entry['file_path'] != name or entry['sha256'] != bundle['files'][name]:
                raise ValueError('view file identity mismatch')
    return {'status': 'PASS', 'fold_id': fold_id, 'counts': counts,
            'bundle_sha256': sha256_file(bundle_path), 'view': view}
