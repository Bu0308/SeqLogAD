# FUSION_ABLATION_REPORT

## Đã hoàn thành

| Ablation | Dữ liệu | Kết quả |
|---|---|---|
| So sánh 7 luật gộp ở 3 chế độ bổ sung × 3 mức ρ × 2 độ lệch | **Tổng hợp** (binormal, 30 seed) | Cauchy gain > 0 ở 18/18 kịch bản; Bonferroni 17; copula 15; Fisher 12; z-mean 9; Stouffer 8; Vovk–Wang 7. Luật trung bình âm khi bổ sung kiểu OR (xem `ARCHITECTURE_COMPARISON` mục 2) |
| Batch so với single | Llama tí hon (CPU) | \|ΔNLL\| ≤ 1e-5 |

## Đã lập kế hoạch, sẽ chạy trong cùng một lượt chấm E1 (không tốn thêm GPU)

| Ablation | So sánh | Trả lời câu hỏi nào |
|---|---|---|
| Bỏ fusion | Sem đơn, Seq đơn, so với K1/K2/K3 | Fusion có lợi không |
| Bỏ từng nhánh | Sem-only, Seq-only, LR-Sem-only, LR-Seq-only | Nhánh nào đóng góp |
| Checkpoint | base / best / latest cho cả hai expert | Hiện tượng NLL giảm thì phát hiện kém đi có lặp lại trên unit mới không |
| Alignment / calibration | ECDF so với z-score thô | Calibration có cần thiết không |
| Luật gộp | Cauchy, VW, Bonferroni, copula, Fisher, Stouffer | Chế độ bổ sung thực tế là AND hay OR |
| Độ phức tạp | 0 tham số so với logistic 3 tham số (cross-fit) | Học trọng số có đáng không |
| Control | Seq-best ⊕ Seq-latest; Sem ⊕ B0; Seq ⊕ B0 | Lợi ích có phải chỉ do ensemble hay chỉ do tần suất template |

## Không áp dụng, kèm lý do

- **Vị trí fusion (early/intermediate):** cần prompt chung hoặc train lại một mô hình 8B; không có nhãn để train. Đã loại ở D-02.
- **Freeze so với fine-tune:** fine-tune backbone hay adapter là train lại expert. Việc này cần nhiều GPU và nằm ngoài lượt được duyệt.
- **Kích thước feature:** luật dùng điểm vô hướng. Hidden state 4096 chỉ được lưu để làm baseline mật độ sau này.
