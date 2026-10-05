import json
from pathlib import Path
import sys
import zipfile

from seqlogad.phase2_execution.durable_attempt import collect_metrics, execute


def test_attempt_streams_redacted_logs_and_records_failed_exit(tmp_path, monkeypatch):
    monkeypatch.setenv('HF_TOKEN', 'fixture-secret')
    attempt = tmp_path / 'attempt'
    code = execute([sys.executable, '-c', 'print("fixture-secret"); raise SystemExit(7)'],
                   attempt, tmp_path)
    assert code == 7
    assert 'fixture-secret' not in (attempt / 'training.log').read_text()
    assert '[TOKEN_HIDDEN]' in (attempt / 'training.log').read_text()
    assert json.loads((attempt / 'training-state.json').read_text())['status'] == 'FAILED'
    assert json.loads((attempt / 'metrics.json').read_text()) == {}


def test_structured_metrics_are_from_selected_checkpoint_and_separate_folds(tmp_path):
    directory = tmp_path / 'P2.2/targets'
    directory.mkdir(parents=True)
    for target, f1 in [('BGL', 0.2), ('HDFS', 0.4), ('HADOOP', 0.6)]:
        with zipfile.ZipFile(directory / f'P2.2_{target}_S42.zip', 'w') as archive:
            archive.writestr('run/metrics.json', json.dumps({
                'source_development_best': {'macro_f1': f1, 'macro_recall': 0.8},
                'step': 100}))
    actual = collect_metrics(tmp_path)
    assert abs(actual['source_development_macro_f1'] - 0.4) < 1e-12
    assert actual['BGL_source_development_macro_recall'] == 0.8
