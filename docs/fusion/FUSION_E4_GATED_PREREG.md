# FUSION-E4-GATED — Đăng ký trước (khóa 2026-10-23T17:51Z, trước khi có điểm nào)

## Vấn đề
Fusion 2 mô hình (Semantic + Sequence) có xu hướng giúp trên BGL. Ở E2C, VW(Sem-mk8, Seq) tăng +0,10 / +0,09 AP nhưng chưa có ý nghĩa thống kê. Trên HDFS thì nó gây hại: ở E3, Cauchy(Seq, Sem) đạt AP 0,355 so với 0,606 của Sequence. Lý do là trên HDFS, Semantic gần như ngẫu nhiên.

Đề xuất: một **cổng chọn không dùng nhãn**. Cổng quyết định, cho từng hệ, có cho Semantic góp tiếng hay không. Đây là phần "domain-adaptive" của đề tài.

**Minh bạch:** ý tưởng cổng nảy ra *sau khi* đã thấy kết quả E1–E3. Vì vậy:
- Ngưỡng của cổng được chốt trước, theo lập luận, không chỉnh trên dữ liệu.
- Mọi kiểm định chạy trên **cohort mới hoàn toàn**.

## Dữ liệu (mới, không trùng E1, E1.1, E2C, E3; đã kiểm overlap = 0)
- **BGL:** 16.384 dòng thuộc SOURCE_VALIDATION (MID), tag `FUSION-E4-GATED-BGL-seed3`. Đã loại các cửa sổ của bundle gốc và của E2C. Có **688 dòng bất thường (4,2%)**. Dùng ở 2 fold: HDFS-target và Hadoop-target.
- **HDFS:** 3.000 block mới, tag `FUSION-E4-GATED-HDFS-BLOCKS`. Đã loại các block của v13r1, E2C và E3. Chấm mọi dòng, tối đa 32 dòng mỗi block, tổng 44.769 cửa sổ. Có **81 block bất thường (2,7%)**. Dùng ở fold Hadoop-target.
- Chỉ dùng nhãn source. Không đụng tới bất kỳ bản ghi nào của hệ đích.
- `00_inputs_e4/SHA256SUMS`: sha256 `a4b379100465334ce75964d435c8f11e960b6d3e1948741dcc25efec287af7a8`.

## Mô hình (đóng băng, không train lại)
- **Sequence:** V13R1 best của từng fold.
- **Semantic:** P2.1 best của từng fold, trung bình 8 mask (seed 42..49), như đã chốt ở E1.1.
- **Dedupe:** mỗi encoding khác nhau chỉ chấm 1 lần rồi sao chép kết quả.
  - BGL: 16.384 dòng nhưng chỉ có 2.962 cửa sổ khác nhau.
  - HDFS: 2.142 message khác nhau.
  - Kiểm tra: chấm lại 256 cửa sổ không dedupe, ghi |ΔNLL| lớn nhất (dung sai 0,01). Nếu vượt dung sai thì ghi là deviation.
- **Fail-closed:** parity anchor như E2C, |ΔAUROC| và |ΔAP| ≤ 0,01.

## Unit
- BGL: 1 dòng.
- HDFS: block, lấy **max** các dòng (đã đăng ký trước ở E3).

## Cổng (`src/seqlogad/fusion/gate.py`)
Cổng tính trên điểm không nhãn của chính cohort đang đánh giá.

- k = ⌈0,05·N⌉.
- O = độ trùng của top-k giữa Seq và Sem. Phần tử hòa điểm ở biên chia đều số suất còn lại.
- E = k²/N là độ trùng kỳ vọng nếu hai mô hình độc lập.
- lift = O/E.
- p-value: hoán vị một phía, 2.000 lần, seed 42.

Quy tắc:
- **Cổng mở khi lift ≥ 2,0 VÀ p < 0,01.**
- Mở: G = VW(p_Seq, p_Sem) = −log(½(p_Seq + p_Sem)), hợp lệ với mọi kiểu phụ thuộc giữa hai mô hình.
- Đóng: G = Sequence. Sequence là mô hình mặc định, chọn từ bằng chứng E1–E3.

Lập luận cho ngưỡng 2: nếu Semantic có tín hiệu bất thường thật thì đuôi trên của nó phải trùng đuôi trên của Sequence nhiều hơn hẳn mức ngẫu nhiên (lift 1). Ngưỡng 2 đòi hỏi "gấp đôi ngẫu nhiên", để một tương quan nhỏ nhưng có ý nghĩa thống kê, xuất hiện khi N lớn, không đủ để mở cổng.

## Giả thuyết (bootstrap cụm 64 unit liên tiếp, 2.000 lần, seed 42)

**H8 (dự đoán, không phải kiểm định):** cổng mở ở cả 2 cohort BGL và đóng ở HDFS.

**Họ chính** (Holm, α = 0,05 một phía):
- **H9a, H9b:** BGL@HDFS-fold và BGL@HADOOP-fold: AP(G) − max(AP(Seq), AP(Sem)) > 0.
- **H10:** HDFS@HADOOP-fold: AP(G) − AP(Seq) > −0,02 (không kém).

**Họ phụ** (Holm): AP(G) − AP(baseline) > 0 trên từng cohort, với các baseline:
- DeepLog (CCS'17), PCA (SOSP'09), Isolation Forest, kNN TF-IDF.
- B0 tần suất và B0 Markov.

Tất cả train trên SOURCE_TRAIN của cùng fold, tối đa 32.768 cửa sổ.

**Khám phá:**
- VW không có cổng; Cauchy không có cổng.
- Độ nhạy của ngưỡng (lift 1,5 và 3,0).
- Sequence so với từng baseline.
- recall, precision ở mức 1% và 5%.

## Hạn chế đã biết
- Quyết định của cổng chỉ tính 1 lần trên cả cohort; bootstrap không lặp lại quyết định đó.
- Bootstrap cụm theo thứ tự rank.
- Đây vẫn là đánh giá trên source (MID), chưa phải hệ đích.

## Hash đóng băng
```
2dbb60ae6ab94b0054156001cbeb808ac327c999b9220c0c6216f27c3f1455df  src/seqlogad/fusion/gate.py
8d9fc629fce1cd6d7823e6903497c953fa05036597935404c323df186466c229  src/seqlogad/fusion/gated_eval.py
5f14c6fb5778e0d5e1273382b3d910562bc49878162a3a2243f74cb5db5f6088  src/seqlogad/fusion/run_confirm.py
6a969b066c6780088c5c02725349f88e0c651333e858202d18f619d92d30db77  src/seqlogad/fusion/scorer.py
3efe0cdf778941e8fb030aaae9b3df5fa3620b3fd614861f4ac625ef3583527e  src/seqlogad/fusion/paper_baselines.py
a66567270ba9b65927bf19e77989e72ffeb7a2b838b6448dfa439abac75b59d9  src/seqlogad/fusion/baselines.py
3e3cdfc5af6a87755b2310ea76d6189631c82d306f337b4a043dda59e10cd3cc  src/seqlogad/fusion/evaluate.py
8dca67b1802d8ccedf27d0164cbbdc849cd2625694446032403e55cc176b75ad  src/seqlogad/fusion/metrics.py
700a8acd1099c1be2a6dfb2cdb88e8e493c503d3ff55aac11cccf564acc5eaf0  src/seqlogad/fusion/calibration.py
b5dd257d675b7a0152dc06c0f96190aad191af5d032c6e1e9eb5b2f83db73018  src/seqlogad/fusion/rules.py
6911d83f413168a4a2650d34456518f9809a3472b2249baa0714adbb2b13070c  scripts/build_confirm_cohort.py
14a76da55086407613b85157d173ef1be263c9985c965ad3aa1e82af78cc217c  scripts/build_block_cohort.py
```

## Phụ lục D-20 (2026-10-23T18:20Z: đã chấm xong điểm BGL, CHƯA mở nhãn, chưa đánh giá)
- Kiểm tra dedupe trên BGL:
  - Fold HDFS: |ΔNLL| lớn nhất 0,0161 trên 256 cửa sổ.
  - Fold Hadoop: |ΔNLL| lớn nhất 0,0205.
  - Cả hai vượt dung sai 0,01.
- Parity anchor vẫn PASS (AUROC 0,8056 so với giá trị đã ghi 0,8025).
- Script chain dừng sai chỗ: nó coi việc vượt dung sai là lỗi chặn. Theo bản đăng ký ở trên, trường hợp này chỉ ghi thành **deviation** và chạy tiếp.
- **Xử lý:**
  - Giữ nguyên điểm đã dedupe.
  - Chấm tiếp HDFS.
  - Thêm chẩn đoán `runs/E4-D20-dedupe-diag.json`, so hai đại lượng:
    - nhiễu nền do khác thành phần batch: cùng cửa sổ, chấm trực tiếp 2 lần với các cửa sổ đi kèm khác nhau;
    - chênh lệch dedupe so với chấm trực tiếp.
- Đọc kết quả chẩn đoán:
  - Nếu chênh lệch dedupe ≈ nhiễu nền, dedupe không đưa thêm sai số nào.
  - Nếu không, báo cáo E4 phải ghi rõ hạn chế này.
- Không đổi giả thuyết, cổng, ngưỡng hay cohort.
