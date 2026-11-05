# TARGET_VIEW_DESIGN — View hệ đích không nhãn (TV-001)

**Trạng thái (2026-10-28):** thiết kế + builder. **Không đọc nhãn đích.** Chưa chấm điểm, chưa có kết quả.
Mục đích: tạo dữ liệu cho một lượt đánh giá trên hệ **chưa từng thấy** (E6-TARGET, sẽ đăng ký trước riêng),
trả lời phản biện (1) chưa có bằng chứng cross-system và (2) chưa có calibration bằng buffer đích.

## 1. Ràng buộc đã ký (không được thay đổi ở đây)

| Hợp đồng | Nội dung dùng ở đây |
|---|---|
| CS-SPLIT-001 v1.0 (`configs/protocols/cross-system-split-v1.yaml`, G0) | Mỗi kiến trúc chia theo thời gian: EARLY 50% · GUARD 5% (bỏ) · MID 15% · LATE 30%. Vai trò đích: `TARGET_BURN_IN = EARLY`, `TARGET_EVALUATION = MID + LATE`. Unit (block/application) gán trọn vào đoạn chứa bản ghi cuối; unit sống qua mốc cắt bị loại. |
| ADAPT-INPUT-001 v1.1 (`configs/protocols/target-buffer-v1.yaml`) | Buffer = đúng EARLY, chọn theo thời gian, cấm chọn theo nhãn/điểm. Giả định nhiễm bẩn ≤ 5% (giả định, chưa đo). Buffer REJECTED thì cấm dùng để calibrate. |
| Phase 1 record | BUFFER-ARCH-HDFS và BUFFER-ARCH-BGL `READY`; BUFFER-ARCH-HADOOP `REJECTED`. |

## 2. Các bài báo lớn làm thế nào

| Nguồn | Cách dựng tập đánh giá | Hệ quả cho chúng ta |
|---|---|---|
| Le & Zhang, ICSE 2022 | Chia **theo thời gian** (80% đầu train, 20% sau test); chứng minh chia ngẫu nhiên gây rò rỉ (DeepLog BGL F1 0,927 → 0,426). Họ ghi "the HDFS dataset does not contain timestamp information" nên không chia thời gian HDFS (bản session họ dùng; raw HDFS_v1 có timestamp từng dòng). Cửa sổ cố định 20–200 dòng hoặc 0,5–1 giờ; session theo `block_id`. Thêm Specificity. | Giữ chia theo thời gian. Ta chia được HDFS vì stream có timestamp và đã xử lý block vắt qua mốc. Báo cáo thêm FAR/Specificity. |
| Landauer et al., FSE 2024 | Phần lớn bất thường HDFS/BGL bắt được bằng *event mới* và *độ dài*; nhiều chuỗi trùng lặp; Hadoop có 82,9% chuỗi bất thường và chuỗi bình thường giống hệt chuỗi bất thường. | Bắt buộc có baseline mức **template** (novelty, tần suất) tính trên buffer. Hadoop không dùng để khẳng định. |
| ZeroLog (arXiv 2511.05862, preprint; đã đọc mục Experimental Setup) | Ở cấu hình OpenStack→HDFS/BGL, **dữ liệu đích không nhãn dùng để train** gồm số log bình thường và bất thường bằng nhau ("an equal number of normal and anomalous unlabeled logs"); dựng tập như vậy cần biết nhãn. Mục này không mô tả tỉ lệ lớp của tập test. | Không làm theo cách dựng dữ liệu đích dựa vào nhãn. Ta giữ **tỉ lệ tự nhiên**. Không khẳng định gì về tập test của ZeroLog. |
| LogTAD, LogTransfer, MetaLog — **theo mô tả cấu hình baseline trong ZeroLog**, chưa đọc bài gốc | Train trên % log đích (ví dụ 30% bình thường + 1% bất thường của BGL). | Ta không dùng nhãn đích nào trước ranh giới đánh giá. Cần đọc bài gốc trước khi trích trong luận văn. |
| Bates et al., Ann. Stat. 2023 | p-value conformal $p(x)=\frac{1+\#\{j: S_j\ge S(x)\}}{n+1}$ hợp lệ khi calibration và điểm bình thường mới hoán đổi được (exchangeable). | Calibration trên mẫu buffer; độ phân giải $1/(n+1)$. |
| Barber et al., Ann. Stat. 2023 | Khi không hoán đổi được: khoảng hụt $\le \sum_i w_i\, d_{TV}(Z_i, Z_{n+1}) / (1+\sum_i w_i)$; drift → ưu tiên điểm gần thời gian. | Thêm biến thể calibration trên **20% cuối của EARLY** (gần LATE hơn), đăng ký trước là sensitivity. Đo drift không nhãn. |
| Bashari, Sesia, Romano, arXiv 2502.04807 (2025; preprint, **chỉ đọc tóm tắt**) | Calibration bị nhiễm outlier → p-value **bảo thủ** (type-I thấp hơn danh nghĩa, mất power) nếu outlier có điểm cao; có thể sai nếu outlier có điểm thấp. | Không lọc buffer bằng nhãn (bị cấm). Báo cáo rủi ro: bão alert lặp lại trong BGL có thể làm "bình thường hoá" chính dạng alert đó. |
| Kim et al., AAAI 2022 | Point-adjust làm phồng kết quả, điểm ngẫu nhiên có thể ngang SOTA. | Không dùng point-adjust. Unit cố định trước. |
| Boyd et al., ECML-PKDD 2013 (**trích từ trí nhớ, chưa đọc lại**) | Ước lượng AP và khoảng tin cậy; sai số chủ yếu phụ thuộc số mẫu dương. | Cỡ mẫu chấm điểm chọn theo số dương kỳ vọng (mục 5). |
| López de Prado, *Advances in Financial ML* 2018 (**trích từ trí nhớ, chưa đọc lại**) | Purging/embargo quanh ranh giới train/test khi nhãn tự tương quan theo thời gian. | Cờ embargo 1 giờ đầu LATE, dùng làm sensitivity. |

## 3. Quyết định

| ID | Quyết định | Lý do / bằng chứng |
|---|---|---|
| TV-D1 | **Chỉ LATE** là tập đánh giá chính; bỏ MID. **Là amendment của CS-SPLIT-001 (vốn ghi MID+LATE) — CHƯA có chữ ký researcher.** | Unit dev của E1–E5 (đã mở nhãn, dùng để chọn cấu hình) nằm trong MID của BGL và HDFS — chính MID thuộc `TARGET_EVALUATION` (audit A7). Mọi builder cohort lọc `SOURCE_VALIDATION` (= MID) theo code. Khoảng cách ~26–28 phút tới LATE chỉ đo trên sidecar V13R1 (2.048 unit/hệ); unit của E2C/E3/E4 không còn bản local nên chưa đo. |
| TV-D2 | Fold đích: **BGL, HDFS**. Loại Hadoop. **Theo BUFFER-REJECT-001, "drop the architecture" là quyền researcher — CHƯA có chữ ký.** | Buffer Hadoop REJECTED (cấm calibrate); LATE Hadoop chỉ 15 application. |
| TV-D3 | Builder **không mở file nhãn nào**. Nhãn đọc ở bước riêng sau khi khoá prereg, có ghi audit. | Protocol v2: "Use target labels only at the final evaluation boundary". |
| TV-D4 | Unit: BGL = **dòng** (nhãn theo dòng); phụ: chunk 100 dòng liên tiếp (gộp max). HDFS = **block** (gộp max mọi dòng, **không cắt 32 dòng** như E3/E4). | Khớp độ mịn nhãn và cách train Sequence; chunk 100 dòng để so với tài liệu. LATE HDFS: trung vị 19 dòng/block, max 284. |
| TV-D5 | Window Sequence = dòng đích + ≤ 8 dòng trước **cùng nhóm, cùng LATE**. | Như P2.2; không lấy ngữ cảnh từ MID. |
| TV-D6 | `template_key` = message chuẩn hoá, mọi từ có ≥ 3 chữ số thay bằng `<V>` (luật `fusion/volatile.py`, cố định từ D-22). **Không dùng** Drain parser có sẵn. Luật này được đặt **sau khi xem dữ liệu HDFS nguồn (MID)**, nhưng trước khi xem dữ liệu LATE — không gọi là "tiên nghiệm". | Đo không nhãn: 74% dòng LATE của BGL có message chuẩn hoá chưa thấy trong EARLY; HDFS đúng 1 dòng/block mới → normalizer để lọt identifier. Drain có sẵn được fit trên BASE_TRAIN v1.1 **đã lọc bằng nhãn bình thường** ⇒ dùng nhãn đích. |
| TV-D7 | Bộ nhớ đích (B0) = đếm `template_key` và message trên **toàn bộ EARLY**. | Rẻ (CPU), hợp lệ theo hợp đồng buffer. |
| TV-D8 | Calibration: mẫu **4.095 unit** từ EARLY, chọn bằng hash trong 20 tầng thời gian (đều số bản ghi). Biến thể `recent`: chỉ tầng thuộc 20% cuối EARLY. | Độ phân giải p = 1/4096; đủ cho FAR 0,1%–1%. Barber 2023 cho biến thể gần thời gian. |
| TV-D9 | Mọi unit LATE có `stratum` (20 tầng thời gian), cờ `embargo_1h`, cờ `in_sample` (mẫu cụm phân tầng, hash, không nhãn). Chấm toàn bộ hay chấm mẫu: chốt trong prereg theo ngân sách. | Mẫu tỉ lệ đều theo tầng ⇒ tự trọng số; CI bằng bootstrap cụm theo tầng. |
| TV-D10 | Giữ tần suất tự nhiên (không khử trùng lặp unit khi tính metric); khử trùng lặp **chỉ để tiết kiệm tính toán** (input giống hệt ⇒ điểm giống hệt). | Metric phản ánh vận hành thật; đã kiểm ở D-20 rằng dedupe không làm sai điểm. |

## 4. Nội dung view (mỗi fold đích)

```
data/processed/target-views/TV-001/<FOLD>/
  buffer/records.parquet          rank, effective_ts, group, normalized_message, template_key
  buffer/memory.parquet           template_key/message → count trong EARLY (B0)
  buffer/calibration_units.parquet unit_id, stratum, recent, window/block membership
  evaluation/events.parquet       bản ghi LATE: rank, effective_ts, group, normalized_message, template_key
  evaluation/windows.parquet      target_rank, context_ranks (≤8), dedupe_key
  evaluation/units.parquet        unit_id, kind, first/last ts, n_lines, stratum, chunk100, embargo_1h, in_sample
  manifests/view.json             hash của stream/fold/buffer/hợp đồng/normalizer/code; bất biến; chẩn đoán drift; target_labels_read=false
```

Không có cột nhãn ở bất kỳ file nào. Builder kiểm: membership LATE khớp stream; buffer membership khớp `BUFFER-ARCH-*.json`;
LATE nghiêm ngặt sau EARLY; không unit nào nằm ở hai đoạn; text chuẩn hoá khớp `norm_h` đã đóng băng.

## 5. Cỡ mẫu (nếu không chấm toàn bộ)

Ước tính chỉ dùng **tỉ lệ công bố toàn dataset** (HDFS 2,93% block, BGL 7,34% dòng), không dùng nhãn LATE.
- HDFS: 20.000 block ⇒ ~586 block dương kỳ vọng. Toàn bộ LATE: 188.607 block, 735.288 window khác nhau.
- BGL: toàn bộ LATE chỉ có 226.135 window khác nhau (1.424.388 dòng) ⇒ đề xuất **chấm toàn bộ**, tránh sai số mẫu
  và hiệu ứng cụm (alert BGL đến theo đợt).
Số window khác nhau của từng phương án được ghi vào `view.json` để ước chi phí GPU trước khi prereg.

## 6. Kết quả build và cách đọc đúng (2026-10-28)

- Build không đọc nhãn; mọi bất biến PASS. Trước khi viết thiết kế, các thống kê **cấu trúc không nhãn** của LATE
  (số dòng, số window khác nhau, tỉ lệ message mới) đã được xem và ảnh hưởng tới lựa chọn chấm toàn bộ/lấy mẫu. Ghi rõ điều này trong prereg.
- BGL: 72–73% dòng LATE mang template không có trong EARLY (vẫn ~72% sau khi bỏ tên ngày/tháng, nên không phải do token lịch).
  Nhiều template mới trùng tên các loại alert BGL quen thuộc (parity error, MACHINE CHECK, ddr error, ciod error).
  **Không có nhãn thì không tách được drift của dữ liệu bình thường với các đợt bất thường.** Vì vậy chỉ được nói
  "phân phối LATE khác buffer mạnh", không được nói "drift của dữ liệu bình thường mạnh".
  Hệ quả: một baseline novelty (B0) có thể rất mạnh trên BGL; đây là điểm Landauer et al. đã cảnh báo.
- HDFS: 12.962 message → 123 template key; 4 key mới; JSD 0,08–0,25 bit.

## 7. Liêm chính: chồng lấn với TEST v1.1 đã niêm phong

Protocol v2 (dòng 38) yêu cầu tiếp tục bảo vệ các partition TEST v1.1 đã niêm phong. Theo `docs/split-artifacts-and-test-seal.md`,
TEST v1.1 của BGL là 474.797 dòng **cuối** corpus; LATE v2 là 30% cuối ⇒ TEST v1.1 BGL nằm trong LATE (HDFS: cần kiểm bằng công cụ
validate, không mở membership). **Mở nhãn LATE đồng nghĩa với mở nhãn TEST v1.1.** Trước bước đó cần quyết định có chữ ký của
researcher: dùng quy trình `seqlogad-final-test-access`, hoặc ghi một ngoại lệ có chữ ký. Builder TV-001 chỉ đọc raw text (như
các bundle Phase 2 khác), không đọc membership TEST, không đọc nhãn.

Cập nhật 2026-11-04: HDFS cũng nằm trong LATE (băm TEST tính lại khớp cả hai dataset). Bản sửa đổi đề xuất, chưa ký:
[`docs/protocol/P0-target-evaluation-amendment-2026-11-04.md`](../protocol/P0-target-evaluation-amendment-2026-11-04.md).

Sự cố 2026-10-28: trong lúc kiểm tra, assistant đã in 400 byte đầu của `data/processed/splits/bgl/sealed/TEST.jsonl`
(khoảng rank cấu trúc của một unit; không nhãn, không kết quả). Đây là truy cập ngoài quy trình; ghi nhận ở đây và trong
`_agent_ops/IMPLEMENTATION_LOG.md`. Không có thông tin nhãn nào bị lộ.

## 8. Giới hạn đã biết

- Nhiễm bẩn buffer chưa đo được trước ranh giới đánh giá (ROB-CONTAM-001). BGL toàn dataset 7,3% dòng alert > giới hạn 5% đã khai.
- Exchangeability EARLY↔LATE không được đảm bảo; chỉ đo drift không nhãn và báo cáo FAR thực tế ở ranh giới đánh giá.
- Một seed huấn luyện; không thay đổi ở bước này.
- HDFS: 19,8% bản ghi bị loại do block vắt mốc (EXC-001/002); chênh lệch tỉ lệ bất thường của tập bị loại chưa đo.
