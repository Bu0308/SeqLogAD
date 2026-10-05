"""Capture RunPod training evidence for the existing long-term-job collection."""
import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import uuid
import zipfile

from collection_archive_v13r1 import seal, sha, stream_hash

TRAIN_NAME = 'P2.2 Sequence V13R1 RunPod attempt'
METRICS = ['accuracy', 'precision', 'recall', 'f1', 'auroc', 'average_precision']


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def pmem(root, args, output=False):
    result = subprocess.run([sys.executable, '-m', 'pmem', *args], cwd=root,
                            check=True, capture_output=True, text=True)
    if output:
        return result.stdout
    print(result.stdout, end='')


def prepare(root, uploads, attempt):
    contract = json.loads((uploads / 'RUNPOD_UPLOAD_MANIFEST.json').read_text())
    dest = root / 'handoff_inputs'
    dest.mkdir(parents=True, exist_ok=True)
    for name, row in contract['files'].items():
        if Path(name).name != name or sha(uploads / name) != row['sha256']:
            raise ValueError('Handoff input identity mismatch: ' + name)
        target = dest / name
        shutil.copy2(uploads / name, target)
        pmem(root, ['track', target.relative_to(root).as_posix(), '--update'])
    shutil.copy2(uploads / 'RUNPOD_UPLOAD_MANIFEST.json', dest)
    pmem(root, ['track', 'handoff_inputs/RUNPOD_UPLOAD_MANIFEST.json', '--update'])
    kit = json.loads((dest / 'RUNPOD_UPLOAD_MANIFEST.json').read_text())
    path = root / 'collection_capture/run_inputs' / (attempt + '.json')
    value = {'schema': 'SEQLOGAD-RUNPOD-CAPTURE-INPUT-1', 'seed': 42,
        'architecture_id': 'ARCH-SEQ-LO-001', 'variant_id': 'VAR-SEQ-LO-001-V013R1',
        'run_intent': 'development', 'target_folds': kit['targets'],
        'input_file_hashes': {name: row['sha256'] for name, row in contract['files'].items()},
        'dataset_bundle_manifest_sha256': kit['sequence_bundle_manifest_sha256'],
        'source_development_manifest_sha256': kit['source_development_manifest_sha256'],
        'target_labels_used_for_selection': False,
        'checkpoint_selection': kit['checkpoint_selection'],
        'scientific_status': 'NOT_EVALUATED', 'privacy': 'RESTRICTED',
        'recorded_before_training': True, 'attempt_id': attempt}
    write(path, value)
    pmem(root, ['track', path.relative_to(root).as_posix(), '--update'])
    pmem(root, ['note', 'Prepared immutable V13R1 training capture inputs: ' + path.relative_to(root).as_posix(),
                '--tag', 'method', '--tag', 'V13R1'])
    print('COLLECT_INPUT_CONFIG=' + path.relative_to(root).as_posix())


def verified_zip(path):
    sidecar = Path(str(path) + '.sha256')
    expected, name = sidecar.read_text().strip().split('  ', 1)
    if name != path.name or expected != sha(path):
        raise ValueError('ZIP checksum mismatch: ' + path.name)
    with zipfile.ZipFile(path) as handle:
        names = handle.namelist()
        if len(names) != len(set(names)) or handle.testzip() is not None:
            raise ValueError('Invalid ZIP: ' + path.name)
        if not any(n.count('/') == 1 and n.endswith('/checksums.sha256') for n in names):
            raise ValueError('ZIP root checksum ledger missing')
        for name in names:
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name:
                raise ValueError('Unsafe ZIP member')
        for ledger in [n for n in names if n.endswith('/checksums.sha256')]:
            prefix = ledger.rsplit('/', 1)[0] + '/'
            for line in handle.read(ledger).decode().splitlines():
                digest, member = line.split('  ', 1)
                actual = prefix + member
                if actual not in names:
                    actual = names[0].split('/')[0] + '/' + member
                with handle.open(actual) as stream:
                    if stream_hash(stream) != digest:
                        raise ValueError('Nested ledger mismatch: ' + member)
    return path


def fold_report(root, target, report):
    kit = json.loads((root / 'handoff_inputs/RUNPOD_UPLOAD_MANIFEST.json').read_text())
    path = verified_zip(root / 'P2.2/targets' / ('P2.2_' + target + '_S42.zip'))
    with zipfile.ZipFile(path) as handle:
        hits = [n for n in handle.namelist() if n.count('/') == 1 and n.endswith('/manifest.json')]
        if len(hits) != 1:
            raise ValueError('Expected one completed run manifest')
        prefix = hits[0].rsplit('/', 1)[0] + '/'
        manifest = json.loads(handle.read(hits[0]))
        metrics = json.loads(handle.read(prefix + 'metrics.json'))
        if manifest.get('real_training_completed') is not True or manifest.get('seed') != 42:
            raise ValueError('Incomplete or wrong-seed training artifact')
        if manifest.get('completion_status') != 'TRAINING_COMPLETED_REQUIRES_REVIEW':
            raise ValueError('Completed training status missing')
        expected = {'implementation_sha256': kit['implementation_sha256'],
                    'bundle_sha256': kit['sequence_bundle_manifest_sha256'],
                    'source_development_manifest_sha256': kit['source_development_manifest_sha256'],
                    'fold_id': 'FOLD-TARGET-ARCH-' + target, 'adapter': 'sequence'}
        if any(manifest.get('identity', {}).get(k) != v for k, v in expected.items()):
            raise ValueError('Training source/data/fold identity mismatch')
        if not manifest['run_id'].endswith('-' + target + '-S42-V13R1'):
            raise ValueError('Wrong variant/fold artifact')
        if manifest.get('semantic_adapter_used') is not False:
            raise ValueError('Unexpected Semantic reuse')
        for name in METRICS:
            value = metrics['source_development_best']['macro_' + name]
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('Missing/nonfinite source metric: ' + name)
        adapter = prefix + manifest['checkpoint'] + '/adapter/adapter_model.safetensors'
        with handle.open(adapter) as stream:
            if stream_hash(stream) != manifest['checkpoint_sha256']:
                raise ValueError('Selected checkpoint digest mismatch')
        for name in ['manifest.json', 'config.yaml', 'metrics.json', 'environment.json', 'dependency-lock.txt']:
            out = report / 'fold_reports' / target / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(handle.read(prefix + name))
    return {'target_fold': target, 'run_alias': manifest['run_id'],
            'artifact_path': path.relative_to(root).as_posix(), 'sha256': sha(path),
            'checkpoint_sha256': manifest['checkpoint_sha256'],
            'source_metrics': metrics['source_development_best'],
            'scientific_status': manifest['scientific_results']}


def native_index(root, report):
    with sqlite3.connect((root / '.pmem/pmem.db').as_uri() + '?mode=ro', uri=True) as con:
        con.row_factory = sqlite3.Row
        runs = [dict(r) for r in con.execute('SELECT * FROM runs ORDER BY timestamp, run_id')]
    training = [r for r in runs if r['name'] == TRAIN_NAME]
    eligible = [r for r in training if r['status'] == 'success' and
                json.loads(r['config_json']).get('variant_id') == 'VAR-SEQ-LO-001-V013R1']
    if not eligible:
        raise ValueError('No successful native training run with captured V13R1 config')
    captured = json.loads(eligible[-1]['metrics_json'])
    required = ['source_development_macro_f1'] + [target + '_source_development_macro_' + name
        for target in ['BGL', 'HDFS', 'HADOOP'] for name in METRICS]
    if any(name not in captured or not isinstance(captured[name], (int, float)) or
           not math.isfinite(captured[name]) for name in required):
        raise ValueError('Native Projmem training metrics incomplete/nonfinite')
    links = []
    for row in runs:
        args = shlex.split(row['command'])
        attempt = args[args.index('--attempt') + 1] if '--attempt' in args else None
        links.append({'native_run_id': row['run_id'], 'name': row['name'],
            'technical_status': row['status'], 'seed': row['seed'],
            'attempt_id': Path(attempt).name if attempt else None,
            'config': json.loads(row['config_json']), 'metrics': json.loads(row['metrics_json']),
            'stdout_path': row['stdout_path'], 'stderr_path': row['stderr_path'],
            'timestamp_utc': row['timestamp'], 'scientific_status': 'NOT_EVALUATED'})
    write(report / 'NATIVE_RUN_LINKS.json', {'schema': 'SEQLOGAD-NATIVE-RUN-LINKS-1', 'runs': links})
    with (report / 'NATIVE_RUN_INDEX.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['native_run_id', 'name', 'technical_status',
            'seed', 'attempt_id', 'timestamp_utc', 'scientific_status'])
        writer.writeheader()
        writer.writerows({k: row[k] for k in writer.fieldnames} for row in links)
    mapped = {row['attempt_id'] for row in links if row['attempt_id']}
    return [p.name for p in (root / 'attempts').iterdir() if p.is_dir() and p.name not in mapped]


def capture(root, report):
    report.mkdir(parents=True, exist_ok=False)
    kit = json.loads((root / 'handoff_inputs/RUNPOD_UPLOAD_MANIFEST.json').read_text())
    folds = [fold_report(root, target, report) for target in kit['targets']]
    final = verified_zip(root / 'P2.2/seqlogad_outputs_P2.2_S42_FINAL.zip')
    with zipfile.ZipFile(final) as handle:
        for row in folds:
            source = root / row['artifact_path']
            name = 'P2.2_S42/targets/' + source.name
            with handle.open(name) as stream:
                if stream_hash(stream) != row['sha256']:
                    raise ValueError('Final bundle differs from per-fold artifact')
    unmatched = native_index(root, report)
    write(report / 'COLLECTION_MANIFEST.json', {'schema': 'SEQLOGAD-TRAINING-CAPTURE-1',
        'status': 'TRAINING_CAPTURE_VERIFIED_ALETHEIA_ACCEPTANCE_PENDING',
        'architecture_id': 'ARCH-SEQ-LO-001', 'variant_id': 'VAR-SEQ-LO-001-V013R1',
        'folds': folds, 'unlinked_attempt_ids': unmatched,
        'base_model_weights_included': False, 'normalized_source_data_included': True,
        'target_metrics': 'NOT_EVALUATED', 'privacy_review': 'PENDING_HUMAN_REVIEW'})
    with (report / 'MISSING_AND_EXCLUDED_ITEMS.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['item', 'status', 'reason'])
        for item in ['Aletheia import acceptance', 'human privacy/license review',
                     'ground-truth and causal audit', 'reviewed graph and research-record merge',
                     'capture coverage across full project history']:
            writer.writerow([item, 'PENDING_REVIEW', 'To complete against canonical long-term-job collection after download'])
        writer.writerow(['target holdout results', 'NOT_YET_AVAILABLE', 'Not evaluated in V13R1 development training'])
        writer.writerow(['base model bytes', 'EXCLUDED', 'Pinned model/revision recorded; HF cache remains outside private capture'])
        for attempt in unmatched:
            writer.writerow([attempt, 'UNLINKED_ATTEMPT_PRESERVED', 'Journal/log retained; no native completed run inferred'])
    for path in sorted(report.rglob('*')):
        if path.is_file():
            pmem(root, ['track', path.relative_to(root).as_posix(), '--update'])


def finalize(root, exports):
    capture_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    relative = 'collection_capture/' + capture_id
    command = ['run', '--name', 'V13R1 collect evidence verification', '--seed', '42', '--',
               sys.executable, str(Path(__file__).resolve()), 'capture', '--root', str(root),
               '--report', relative]
    result = pmem(root, command, output=True)
    print(result, end='')
    if not re.search(r'(?m)^Run run_[0-9a-f]+ success$', result):
        raise ValueError('Projmem capture validation failed; no collect-ready declaration')
    report = root / relative
    native_index(root, report)
    for name in ['NATIVE_RUN_LINKS.json', 'NATIVE_RUN_INDEX.csv']:
        pmem(root, ['track', relative + '/' + name, '--update'])
    pmem(root, ['export-bundle', '--out', relative + '/projmem-development-bundle.json'])
    export = pmem(root, ['export', '--json'], output=True)
    (report / 'projmem-project-export.json').write_text(export)
    write(report / 'toolchain.json', {'python': sys.version, 'projmem': pmem(root, ['--version'], output=True).strip()})
    result = seal(root, exports, capture_id)
    print(json.dumps(result, indent=2))
    print('COLLECT_READY=YES')
    print('ALETHEIA_ACCEPTANCE=PENDING_REVIEW')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare', 'capture', 'finalize'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--uploads', type=Path)
    parser.add_argument('--attempt')
    parser.add_argument('--report')
    parser.add_argument('--exports', type=Path, default=Path('/workspace/exports'))
    args = parser.parse_args()
    root = args.root.resolve()
    if args.stage == 'prepare':
        if not args.uploads or not args.attempt or Path(args.attempt).name != args.attempt:
            parser.error('prepare requires uploads and a safe attempt id')
        prepare(root, args.uploads, args.attempt)
    elif args.stage == 'capture':
        if not args.report or Path(args.report).is_absolute() or '..' in Path(args.report).parts:
            parser.error('capture requires a project-relative report')
        capture(root, root / args.report)
    else:
        finalize(root, args.exports)


if __name__ == '__main__':
    main()
