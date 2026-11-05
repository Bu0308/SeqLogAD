#!/usr/bin/env bash
# FUSION-E1.1 (exploratory) on the same pod: A+B re-evaluation and C multi-mask Semantic.
set -euo pipefail
ROOT=${ROOT:-/workspace/fusion}; cd "$ROOT"
export HF_HOME=${HF_HOME:-/workspace/hf-cache} PYTHONDONTWRITEBYTECODE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
PY="$ROOT/venv/bin/python"; CODE="$ROOT/kit/code"; E1=${E1:-runs/E1-20261023T112847Z}
E11=${E11:-runs/E11-$(date -u +%Y%m%dT%H%M%SZ)}
echo "== tests"; (cd "$CODE" && PYTHONPATH=src "$PY" -m pytest -q -p no:cacheprovider tests/fusion | tail -2)
(cd "$CODE" && PYTHONPATH=src "$PY" -c "from seqlogad.sequence.implementation import implementation_digest as d; assert d('.')=='78a188515d5a74b4ca1bf9c5b763e6e92281ba5746ff22c29e488dbf93dce3e3'; print('IMPLEMENTATION=PASS')")
echo "== C multimask (GPU)"
"$PY" -m pmem run --name "FUSION-E1.1 multimask semantic" --seed 42 --artifact "$E11/multimask_manifest.json" -- \
  env PYTHONPATH="$CODE/src" "$PY" -m seqlogad.fusion.run_multimask --repo "$CODE" --inputs "$ROOT/inputs" \
  --artifacts "$ROOT/kit/artifacts" --e1-run "$ROOT/$E1" --out "$ROOT/$E11" --config "$CODE/configs/fusion/fusion-e1.yaml"
for f in "$ROOT/$E1"/scores/*.jsonl; do ln -sf "$f" "$ROOT/$E11/scores/$(basename "$f")"; done
echo "== evaluation A+B+C (CPU)"
for v in best best-mkmean best-mkmax; do
  "$PY" -m pmem run --name "FUSION-E1.1 evaluation $v" --seed 42 --metrics "$E11/summary-$v.json" -- \
    bash -c "PYTHONPATH=$CODE/src $PY -m seqlogad.fusion.evaluate --run $ROOT/$E11 --inputs $ROOT/inputs \
      --config $CODE/configs/fusion/fusion-e1.1-$v.yaml --out $ROOT/$E11/results-$v.json && \
      mv $ROOT/$E11/summary.json $ROOT/$E11/summary-$v.json"
done
echo "E11_DIR=$E11"; echo "SAFE_TO_STOP_POD=YES"
