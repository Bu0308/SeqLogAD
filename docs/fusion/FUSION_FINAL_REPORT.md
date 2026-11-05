# FUSION_FINAL_REPORT — SeqLogAD: Semantic + Sequence Fusion (FUSION-E1)

**Trạng thái (2026-10-23):**
- Nghiên cứu, thiết kế, hiện thực và test cục bộ **đã xong**.
- Lượt chấm GPU và đánh giá thật **chưa chạy**: phiên làm việc chưa kết nối RunPod MCP và chưa có ngân sách được duyệt.
- **Chưa có** kết luận khoa học nào về việc fusion có cải thiện hay không.

## 1. Mục tiêu

Xác định hai expert LLM đã train có bổ sung thông tin cho nhau không, và một luật fusion có cơ sở khoa học có phát hiện bất thường tốt hơn expert đơn tốt nhất không. Bối cảnh là LOAO xuyên hệ thống, không có nhãn đích.

## 2. Hai mô hình có sẵn

Chi tiết ở `TRAINING_AUDIT_REPORT.md`.

- **Model A — Semantic:** NLL khi tái tạo thông điệp bị che 30%.
- **Model B — Sequence V13R1:** NLL của log kế tiếp, với tối đa 8 bản ghi trước.
- Cả hai là LoRA r16 (13,6 triệu tham số) trên cùng Llama-3.1-8B NF4 đóng băng.
- Đầu ra của mỗi expert là một số vô hướng trên mỗi unit.

Vấn đề chính:
- Semantic chưa từng được đo AUROC/AP.
- Sequence phát hiện kém đi khi train lâu hơn; checkpoint tốt nhất rơi vào step 100–300.
- Thiếu adapter Semantic-BGL.
- Lỗi nạp checkpoint Semantic (đã có bridge sửa).

## 3. Phương pháp chọn và lý do

Chọn **K1: Cauchy combination trên p-value ECDF không dùng nhãn (late fusion, 0 tham số)**. Đi kèm hai biến thể:
- **K2:** LR-Cauchy, dùng hiệu NLL_adapter − NLL_base.
- **K3:** Vovk–Wang mean.

Các ứng viên này được kiểm định theo thứ tự cố định K1 → K2 → K3.

**Vì sao:**
- Đầu vào là điểm vô hướng, và thang đo của hai expert lệch nhau khoảng 100 lần.
- Không có nhãn đích; nhãn source chỉ đủ cho khoảng 2 tham số. Vì vậy mọi kiểu fusion sâu hoặc fusion có học đều không đáng tin, và đã bị loại kèm lý do.
- Mô phỏng D-07, chạy trước khi có điểm thật, cho thấy Cauchy là luật **duy nhất** có fusion gain dương ở cả 18 kịch bản AND/OR/MIXED. Luật trung bình (Vovk–Wang, Stouffer) thua tới −0,37 AP khi bổ sung kiểu OR.

Cơ sở tài liệu:
- Liu & Xie, JASA 2020.
- Vovk & Wang, Biometrika 2020.
- Bates et al., Ann. Stat. 2023.
- Gupta et al., EMNLP 2025.
- Ren et al., NeurIPS 2019 và Serrà et al., ICLR 2020 (cho K2).
- Đầy đủ 27 công trình ở `FUSION_LITERATURE_REVIEW.md`.

**Không** khẳng định K1 tốt nhất tuyệt đối.

## 4. Kiến trúc và hiện thực

Chi tiết ở `FUSION_IMPLEMENTATION_PLAN.md`.

- Package `src/seqlogad/fusion/` gồm 12 module, mỗi module dưới 220 dòng.
- Package nằm ngoài implementation digest, nên digest V13R1 vẫn là `78a18851…` (có test).
- Thành phần chính:
  - Bridge nạp Semantic.
  - Bộ chấm batch cho một base cộng 10 adapter.
  - Parity fail-closed: phải tái lập AUROC/AP/NLL đã ghi.
  - Baseline B0, các luật fusion, comparator logistic cross-fit.
  - Metrics, cluster bootstrap, DeLong.
- Test: 30/30 pass (Projmem `run_c4320284e319419291a44878871d49bb`). Test phát hiện và sửa hai lỗi thật:
  - `set_adapter` của PEFT bật lại gradient.
  - Luật VW làm giảm AP khi bổ sung kiểu OR.

## 5. Protocol đánh giá (đã đóng băng)

Chi tiết ở `FUSION_EVALUATION_PROTOCOL.md` (config sha `4a83b835…`).

- **Dữ liệu và metric:** unit source-dev mới (BGL 67 dương, HDFS 21 dương). Metric chính AP; phụ AUROC, recall@1%/5%, chỉ số độ bổ sung.
- **Fusion Gain:** so với max của hai expert đơn, có khoảng tin cậy cluster bootstrap 95%.
- **Control:** Seq-best ⊕ Seq-latest, Sem ⊕ B0, Seq ⊕ B0.
- **Giới hạn:** chỉ một seed, nên mọi kết luận sẽ là *preliminary*.

## 6. RunPod

**Chưa tạo pod.**

Chưa tạo vì: không có RunPod MCP và không có `runpodctl` trong phiên này. Theo hướng dẫn chính thức, người dùng phải tự cài plugin và đăng nhập OAuth. Chỉ thị cũng yêu cầu duyệt chi phí trước khi tạo pod.

Ước tính chi phí:
- Khoảng 40.000 lượt forward (10 adapter + 2 job base + parity), cộng cài môi trường, tải 16 GB trọng số và giải nén.
- Tổng **khoảng 1–2 giờ A40**; đề xuất **trần 3 giờ**.
- Giá A40 phải xem trực tiếp qua MCP. Theo mức thường gặp khoảng 0,35–0,45 USD/giờ, phần GPU chỉ khoảng **0,4–1,4 USD**.
- Storage 60 GB tốn thêm theo giá volume hiện hành. Đây là ước tính, chưa phải giá đã xác minh.

## 7. Kết quả

**Chưa có kết quả.** Xem `FUSION_EXPERIMENT_RESULTS.md`; không có số nào bị bịa.

## 8. Giới hạn đã biết

- E1 đo **tính bổ sung trên log của hệ nguồn, ở giai đoạn sau khi train**, chưa phải phát hiện trên hệ đích chưa từng thấy. Phần đó là E2, cần amendment LATE và đồng ý mở nhãn.
- Fold BGL chỉ có Semantic dạng base.
- Hadoop: theo Landauer 2024, khoảng 82,9% chuỗi Hadoop là bất thường, nên AP ở Hadoop có thể không có nhiều ý nghĩa. Chỉ dùng Hadoop để mô tả.
- Chỉ một seed. Không tất định ở mức bit.

## 9. Bước tiếp theo

1. Bạn cài và đăng nhập RunPod theo hướng dẫn chính thức (lệnh ở phần trả lời trong chat), rồi duyệt ngân sách.
2. Tạo đúng 1 pod A40 kèm volume, upload kit (2,2 GB, có `SHA256SUMS`), đặt secret `HF_TOKEN`, rồi chạy `scripts/fusion_e1_runpod.sh`.
3. Tải `exports/fusion-<RUN_ID>.tar.gz` + `.sha256` về, kiểm lại, import Projmem, rồi dừng pod.
4. Điền `FUSION_EXPERIMENT_RESULTS.md` và `FUSION_ABLATION_REPORT.md` từ `results.json` và quyết định theo gate ở mục 4 của protocol.
