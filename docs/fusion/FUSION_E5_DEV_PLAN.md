# FUSION-E5-DEV: kế hoạch (khóa 2026-10-24, trước khi chấm điểm)

**Mục đích:** phát triển, không phải xác nhận. Chọn **một** cấu hình fusion 2 mô hình. Nếu chọn được thì đem kiểm trên tập mới ở E5-CONFIRM.

## Dữ liệu
Dùng lại cohort E4 làm DEV:
- BGL: 16.384 dòng, ở 2 fold.
- HDFS: 3.000 block, ở fold Hadoop.

Nhãn của E4 đã được mở, nên mọi con số ở đây **không được coi là bằng chứng xác nhận**.

## Điểm số
Mô hình đóng băng, chấm có dedupe:
- `sequence_<fold>_best`.
- `semantic_<fold>_best_mkmean`: Semantic gốc, trung bình 8 mask.
- `semantic_template_<fold>_best_mkmean`: Semantic không tính NLL ở các từ chứa ≥ 3 chữ số (`fusion/volatile.py`, D-22).

Điểm rút gọn (window_id → nll_mean) **được tải về máy trước khi tắt pod**.

## Không gian cấu hình
- Biến thể Semantic: {gốc, template}.
- Luật gộp: các luật trung bình tổng quát M_{r,w}, với
  - r ∈ {1; 0,5; 0; −0,5; −1; −2; −4; −8; −∞},
  - w ∈ {0,3; 0,4; 0,5; 0,6; 0,7; 0,8; 0,85; 0,9; 0,95} (w là trọng số của Sequence),
- cộng thêm Cauchy.
- Unit: BGL tính theo từng dòng; HDFS tính theo block, lấy max (như E3 và E4).

## Tiêu chí chọn (chốt trước)
- gain(cohort) = AP(fused) − max(AP(Seq), AP(Sem cùng biến thể)).
- Một cấu hình **đạt** khi thỏa cả hai điều kiện:
  - gain ≥ −0,02 trên **cả 3** cohort;
  - gain > 0 trên ít nhất 1 cohort BGL.
- Trong các cấu hình đạt, chọn cấu hình có gain thấp nhất (worst-case) lớn nhất. Nếu hòa, chọn cấu hình có gain trung bình lớn hơn.
- **Nếu không có cấu hình nào đạt:** dừng, không chạy E5-CONFIRM. Ghi nhận giới hạn trong luận văn.
