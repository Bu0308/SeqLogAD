"""Seal a private training capture after the final Projmem run has returned."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tarfile


def stream_hash(handle):
    h = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b''):
        h.update(chunk)
    return h.hexdigest()


def sha(path):
    with Path(path).open('rb') as handle:
        return stream_hash(handle)


def seal(root, exports, capture_id):
    root, exports = Path(root).resolve(), Path(exports).resolve()
    if exports == root or root in exports.parents:
        raise ValueError('Export archive must be outside the persistence directory')
    report = root / 'collection_capture' / capture_id
    snapshot = report / 'pmem-snapshot.db'
    db = root / '.pmem/pmem.db'
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as source:
        if source.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Projmem DB integrity failed')
        with sqlite3.connect(snapshot) as dest:
            source.backup(dest)
    with sqlite3.connect(snapshot.as_uri() + '?mode=ro', uri=True) as dest:
        if dest.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('SQLite snapshot integrity failed')
    inventory = report / 'FILE_INVENTORY.json'
    files = [p for p in sorted(root.rglob('*')) if p.is_file() and p != inventory]
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('Persistence contains a symlink; explicit review needed')
    rows = [{'path': p.relative_to(root).as_posix(), 'size': p.stat().st_size,
             'sha256': sha(p)} for p in files]
    inventory.write_text(json.dumps({'schema': 'SEQLOGAD-PRIVATE-CAPTURE-INVENTORY-1',
        'privacy': 'RESTRICTED_NOT_PUBLIC_REVIEWED', 'files': rows}, indent=2) + '\n')
    exports.mkdir(parents=True, exist_ok=True)
    out = exports / ('SeqLogAD_sequence-v13r1_FULL_' + capture_id + '.tar.gz')
    partial = Path(str(out) + '.partial')
    with tarfile.open(partial, 'w:gz') as handle:
        handle.add(root, arcname='sequence-v13r1')
    verify_archive(partial, rows, inventory.relative_to(root).as_posix())
    partial.replace(out)
    digest = sha(out)
    Path(str(out) + '.sha256').write_text(digest + '  ' + out.name + '\n')
    return {'archive': str(out), 'sha256': digest, 'files_verified': len(rows) + 1,
            'sqlite_snapshot': str(snapshot)}


def verify_archive(archive, rows, inventory_path):
    expected = {'sequence-v13r1/' + r['path']: r for r in rows}
    with tarfile.open(archive, 'r:gz') as handle:
        names = [m.name for m in handle.getmembers() if m.isfile()]
        if set(names) != set(expected) | {'sequence-v13r1/' + inventory_path}:
            raise ValueError('Archive file inventory mismatch')
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive members')
        for name, row in expected.items():
            with handle.extractfile(name) as member:
                if stream_hash(member) != row['sha256']:
                    raise ValueError('Archive bytes changed: ' + name)
