#!/bin/bash
set -uo pipefail
cd /workspace/fusion
POD_ID=$(tr "\0" "\n" < /proc/1/environ | sed -n "s/^RUNPOD_POD_ID=//p")
# cost guard: the pod stops itself 4 h after the chain starts, whatever happens
(setsid nohup bash -c "sleep 14400; runpodctl pod stop $POD_ID || runpodctl stop pod $POD_ID" > setup/guard.log 2>&1 < /dev/null &)
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
STAMP=$(date -u +%Y%m%dT%H%M%SZ); RB=runs/E4-BGL-$STAMP; RH=runs/E4-HDFS-$STAMP; echo "RUNS=$RB $RH"
score() {  # name, out, inputs, bundle, sidecar, folds
  $PY -m pmem run --name "$1" --seed 42 --artifact "$2/confirm_manifest.json" -- \
    env PYTHONPATH=$CODE/src $PY -m seqlogad.fusion.run_confirm --repo $CODE --inputs /workspace/fusion/inputs \
    --confirm-inputs "$3" --bundle-name "$4" --sidecar-name "$5" --folds "$6" --dedupe \
    --artifacts /workspace/fusion/kit/artifacts --out "/workspace/fusion/$2" --config $CODE/configs/fusion/fusion-e1.yaml \
    || { echo "SCORING_FAILED $1"; exit 1; }
  grep -q '"pass": false' "$2/confirm_manifest.json" && { echo "ANCHOR_OR_DEDUPE_FAILED $1"; exit 1; }
  echo "SCORED $1 $(date -u +%T)"
}
score "FUSION-E4 scoring BGL" $RB /workspace/fusion/e4/bgl phase2_sequence_confirm source_dev_confirm FOLD-TARGET-ARCH-HDFS,FOLD-TARGET-ARCH-HADOOP
score "FUSION-E4 scoring HDFS" $RH /workspace/fusion/e4/hdfs phase2_sequence_blocks source_dev_blocks FOLD-TARGET-ARCH-HADOOP
$PY -m pmem run --name "FUSION-E4 gated evaluation" --seed 42 --artifact "runs/E4-results-$STAMP.json" -- \
  env PYTHONPATH=$CODE/src $PY -m seqlogad.fusion.gated_eval --run-bgl /workspace/fusion/$RB --run-hdfs /workspace/fusion/$RH \
  --e4-inputs /workspace/fusion/e4 --original-bundle /workspace/fusion/inputs/phase2_sequence \
  --out /workspace/fusion/runs/E4-results-$STAMP.json || { echo EVAL_FAILED; exit 1; }
echo "CHAIN_COMPLETE $(date -u +%T) runs/E4-results-$STAMP.json"
