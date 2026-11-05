# FUSION_REPRODUCIBILITY_GUIDE — Tái lập FUSION-E1

## Phần cứng

- **GPU:** 1 × NVIDIA A40 48 GB, có BF16 native.
  - VRAM dự kiến khoảng 12–20 GB: base NF4 cỡ 5,5 GB, 10 adapter FP32 cỡ 0,55 GB, logits với token budget 4.096 cỡ 2–3 GB.
  - Lần train trước đo được đỉnh 12,1 GB reserved trên cùng stack.
- **Ổ đĩa:** ≥ 60 GB persistent cho HF cache (16 GB), venv (khoảng 10 GB), kit (2,2 GB), giải nén ZIP (2,3 GB) và kết quả.
- **Máy local** (M1 8 GB) chỉ chạy được test CPU và bước đánh giá. Không chạy được 8B.

## Môi trường

- Image: RunPod PyTorch, CUDA 12.8.
- Phụ thuộc lấy từ `configs/fusion/requirements-fusion-e1.txt`. File này giống lock của lần train V13R1 (torch 2.9.1, transformers 4.57.6, peft 0.18.1, bitsandbytes 0.49.2, accelerate 1.12.0, polars 1.44.2, pyarrow 19.0.1, numpy 2.5.4), thêm scipy 1.18.1 và pytest 9.1.1.
- Projmem 0.4.0a1 (wheel sha `637964ee…`).
- Secret RunPod `HF_TOKEN`: tài khoản phải được duyệt quyền gated `meta-llama/Llama-3.1-8B`. Revision cố định `d04e592b…`.

## Dữ liệu và checkpoint (kit)

Kit nằm ở `/Users/apple/study/seqlogad-fusion/00_inputs_immutable/` (khoảng 2,2 GB, 169 file, có `SHA256SUMS`):

| Thư mục | Nội dung |
|---|---|
| `code/` | `src/seqlogad` (đã gồm `fusion/`), `configs/{models,protocols,fusion}`, `tests/fusion`, `scripts/fusion_e1_runpod.sh` |
| `inputs/` | `phase2-sequence-s42.zip` (`4ed76b92…`), `phase2-final.zip` (`ebcfdfd6…`), `phase2-source-development-v13r1.zip` (`c765eb88…`), wheel Projmem |
| `artifacts/` | `P2.2/{targets,recovery/*}` và `P2.1/{targets,recovery/*}`, giữ nguyên tên gốc và `.sha256` gốc |

Kit được dựng từ bản Drive xuất về trong `~/Downloads` (chỉ đọc, không sửa).

## Lệnh

```bash
# Local (CPU): test
PYTHONPATH=src python -m pytest -q tests/fusion
```

```bash
# Pod: sau khi upload kit vào /workspace/fusion/kit
bash /workspace/fusion/kit/code/scripts/fusion_e1_runpod.sh
```

Runbook làm lần lượt các bước sau:
1. Kiểm `SHA256SUMS`.
2. Chẩn đoán GPU và kiểm BF16.
3. Cài venv theo đúng phiên bản pin.
4. Giải nén inputs.
5. Chạy `pytest tests/fusion` trên pod và kiểm implementation digest.
6. `pmem run … seqlogad.fusion.run_scoring` (parity fail-closed, rồi chấm 10 adapter + 2 job base).
7. `pmem run … seqlogad.fusion.evaluate` → `results.json`, `summary.json`.
8. Đóng gói `exports/fusion-<RUN_ID>.tar.gz` + `.sha256`, rồi in `SAFE_TO_STOP_POD=YES`.

Chỉ chạy lại bước đánh giá (CPU, local hoặc pod):

```bash
PYTHONPATH=src python -m seqlogad.fusion.evaluate --run runs/<RUN_ID> --inputs <inputs> --config configs/fusion/fusion-e1.yaml --out runs/<RUN_ID>/results.json
```

## Seed và tính tất định

- Seed 42 cho: lựa chọn cohort (`select_windows`), mask Semantic, bootstrap, split. Không có bước nào train.
- `CUBLAS_WORKSPACE_CONFIG=:4096:8` được đặt. Tuy vậy FlashAttention/SDPA vẫn có thể không tất định ở mức bit, nên parity dùng dung sai (|ΔAUROC|, |ΔAP| ≤ 0,01; NLL ≤ max(2%, 0,002)).

## Kiểm lại identity

- `implementation_digest(code) == 78a18851…`. Kiểm ở test `test_fusion_package_does_not_change_sequence_identity` và trong runbook.
- `run_manifest.json` lưu sha của mọi đầu vào, adapter, config, GPU, VRAM đỉnh và thời gian.
