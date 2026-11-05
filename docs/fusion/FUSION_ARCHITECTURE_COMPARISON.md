# FUSION_ARCHITECTURE_COMPARISON

**Ràng buộc thực tế** (xem `TRAINING_AUDIT_REPORT.md`):
- Mỗi expert chỉ cho ra **một số vô hướng trên mỗi unit**.
- Hai expert dùng chung một backbone Llama-3.1-8B đóng băng, khác adapter, prompt và hệ số (2 so với 8).
- **0 nhãn đích.** Nhãn source chỉ có 67 + 21 mẫu dương mới (cộng 16 + 10 đã dùng để chọn checkpoint).
- Một seed. M1 8 GB không chạy được 8B, nên mọi forward phải chạy trên GPU.

Nguyên tắc EPV ≥ 10 cho phép khoảng **2 tham số học từ nhãn**.

## 1. So sánh các họ phương pháp

| Họ | Tương thích | Cần dữ liệu | Nguy cơ overfit | Chi phí | Bằng chứng | Kết luận |
|---|---|---|---|---|---|---|
| Early fusion / concatenation đầu vào | Thấp: hai expert dùng prompt khác nhau trên cùng backbone; ghép prompt là tạo **một expert mới** và phải train lại | Nhiều | Cao | Train 8B | Baltrušaitis 2019 (khung lý thuyết) | Loại |
| Intermediate fusion: cross-attention, bidirectional, MulT, MBT, Transformer fusion | Thấp: cần chuỗi feature, cần end-to-end supervised | Hàng nghìn nhãn | Rất cao (26–114 mẫu dương) | GPU train | MulT ACL'19, MBT NeurIPS'21 | Loại |
| Tensor / bilinear (TFN, LMF) | Đầu vào vô hướng làm tích ngoài suy biến | Có nhãn | Cao | Thấp | TFN EMNLP'17, LMF ACL'18 | Loại |
| Gated / adaptive (GMU, gate MLP), MoE (Shazeer'17, LogMoE ASE'25), AdapterFusion, MoLE, X-LoRA | Gate cần loss có nhãn; LogMoE cần nhãn source | Có nhãn | Rất cao | Train | LogMoE (cross-system, có nhãn) | Chỉ làm comparator tối giản (logistic 3 tham số, cross-fit) |
| Gộp LoRA (LoraHub, TIES, DARE, LoRA Soups) | Hai objective khác nhau; gộp ra **một** NLL mới, mất tính đa dạng | Few-shot có nhãn | Cao | Thấp | NeurIPS'23, ICML'24 | Loại |
| Contrastive fusion | Cần cặp positive/negative và train | Nhiều | Cao | Train | — | Loại |
| **Late / decision fusion ở mức điểm, hiệu chỉnh không cần nhãn** | **Cao:** dùng đúng đầu ra thực của hai expert | Không cần nhãn | Thấp | CPU (sau một lượt chấm GPU) | Bates (Ann. Stat. 2023), Vovk–Wang (Biometrika 2020), Liu–Xie (JASA 2020), Gupta (EMNLP 2025), Kriegel (SDM 2011) | **Chọn** |

## 2. Mô phỏng chọn luật (D-07, trước khi có bất kỳ điểm thật nào)

Cách làm:
- Mô phỏng hai expert binormal, tương quan ρ ∈ {0; 0,5; 0,8} và độ lệch d ∈ {1,5; 3}.
- Ba chế độ bổ sung:
  - **AND:** cả hai expert cùng thấy mọi bất thường.
  - **OR:** mỗi bất thường chỉ một expert thấy. Đây là kiểu R1 dự đoán cho burst và context break.
  - **MIXED:** trộn hai kiểu trên.
- Mỗi kịch bản 30 seed. Fusion gain = AP(fused) − max AP(expert đơn).

Script `scripts/fusion_rule_simulation.py`; kết quả đầy đủ ở `evidence/D07-rule-simulation.json` (Projmem `run_e95caddef1a94f98af70b259fcaa8371`).

| Luật | Số kịch bản gain > 0 (trên 18) | AND | OR / MIXED |
|---|---|---|---|
| **Cauchy combination** | **18** | +0,008 … +0,13 | +0,02 … +0,28 |
| Bonferroni 2·min p | 17 | nhỏ (≈ 0 đến +0,07) | lớn |
| Copula một phía | 15 | **âm khi ρ cao** (−0,15) | lớn nhất ở OR với ρ cao |
| Fisher | 12 | tốt | âm khi ρ cao |
| z-score mean | 9 | tốt | âm |
| Stouffer | 8 | tốt nhất ở AND | âm tới −0,24 |
| Vovk–Wang 2·mean p | 7 | tốt | **âm tới −0,37** |

Ý nghĩa:
- Các luật trung bình (cộng, AND-mềm) pha loãng những bất thường chỉ một expert thấy.
- Các luật lấy cực trị thì yếu khi hai expert cùng thấy.
- **Cauchy** bền nhất khi chưa biết dữ liệu thật thuộc chế độ nào. Đây là bằng chứng mô phỏng, chưa phải bằng chứng trên dữ liệu log.

## 3. Top 3 và kiến trúc được chọn

| | **K1: Cauchy late fusion (chính)** | **K2: LR-Cauchy (trừ NLL của mô hình nền)** | **K3: Vovk–Wang mean** |
|---|---|---|---|
| Vì sao hợp với hai expert này | Đầu vào là điểm vô hướng; thang đo lệch nhau khoảng 100 lần; không có nhãn; bền với chế độ bổ sung chưa biết | Sequence càng train càng phát hiện kém; mô hình nền là tham chiếu tự nhiên vì cùng backbone (Serrà ICLR 2020) | Tiền lệ gần nhất (Gupta EMNLP 2025, layer-ensemble trên LLM); hợp lệ dưới mọi phụ thuộc |
| Nối ở tầng | Quyết định, sau khi gộp về unit | Như K1, trên r = NLL_adapter − NLL_base | Như K1 |
| Feature | p_sem, p_seq (ECDF, mid-rank) | p của r_sem, p của r_seq | p_sem, p_seq |
| Projection / alignment | Không cần projection. Căn unit theo (architecture, rank) và hiệu chỉnh ECDF | Như K1 + cùng prompt và mask cho base | Như K1 |
| Backbone | Đóng băng cả base lẫn adapter | Đóng băng | Đóng băng |
| Huấn luyện | **Không**: 0 tham số | 0 tham số | 0 tham số |
| Loss | Không có | Không có | Không có |
| Rủi ro | Bị chi phối bởi một expert nhiễu nặng ở đuôi | Base đã phát hiện tốt sẵn thì r mất tín hiệu | Pha loãng khi bổ sung kiểu OR (D-07) |
| Đo | ΔAP so với max expert đơn; recall@1%/5%; DeLong | Như K1 + AP của base và của r | Như K1 |

**Kiến trúc chọn để thử trước:** K1. Nó dùng được ngay với đúng thứ hai mô hình đang có (điểm NLL), không có tham số nào nên không thể overfit 26–114 mẫu dương, và chỉ cần một lượt chấm GPU. K2 và K3 chạy kèm theo thứ tự kiểm định cố định. **Không** khẳng định K1 tốt nhất tuyệt đối; đây là lựa chọn hợp lý nhất *trước* khi có dữ liệu.

**Sensitivity và comparator** (chạy cùng lượt, báo cáo đầy đủ): Bonferroni, copula một phía, Fisher, Stouffer, z-score mean, logistic học được (3 tham số, cross-fit theo nửa thời gian).

**Control:** Seq-best ⊕ Seq-latest (ensemble cùng một expert); Sem ⊕ B0 và Seq ⊕ B0 (B0 = −log tần suất trên SOURCE_TRAIN).
