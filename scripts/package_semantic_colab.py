"""Create a small code/config upload bundle, never raw logs, labels or credentials."""
from pathlib import Path
import json
import shutil
import stat
import tempfile
import zipfile
from seqlogad.common.checksum import sha256_file
from seqlogad.semantic.contracts import dump
from seqlogad.semantic.prepare import git_state


def package(root=Path('.'), destination=Path('outputs/colab/seqlogad_code')):
    root = root.resolve()
    if destination.exists():
        raise ValueError('package destination exists; use a new output path')
    destination.mkdir(parents=True)
    paths = [root / 'pyproject.toml', root / 'configs/models/base-freeze-v1.yaml',
             root / 'configs/models/semantic-v1.yaml', root / 'src/seqlogad/__init__.py',
             root / 'src/seqlogad/common/__init__.py', root / 'src/seqlogad/common/checksum.py']
    paths += list((root / 'src/seqlogad/semantic').glob('*.py'))
    paths += list((root / 'src/seqlogad/protocol').glob('*.py'))
    for source in paths:
        target = destination / source.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    files = {p.relative_to(destination).as_posix(): sha256_file(p) for p in destination.rglob('*') if p.is_file()}
    dump(destination / 'CODE_PROVENANCE.json', {'git': git_state(root), 'files': files})
    shutil.make_archive(str(destination), 'zip', destination.parent, destination.name)
    return destination


def verify_archive(archive, expected_root, verify_code=False):
    with tempfile.TemporaryDirectory() as folder:
        with zipfile.ZipFile(archive) as handle:
            names = handle.namelist()
            if len(names) != len(set(names)) or any(Path(name).is_absolute() or '..' in Path(name).parts for name in names):
                raise ValueError('unsafe or duplicate archive member')
            if any(((info.external_attr >> 16) & 0o170000) == stat.S_IFLNK for info in handle.infolist()):
                raise ValueError('archive symlink forbidden')
            handle.extractall(folder)
        root = Path(folder) / expected_root
        if not root.is_dir():
            raise ValueError('archive root mismatch')
        if verify_code:
            provenance = json.loads((root / 'CODE_PROVENANCE.json').read_text())['files']
            actual = {path.relative_to(root).as_posix(): sha256_file(path) for path in root.rglob('*')
                      if path.is_file() and path.name != 'CODE_PROVENANCE.json'}
            if provenance != actual:
                raise ValueError('code provenance mismatch')
        return len([path for path in root.rglob('*') if path.is_file()])


def package_final(root=Path('.')):
    root = root.resolve()
    data_zip = root / 'outputs/colab/phase2-final.zip'
    if not data_zip.is_file():
        raise ValueError('final data package is missing; data is unchanged, rebuild it explicitly only if required')
    with tempfile.TemporaryDirectory() as folder:
        code_root = Path(folder) / 'seqlogad_code'
        package(root, code_root)
        generated = code_root.with_suffix('.zip')
        code_zip = root / 'outputs/colab/seqlogad-code-final.zip'
        shutil.copyfile(generated, code_zip)
    verify_archive(data_zip, 'phase2')
    verify_archive(code_zip, 'seqlogad_code', verify_code=True)
    return {'data': str(data_zip), 'data_sha256': sha256_file(data_zip),
            'data_rebuilt': False, 'code': str(code_zip), 'code_sha256': sha256_file(code_zip)}


if __name__ == '__main__':
    print(package_final())
