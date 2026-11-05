# FUSION_EXPERIMENT_RESULTS — FUSION-E1

## Lần chạy

| Mục | Giá trị |
|---|---|
| RUN_ID | `E1-20261023T112847Z` |
| Thời gian | 2026-10-23, 11:28–12:02 UTC |
| Pod | RunPod `v9v82clkksqjhv`, NVIDIA A40 48 GB, Secure Cloud, $0,59/giờ |
| Môi trường | torch 2.9.1+cu128, BF16 |
| Projmem trên pod | chấm điểm `run_e7427df849e14f5987c661c14f3212fc`, đánh giá `run_9183c19d97164256905a33c40cf5ec7a` (cả hai success) |
| Chi phí | khoảng $0,44 (số dư $4,63 → $4,20) |
| VRAM đỉnh | 17,9 GB allocated / 46,7 GB reserved |
| Bằng chứng | `evidence/E1-20261023T112847Z/` (results, summary, parity, manifest, pmem.db, log). Export đầy đủ 97 MB (sha `52334d41…`) nằm trên volume của pod |

## Parity: QUA cả 5 run (fail-closed)

| Run | Ghi lúc train | Tái lập trên A40 |
|---|---|---|
| Sequence HDFS-fold, BGL | AUROC 0,8025, AP 0,0890 | AUROC 0,8067, AP 0,0906 |
| Semantic HDFS-fold | NLL BGL 0,8196 | NLL BGL 0,8238 |

Hai run Sequence còn lại (fold Hadoop, fold BGL) và Semantic fold Hadoop cũng đều PASS.

## Kết quả trên unit mới (chưa dùng để chọn checkpoint)

Tỉ lệ bất thường: BGL 4,4% (67/1.536); HDFS 1,4% (21/1.519).

| Nguồn | Fold | Sequence best | Semantic best | B0 tần suất | Base Seq / Base Sem | **Cauchy (K1, chính)** | VW mean (K3) | Seq ⊕ B0 (control) |
|---|---|---|---|---|---|---|---|---|
| BGL | HDFS-tgt | AP .145 / AUROC .857 | .109 / .670 | .108 / .806 | .062/.496 · .072/.478 | .124 / .769 | **.180** / .799 | .181 / **.890** |
| BGL | Hadoop-tgt | .121 / .815 | .118 / .709 | .108 / .806 | như trên | .115 / .741 | **.205** / .776 | .157 / .857 |
| HDFS | Hadoop-tgt | **.215** / .744 | .032 / .639 | .037 / .731 | .023/.560 · .014/.369 | .121 / .713 | .057 / .711 | .218 / .753 |
| HDFS | BGL-tgt (Sem base) | .216 / .721 | — (base .014/.369) | .037 / .731 | | .115 / .605 | .018 / .558 | .218 / .743 |

## Fusion Gain (AP fused − max AP đơn; CI 95% bằng cluster bootstrap, 2.000 lần)

| Nguồn / fold | K1 Cauchy | K2 LR-Cauchy | K3 VW mean |
|---|---|---|---|
| BGL / HDFS-tgt | −0,021 [−0,120; +0,018] | −0,087 [−0,243; −0,032] | +0,035 [−0,114; +0,142] |
| BGL / Hadoop-tgt | −0,006 [−0,107; +0,013] | −0,066 [−0,255; −0,032] | +0,083 [−0,091; +0,193] |
| HDFS / Hadoop-tgt | −0,095 [−0,186; +0,001] | −0,007 [−0,057; +0,028] | −0,158 [−0,321; −0,025] |
| HDFS / BGL-tgt (exploratory) | −0,101 [−0,193; +0,001] | +0,008 [−0,072; +0,080] | −0,198 [−0,399; −0,041] |

## Kết luận theo protocol đã đăng ký

- **K1 (Cauchy) KHÔNG đạt tiêu chí thành công** ở bất kỳ fold nào: gain điểm âm, cận dưới CI < 0. Vì kiểm định theo thứ tự cố định, K2 và K3 cũng không được khẳng định.
- **Semantic không hơn B0.** AUROC BGL .67–.71 so với .806 của B0; AP HDFS .032 so với .037. Semantic **có hơn** mô hình nền (.48/.37), nên LoRA có tác dụng, nhưng chưa đủ.
- **Sequence là expert mạnh nhất:**
  - hơn base: AUROC .50 → .82–.86 trên BGL;
  - hơn B0 về AP: BGL .145 so với .108; HDFS .215 so với .037;
  - checkpoint latest kém hơn best trên BGL. Hiện tượng "train lâu hơn thì phát hiện kém đi" được xác nhận trên unit mới.
- **Độ bổ sung có thật nhưng nhỏ.** Ở top 5%, Semantic bắt được 6 bất thường mà Sequence bỏ sót (BGL), Sequence bắt 9–11; Jaccard top 5% ≈ 0,01. Tuy vậy Semantic quá nhiễu nên phần lớn luật gộp bị kéo xuống.
- **Quan sát post-hoc (chưa khẳng định):**
  - Trên BGL, VW mean (AP .18–.21) và Seq ⊕ B0 (AUROC .86–.89) là tốt nhất.
  - Mô phỏng D-07 không dự báo đúng: Semantic yếu hơn nhiều so với giả định hai expert có độ mạnh ngang nhau.
- **Comparator logistic học được: kết quả không hợp lệ** (AUROC .39–.46 trên BGL). Nguyên nhân là lỗi đánh giá: điểm out-of-fold từ hai mô hình có intercept khác nhau (−3,5 so với −6,5) bị gộp chung để xếp hạng. Cần sửa (xếp hạng trong từng fold hoặc bỏ intercept) rồi chạy lại trên CPU. Kết luận này đến từ phân tích, chưa chạy lại.
- **Chi phí suy luận trên A40, batch theo token budget 4.096:**

  | Expert | Tốc độ | Thời gian / 1.000 unit |
  |---|---|---|
  | Sequence | khoảng 19–20 cửa sổ/giây | khoảng 52 giây |
  | Semantic | khoảng 78–86 bản ghi/giây | khoảng 12 giây |

  Tham số: mỗi adapter 13,6 triệu; luật fusion 0.

**Mọi kết luận là preliminary:** một seed, chỉ đánh giá trên source-dev (cùng hệ thống, giai đoạn sau), chưa có hệ đích.

---

# FUSION-E1.1 — KHÁM PHÁ (post hoc, thiết kế sau khi đã xem E1; không phải kết quả khẳng định)

## Lần chạy

| Mục | Giá trị |
|---|---|
| Pod | `a3xfs2sf1zj0fu`, A40 Secure, EU-SE-1. Pod cũ `v9v82clkksqjhv` không bật lại được (máy chủ hết GPU) nên đã xóa theo yêu cầu |
| Thời gian | 2026-10-23, 12:25–13:18 UTC |
| Chi phí | khoảng $0,55 (số dư $4,20 → $3,65) |
| Chạy lại E1 | `E1R-20261023T123402Z`: 12 job chấm điểm **khớp E1 tới 3 chữ số thập phân**; 5/5 parity PASS |
| Code | kit gốc + overlay 9 file (`evidence/E11-*/kit/OVERLAY_E11.sha256`) |
| Projmem trên pod | chấm `run_4937e926…`, đánh giá `run_b4dfac79…`, multimask `run_aefd4675…`, đánh giá E1.1 `run_1e2fdd85…` / `run_16f4f1b0…` / `run_0f5fca9b…` |
| Bằng chứng | `evidence/E11-20261023T130134Z/` |

## A. Comparator logistic đã sửa lỗi xếp hạng (D-15)

Sau khi sửa, kết quả hợp lệ (AUROC 0,74–0,80 trên BGL) nhưng vẫn **thua Sequence đơn**:

| Nguồn / fold | Gain AP | CI 95% |
|---|---|---|
| BGL / HDFS-tgt | −0,036 | [−0,218; −0,015] |
| BGL / Hadoop-tgt | −0,031 | [−0,227; −0,015] |
| HDFS | +0,011 | không có ý nghĩa thống kê |

Kết luận: fusion head có train không mang lại lợi ích.

## B. Sequence ⊕ B0 (so với thành phần tốt hơn của chính nó)

| Nguồn / fold | Luật Cauchy | Luật VW mean |
|---|---|---|
| BGL / HDFS-tgt | +0,037 [+0,014; +0,053], p = 0,003 | **+0,174 [+0,069; +0,304], p = 0,001 → AP 0,319, AUROC 0,928** |
| BGL / Hadoop-tgt | +0,035 [+0,005; +0,053], p = 0,012 | **+0,154 [+0,050; +0,293], p = 0,002 → AP 0,275, AUROC 0,902** |
| HDFS (2 fold) | +0,003 (không ý nghĩa) | −0,169 / −0,170 (có hại: B0 trên HDFS gần mức ngẫu nhiên) |

## C. Semantic chấm với 8 mask (seed 42–49). Seed 42 khớp E1 tuyệt đối (|Δ| = 0)

| Biến thể Semantic | BGL / HDFS-tgt AP · AUROC | BGL / Hadoop-tgt AP · AUROC | HDFS / Hadoop-tgt AP · AUROC |
|---|---|---|---|
| 1 mask (E1) | 0,109 · 0,670 | 0,118 · 0,709 | 0,032 · 0,639 |
| **trung bình 8 mask** | **0,171 · 0,842** | **0,237 · 0,871** | 0,066 · 0,519 |
| max 8 mask | 0,143 · 0,763 | 0,132 · 0,781 | 0,019 · 0,530 |

**Kết luận về Semantic:**
- Trên BGL, trung bình 8 mask **vượt B0** (AUROC 0,806) và ở fold Hadoop **vượt cả Sequence** (AP 0,237 so với 0,121). Kết quả này xác nhận dự đoán của R1: điểm Semantic hiện phụ thuộc vào việc từ bất thường có rơi vào đúng phần bị che hay không, nên lấy trung bình nhiều lần che làm điểm ổn định hơn.
- Trên HDFS, Semantic vẫn không dùng được.

**Fusion với Semantic trung bình 8 mask, luật VW, trên BGL:**

| Fold | AP | AUROC | Gain | CI 95% | p |
|---|---|---|---|---|---|
| HDFS-tgt | 0,317 | 0,925 | +0,147 | [−0,084; +0,303] | 0,097 |
| Hadoop-tgt | 0,369 | 0,924 | +0,133 | [−0,109; +0,318] | 0,146 |

Gain điểm dương nhưng CI vẫn chứa 0. Luật Cauchy, Bonferroni và copula đều không có gain.

## Tóm tắt E1.1

- **Trên BGL:** hai cấu hình tốt nhất là (i) **Seq ⊕ B0, luật VW** (gain có ý nghĩa thống kê) và (ii) **Sem trung bình 8 mask ⊕ Seq, luật VW** (AP cao nhất, 0,369, nhưng chưa có ý nghĩa thống kê).
- **Trên HDFS:** Sequence đơn tốt nhất; mọi cách gộp đều không giúp được.
- Cả hai cấu hình đều được chọn **sau khi đã xem dữ liệu**, nên phải xác nhận lại trên dữ liệu độc lập (hệ đích E2 hoặc seed mới), với luật chốt trước. Gộp 3 thành phần (Sem trung bình 8 mask + Seq + B0) chưa được thử.

---

# FUSION-E2-CONFIRM — XÁC NHẬN TRÊN COHORT ĐỘC LẬP (đăng ký trước: `FUSION_E2_CONFIRM_PREREG.md`, kèm phụ lục D-18)

## Lần chạy

| Mục | Giá trị |
|---|---|
| Pod | `9cl3v8246zip6x`, A40 Secure, EU-SE-1 |
| Thời gian | 2026-10-23, 14:32–14:55 UTC |
| RUN | `E2C-20261023T143258Z` |
| Projmem trên pod | chấm `run_96b4ca04…`, đánh giá `run_1c664859…` |
| Anchor parity | PASS: AUROC 0,8056 so với 0,8025 đã ghi; AP 0,0903 so với 0,0890 |
| Cohort mới | BGL 2.048 dòng, 89 bất thường. HDFS 1.969 block, 18 bất thường (đã loại 57 block trùng E1) |
| Bằng chứng | `evidence/E2C-20261023T143258Z/` |

## Họ giả thuyết chính (Holm, α = 0,05)

| Giả thuyết | Fold HDFS-tgt (BGL) | Fold Hadoop-tgt (BGL) | Kết luận |
|---|---|---|---|
| **H1: VW(Seq, B0) hơn max(Seq, B0)** | **+0,181 [+0,052; +0,353], p = 0,001** | **+0,132 [+0,022; +0,300], p = 0,001** | **XÁC NHẬN** ở cả 2 fold |
| H2: VW(Sem-mk8, Seq) hơn max | +0,103 [−0,102; +0,251], p = 0,14 | +0,092 [−0,096; +0,268], p = 0,19 | Không xác nhận |

## Giả thuyết phụ

| Giả thuyết | Kết quả |
|---|---|
| H3: Sem-mk8 hơn Sem 1 mask | +0,055 (p = 0,026) và +0,071 (p = 0,010) trên BGL. Xác nhận ở mức danh nghĩa |
| H3b: Sem-mk8 hơn B0 | p = 0,11 và 0,04. Chưa thuyết phục |
| H4: Cauchy(Seq, B0) không kém Seq trên HDFS | Đạt ở cả 2 fold (cận dưới CI −0,005 và −0,003) |

**Khám phá:** VW 3 thành phần (Sem-mk8, Seq, B0) trên BGL đạt **AP 0,442 / 0,432 và AUROC 0,939 / 0,929**. Gain so với thành phần đơn tốt nhất là +0,292 [+0,021; +0,465] và +0,253 [+0,024; +0,422]. Cấu hình này là khám phá, chưa được đăng ký trước.

## Cảnh báo quan trọng: HDFS không tái lập

Trên cohort mới, **mọi phương pháp gần như ngẫu nhiên trên HDFS**: Sequence AUROC 0,55 / 0,54, AP 0,016–0,044, tỉ lệ bất thường 0,9%. Ở E1 cùng chỉ số này là AUROC 0,72–0,74, AP 0,215. Kết quả HDFS ở E1 dựa trên 21 mẫu dương và **không ổn định**. Hiện chưa thể khẳng định phát hiện được bất thường trên HDFS.

---

# FUSION-E3-HDFS (2026-10-23, pod `qgt8q0e3unb5w4`) và baseline bài báo
3.000 block HDFS, 65 block bất thường. Chấm mọi dòng; block-max là cách tổng hợp chính.

| Phương pháp | AP | AUROC |
|---|---|---|
| **Sequence** | **0,606** | 0,762 |
| DeepLog (CCS'17) | 0,378 | 0,740 |
| PCA (SOSP'09) | 0,177 | 0,475 |
| kNN TF-IDF | 0,021 | 0,492 |
| Isolation Forest | 0,023 | 0,241 |
| Semantic (1 mask) | 0,061 | 0,544 |
| Cauchy(Seq, Sem) | 0,355 | 0,732 |

- H5a, H5b, H6 PASS sau Holm.
- H7: Cauchy(Seq, B0) không kém Sequence.
- Các baseline ở đây chưa ghép cặp bootstrap (unpaired).
- Bằng chứng: `evidence/E3H-20261023T161559Z/`.

# FUSION-E4-GATED (2026-10-23, pod `dar52u92uqpe7r`, đăng ký trước `FUSION_E4_GATED_PREREG.md`)
Cohort mới hoàn toàn:
- BGL: 16.384 dòng, 688 bất thường, dùng ở 2 fold.
- HDFS: 3.000 block, 81 bất thường, fold Hadoop.

Semantic dùng trung bình 8 mask. G = cổng tail-lift: nếu lift ≥ 2 và p < 0,01 thì dùng VW(Seq, Sem), ngược lại dùng Seq.

| Cohort | lift (cổng) | Seq AP | Sem AP | **G AP** | VW không cổng | Cauchy không cổng | DeepLog | PCA | kNN |
|---|---|---|---|---|---|---|---|---|---|
| BGL@HDFS-fold | 1,45 (đóng) | 0,136 | 0,156 | 0,136 | **0,259** | 0,156 | 0,111 | 0,122 | 0,168 |
| BGL@HADOOP-fold | 2,46 (mở) | 0,116 | 0,195 | **0,275** | 0,275 | 0,164 | 0,111 | 0,122 | 0,168 |
| HDFS@HADOOP-fold (max) | 2,98 (mở) | **0,705** | 0,206 | 0,472 | 0,472 | 0,691 | 0,544 | 0,267 | 0,026 |

**Họ chính (Holm): KHÔNG đạt cả 3.**
- H9a (BGL@HDFS): gain −0,020. Cổng đóng nên G chính là Seq.
- H9b (BGL@HADOOP): gain +0,080, CI [−0,022; +0,168], p = 0,061.
- H10 (HDFS): G − Seq = −0,234, CI [−0,318; −0,082].
- Dự đoán H8 về hành vi của cổng sai ở 2/3 cohort.

**Khám phá:**
- VW(Seq, Sem-mk8) không cổng trên BGL: +0,104 [+0,014; +0,173] ở fold HDFS và +0,080 [−0,022; +0,168] ở fold Hadoop.
- Gộp cả E2C (+0,10 / +0,09), mức tăng dương ở 4/4 lần đo trên BGL; chỉ 1 lần có ý nghĩa thống kê.
- Trên HDFS, Cauchy không cổng (0,691) gần bằng Seq (0,705): luật Cauchy chịu được một mô hình nhiễu, nhưng trên BGL gần như không tăng.

**Sequence so với DeepLog trên HDFS (ghép cặp):** +0,162 [+0,074; +0,247].

**Họ phụ:** G trên BGL@HADOOP thắng mọi baseline sau Holm.

**Chẩn đoán D-20:** chênh lệch do dedupe không đáng kể.

**Kết luận:** độ trùng ở đuôi trên đo mức "cùng thấy hiếm", không phải "cùng thấy bất thường". Trên HDFS, các message hiếm nhưng bình thường đẩy cả hai mô hình lên cao. Phát hiện không cần nhãn khi nào nên dùng Semantic vẫn là bài toán mở (đúng với cảnh báo của Ma et al., SIGKDD Explor. 2023).

Bằng chứng: `evidence/E4-20261023T180203Z/`.
