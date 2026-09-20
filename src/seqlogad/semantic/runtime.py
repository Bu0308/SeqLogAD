"""Colab environment validation and reproducibility records; never print secrets."""
import importlib.metadata as md
import json
import platform
import subprocess
import sys
from pathlib import Path


def install_missing(repo_root):
    import yaml
    from packaging.version import Version
    base = yaml.safe_load((Path(repo_root) / 'configs/models/base-freeze-v1.yaml').read_text())['base_freeze']
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('Select a Python 3.12 Colab runtime; frozen environment must not silently change')
    missing = []
    for name, wanted in base['runtime']['pins'].items():
        try:
            actual = md.version(name)
        except md.PackageNotFoundError:
            missing.append(f'{name}=={wanted}'); continue
        if Version(actual).base_version != wanted:
            raise RuntimeError(f'{name}={actual}; requires {wanted}. Create the isolated environment described in notebook.')
    if missing:
        subprocess.run([sys.executable, '-m', 'pip', 'install', *missing,
            '--extra-index-url', base['runtime']['torch_index']], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'check'], check=True)


def environment():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('Enable an NVIDIA CUDA GPU runtime')
    free, total = torch.cuda.mem_get_info()
    return {'python': platform.python_version(), 'platform': platform.platform(),
        'packages': {d.metadata['Name']: d.version for d in md.distributions()},
        'torch': torch.__version__, 'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(),
        'free_vram_bytes': free, 'total_vram_bytes': total,
        'native_bf16': torch.cuda.is_bf16_supported(including_emulation=False)}


def seed_all(seed):
    import random
    import torch
    random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True, warn_only=True)


def export_environment(directory):
    from .contracts import dump
    directory = Path(directory)
    dump(directory / 'environment.json', environment())
    frozen = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode()
    (directory / 'dependency-lock.txt').write_text(frozen)
    report = subprocess.check_output([sys.executable, '-m', 'pip', 'inspect']).decode()
    (directory / 'install-report.json').write_text(report)
