#!/usr/bin/env bash
# FUSION-E1 on one RunPod A40 pod.  Run from /workspace/fusion after uploading the
# kit directory to /workspace/fusion/kit (code/ inputs/ artifacts/ SHA256SUMS).
# Requires the RunPod secret HF_TOKEN (gated meta-llama/Llama-3.1-8B); never echo it.
set -euo pipefail
ROOT=${ROOT:-/workspace/fusion}
RUN_ID=${RUN_ID:-E1-$(date -u +%Y%m%dT%H%M%SZ)}
export HF_HOME=${HF_HOME:-/workspace/hf-cache}
export PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false CUBLAS_WORKSPACE_CONFIG=:4096:8
cd "$ROOT"

echo "== 1. integrity"
test -f kit/SHA256SUMS || { echo "kit/SHA256SUMS missing; upload the kit first"; exit 2; }
( cd kit && sha256sum -c SHA256SUMS --quiet ) && echo "KIT_SHA256=PASS"

echo "== 2. environment"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
test -n "${HF_TOKEN:-}" || { echo "HF_TOKEN secret missing"; exit 2; }
if [ ! -x venv/bin/python ]; then
  python3 -m venv venv
  venv/bin/pip install -q --upgrade pip
  venv/bin/pip install -q --extra-index-url https://download.pytorch.org/whl/cu128 \
      -r kit/code/configs/fusion/requirements-fusion-e1.txt
  venv/bin/pip install -q kit/inputs/projmem-0.4.0a1-py3-none-any.whl
fi
PY="$ROOT/venv/bin/python"
"$PY" - <<'PY'
import torch, transformers, peft, bitsandbytes
assert torch.cuda.is_available(), "CUDA unavailable"
print({"gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "cuda": torch.version.cuda,
       "bf16": torch.cuda.is_bf16_supported(including_emulation=False),
       "transformers": transformers.__version__, "peft": peft.__version__, "bnb": bitsandbytes.__version__})
PY

echo "== 3. inputs"
mkdir -p inputs
for z in phase2-sequence-s42 phase2-final phase2-source-development-v13r1; do
  [ -d "inputs/$z.done" ] || { unzip -q -o "kit/inputs/$z.zip" -d inputs && mkdir -p "inputs/$z.done"; }
done

echo "== 4. tests on the pod"
cd kit/code
PYTHONPATH=src "$PY" -m pytest -q -p no:cacheprovider tests/fusion
PYTHONPATH=src "$PY" -c "from seqlogad.sequence.implementation import implementation_digest as d; \
assert d('.') == '78a188515d5a74b4ca1bf9c5b763e6e92281ba5746ff22c29e488dbf93dce3e3'; print('IMPLEMENTATION=PASS')"

echo "== 5. scoring (Projmem-tracked)"
cd "$ROOT"
[ -d .pmem ] || "$PY" -m pmem init >/dev/null
"$PY" -c "import json,yaml; json.dump(yaml.safe_load(open('kit/code/configs/fusion/fusion-e1.yaml')), open('fusion-e1.config.json','w'), indent=2)"
"$PY" -m pmem run --name "FUSION-E1 scoring $RUN_ID" --seed 42 \
  --config fusion-e1.config.json --artifact "runs/$RUN_ID/run_manifest.json" -- \
  env PYTHONPATH="$ROOT/kit/code/src" "$PY" -m seqlogad.fusion.run_scoring \
    --repo "$ROOT/kit/code" --inputs "$ROOT/inputs" --artifacts "$ROOT/kit/artifacts" \
    --out "$ROOT/runs/$RUN_ID" --config "$ROOT/kit/code/configs/fusion/fusion-e1.yaml"

echo "== 6. evaluation (CPU, Projmem-tracked)"
"$PY" -m pmem run --name "FUSION-E1 evaluation $RUN_ID" --seed 42 \
  --metrics "runs/$RUN_ID/summary.json" --artifact "runs/$RUN_ID/results.json" -- \
  env PYTHONPATH="$ROOT/kit/code/src" "$PY" -m seqlogad.fusion.evaluate \
    --run "$ROOT/runs/$RUN_ID" --inputs "$ROOT/inputs" \
    --config "$ROOT/kit/code/configs/fusion/fusion-e1.yaml" --out "$ROOT/runs/$RUN_ID/results.json"

echo "== 7. export"
mkdir -p "$ROOT/exports"
tar -C "$ROOT" -czf "$ROOT/exports/fusion-$RUN_ID.tar.gz" --exclude="runs/$RUN_ID/work" \
    "runs/$RUN_ID" .pmem fusion-e1.config.json
( cd "$ROOT/exports" && sha256sum "fusion-$RUN_ID.tar.gz" > "fusion-$RUN_ID.tar.gz.sha256" )
echo "FUSION_E1_EXPORT=$ROOT/exports/fusion-$RUN_ID.tar.gz"
echo "SAFE_TO_STOP_POD=YES"
