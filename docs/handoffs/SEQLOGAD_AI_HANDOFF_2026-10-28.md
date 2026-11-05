# SeqLogAD — Bàn giao cho AI tiếp theo (2026-10-28)

Đọc toàn bộ file này trước khi làm bất cứ việc gì. Mọi con số dưới đây đều đã đo lại trong repo, trừ khi ghi "chưa xác minh".

---

## 0. Dự án trong 10 dòng

- Đề tài: *Applying LLMs to Domain-Adaptive Fusion* cho phát hiện bất thường log **xuyên hệ thống**, LOAO (leave-one-architecture-out), không dùng nhãn hệ đích.
- 4 kiến trúc: BGL, HDFS, Hadoop, OpenStack (OpenStack chỉ làm nguồn). 3 fold đích: BGL, HDFS, Hadoop.
- 2 expert, cùng Llama-3.1-8B NF4 đóng băng + LoRA r16 riêng:
  - **Semantic (P2.1):** NLL tái tạo message bị che 30%.
  - **Sequence (V13R1):** NLL của dòng kế tiếp với ≤ 8 dòng trước cùng nhóm.
- Hợp đồng đã ký (G0, 2026-09-06), **không được sửa lặng lẽ**:
  - `configs/protocols/cross-system-split-v1.yaml` (CS-SPLIT-001): mỗi kiến trúc chia theo thời gian EARLY 50% / GUARD 5% / MID 15% / LATE 30%. Nguồn: train = EARLY, val = MID. Đích: burn-in = EARLY, evaluation = MID + LATE.
  - `configs/protocols/target-buffer-v1.yaml` (ADAPT-INPUT-001): buffer = EARLY của đích, chọn theo thời gian, cấm chọn theo nhãn. Buffer Hadoop **REJECTED**.
- Protocol v2: `docs/research-protocol-v2-domain-adaptive-fusion.md`. Protocol v1.1 cũ vẫn bảo vệ **TEST đã niêm phong** của HDFS/BGL (`data/processed/splits/*/sealed/`, `open_count = 0`).

## 1. Trạng thái trước phiên này (fusion E1–E5, 23–24/10)

Chi tiết: `docs/fusion/FUSION_RESEARCH_DECISION_LOG.md` (D-01…D-24), `docs/fusion/FUSION_EXPERIMENT_RESULTS.md`.

- **Mọi kết quả fusion đều trên source-dev (MID của hệ nguồn), chưa có số nào trên hệ đích.**
- E1: Cauchy fusion đăng ký trước — **âm tính** (D-14).
- E2-CONFIRM: **xác nhận** VW(Sequence, B0) hơn cả hai thành phần trên BGL, 2 fold, Holm (D-19). VW(Semantic, Sequence) không xác nhận.
- E3: Sequence AP 0,606 trên HDFS, hơn DeepLog 0,378 (lưu ý: E3/E4 chỉ chấm **32 dòng đầu** mỗi block).
- E4: cổng tail-lift thất bại (D-21). HDFS: ghép Semantic làm tụt AP 0,705 → 0,472.
- E5-DEV: Semantic không thêm giá trị ngoài độ hiếm template; B0 độ hiếm template đạt AP 0,697 trên HDFS, gần Sequence 0,705 (D-23). Script tạo con số này **không được lưu** (chỉ còn output `e5dev_rarity_explore.txt`).
- Đã xoá các pod RunPod (D-24). RunPod MCP hiện lỗi 401.

## 2. Phản biện của giảng viên (dự kiến) và đánh giá đã kiểm chứng

| # | Phản biện | Đánh giá |
|---|---|---|
| 1 | Chưa kiểm chứng cross-system | **Đúng, nặng hơn mô tả**: không có số nào trên hệ đích. |
| 2 | "Domain-adaptive" nhưng calibration transductive | **Đúng** (D-06). |
| 3 | Baseline yếu; B0-template ≈ Sequence trên HDFS | **Đúng** (0,697 vs 0,705). |
| 4 | Semantic chưa có bằng chứng ngữ nghĩa; loss trên cả dòng | **Đúng**: HDFS AUROC 0,472; `src/seqlogad/semantic/objective.py:36` đặt `labels` cho **toàn bộ dòng gốc**, ~70% số từ đã có sẵn trong prompt ⇒ loss bị phần chép lại chi phối. |
| 5 | 1 seed, ít mẫu dương, thiếu adapter Semantic-BGL, G0/G2 | Phần lớn đúng; **G0 đã PASSED** (`docs/BAO-CAO-KIEN-TRUC-VA-PHASE-1.md:8`). G2 và baseline Transformer Encoder chưa kiểm. |
| 6 | Khả thi triển khai | Hợp lý; con số 1.540 s / 44.769 window chưa xác minh nguồn. |

## 3. Việc đã làm trong phiên này: TV-001 (view hệ đích không nhãn)

Thiết kế + lý do + tài liệu tham khảo: **`docs/fusion/TARGET_VIEW_DESIGN.md`** (đọc kỹ mục 3, 6, 7).

Code (ngoài 5 package bị băm vào digest V13R1, nên không làm hỏng identity của Sequence):
- `configs/fusion/target-view-v1.yaml` — mọi tham số, cố định trước khi có nhãn/điểm đích.
- `src/seqlogad/target/materialize.py` — raw → text chuẩn hoá cho EARLY + LATE; kiểm từng dòng khớp `norm_h` đã đóng băng; `template_key` (từ ≥ 3 chữ số → `<V>`).
- `src/seqlogad/target/units.py` — unit (BGL = dòng; HDFS = block, không cắt 32 dòng), window ≤ 8 dòng trước cùng nhóm trong LATE, 20 tầng thời gian đều số bản ghi, mẫu hash phân tầng, `dedupe_key`.
- `src/seqlogad/target/diagnostics.py` — bộ nhớ B0 trên buffer, chẩn đoán drift không nhãn (template mới, message mới, JSD).
- `src/seqlogad/target/view.py`, `scripts/build_target_view.py`, `tests/target/test_target_view_units.py` (8 pass).

Chạy bằng **`.venv/bin/python`** (python3 hệ thống lỗi ABI numpy/pandas):
```
PYTHONPATH=src .venv/bin/python scripts/build_target_view.py --project . --out data/processed/target-views/TV-001
```
Output đã build (gitignored, không commit): `data/processed/target-views/TV-001/FOLD-TARGET-ARCH-{BGL,HDFS}/` với `manifests/view.json` chứa hash, bất biến, số đếm, drift.

Kết quả (không nhãn; mọi bất biến PASS; `target_labels_read = false`):

| | BGL | HDFS |
|---|---|---|
| Unit LATE | 1.424.389 dòng | 188.607 block (trung vị 19 dòng, max 284) |
| Window khác nhau, toàn bộ | 226.135 | 735.288 |
| Window khác nhau, mẫu 20.000 block | — | 170.767 |
| Calibration (4.095 đều + 4.095 "recent" = 20% cuối EARLY) | chỉ **608** window khác nhau (nhiều tie) | 75.060 |
| Template LATE mới so với buffer | 685/957 key; ~72% dòng (không phải do token ngày tháng) | 4/123 key |
| JSD template theo tầng | 0,87–0,999 bit | 0,08–0,25 bit |

**Cách đọc đúng:** với BGL, nhiều template mới chính là các loại alert (parity error, MACHINE CHECK, ddr error, ciod error). Không có nhãn thì **không tách được** drift của dữ liệu bình thường với đợt bất thường. Chỉ được nói "phân phối LATE khác buffer mạnh". B0 novelty có thể rất mạnh trên BGL.

## 4. Kiểm tra liêm chính đã làm — và các điểm còn mở

1. **TEST v1.1 nằm trong LATE.** TEST v1.1 BGL = 474.797 dòng cuối ⇒ nằm trong LATE (HDFS chưa kiểm; chỉ kiểm bằng công cụ `seqlogad-split-dataset validate`, **không** mở membership). Mở nhãn LATE = mở nhãn TEST v1.1 ⇒ cần quyết định có chữ ký researcher.
2. **Sự cố đã khai:** assistant đã in 400 byte đầu `data/processed/splits/bgl/sealed/TEST.jsonl` (khoảng rank cấu trúc, không nhãn). Ghi ở `TARGET_VIEW_DESIGN.md` mục 7 và `_agent_ops/IMPLEMENTATION_LOG.md`.
3. **TV-D1 (chỉ LATE) và TV-D2 (bỏ Hadoop) là amendment hợp đồng — chưa có chữ ký researcher.**
4. Các thống kê **cấu trúc không nhãn** của LATE đã được xem trước khi chọn "chấm toàn bộ BGL / lấy mẫu HDFS" ⇒ phải khai trong prereg.
5. Luật `template_key` được đặt sau khi xem dữ liệu HDFS nguồn (D-22) ⇒ không gọi là "tiên nghiệm".
6. Phiên này **chưa ghi vào Projmem DB** (`.pmem/pmem.db`), dù SESSION_BRIEF yêu cầu mọi thay đổi/attempt được lưu. AI tiếp theo nên ghi bổ sung (run + note) cho TV-001 và sự cố seal.
7. Trích dẫn: Bashari 2025 chỉ đọc tóm tắt; Boyd 2013 và López de Prado 2018 trích từ trí nhớ; LogTAD/MetaLog chỉ biết qua mô tả trong ZeroLog. Đọc lại bài gốc trước khi đưa vào luận văn.

## 5. Định hướng: sửa gì, thiết kế thêm gì (theo thứ tự)

### P0 — Quyết định của researcher (chặn mọi bước sau)
Soạn văn bản quyết định để researcher ký (lưu vào `configs/protocols/` theo kiểu `g0-signatures.yaml`, phiên bản mới, hash mới):
- TV-D1: thu hẹp TARGET_EVALUATION thành LATE (lý do: MID đã bị mở nhãn khi làm dev).
- TV-D2: bỏ Hadoop khỏi fold đích (BUFFER-REJECT-001).
- Chồng lấn TEST v1.1: (a) dùng `seqlogad-final-test-access` với câu xác nhận + lý do + audit, hoặc (b) ngoại lệ có chữ ký trong `leak-cs-001-exceptions.yaml`. Không AI nào được tự chọn.

### P1 — Prereg E6-TARGET (trả lời phản biện 1, 2)
Viết `docs/fusion/FUSION_E6_TARGET_PREREG.md` + sha256, khoá **trước** khi chấm. Nội dung tối thiểu:
- Fold: HDFS-target (chính), BGL-target (phụ, có cảnh báo phân phối lệch).
- Expert theo fold: Sequence_<fold> best checkpoint; B0 tính trên buffer EARLY của đích. Cấu hình chính đã xác nhận: **VW(Sequence, B0)** (không cần Semantic ⇒ tránh thiếu adapter Semantic-BGL).
- Giả thuyết chính (Holm): H1 VW(Seq, B0) > max(Seq, B0) về AP; H2 Seq > DeepLog cùng unit. Phụ: FAR thực tế ở α danh nghĩa 1% / 0,1% với calibration `uniform` vs `recent` vs transductive.
- Unit/metric: BGL theo dòng (phụ: chunk 100 dòng, gộp max); HDFS theo block (gộp max mọi dòng). AP chính; AUROC, recall@FAR, Specificity/FAR. Không point-adjust.
- Thống kê: bootstrap cụm phân tầng (cụm = block HDFS; chunk 100 dòng cho BGL do alert theo đợt).
- Phạm vi chấm: BGL toàn bộ (~226k window khác nhau); HDFS mẫu 20k block hoặc toàn bộ (~735k) — chọn theo ngân sách, ghi rõ.
- Sensitivity đăng ký trước: bỏ unit trong cờ `embargo` 1 giờ; chỉ dùng calibration `recent`.
- Ranh giới nhãn: đọc nhãn **một lần**, qua một hàm có ghi audit vào `data/processed/protocol/label-access-audit.jsonl`; sau đó đo luôn nhiễm bẩn buffer (ROB-CONTAM-001) và chênh lệch tỉ lệ bất thường của 19,8% block HDFS bị loại do vắt mốc (EXC-001/002).
- Báo cáo kể cả khi âm tính.

Ước chi phí (dựa trên ~29 window/s của E4, **chưa xác minh**): BGL ~2,2 giờ A40; HDFS mẫu ~1,6 giờ (toàn bộ ~7 giờ); calibration HDFS ~0,7 giờ. Cần sửa token RunPod MCP (401) và được duyệt ngân sách trước khi tạo pod. Kéo điểm rút gọn về máy **trước** khi dừng pod (pod dừng thường không khởi động lại được).

Việc cần code thêm: một scorer đọc trực tiếp view TV-001 (`evaluation/windows.parquet` + `events.parquet`, `buffer/calibration_windows.parquet`), chấm theo `dedupe_key` rồi nhân ra mọi unit; tái dùng `src/seqlogad/fusion/scorer.py`, `rules.py`, `metrics.py`, `calibration.py` nếu được.

### P2 — Baseline công bằng mức template và message (phản biện 3), chỉ CPU
Chạy trên đúng unit TV-001, fit chỉ trên buffer EARLY của đích:
- B0: template mới, −log tần suất template, Markov n-gram trên `template_key`.
- DeepLog, PCA, IsolationForest, kNN — **cả hai mức** `normalized_message` và `template_key`.
- Các detector đơn giản của Landauer (event mới + độ dài, ECVC).
Kết luận cần trả lời: Sequence có hơn baseline mức template không. Nếu không, phải viết lại luận điểm về giá trị của LLM.
Lưu luôn script (lỗ provenance của E5-DEV không được lặp lại).

### P3 — Semantic (phản biện 4)
- Exploratory, không train lại: chấm NLL **chỉ trên token bị mask** (tính lại mask từ `corrupt()` với cùng seed); so với NLL toàn dòng và với độ hiếm template.
- Nếu muốn train lại với loss chỉ trên token mask: đó là **variant mới** (theo kiểu `VAR-…` trong Projmem), kit mới, không sửa `src/seqlogad/semantic/` tại chỗ (nằm trong digest V13R1).
- Adapter Semantic-BGL vẫn thiếu; lỗi nạp checkpoint Semantic đã có bridge trong `fusion/loading.py` (D-03).

### P4 — Độ ổn định và hiện vật (phản biện 5)
- Ghi rõ "1 seed, kết quả sơ bộ"; nếu có ngân sách, seed thứ 2 cho Sequence trên fold HDFS.
- Kiểm trạng thái G2 (đo độ đa dạng expert) và báo cáo đúng.
- Baseline Transformer Encoder: hoặc làm, hoặc ghi rõ là ngoài phạm vi.

### P5 — Khả thi triển khai (phản biện 6)
Sau E6: đo thông lượng thật (window/s, có dedupe), số cảnh báo/ngày ở FAR 1% và 0,1% trên LATE, độ trễ phát hiện. Đặt đúng tên: prototype nghiên cứu.

### P6 — Dọn dẹp
- `_agent_ops/SESSION_BRIEF.md` còn dừng ở 19/10 (không có fusion, không có TV-001) — cập nhật.
- **Chưa commit gì** trên branch `codex/sequence-v13r1`; nhiều file fusion untracked. Khi commit: stage từng file, **không** `git add .`, không commit data/model/log.
- E3/E4 chỉ chấm 32 dòng đầu mỗi block — ghi vào giới hạn khi nhắc lại số E3/E4.

## 6. Quy tắc bắt buộc cho AI tiếp theo

- Không đọc nhãn đích, không mở `data/processed/splits/*/sealed/*`, trước khi researcher ký P0.
- Không sửa `src/seqlogad/{common,protocol,semantic,sequence,phase2_execution}` (digest V13R1 `78a18851…`). Code mới đặt ở package khác.
- Không bao giờ xoá checkpoint/adapter P2.1, P2.2, kit, bản gốc trên Drive, bằng chứng fusion.
- Không sửa giá trị trong hợp đồng đã ký để "cho qua"; mọi thay đổi = phiên bản mới + chữ ký.
- Mọi lần chạy/attempt (kể cả thất bại) ghi vào Projmem DB hiện có.
- Đầu phiên: `.venv/bin/python _agent_ops/tools/session_start.py --root .`, rồi đọc `_agent_ops/CURRENT_TASK.md` (mục ACTIVE TV-001).
