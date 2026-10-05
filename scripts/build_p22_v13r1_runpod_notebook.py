"""Audited V13R1 notebook with durable attempt evidence and numeric DB metrics."""
import json
from pathlib import Path

from build_p22_v13_runpod_notebook import build_v13_notebook, _replace_once


NOTEBOOK_NAME = "P2.2_run_all_sequence_lora_s42_v13r1.ipynb"
JOURNAL = r'''
# Journal exists before runtime setup, including failures before Projmem installs.
import json, datetime, traceback
ATTEMPT_ROOT = PERSISTENT_ROOT / "attempts" / SESSION_ROOT.name
ATTEMPT_ROOT.mkdir(parents=True, exist_ok=False)
JOURNAL_PATH = ATTEMPT_ROOT / "lifecycle.jsonl"

def journal(event, detail=""):
    token = os.environ.get("HF_TOKEN")
    if token:
        detail = detail.replace(token, "[TOKEN_HIDDEN]")
    with JOURNAL_PATH.open("a") as handle:
        handle.write(json.dumps({"event": event, "detail": detail,
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}) + "\n")
        handle.flush()
        os.fsync(handle.fileno())

journal("STARTED")
'''
PMEM_INIT = r'''
run_live([PYTHON, "-m", "pip", "install", str(pmem_wheel)])
pmem_cli = str(VENV / "bin/pmem")
run_live([pmem_cli, "init", "--name", "SeqLogAD Sequence V13R1",
          "--metric", "source_development_macro_f1", "--metric-direction", "max"],
         cwd=str(PERSISTENT_ROOT))
for prior in sorted((PERSISTENT_ROOT / "attempts").glob("*/lifecycle.jsonl")):
    stamp = prior.parent / "journal-registered"
    if stamp.exists() or prior == JOURNAL_PATH:
        continue
    run_live([pmem_cli, "track", str(prior.relative_to(PERSISTENT_ROOT)), "--update"],
             cwd=str(PERSISTENT_ROOT))
    run_live([pmem_cli, "note", "Recovered prior attempt journal: " + str(prior.parent.name)
              + "; inspect final event and training-state.json. No completion is inferred.",
              "--tag", "recovered-attempt"], cwd=str(PERSISTENT_ROOT))
    stamp.write_text("registered\n")
run_live([pmem_cli, "note", "Attempt started: " + SESSION_ROOT.name,
          "--tag", "attempt-start"], cwd=str(PERSISTENT_ROOT))
journal("PROJMEM_INITIALIZED")
'''


def guarded(source, phase):
    prefix = f'journal("{phase}_STARTED")\ntry:\n'
    body = "\n".join("    " + line for line in source.splitlines())
    suffix = f'''
except BaseException:
    journal("{phase}_FAILED", traceback.format_exc())
    if "pmem_cli" in globals() and Path(pmem_cli).is_file():
        run_live([pmem_cli, "note", "Attempt " + SESSION_ROOT.name + " failed in {phase}; see durable journal.",
                  "--tag", "attempt-failure"], check=False, cwd=str(PERSISTENT_ROOT))
    raise
journal("{phase}_COMPLETED")
'''
    return prefix + body + suffix


def build_r1_notebook(code_zip, data_zip, label_zip, pmem_wheel, label_manifest_sha256):
    notebook = build_v13_notebook(code_zip, data_zip, label_zip, pmem_wheel, label_manifest_sha256)
    sources = ["".join(cell["source"]) for cell in notebook["cells"]]
    # Only runtime identities change; uploaded filenames already carry R1.
    sources = [s.replace('"sequence-v13"', '"sequence-v13r1"')
                .replace('/sequence-v13/', '/sequence-v13r1/')
                .replace('phase2_source_development_v13', 'phase2_source_development_v13r1')
                .replace('"v13",', '"v13r1",')
                .replace('Sequence V13', 'Sequence V13R1')
                .replace('Candidate v1.3', 'Candidate v1.3.1') for s in sources]
    sources[1] += JOURNAL
    marker = 'run_live([PYTHON, "-m", "pip", "install", "torch==2.9.1", "--index-url",'
    sources[5] = _replace_once(sources[5], marker, PMEM_INIT + '\n' + marker)
    # Duplicate wheel installation is harmless but unnecessary.
    last_install = 'run_live([PYTHON, "-m", "pip", "install", str(pmem_wheel)])'
    pos = sources[5].rfind(last_install)
    sources[5] = sources[5][:pos] + sources[5][pos:].replace(last_install, '', 1)
    old_init = '''pmem_cli = str(VENV / "bin/pmem")
run_live([pmem_cli, "init", "--name", "SeqLogAD Sequence V13R1",
          "--metric", "source_development_macro_f1",
          "--metric-direction", "max"], cwd=str(PERSISTENT_ROOT))
'''
    sources[9] = _replace_once(sources[9], old_init, '')
    old = '[pmem_cli, "run", "--name", "P2.2 Sequence V13R1 RunPod attempt",\n     "--seed", "42", "--", *args]'
    new = '''[pmem_cli, "run", "--name", "P2.2 Sequence V13R1 RunPod attempt",
     "--seed", "42", "--metrics", str((ATTEMPT_ROOT / "metrics.json").relative_to(PERSISTENT_ROOT)),
     "--", PYTHON, "-m", "seqlogad.phase2_execution.durable_attempt",
     "--attempt", str(ATTEMPT_ROOT), "--persistent-root", str(PERSISTENT_ROOT), "--", *args]'''
    sources[9] = _replace_once(sources[9], old, new)
    sources[11] += '\njournal("COMPLETED")\nrun_live([pmem_cli, "track", str(JOURNAL_PATH.relative_to(PERSISTENT_ROOT)), "--update"], cwd=str(PERSISTENT_ROOT))\n'
    for index, phase in ((3, 'UV'), (5, 'SETUP'), (7, 'AUTH'), (9, 'TRAIN'), (11, 'EXPORT')):
        sources[index] = guarded(sources[index], phase)
    sources[0] += "\nV13R1 records source-development metrics in Projmem. Keep the entire persistent directory, including `.pmem`, `attempts` and exports. Before Projmem installs, failures are retained in the journal and registered on the next successful setup. Live progress is in `attempts/<id>/training.log`.\n"
    for cell, source in zip(notebook['cells'], sources, strict=True):
        cell['source'] = source.splitlines(keepends=True)
    return notebook


def write_r1_notebook(root, code_zip, data_zip, label_zip, pmem_wheel, label_manifest_sha256):
    path = Path(root) / 'notebooks' / NOTEBOOK_NAME
    path.write_text(json.dumps(build_r1_notebook(code_zip, data_zip, label_zip, pmem_wheel,
                                               label_manifest_sha256), indent=1) + '\n')
    return path
