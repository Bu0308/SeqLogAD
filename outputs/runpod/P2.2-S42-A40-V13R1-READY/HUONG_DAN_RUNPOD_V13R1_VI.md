# RunPod V13R1: train và tải đủ dữ liệu để collect

Cập nhật 05/10/2026. Đối chiếu với “Hướng dẫn thu thập dữ liệu quá trình để phục vụ Aletheia — Minh Quân” trong `/Users/apple/study/long-term job`.

**Dùng notebook có hậu tố `_collect.ipynb` và gói ZIP `P2.2-S42-A40-V13R1-READY.zip`.** Notebook bổ sung bước thu thập bằng chứng; cấu hình và mã nguồn train V13R1 giữ nguyên. Bộ READY có một notebook, một hướng dẫn và một manifest định danh. Các bộ cũ và lịch sử Projmem được giữ nguyên theo yêu cầu mới nhất.

## 1. Chuẩn bị Pod và token

1. Xin quyền truy cập [meta-llama/Llama-3.1-8B](https://huggingface.co/meta-llama/Llama-3.1-8B) trên tài khoản Hugging Face của người chạy; tạo token đọc model.
2. Trong RunPod Secrets tạo secret `huggingface_token`. Trong template/Pod đặt biến `HF_TOKEN` bằng chuỗi `{{ RUNPOD_SECRET_huggingface_token }}`. Không dán token vào notebook.
3. Tạo Network Volume, đề xuất 100 GB, tại data center có A40. Deploy **1 A40 48 GB**, gắn đúng volume vào `/workspace` ngay khi tạo Pod; chọn On-Demand. Dung lượng này là dự trù, chưa phải số đo training.
4. Dùng template PyTorch có JupyterLab và image:

   ```text
   runpod/pytorch:1.0.3-cu1281-torch291-ubuntu2404
   ```

5. Đề xuất container disk 30 GB, từ 8 vCPU/32 GB RAM. Guard bắt buộc kiểm tra A40, ít nhất 40 GiB VRAM tổng và BF16 native.

Hướng dẫn chính thức: [Network Volumes](https://docs.runpod.io/storage/network-volumes), [Secrets](https://docs.runpod.io/pods/templates/secrets), [JupyterLab](https://docs.runpod.io/pods/connect-to-a-pod), [gated models](https://huggingface.co/docs/hub/models-gated). Nếu không có GPU/image đúng, gửi lại lỗi để chọn phương án có kiểm tra.

## 2. Upload toàn bộ gói

Giải nén `P2.2-S42-A40-V13R1-READY.zip` trên máy cá nhân. Trong RunPod JupyterLab tạo `/workspace/uploads`, rồi upload **toàn bộ 9 file** vào thư mục đó, không lồng thêm một cấp.

| File | Vai trò |
| --- | --- |
| `P2.2_run_all_sequence_lora_s42_v13r1_collect.ipynb` | **Notebook phải mở để train và collect** |
| `collect_v13r1.py` | Lưu đầu vào trước train, kiểm tra và xuất capture sau train |
| `collection_archive_v13r1.py` | SQLite backup, inventory và đóng gói cả thư mục ẩn |
| `HUONG_DAN_RUNPOD_V13R1_VI.md` | Hướng dẫn này |
| `seqlogad-code-all-experts-s42-v13r1.zip` | Code/config train V13R1 gốc |
| `phase2-sequence-s42.zip` | Dữ liệu Sequence nguồn |
| `phase2-source-development-v13r1.zip` | Nhãn development nguồn và provenance |
| `projmem-0.4.0a1-py3-none-any.whl` | Projmem chính xác 0.4.0a1 |
| `RUNPOD_UPLOAD_MANIFEST.json` | Manifest duy nhất: hash mọi file bàn giao, code identity, dataset và metadata thu thập |

Giữ nguyên ba ZIP đầu vào. Notebook tự kiểm tra hash rồi giải nén. Chỉ để một bản của mỗi file trong `uploads`.

## 3. Run All đúng notebook

Mở **`P2.2_run_all_sequence_lora_s42_v13r1_collect.ipynb`**, chọn kernel Python có sẵn của template, bấm **Run → Run All Cells** một lần. Notebook tự tạo môi trường Python 3.12 riêng, cài dependencies và Projmem từ wheel. Lần đầu tải base model vào `/workspace/SeqLogAD/hf-cache`.

Notebook tự thực hiện:

1. Tạo journal và attempts trên volume trước setup.
2. Kiểm tra hash/CRC đầu vào, cài môi trường, kiểm tra GPU và xác thực Hugging Face.
3. Copy bộ đầu vào vào `sequence-v13r1/handoff_inputs`; track hash trong Projmem; tạo config capture riêng cho attempt **trước training**.
4. Chạy BGL → HDFS → HADOOP qua **`pmem run --seed 42 --config ... --metrics ...`**. Seed, adapter, loss, checkpoint selection và early stopping giữ nguyên V13R1.
5. Lưu checkpoint/recovery và ZIP kết quả từng fold.
6. Kiểm tra đủ sáu source metrics, manifest, môi trường, config và selected checkpoint bytes/hash.
7. Tạo index từ **mọi native run trong DB**, giữ cả trạng thái failed. Liên kết training run với attempt, config và metrics. Journal không có native run được liệt kê là unlinked, không suy ra completed run.
8. Export Projmem, tạo SQLite backup độc lập, inventory/hash tất cả file rồi đóng gói cả thư mục `sequence-v13r1`, bao gồm `.pmem` ẩn. Đọc lại mọi file trong archive để so hash.

**Chờ cell cuối kết thúc và `COLLECT_READY=YES`.** Dòng `SAFE_TO_STOP_RUNTIME=YES` của phần train xuất hiện sớm hơn bước collect; chưa dùng nó để kết luận gói collect đã hoàn thành.

Không chạy đồng thời hai notebook hay hai Pod vào cùng thư mục persistence. Không tự đổi seed, model, precision, batch hoặc sửa source của phiên bản đã đóng gói.

## 4. Database và log

DB thật:

```text
/workspace/SeqLogAD/sequence-v13r1/.pmem/pmem.db
```

Theo dõi Projmem sau setup trong terminal:

```bash
cd /workspace/SeqLogAD/sequence-v13r1
/workspace/SeqLogAD/venv-py312/bin/pmem summary
```

Log và lifecycle nằm trong `attempts/<id>`. `pmem run` ghi run khi child process trả về. Hard kill có thể để lại journal/log/recovery mà chưa có native run kết thúc; lần setup sau đăng ký journal cũ. Tất cả attempts được giữ, kể cả lần lỗi. DB không chứa toàn bộ checkpoint bytes nên phải tải gói FULL.

Để xem log mới nhất:

```bash
python3 - <<'PY'
from pathlib import Path
logs = list(Path('/workspace/SeqLogAD/sequence-v13r1/attempts').glob('*/training.log'))
if logs:
    p = max(logs, key=lambda f: f.stat().st_mtime)
    print(p)
    print('\n'.join(p.read_text(errors='replace').splitlines()[-60:]))
else:
    print('Chưa đến bước training; kiểm tra cell setup/auth.')
PY
```

## 5. Tải file nào để collect trên máy dự án?

Khi `COLLECT_READY=YES`, notebook in đường dẫn trong `/workspace/exports`:

```text
SeqLogAD_sequence-v13r1_FULL_<timestamp-id>.tar.gz
SeqLogAD_sequence-v13r1_FULL_<timestamp-id>.tar.gz.sha256
```

Trong JupyterLab mở `/workspace/exports`, Download **cả hai file** và gửi lại người phụ trách. Không chỉ tải scientific ZIP hay riêng DB.

Gói FULL chứa:

- `.pmem/pmem.db`, các artifact Projmem, notes và lịch sử native run còn giữ trên volume.
- Bộ code/config/data/label-sidecar/wheel và notebook đầu vào có hash.
- Attempts, log train, lifecycle, metrics và recovery còn lưu trên volume.
- ZIP kết quả ba fold và selected checkpoint của mỗi fold.
- `collection_capture/<id>/NATIVE_RUN_INDEX.csv`, `NATIVE_RUN_LINKS.json`.
- Config, metrics, environment và dependency lock từng fold trong `fold_reports`.
- `projmem-development-bundle.json`, `projmem-project-export.json`, `toolchain.json`.
- `pmem-snapshot.db` đã kiểm tra SQLite integrity.
- `COLLECTION_MANIFEST.json`, `FILE_INVENTORY.json`, `MISSING_AND_EXCLUDED_ITEMS.csv`.

Base-model cache, virtualenv và `/tmp` không được đưa vào FULL; định danh/revision model và môi trường nằm trong các manifest. Các checkpoint trung gian chỉ có thể thu thập nếu chúng còn được retention policy giữ; không tuyên bố có mọi checkpoint từng tạo.

Có thể Save Notebook As bản có output trước khi tải để gửi riêng notebook đã chạy. Notebook đầu vào và log train đã nằm trong FULL; bản giao diện có output cần Save và tải riêng nếu muốn giữ nó.

Tại máy nhận, đối chiếu checksum trước khi giải phóng volume:

```bash
shasum -a 256 /duong/dan/toi/SeqLogAD_sequence-v13r1_FULL_<timestamp-id>.tar.gz
```

Thay bằng đường dẫn thật, so kết quả với `.sha256`. Nếu file lớn khó Download qua trình duyệt, dùng SSH/SCP theo thông tin Pod. Gửi kèm GPU, native run ID và thông tin gián đoạn nếu có.

## 6. Nếu train xong nhưng bước collect lỗi

Giữ nguyên volume và log. Sau khi chắc chắn không còn train/collect ghi file, chạy lại **chỉ cell collect cuối**; không cần train lại. Mỗi lần collect tạo report riêng, không ghi đè capture cũ. Các lỗi kiểm tra không in `COLLECT_READY=YES`.

Có thể chạy từ terminal:

```bash
cd /workspace/SeqLogAD/sequence-v13r1
/workspace/SeqLogAD/venv-py312/bin/python /workspace/uploads/collect_v13r1.py finalize --root /workspace/SeqLogAD/sequence-v13r1 --exports /workspace/exports
```

Nếu chưa có training thành công đủ ba fold, bước finalize sẽ từ chối báo ready. Lúc đó tải bằng chứng lỗi riêng sau khi mọi tiến trình đã dừng:

```bash
mkdir -p /workspace/exports
tar -czf /workspace/exports/SeqLogAD_sequence-v13r1_FAILED_OR_INTERRUPTED.tar.gz -C /workspace/SeqLogAD sequence-v13r1
sha256sum /workspace/exports/SeqLogAD_sequence-v13r1_FAILED_OR_INTERRUPTED.tar.gz
```

Lỗi hash: upload lại đúng bộ file. 401/403: kiểm tra `HF_TOKEN` và quyền gated model. OOM/NaN/identity mismatch: giữ bằng chứng, gửi traceback; không bỏ guard. Mất tab: kiểm tra tiến trình cũ trước khi chạy lại. Mất Pod: gắn đúng volume/GPU/image/secret; Run All phục hồi từ checkpoint hợp lệ gần nhất, có thể phải chạy lại phần tiến độ sau recovery.

## 7. Ghép với collection trong long-term job

Sau khi tải về, người phụ trách dùng gói FULL để bổ sung collection hiện tại tại `/Users/apple/study/long-term job/seqlogad-projmem-collection`. DB RunPod là DB riêng; **không ghi đè DB gốc**, không xóa run lỗi. Export/import cần kiểm tra conflict và provenance trước khi áp dụng.

`COLLECT_READY=YES` có nghĩa gói bằng chứng training đã được kiểm tra và có đủ đầu vào để thu thập tiếp. Nó chưa có nghĩa mọi mục của protocol Aletheia đã được nghiệm thu. Run bridge/research manifest chuẩn, toàn bộ coverage của dự án, reviewed graph, human review privacy/license, ground-truth/causal audit và Aletheia import acceptance được hoàn thiện sau khi ghép với collection gốc. Mọi thiếu hụt được ghi trong `MISSING_AND_EXCLUDED_ITEMS.csv`.

Gói FULL là **restricted**, có thể chứa log và dữ liệu nguồn đã chuẩn hóa. Không coi đó là public sanitized package. Target F1/AUROC/AP vẫn `NOT_EVALUATED`; các metrics hiện có là source development, early stopping theo source macro F1.
