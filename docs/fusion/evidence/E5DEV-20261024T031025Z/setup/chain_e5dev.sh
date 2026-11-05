#!/bin/bash
set -uo pipefail
cd /workspace/fusion
POD_ID=$(tr "\0" "\n" < /proc/1/environ | sed -n "s/^RUNPOD_POD_ID=//p")
(setsid nohup bash -c "sleep 10800; runpodctl pod stop $POD_ID || runpodctl stop pod $POD_ID" > setup/guard.log 2>&1 < /dev/null &)
until grep -q VENV_DONE setup/venv.log 2>/dev/null; do sleep 15; done
echo "VENV_READY $(date -u +%T)"
venv/bin/pip install -q kit/inputs/projmem-0.4.0a1-py3-none-any.whl && echo DEPS_INSTALLED
export HF_TOKEN=$(tr "\0" "\n" < /proc/1/environ | sed -n "s/^HF_TOKEN=//p") HF_HOME=/workspace/hf-cache PYTHONDONTWRITEBYTECODE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
PY=/workspace/fusion/venv/bin/python; CODE=/workspace/fusion/kit/code
mkdir -p inputs; for z in phase2-sequence-s42 phase2-final phase2-source-development-v13r1; do unzip -q -o kit/inputs/$z.zip -d inputs; done; echo INPUTS_READY
(cd e4 && sha256sum -c SHA256SUMS --quiet) && echo E4_INPUTS_SHA256=PASS || { echo E4_INPUTS_FAILED; exit 1; }
(cd $CODE && PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider tests/fusion 2>&1 | tail -1)
(cd $CODE && PYTHONPATH=src $PY -c "from seqlogad.sequence.implementation import implementation_digest as d; assert d('.')=='78a188515d5a74b4ca1bf9c5b763e6e92281ba5746ff22c29e488dbf93dce3e3'; print('IMPLEMENTATION=PASS')") || { echo IMPLEMENTATION_FAILED; exit 1; }
[ -d .pmem ] || $PY -m pmem init >/dev/null
STAMP=$(date -u +%Y%m%dT%H%M%SZ); RB=runs/E5DEV-BGL-$STAMP; RH=runs/E5DEV-HDFS-$STAMP; echo "RUNS=$RB $RH"
anchor_ok() { $PY -c "import json,sys;d=json.load(open('$1/confirm_manifest.json'));sys.exit(0 if all(v['pass'] for e in d['anchor'].values() for v in e.values()) else 1)"; }
score() {  # name, out, inputs, bundle, sidecar, folds
  $PY -m pmem run --name "$1" --seed 42 --artifact "$2/confirm_manifest.json" -- \
    env PYTHONPATH=$CODE/src $PY -m seqlogad.fusion.run_confirm --repo $CODE --inputs /workspace/fusion/inputs \
    --confirm-inputs "$3" --bundle-name "$4" --sidecar-name "$5" --folds "$6" --dedupe --semantic-kinds semantic,semantic_template \
    --artifacts /workspace/fusion/kit/artifacts --out "/workspace/fusion/$2" --config $CODE/configs/fusion/fusion-e1.yaml \
    || { echo "SCORING_FAILED $1"; exit 1; }
  anchor_ok "$2" || { echo "ANCHOR_FAILED $1"; exit 1; }
  echo "SCORED $1 $(date -u +%T)"
}
score "FUSION-E5DEV scoring BGL" $RB /workspace/fusion/e4/bgl phase2_sequence_confirm source_dev_confirm FOLD-TARGET-ARCH-HDFS,FOLD-TARGET-ARCH-HADOOP
score "FUSION-E5DEV scoring HDFS" $RH /workspace/fusion/e4/hdfs phase2_sequence_blocks source_dev_blocks FOLD-TARGET-ARCH-HADOOP
$PY - "$RB" "$RH" <<'PYEOF'
import gzip, json, re, sys
from pathlib import Path
out = {}
for run in sys.argv[1:]:
    for f in sorted(Path(run, "scores").glob("*.jsonl")):
        if not re.search(r"(sequence_\w+_best|_best_mkmean|_best_mk42)\.jsonl$", f.name):
            continue
        rows = [json.loads(l) for l in f.read_text().splitlines()]
        out[f"{Path(run).name}/{f.stem}"] = {r["window_id"]: (r["nll_mean"] if r["status"] != "ABSTAIN" else None) for r in rows}
    out[f"{Path(run).name}/manifest"] = json.loads(Path(run, "confirm_manifest.json").read_text())
with gzip.open("/workspace/fusion/runs/E5DEV-compact.json.gz", "wt") as fh:
    json.dump(out, fh)
print("EXPORT_KEYS", len(out))
PYEOF
sha256sum runs/E5DEV-compact.json.gz && ls -la runs/E5DEV-compact.json.gz
echo "CHAIN_COMPLETE $(date -u +%T)"
