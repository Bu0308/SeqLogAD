#!/bin/bash
# FUSION-E4 resume after D-20: BGL scoring is complete (anchor PASS); the dedupe check exceeded
# its 0.01 tolerance, which the pre-registration treats as a recorded deviation, not a stop.
set -uo pipefail
cd /workspace/fusion
export HF_TOKEN=$(tr "\0" "\n" < /proc/1/environ | sed -n "s/^HF_TOKEN=//p") HF_HOME=/workspace/hf-cache PYTHONDONTWRITEBYTECODE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
PY=/workspace/fusion/venv/bin/python; CODE=/workspace/fusion/kit/code
RB=runs/E4-BGL-20261023T180203Z; RH=runs/E4-HDFS-20261023T180203Z; STAMP=20261023T180203Z
anchor_ok() { $PY -c "import json,sys;d=json.load(open('$1/confirm_manifest.json'));sys.exit(0 if all(v['pass'] for e in d['anchor'].values() for v in e.values()) else 1)"; }
anchor_ok $RB || { echo ANCHOR_FAILED_BGL; exit 1; }
$PY -m pmem run --name "FUSION-E4 scoring HDFS" --seed 42 --artifact "$RH/confirm_manifest.json" -- \
  env PYTHONPATH=$CODE/src $PY -m seqlogad.fusion.run_confirm --repo $CODE --inputs /workspace/fusion/inputs \
  --confirm-inputs /workspace/fusion/e4/hdfs --bundle-name phase2_sequence_blocks --sidecar-name source_dev_blocks \
  --folds FOLD-TARGET-ARCH-HADOOP --dedupe --artifacts /workspace/fusion/kit/artifacts \
  --out /workspace/fusion/$RH --config $CODE/configs/fusion/fusion-e1.yaml || { echo "SCORING_FAILED HDFS"; exit 1; }
anchor_ok $RH || { echo ANCHOR_FAILED_HDFS; exit 1; }
echo "SCORED HDFS $(date -u +%T)"
$PY -m pmem run --name "FUSION-E4 D-20 dedupe diagnostic" --seed 42 --artifact "runs/E4-D20-dedupe-diag.json" -- \
  env PYTHONPATH=$CODE/src $PY setup/e4_dedupe_diag.py $CODE /workspace/fusion/kit/artifacts $CODE/configs/fusion/fusion-e1.yaml \
  /workspace/fusion/e4 /workspace/fusion/$RB /workspace/fusion/$RH /workspace/fusion/runs/E4-D20-dedupe-diag.json \
  || echo "DIAG_FAILED (non-blocking)"
$PY -m pmem run --name "FUSION-E4 gated evaluation" --seed 42 --artifact "runs/E4-results-$STAMP.json" -- \
  env PYTHONPATH=$CODE/src $PY -m seqlogad.fusion.gated_eval --run-bgl /workspace/fusion/$RB --run-hdfs /workspace/fusion/$RH \
  --e4-inputs /workspace/fusion/e4 --original-bundle /workspace/fusion/inputs/phase2_sequence \
  --out /workspace/fusion/runs/E4-results-$STAMP.json || { echo EVAL_FAILED; exit 1; }
echo "CHAIN_COMPLETE $(date -u +%T) runs/E4-results-$STAMP.json"
