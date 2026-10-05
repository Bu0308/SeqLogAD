"""V13 notebook must bind the labeled sidecar and keep F1 selection explicit."""
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_p22_v13_runpod_notebook import build_v13_notebook  # noqa: E402
from build_p22_v13r1_runpod_notebook import build_r1_notebook
from build_p22_v13r1_runpod_notebook import JOURNAL


def test_v13_notebook_compiles_and_binds_source_development(tmp_path):
    paths = [tmp_path / name for name in ("code.zip", "data.zip", "labels.zip", "pmem.whl")]
    for path in paths:
        path.write_bytes(path.name.encode())
    notebook = build_v13_notebook(*paths[:3], paths[3], "a" * 64)
    code = "\n".join("".join(cell["source"]) for cell in notebook["cells"]
                     if cell["cell_type"] == "code")
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"v13-cell-{index}", "exec")
    assert '"--sequence-candidate", "v13"' in code
    assert '"--source-development-root", SOURCE_DEVELOPMENT_ROOT' in code
    assert '"--metric", "source_development_macro_f1"' in code
    assert '"--metric-direction", "max"' in code
    assert '"source_dev_sha256": EXPECTED_SOURCE_DEVELOPMENT_ZIP_SHA256' in code
    assert 'SAFE_TO_STOP_RUNTIME=YES' in code


def test_r1_notebook_isolated_identity_and_durable_capture(tmp_path):
    paths = [tmp_path / name for name in ('code.zip', 'data.zip', 'labels.zip', 'pmem.whl')]
    for path in paths:
        path.write_bytes(path.name.encode())
    notebook = build_r1_notebook(*paths[:3], paths[3], 'a' * 64)
    code = '\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code')
    for index, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), f'r1-cell-{index}', 'exec')
    assert '"--sequence-candidate", "v13r1"' in code
    assert 'PERSISTENT_ROOT = STATE_ROOT / "sequence-v13r1"' in code
    assert '"--metrics"' in code and 'durable_attempt' in code
    assert code.index('journal("STARTED")') < code.index('run_live(["nvidia-smi"])')
    assert code.index('"--tag", "attempt-start"') < code.index('"torch==2.9.1"')
    assert 'SOURCE_DEVELOPMENT_ROOT = str(RUNTIME_ROOT / "phase2_source_development_v13r1")' in code
    assert code.count('"init", "--name", "SeqLogAD Sequence V13R1"') == 1


def test_durable_journal_contains_parseable_json_lines(tmp_path):
    import json
    import os
    ns = {'PERSISTENT_ROOT': tmp_path, 'SESSION_ROOT': Path('session'), 'os': os}
    exec(JOURNAL, ns)
    ns['journal']('TEST')
    rows = [json.loads(line) for line in ns['JOURNAL_PATH'].read_text().splitlines()]
    assert [row['event'] for row in rows] == ['STARTED', 'TEST']
