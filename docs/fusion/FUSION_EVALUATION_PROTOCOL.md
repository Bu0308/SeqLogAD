# FUSION_EVALUATION_PROTOCOL — Đăng ký trước cho FUSION-E1

**Trạng thái:** ĐÓNG BĂNG trước mọi điểm fusion thật. Cấu hình `configs/fusion/fusion-e1.yaml` có sha256 `4a83b8359af9b94d932f3ab1a97efbb51dd4c8c31559014860014bb7a89ae617`; danh sách hash code ở cuối file. Mọi thay đổi sau thời điểm này là phiên bản mới (E1.1 …) và phải ghi vào decision log. Bằng chứng tài liệu về cách 18 bài báo đánh giá nằm ở `evidence/EVAL_PROTOCOL_EVIDENCE.md`; tổng quan 27 công trình nằm ở `FUSION_LITERATURE_REVIEW.md`.

## 1. Câu hỏi và phạm vi

**Câu hỏi:** Trên các unit source-development **mới** (chưa từng dùng để chọn checkpoint), điểm gộp của Semantic và Sequence có phát hiện bất thường tốt hơn expert đơn tốt nhất không? Có tốt hơn các control (ensemble cùng một expert, expert + B0) không?

**Phạm vi đánh giá E1:**
- Chỉ dùng nhãn **source** đã được phép. Không đọc bản ghi hay nhãn nào của kiến trúc đích.
- Đây là bằng chứng về **tính bổ sung giữa hai expert trên log của hệ thống nguồn, ở giai đoạn thời gian sau khi train (MID)**. Đây **chưa** là bằng chứng phát hiện trên hệ thống chưa từng thấy. Đánh giá trên hệ đích là giai đoạn E2: cần amendment chọn LATE làm metric chính, hiệu chỉnh theo buffer và sự đồng ý mở nhãn.

| Fold | Expert | Unit báo cáo | Vai trò |
|---|---|---|---|
| HDFS-target | Sem_HDFS + Seq_HDFS | BGL: 1.536 dòng, 67 dương | **Khẳng định chính** |
| Hadoop-target | Sem_Hadoop + Seq_Hadoop | BGL (67 dương) và HDFS (21 dương, 1.508 block) | Khẳng định phụ |
| BGL-target | Sem **base** + Seq_BGL | HDFS (21 dương) | Exploratory (thiếu Semantic-BGL) |

## 2. Metric

- **Metric chính: Average Precision (PR-AUC)** trên unit mới, theo từng nguồn. Lý do chọn:
  - Tỉ lệ dương chỉ 1,4–4,4%, mất cân bằng nặng; AP không cần ngưỡng.
  - Lý do theo tài liệu: xem `FUSION_LITERATURE_REVIEW.md`.
- **Metric phụ:**
  - AUROC.
  - Recall, precision và FPR ở ngân sách cảnh báo 1% và 5%. Ngưỡng chọn không dùng nhãn, bằng cách gắn cờ top-k.
  - Spearman ρ giữa hai expert trên mẫu âm và trên mẫu dương.
  - Jaccard của top 5% (không dùng nhãn).
  - Số mẫu dương chỉ một expert bắt được.
- **Fusion Gain** = AP(fused) − max(AP_Sem, AP_Seq). Max được tính lại trong từng lần bootstrap, nên đây là phép so sánh với expert đơn tốt nhất kiểu oracle, mang tính bảo thủ. Báo cả gain tuyệt đối và tương đối.
- **Hiệu quả tính toán:**
  - Tham số: backbone khoảng 8,03 tỉ (đóng băng); mỗi adapter 13.631.488; fusion 0 (K1–K3) hoặc 3 (logistic).
  - VRAM đỉnh, thời gian chấm (giây/unit), throughput (lấy từ `run_manifest.json`).

## 3. Luật, thứ tự kiểm định, control

- **Luật chính (fixed-sequence):** K1 `cauchy` → K2 `lr_cauchy` → K3 `vovk_wang_mean`. Chỉ khẳng định K(i+1) khi K(i) đã khẳng định được. Lý do chọn thứ tự: mô phỏng D-07.
- **Sensitivity** (báo cáo, không dùng để khẳng định): `bonferroni_min`, `copula_onesided`, `fisher`, `stouffer`, `zscore_mean`, `learned_logistic` (L2 = 1, cross-fit theo hai nửa thời gian).
- **Control:**
  - `sequence_best_plus_latest`: nếu fusion không hơn control này thì lợi ích chỉ là hiệu ứng ensemble.
  - `semantic_plus_b0` và `sequence_plus_b0`: nếu B0 thay thế được expert kia thì lợi ích không đến từ LLM.
- **Ablation trong cùng lượt chấm:**
  - Checkpoint: base / best / latest.
  - Từng nhánh riêng: Sem, Seq.
  - LR so với điểm thô.
  - Calibration so với không calibration (`zscore_mean`).
  - Luật gộp.
  - Có tham số học được so với không có.

## 4. Thống kê

- Paired **cluster bootstrap** theo khối thời gian (64 cửa sổ liên tiếp mỗi khối, 24 khối mỗi nguồn), 2.000 lần lấy mẫu, seed 42. Có khoảng tin cậy 95% và p một phía cho giả thuyết gain ≤ 0.
- **DeLong** ghép cặp cho AUROC (fusion so với từng expert).
- **Chỉ một seed:** mọi kết luận ghi là *preliminary*.
- **Tiêu chí thành công** (khẳng định cho K1, fold HDFS-target):
  - Cận dưới 95% của Fusion Gain AP > 0, **và**
  - Gain điểm của K1 lớn hơn gain điểm của control `sequence_best_plus_latest`.

  Nếu chỉ đạt điều kiện thứ nhất thì ghi "lợi ích ensemble, chưa chứng minh tính bổ sung".
- **Gate trước khi đọc kết quả fusion:** parity phải PASS (fail-closed trong code). Nếu không tái lập được số đã ghi thì không tính fusion.

## 5. Chống rò rỉ

- 512 unit đã dùng để chọn checkpoint của mỗi nguồn bị **loại** khỏi báo cáo; code tái lập chúng bằng `select_windows(seed 42, n = 512)`.
- Calibration **chỉ dùng thứ hạng** trong cohort, không dùng nhãn.
- Nhãn bị bỏ khỏi dữ liệu mà bộ chấm GPU nhận (`strip_labels`).
- Không có bản ghi đích nào: `build_cohort` từ chối nếu thấy kiến trúc đích.
- Comparator học được chỉ dự đoán ngoài fold (out-of-fold).

## 6. Hash code tại thời điểm đăng ký

```
4a83b835…  configs/fusion/fusion-e1.yaml
bb6482e0…  artifacts.py   a6656727…  baselines.py   700a8acd…  calibration.py
befae47a…  evaluate.py    a11a8fbd…  learned.py     4aae581f…  loading.py
8dca67b1…  metrics.py     3cc7cfa7…  parity.py      b5dd257d…  rules.py
d5e1b1f4…  run_scoring.py deb139ea…  scorer.py      6bac9b6c…  units.py
Implementation digest Sequence: 78a188515d5a74b4ca1bf9c5b763e6e92281ba5746ff22c29e488dbf93dce3e3
```
