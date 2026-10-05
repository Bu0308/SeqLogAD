"""Create the isolated F1-selected Sequence V13 notebook from the V12 runtime flow."""
from __future__ import annotations

import json
from pathlib import Path

from build_p22_runpod_notebook import build_notebook
from seqlogad.common.checksum import sha256_file


NOTEBOOK_NAME = "P2.2_run_all_sequence_lora_s42_v13.ipynb"


def _replace_once(value: str, old: str, new: str) -> str:
    if value.count(old) != 1:
        raise ValueError(f"V13 notebook template drift: {old!r}")
    return value.replace(old, new)


def build_v13_notebook(code_zip: Path, data_zip: Path, label_zip: Path,
                       pmem_wheel: Path, label_manifest_sha256: str) -> dict:
    notebook = build_notebook(code_zip, data_zip, pmem_wheel)
    sources = ["".join(cell["source"]) for cell in notebook["cells"]]
    sources = [source.replace("V12", "V13").replace("v12", "v13").replace("v1.2", "v1.3")
               for source in sources]
    code_hash = sha256_file(code_zip)
    data_hash = sha256_file(data_zip)
    label_hash = sha256_file(label_zip)
    sources[0] = _replace_once(
        sources[0], f"`{data_zip.name}` and `{pmem_wheel.name}`",
        f"`{data_zip.name}`, `{label_zip.name}` and `{pmem_wheel.name}`",
    )
    sources[1] = _replace_once(
        sources[1], f"{code_hash[:12]}-{data_hash[:12]}",
        f"{code_hash[:12]}-{data_hash[:12]}-{label_hash[:12]}",
    )
    sources[1] = _replace_once(
        sources[1], 'DATA_ROOT = str(RUNTIME_ROOT / "phase2_sequence")',
        'DATA_ROOT = str(RUNTIME_ROOT / "phase2_sequence")\n'
        'SOURCE_DEVELOPMENT_ROOT = str(RUNTIME_ROOT / "phase2_source_development_v13")\n'
        f'EXPECTED_SOURCE_DEVELOPMENT_ZIP_SHA256 = {label_hash!r}\n'
        f'EXPECTED_SOURCE_DEVELOPMENT_MANIFEST_SHA256 = {label_manifest_sha256!r}',
    )
    sources[5] = _replace_once(
        sources[5], 'pmem_wheel = locate(EXPECTED_PMEM_WHEEL_SHA256, "*.whl")',
        'pmem_wheel = locate(EXPECTED_PMEM_WHEEL_SHA256, "*.whl")\n'
        'label_zip = locate(EXPECTED_SOURCE_DEVELOPMENT_ZIP_SHA256)',
    )
    sources[5] = _replace_once(
        sources[5], '"data_sha256": EXPECTED_DATA_ZIP_SHA256}',
        '"data_sha256": EXPECTED_DATA_ZIP_SHA256, '
        '"source_dev_sha256": EXPECTED_SOURCE_DEVELOPMENT_ZIP_SHA256}',
    )
    sources[5] = _replace_once(
        sources[5], '    safe_extract(data_zip, partial)',
        '    safe_extract(data_zip, partial)\n'
        '    safe_extract(label_zip, partial)',
    )
    sources[5] = _replace_once(
        sources[5], '    assert (partial / "phase2_sequence/manifests/bundle.json").is_file()',
        '    assert (partial / "phase2_sequence/manifests/bundle.json").is_file()\n'
        '    assert (partial / "phase2_source_development_v13/manifest.json").is_file()',
    )
    sources[5] = _replace_once(
        sources[5], 'assert Path(DATA_ROOT, "manifests/bundle.json").is_file()',
        'assert Path(DATA_ROOT, "manifests/bundle.json").is_file()\n'
        'assert digest(Path(SOURCE_DEVELOPMENT_ROOT) / "manifest.json") == '
        'EXPECTED_SOURCE_DEVELOPMENT_MANIFEST_SHA256',
    )
    sources[9] = _replace_once(
        sources[9], '"--metric", "source_validation_next_log_nll",\n'
        '          "--metric-direction", "min"',
        '"--metric", "source_development_macro_f1",\n'
        '          "--metric-direction", "max"',
    )
    sources[9] = _replace_once(
        sources[9], '    "--expected-bundle-sha256", EXPECTED_BUNDLE_SHA256,',
        '    "--expected-bundle-sha256", EXPECTED_BUNDLE_SHA256,\n'
        '    "--sequence-candidate", "v13",\n'
        '    "--source-development-root", SOURCE_DEVELOPMENT_ROOT,\n'
        '    "--expected-source-development-sha256", '
        'EXPECTED_SOURCE_DEVELOPMENT_MANIFEST_SHA256,',
    )
    for cell, source in zip(notebook["cells"], sources, strict=True):
        cell["source"] = source.splitlines(keepends=True)
    return notebook


def write_v13_notebook(root: Path, code_zip: Path, data_zip: Path,
                       label_zip: Path, pmem_wheel: Path,
                       label_manifest_sha256: str) -> Path:
    path = root / "notebooks" / NOTEBOOK_NAME
    path.write_text(json.dumps(build_v13_notebook(
        code_zip, data_zip, label_zip, pmem_wheel, label_manifest_sha256
    ), indent=1) + "\n")
    return path
