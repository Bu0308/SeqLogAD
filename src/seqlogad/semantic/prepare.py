"""Materialize exact Phase1 source memberships; never consult ground-truth labels.

Reconstruct file-order -> chronological-rank identity and compare to signed stream.
Only then normalize selected EARLY/MID records. Never redefine a split.
"""
import hashlib
import json
import shutil
import subprocess
from array import array
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import pyarrow as pa

from seqlogad.common.checksum import sha256_file
from seqlogad.protocol.architectures import ARCHITECTURES, ADAPTERS, resolve_files
from seqlogad.protocol.normalizer import load_normalizer
from seqlogad.protocol.nul import canonicalize_nul_message
from .contracts import SCHEMA, PARTITIONS, dump, read, membership, validate_bundle


def hash64(raw):
    return int.from_bytes(hashlib.blake2b(raw, digest_size=8).digest(), 'big', signed=True)


def git_state(root):
    if not (Path(root) / '.git').exists():
        info = read(Path(root) / 'CODE_PROVENANCE.json')
        for name, digest in info['files'].items():
            if sha256_file(Path(root) / name) != digest:
                raise ValueError('uploaded implementation checksum mismatch')
        return dict(info['git'], uploaded_code_files_sha256=info['files'])
    def run(*args):
        return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()
    return {'commit': run('rev-parse', 'HEAD'), 'dirty': bool(run('status', '--porcelain')),
            'diff_sha256': hashlib.sha256(run('diff', 'HEAD').encode()).hexdigest()}


def locate_source_rows(root, architecture, stream, index):
    """No normalizer/labels here; all-file hash/chronology verification only."""
    spec = ARCHITECTURES[architecture]
    files = resolve_files(root, spec)
    if len(files) != len(index['source_files']):
        raise ValueError('source file count changed')
    stamps, hashes = array('q'), array('q')
    adapter = ADAPTERS[spec.adapter]
    for path, identity in zip(files, index['source_files']):
        if sha256_file(path) != identity['sha256']:
            raise ValueError('raw corpus changed')
        previous = 0
        with path.open('rb') as handle:
            for number, line in enumerate(handle, 1):
                record = adapter(line, path.relative_to(root).as_posix(), number)
                if record.timestamp_us is not None:
                    previous = record.timestamp_us
                stamps.append(previous)
                hashes.append(hash64(record.raw_message_bytes))
    positions = pl.DataFrame({'effective_ts': pa.array(stamps), 'raw_h': pa.array(hashes)})
    positions = positions.with_row_index('file_position').sort('effective_ts', maintain_order=True)
    if positions.height != stream.height or not positions.select('effective_ts', 'raw_h').equals(stream.select('effective_ts', 'raw_h')):
        raise ValueError('source chronology/content differs from frozen stream')
    return stream.with_columns(positions['file_position']).filter(pl.col('segment').is_in([0, 2])).sort('file_position')


def prepare_architecture(root, architecture, cache):
    folder = root / 'data/processed/protocol/streams' / architecture.lower()
    index = read(folder / 'stream-index.json')
    if sha256_file(folder / 'stream.parquet') != index['stream_parquet_sha256']:
        raise ValueError('stream hash mismatch')
    stream = pl.read_parquet(folder / 'stream.parquet')
    selected = locate_source_rows(root, architecture, stream, index)
    normalizer = load_normalizer(root)
    if normalizer.rule_file_sha256 != index['normalizer']['rule_file_sha256']:
        raise ValueError('normalizer changed')
    # Sequential raw IO; only selected rows enter text normalization.
    wanted = iter(selected.select('file_position', 'norm_h').iter_rows())
    current = next(wanted, None)
    position = 0
    texts = []
    spec = ARCHITECTURES[architecture]
    adapter = ADAPTERS[spec.adapter]
    for path in resolve_files(root, spec):
        with path.open('rb') as handle:
            for number, line in enumerate(handle, 1):
                if current and position == current[0]:
                    record = adapter(line, path.relative_to(root).as_posix(), number)
                    text = normalizer.normalize(canonicalize_nul_message(record.raw_message_bytes).canonical_message)
                    if hash64(text.encode()) != current[1]:
                        raise ValueError('normalized content differs from Phase1')
                    texts.append(text)
                    current = next(wanted, None)
                position += 1
    if current is not None or len(texts) != selected.height:
        raise ValueError('incomplete materialization')
    result = selected.select('rank', 'segment').with_columns(
        pl.lit(architecture).alias('architecture_id'), pl.Series('normalized_message', texts))
    result.sort('rank').write_parquet(cache / f'{architecture}.parquet', compression='zstd')
    return index


def build_bundle(project_root, output_root):
    root, output = Path(project_root).resolve(), Path(output_root).resolve()
    if output.exists():
        raise ValueError('output exists; do not overwrite a prepared bundle')
    staging = output.with_name(output.name + '.building')
    staging.mkdir(parents=True, exist_ok=True)
    cache = staging / '_source_only_cache'; cache.mkdir(exist_ok=True)
    folds = [read(p) for p in sorted((root / 'data/processed/protocol/folds').glob('*.json'))]
    if not folds or any(not f['invariants_all_hold'] or f['target_labels_read'] for f in folds):
        raise ValueError('invalid Phase1 folds')
    receipt = root / 'data/processed/protocol/G0-receipt.json'
    receipt_data = read(receipt)
    required = ['configs/protocols/cross-system-split-v1.yaml', 'configs/parsing/normalizer-cs-v1.yaml']
    required += [f"data/processed/protocol/folds/{f['fold_id']}.json" for f in folds]
    for name in required:
        if sha256_file(root / name) != receipt_data['artifact_sha256'][name]:
            raise ValueError('G0 artifact binding mismatch')
    if receipt_data['gate_state'] != 'PROTOCOL_READY':
        raise ValueError('G0 not ready')
    arches = sorted({a for f in folds for a in f['source_architectures']})
    indices = {}
    for arch in arches:
        print(f'Preparing source view {arch}', flush=True)
        if (cache / f'{arch}.parquet').exists():
            indices[arch] = verify_prepared_cache(root, arch, cache)
        else:
            indices[arch] = prepare_architecture(root, arch, cache)
    provenance = {'created_at': datetime.now(timezone.utc).isoformat(), 'git': git_state(root),
                  'phase1_receipt_sha256': sha256_file(receipt), 'target_labels_read': False,
                  'builder_revision': SCHEMA,
                  'builder_code_sha256': {p.name: sha256_file(p) for p in Path(__file__).parent.glob('*.py')},
                  'builder_config_sha256': sha256_file(root / 'configs/models/semantic-v1.yaml')}
    for fold in folds:
        materialize_fold(root, staging, cache, fold, indices, provenance)
    shutil.rmtree(cache)
    (staging / 'README.md').write_text('Semantic source-only bundle. Upload this entire folder to /content/phase2.\nNo raw corpus, labels, target evaluation or model weights included.\n')
    files = {p.relative_to(staging).as_posix(): sha256_file(p) for p in sorted(staging.rglob('*')) if p.is_file()}
    bundle = dict(provenance, schema_version=SCHEMA, bundle_id='P2.1-SEMANTIC-001',
                  folds=[f['fold_id'] for f in folds], files=files, label_columns=[])
    dump(staging / 'manifests/bundle.json', bundle)
    checks = dict(files, **{'manifests/bundle.json': sha256_file(staging / 'manifests/bundle.json')})
    (staging / 'manifests/checksums.sha256').write_text(''.join(f'{v}  {k}\n' for k, v in sorted(checks.items())))
    for fold in folds:
        print(validate_bundle(staging, fold['fold_id'])['counts'], flush=True)
    staging.rename(output)
    return bundle


def materialize_fold(root, staging, cache, fold, indices, provenance):
    fold_id = fold['fold_id']; base = staging / 'folds' / fold_id
    source_fold = {k: fold[k] for k in ['fold_id', 'target_architecture', 'source_architectures', 'split_contract']}
    source_fold['partitions'] = {p: fold['partitions'][p] for p in PARTITIONS.values()}
    dump(base / 'manifests/fold.json', source_fold)
    lineage = dict(provenance, original_fold_sha256=sha256_file(root / 'data/processed/protocol/folds' / f'{fold_id}.json'), sources={})
    entries = []
    for directory, partition in PARTITIONS.items():
        frames = []
        for member in source_fold['partitions'][partition]['members']:
            arch = member['architecture_id']; index = indices[arch]
            index_path = root / 'data/processed/protocol/streams' / arch.lower() / 'stream-index.json'
            bound = fold['stream_indices'][arch]
            if sha256_file(index_path) != bound['stream_index_sha256'] or index['stream_parquet_sha256'] != bound['stream_parquet_sha256']:
                raise ValueError('fold stream binding mismatch')
            frame = pl.read_parquet(cache / f'{arch}.parquet').filter(pl.col('segment') == (0 if directory == 'train' else 2)).drop('segment')
            if frame.height != member['records'] or membership(frame['rank']) != member['membership_sha256']:
                raise ValueError('fold membership changed')
            frames.append(frame)
            # Neutral ordinals/hashes: raw filename can disclose labels (OpenStack).
            lineage['sources'][arch] = {'stream_index_sha256': bound['stream_index_sha256'],
                'source_files': [{'source_id': f'file-{i:04}', 'sha256': f['sha256'], 'bytes': f['bytes']} for i, f in enumerate(index['source_files'])]}
            entries.append(dict(member, partition=partition, dataset_id=index['dataset_id'],
                                stream_index_sha256=bound['stream_index_sha256']))
        dest = base / f'semantic/{directory}/records.parquet'; dest.parent.mkdir(parents=True, exist_ok=True)
        pl.concat(frames).write_parquet(dest, compression='zstd')
    dump(base / 'manifests/lineage.json', lineage)
    norm = base / 'metadata/normalizer-cs-v1.yaml'; norm.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / 'configs/parsing/normalizer-cs-v1.yaml', norm)
    for item in entries:
        directory = 'train' if item['partition'] == 'SOURCE_TRAIN' else 'val'
        path = base / f'semantic/{directory}/records.parquet'
        item.update(file_path=path.relative_to(staging).as_posix(), sha256=sha256_file(path),
                    record_count=item['records'], sample_count=item['records'],
                    source_corpus_sha256=hashlib.sha256(json.dumps(lineage['sources'][item['architecture_id']]['source_files'], sort_keys=True).encode()).hexdigest())
    dump(base / 'semantic/metadata/view.json', dict(provenance, fold_id=fold_id, schema_version=SCHEMA,
         input_fields=['normalized_message'], provenance_fields=['rank', 'architecture_id'],
         forbidden_fields=['label', 'anomaly', 'target', 'EventID', 'source_file', 'session_id'],
         label_columns=[], partitions=entries, bundle_id='P2.1-SEMANTIC-001',
         label_policy='SOURCE_ONLY_LABEL_FREE_UNRESOLVED_DENY', provenance='SIGNED_PHASE1_FOLDS_UNCHANGED', normalizer_sha256=sha256_file(norm),
         split_contract_sha256=fold['split_contract']['sha256'], clean_normal_claim=False))


def verify_prepared_cache(root, architecture, cache):
    """Resume a preprocessing pass only after rechecking every rank and text hash."""
    folder = root / 'data/processed/protocol/streams' / architecture.lower()
    index = read(folder / 'stream-index.json')
    if sha256_file(folder / 'stream.parquet') != index['stream_parquet_sha256']:
        raise ValueError('cached stream changed')
    for item in index['source_files']:
        if sha256_file(root / item['path']) != item['sha256']:
            raise ValueError('cached corpus changed')
    if sha256_file(root / 'configs/parsing/normalizer-cs-v1.yaml') != index['normalizer']['rule_file_sha256']:
        raise ValueError('cached normalizer changed')
    frame = pl.read_parquet(cache / f'{architecture}.parquet').sort('rank')
    expected = pl.read_parquet(folder / 'stream.parquet').filter(pl.col('segment').is_in([0,2])).sort('rank')
    if not frame.select('rank', 'segment').equals(expected.select('rank', 'segment')):
        raise ValueError('cached source ranks changed')
    texts = frame['normalized_message'].unique().to_list()
    mapping = {text: hash64(text.encode()) for text in texts}
    hashes = frame['normalized_message'].replace_strict(mapping, return_dtype=pl.Int64)
    if hashes.to_list() != expected['norm_h'].to_list():
        raise ValueError('cached content hash mismatch')
    if frame['architecture_id'].unique().to_list() != [architecture]:
        raise ValueError('cached architecture mismatch')
    return index
