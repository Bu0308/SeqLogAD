"""Adapter-only checkpoints and strict continuation identity. Never save base weights."""
from pathlib import Path
import shutil
from .contracts import dump, read
from seqlogad.common.checksum import sha256_file


def seal(directory):
    directory = Path(directory)
    files = {p.relative_to(directory).as_posix(): sha256_file(p) for p in directory.rglob('*')
             if p.is_file() and p.relative_to(directory).as_posix() != 'checksums.sha256'}
    (directory / 'checksums.sha256').write_text(''.join(f'{v}  {k}\n' for k, v in sorted(files.items())))
    return files


def verify_seal(directory, require_nested_ledgers=False):
    """Verify an exhaustive tree ledger; FINAL runs must cover nested ledgers."""
    directory = Path(directory)
    ledger = directory / 'checksums.sha256'
    entries = ledger.read_text().splitlines()
    names = set()
    for line in entries:
        digest, name = line.split('  ', 1)
        from .contracts import safe_path
        path = safe_path(directory, name)
        if not path.is_file() or sha256_file(path) != digest:
            raise ValueError('run checksum mismatch')
        if name in names:
            raise ValueError('duplicate run checksum entry')
        names.add(name)
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*')
              if p.is_file() and p != ledger}
    if names != actual:
        raise ValueError('run ledger incomplete/unexpected files')
    nested = {name for name in actual if name.endswith('/checksums.sha256')}
    if require_nested_ledgers and not nested:
        raise ValueError('final run ledger must directly cover nested checksum ledgers')
    return {'files': len(names), 'nested_ledgers': sorted(nested)}


def verify_checkpoint(directory, identity):
    directory = Path(directory)
    if read(directory / 'manifest.json')['identity'] != identity:
        raise ValueError('resume identity mismatch (base/config/fold/data)')
    entries = (directory / 'checksums.sha256').read_text().splitlines()
    names = set()
    for line in entries:
        digest, name = line.split('  ', 1)
        from .contracts import safe_path
        path = safe_path(directory, name)
        if sha256_file(path) != digest:
            raise ValueError('checkpoint checksum mismatch')
        names.add(name)
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    if names | {'checksums.sha256'} != actual or not {'adapter/adapter_model.safetensors', 'state.pt', 'manifest.json'} <= names:
        raise ValueError('checkpoint incomplete/unexpected files')
    return read(directory / 'manifest.json')


def save_checkpoint(model, optimizer, scaler, directory, step, identity, best,
                    early_stopping=None, scheduler_state=None, adapter_name='semantic'):
    import torch
    import random
    directory = Path(directory)
    temporary = directory.with_name(directory.name + '.partial')
    temporary.mkdir(parents=True, exist_ok=False)
    model.save_pretrained(temporary / 'peft', safe_serialization=True, selected_adapters=[adapter_name])
    source = temporary / f'peft/{adapter_name}'
    if not source.exists():
        source = temporary / 'peft'
    shutil.copytree(source, temporary / 'adapter')
    shutil.rmtree(temporary / 'peft')
    torch.save({'step': step, 'optimizer': optimizer.state_dict(), 'scaler': scaler.state_dict(),
                'torch_rng': torch.get_rng_state(), 'cuda_rng': torch.cuda.get_rng_state_all(),
                'python_rng': random.getstate(), 'best': best,
                'early_stopping': early_stopping or {},
                'scheduler': scheduler_state or {}}, temporary / 'state.pt')
    dump(temporary / 'manifest.json', {'identity': identity, 'step': step, 'best': best,
         'early_stopping': early_stopping or {}, 'scheduler': scheduler_state or {},
         'adapter': adapter_name, 'base_weights_saved': False})
    seal(temporary)
    temporary.rename(directory)
    return directory
