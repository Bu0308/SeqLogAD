# SeqLogAD: Kiểm toán training và nghiên cứu Fusion Semantic + Sequence

**Ngày:** 2026-10-23 · **Phạm vi:** đọc và phân tích, không train, không xóa file, không mở nhãn đích  
**Quy trình:** research-xhigh. Lead tự kiểm tra artifact; R1 phân tích cơ chế, R2 tổng quan tài liệu; C1 phản biện lý thuyết và đóng góp, C2 phản biện phương pháp; V1 kiểm chứng nguồn. Mỗi vai do một agent riêng đảm nhận, nhưng tất cả dùng chung một mô hình nền nên có thể có chung điểm mù.

**Mức độ chắc chắn của từng nhận định** được đánh dấu như sau:
- **[KIỂM]**: lead hoặc V1 đã kiểm trực tiếp trên artifact hay mã nguồn.
- **[SUY]**: suy luận hoặc tính toán.
- **[GT]**: giả thuyết, cần thực nghiệm để xác nhận.

---

## 0. Kết luận chính (đọc phần này trước)

1. **Chưa nên fusion ngay.** Hiện chưa có bằng chứng nào cho thấy hai mô hình bổ sung cho nhau, vì không mô hình nào lưu điểm theo từng đơn vị. Semantic còn chưa từng được đo như một bộ phát hiện bất thường (không có F1, AUROC hay AP). Câu hỏi "hai mô hình có bổ sung nhau không" hiện **chưa trả lời được** [KIỂM]. Trả lời được sau khoảng 1–4 giờ GPU chấm điểm, không cần train.
2. **Sequence V13R1 yếu và có hiện tượng đáng chú ý** [KIỂM]:
   - Trên source-dev, AUROC đạt 0,72–0,80 và AP 0,04–0,095, tức khoảng 2–4,6 lần tỉ lệ dương (base rate).
   - Mô hình dự đoán log kế tiếp càng tốt (NLL giảm) thì khả năng phân biệt bất thường càng **giảm**. Ví dụ ở fold HDFS-target, AUROC đi từ 0,803 xuống 0,610.
   - Checkpoint tốt nhất rơi vào rất sớm (step 100/300).
   - Checkpoint "best" của fold BGL chỉ dựa trên **1 true positive** trên 10 mẫu dương.
3. **Chỉ một fold đủ điều kiện fusion đầy đủ: HDFS-target** [KIỂM]:
   - **BGL-target:** thiếu adapter Semantic.
   - **Hadoop-target:** buffer bị protocol từ chối.
4. **Kiến trúc nên thử đầu tiên** [SUY, chưa có thực nghiệm]: fusion muộn (late fusion), hiệu chỉnh theo buffer bình thường của hệ đích, **không có tham số học từ nhãn**. Các bước:
   1. Tính p-value thực nghiệm (ECDF/conformal) cho từng expert trên buffer.
   2. Gộp hai p-value bằng **trung bình số học Vovk–Wang** (2·p̄).
   3. Conformal hóa lại điểm đã gộp trên một nửa buffer tách riêng.

   Kèm theo là một biến thể **trừ NLL của mô hình nền** (likelihood-ratio). Các kiến trúc deep fusion (cross-attention, tensor fusion, MoE, gate học được, gộp LoRA) **không phù hợp** với tình huống này: chỉ có khoảng 26 mẫu dương ở source, 0 nhãn đích và đầu ra là điểm vô hướng.
5. **Việc phải làm trước khi fusion:**
   - Viết bridge loader cho Semantic, đặt ngoài 5 thư mục đang bị hash.
   - Viết bộ chấm điểm batch, lưu điểm theo đơn vị và theo token.
   - Chấm 3 phiên bản cho mỗi expert: mô hình nền, checkpoint best, checkpoint latest.
   - Chạy baseline B0 chỉ dùng buffer đích.
   - Ký một bản pre-registration.

---

## 1. Training Audit Report

### 1.1 Nguồn dữ liệu đã kiểm tra

- **Google Drive** `SeqLogAD` (ID `1VcD3vx0…`, chủ sở hữu `luuquocviet005@…`, sửa lần cuối 2026-10-22).
  - Connector truy cập được metadata thư mục nhưng **không liệt kê được file con** (API trả về rỗng; connector thứ hai lỗi xác thực).
  - Vì vậy mình kiểm kê qua **bản Drive xuất ZIP trong Downloads**: 286 mục, tất cả qua kiểm tra CRC.
  - Bản xuất thiếu 3 part (semantic 002, 005, 006). Đó chính là 3 shard trọng số Llama, Drive tải thẳng file thô thay vì nén (xem mục 2).
- **Checksum:** tất cả 12 ZIP artifact khớp file `.sha256`. 5 adapter được chọn khớp `checkpoint_sha256` trong manifest. Gói FULL `cdc29963…` khớp checksum [KIỂM].

### 1.2 Hai mô hình là gì

| | **Semantic expert (P2.1, LORA-SEM-001)** | **Sequence expert (P2.2 V13R1, LORA-SEQ-003-R1 v1.3.1)** |
|---|---|---|
| Backbone | Llama-3.1-8B BASE, revision `d04e592b`, đóng băng, NF4 4-bit QLoRA, double quantization, BF16 | giống Semantic (cùng backbone) |
| Adapter | LoRA r16, α32, dropout 0,05, q/k/v/o, **LoRA thường** (α/r = 2) | LoRA r16, α32, q/k/v/o, **rsLoRA** (α/√r = 8) |
| Đầu vào | 1 thông điệp log đã chuẩn hóa; che 30% số từ, mask cố định theo sha256(text, seed) | tối đa 8 bản ghi trước đó cùng biên kiến trúc/partition/group, tối đa 512 token |
| Mục tiêu | Khôi phục thông điệp (causal denoising reconstruction); loss tính trên **mọi** token của thông điệp | Dự đoán log kế tiếp (teacher forcing); ngữ cảnh đa thang 1/2/4/full |
| Điểm bất thường | NLL trung bình trên token của thông điệp | NLL trung bình trên token của log kế tiếp |
| Chọn checkpoint | NLL tái tạo thấp nhất trên source-validation (không dùng nhãn) | macro F1 lớn nhất trên **nhãn source** (BGL 16 dương/496 âm; HDFS 10/501) |
| Hạ tầng | Colab, RTX PRO 6000 Blackwell 96 GB, torch 2.9.1+cu128 | Colab, RTX PRO 6000 Blackwell, ngày 2026-10-22, tổng 8.233 giây |
| VRAM đỉnh | khoảng 10,1 GB cấp phát / 12,1 GB giữ | khoảng 10,2 GB / 12,1 GB |
| Chiều biểu diễn | hidden state 4096 (Llama-3.1-8B); không lưu embedding nào | như Semantic |

### 1.3 Đường cong học (learning curves)

**Sequence** (đánh giá mỗi 100 step trên source-dev đã gán nhãn) [KIỂM]:

| Fold (nguồn dev) | Step: val NLL / AUROC / AP | Best | Dừng |
|---|---|---|---|
| BGL-target (HDFS) | 100: .239/.756/.053 · 200: .152/.776/.055 · **300: .114/.774/.095** · 400: .113/.739/.046 · 500: .090/.781/.056 · 600: .095/.711/.063 | step 300, F1 .167 (P = .5, R = .1, tức **1 TP**) | 600 |
| HDFS-target (BGL) | **100: .207/.803/.089** · 200: .126/.727/.070 · 300: .108/.659/.062 · 400: .093/.610/.059 | step 100, F1 .176 | 400 |
| Hadoop-target (BGL + HDFS) | **100**: BGL .804/.087, HDFS .724/.040 · 200: .802/.086, .758/.046 · 300: .671/.066 · 400: .690/.065, .712/.043 | step 100, macro F1 .143 | 400 |

Tỉ lệ dương: HDFS-dev khoảng 0,020; BGL-dev khoảng 0,031.

Nhận định:
- Không có underfit về mặt mô hình ngôn ngữ: train NLL giảm mạnh, val NLL cũng giảm.
- Có **"overfit với mục tiêu phát hiện"**: mô hình ngôn ngữ càng tốt thì phân biệt bất thường càng kém.
- Ngưỡng có F1 tốt nhất trên BGL nhảy từ ≤ 0,025 (step 100–200) lên 0,25–0,36 (step 300–400). Như vậy điểm của các mẫu dương đã tụt xuống dưới điểm của nhiều dòng bình thường [KIỂM, V1 đã sửa số liệu].
- Giải thích phù hợp nhất [GT]: dữ liệu train ở source không sạch (`clean_normal_claim: false`, `sequence-reference-v13r1.yaml:71`), nên mô hình học dự đoán luôn cả bất thường, cộng thêm việc sao chép trong ngữ cảnh khi alert xuất hiện thành cụm (burst).
- Chưa đo step 0 (mô hình nền), nên giả thuyết "mô hình nền đã là bộ phát hiện tốt nhất" **chưa kiểm được**.

**Semantic** (chỉ có NLL tái tạo, không có metric bất thường) [KIỂM]:

| Fold | Best | Val NLL theo nguồn tại best |
|---|---|---|
| HDFS-target | step 600, 0,2963 (dừng ở 900) | BGL 0,82 · Hadoop 0,062 · OpenStack 0,0071 |
| Hadoop-target | step 500, 0,2945 (dừng ở 800) | BGL 0,84 · HDFS 0,030 · OpenStack 0,0091 |
| BGL-target | **không có trong lần chạy này**; chỉ có `BGL-REGISTERED_EXTERNALLY.json` (adapter sha `63b17c16…`, archive `d513dab2…`, step 800) | không tìm thấy byte adapter ở Drive xuất về lẫn trên máy |

NLL chênh khoảng 100 lần giữa các nguồn. Con số này phản ánh mức thuộc lòng template của từng nguồn, không phải mức bất thường [SUY].

### 1.4 Probe tổng hợp (mỗi loại chỉ 1 ví dụ, chỉ để chẩn đoán)

- **Sequence:** chỉ "unexpected_next_event" đẩy điểm lên mạnh (+4,2 đến +5,2 nats). Mọi nhiễu loạn về thứ tự cho |Δ| ≤ 0,82 và đổi dấu giữa các fold. Mô hình gần với "túi template gần đây + sao chép" hơn là một mô hình hiểu thứ tự [GT].
- **Semantic:** semantic_change +1,16/+2,23; format_change 0; OOV +0,41/+0,22.

### 1.5 Vấn đề phát hiện trong lúc kiểm toán (ảnh hưởng tới fusion)

| # | Vấn đề | Mức | Ảnh hưởng tới fusion |
|---|---|---|---|
| A1 | Không có điểm theo đơn vị nào được lưu (`selection.json` chỉ chứa ID) | Chặn | Không tính được tương quan hay độ bổ sung khi chưa chạy inference |
| A2 | Semantic chưa từng được đo AUROC/AP | Chặn | Không biết Semantic có phát hiện được bất thường hay không |
| A3 | Loader Semantic từ chối chính checkpoint của nó: `expert.py:24` tính lại hash từ `config.yaml`, nhưng file này đã bị ghi đè sau khi train (`train.py:223-224`). Manifest ghi `6a1baa87…`, tính lại ra `866364ba…` | Chặn | Không nạp được Semantic |
| A4 | Bẫy implementation digest: Sequence kiểm `implementation_digest` trên mọi `*.py` trong common/protocol/semantic/sequence/phase2_execution (`implementation.py:10-11`). Sửa code trong các thư mục này sẽ khiến Sequence từ chối nạp | Chặn nếu sửa sai chỗ | Bridge phải nằm trong package mới |
| A5 | Thiếu adapter Semantic-BGL | Chặn cho fold BGL | Fusion fold BGL chỉ làm được khi khôi phục hoặc train lại (khoảng 1 GPU-giờ, cần bạn đồng ý) |
| A6 | Buffer Hadoop bị protocol từ chối; Hadoop chỉ có khoảng 55 ứng dụng | Giới hạn | Hadoop chỉ dùng để mô tả, không suy luận |
| A7 | Unit source-dev nằm trong đoạn MID, mà MID cũng thuộc TARGET_EVALUATION của fold khác | Chặn trước khi mở nhãn | Metric đích chính phải tính trên LATE (cần bản bổ sung protocol) |
| A8 | Mọi lần forward đều dùng batch 1 | Chặn khi chấm tập đích | Chấm toàn bộ tập đích BGL mất khoảng 56 giờ, HDFS khoảng 111 giờ cho mỗi checkpoint |
| A9 | Chọn checkpoint không cân xứng: Sequence theo F1 dùng nhãn, Semantic theo NLL (đúng tiêu chí đã làm Sequence kém đi) | Nên sửa | Cần đo best/latest/step 0 cho cả hai expert |
| A10 | Khác biệt về nguồn gốc (provenance) | Phải ghi lại | Xem ba ý bên dưới |

Chi tiết A10:
- Sequence chạy trên **Colab RTX PRO 6000**, không phải A40, bằng notebook biến thể `_colab.ipynb` và `collect_v13r1.py` đã sửa (chỉ đổi đường dẫn và tên). Code, data, source-dev và wheel giống hệt gói READY [KIỂM].
- Semantic là **một lần chạy khác**: FINAL zip `d9c499fa…` khác bản ngày 19/9 `d04b5dd4…`; HDFS 0,2963 so với 0,31493 đã ghi trong repo; code zip `db79892b…`; và **không có Projmem DB** cho lần chạy này.
- Có cảnh báo không tất định (non-deterministic) của CuBLAS/FlashAttention, nên không tái lập được từng bit.

---

## 2. File Cleanup Report (chỉ đề xuất, chưa xóa gì)

Máy của bạn là M1 8 GB RAM, ổ còn **7,5 GB trống (đầy 97%)**. Không thể chạy 8B NF4 trên máy này (bitsandbytes cần CUDA), nên mọi bước chấm điểm đều phải chạy trên GPU (Colab).

| File/Folder (Downloads) | Dung lượng | Vai trò | Đề xuất | Lý do |
|---|---|---|---|---|
| `sequence-…-001.zip` → `exports/…FULL_20261022T111425Z-031755f8.tar.gz` + `.sha256` | 1,84 GB | Bộ bằng chứng đầy đủ đã niêm phong của V13R1 (.pmem, attempts, targets, recovery, FINAL, inputs) | **Giữ** (bản gốc chuẩn) | Đã khớp checksum; chứa trọn cây `sequence-v13r1` |
| `sequence-…-001/002.zip` → `sequence/sequence-v13r1/**` dạng giải nén | khoảng 1,85 GB | Bản trùng của gói FULL | **Cân nhắc → Xóa** sau khi đã trích FULL và kiểm lại sha | Trùng 100% với FULL |
| └ `P2.2/targets/P2.2_{BGL,HDFS,HADOOP}_S42.zip` | 3 × 151 MB | Adapter best + metric + log của từng fold | **Giữ** (đầu vào fusion) | Checkpoint dùng để chấm điểm |
| └ `P2.2/recovery/*/LATEST_RECOVERY.zip` | 3 × 301 MB | Checkpoint best + **latest** (BGL 300/600; HDFS và Hadoop 100/400) | **Giữ** | Cần cho ablation best so với latest |
| └ `P2.2/seqlogad_outputs_P2.2_S42_FINAL.zip` | 455 MB | Gói gộp 3 ZIP target | Cân nhắc | Trùng với targets; giữ một trong hai (FINAL là bản niêm phong) |
| └ `.pmem/`, `attempts/`, `collection_capture/`, `projmem_exports/` | khoảng 2 MB | Provenance: 5 lần chạy, 4 lần thử bị lỗi | **Giữ** | Bắt buộc theo yêu cầu Projmem; cần import vào collection chính |
| └ `handoff_inputs/` và `uploads/`: notebook `_colab.ipynb`, `collect_v13r1.py`, manifest | < 0,1 MB | Bằng chứng về sai lệch nền tảng chạy | **Giữ** | Chứng minh đã chạy trên Colab |
| └ `uploads/` và `handoff_inputs/`: phase2-sequence, source-dev, code, wheel | khoảng 2 × 29 MB | Trùng byte với gói READY trong repo | Xóa được | Hash giống hệt `outputs/runpod/…READY/` |
| └ `runtime/ad0f313b…` | khoảng 33 MB | Code và data đã giải nén | Xóa được | Tái tạo được từ ZIP |
| └ `uploads/__pycache__/` | 6 KB | Bytecode | Xóa | Rác |
| `semantic-…-001.zip` (HDFS target) | 151 MB | Adapter Semantic HDFS step 600 | **Giữ** | Đầu vào fusion |
| `semantic-…-010.zip` (Hadoop target) | 151 MB | Adapter Semantic Hadoop step 500 | **Giữ** | Đầu vào fusion |
| `semantic-…-003.zip` (HDFS recovery: 600 + 900) | 301 MB | Checkpoint best + latest | **Giữ** | Ablation |
| `semantic-…-004.zip` (Hadoop recovery 500 + 800, kèm shard Llama số 4, 1,17 GB) | 1,23 GB | Checkpoint + trọng số nền | Giữ phần recovery; **xóa shard** | Trọng số nền tải lại từ HF |
| `semantic-…-007.zip` (FINAL Semantic) | 301 MB | Gói gộp 2 target | Cân nhắc | Trùng với 001 + 010 |
| `semantic-…-008.zip` (`phase2-final.zip` 8 MB + log xet) | 8 MB | Data Semantic | Xóa được | Trùng hash với `outputs/runpod/P2.1-S42-A40-upload/phase2-final.zip` |
| `semantic-…-009.zip` (code zip `db79892b…`) | 0,1 MB | Code đã chạy Semantic | **Giữ** | Không có bản nào khác trên máy; là provenance |
| `f8b9704a…-005` | 4,98 GB | Shard trọng số Llama-3.1-8B số 1 (safetensors, 82 tensor) | **Xóa** | Tải lại được từ HF (gated); hf-cache xuất từ Drive đã hỏng vì symlink bị biến thành file 76 byte |
| `Không được xác nhận 954485/418181.crdownload` | 1,74 + 1,61 GB | Shard 2 và 3 đang tải dở, đứng từ 14:46 | **Xóa / hủy tải** | Không cần cho fusion |

**Còn thiếu, cần bổ sung:**
1. Adapter Semantic-BGL (sha `63b17c16…` / archive `d513dab2…`).
2. Projmem DB hoặc log của lần chạy Semantic trên Colab.
3. Xác nhận từ bạn của bạn rằng thư mục Drive không còn file nào khác. Bản xuất ZIP đã bao gồm toàn bộ, trừ 3 shard.

Sau khi dọn có thể thu hồi khoảng 9–12 GB.

**Cấu trúc thư mục đề xuất cho giai đoạn Fusion** (đặt ngoài git, ví dụ trên ổ ngoài):

```text
seqlogad-fusion/
  00_inputs_immutable/                # chỉ đọc, kèm SHA256SUMS
    sequence_v13r1/FULL_20261022T111425Z-031755f8.tar.gz(+.sha256)
    sequence_v13r1/{targets,recovery}/
    semantic_p21_colab_rtx6000/{targets,recovery}/, SUMMARY.json, BGL-REGISTERED_EXTERNALLY.json, code_db79892b.zip
    provenance/ (notebook colab, collector colab, manifest, pmem.db snapshot)
  01_bridge/                          # package mới, nằm ngoài 5 thư mục đang bị hash
  02_scores/{fold}/{expert}/{checkpoint_sha}/   # parquet: điểm theo unit + theo token, input_sha
  03_baselines_B0/
  04_fusion/{rule_id}/
  05_reports/
  PREREGISTRATION.md (+ sha256, ký trước khi mở nhãn đích)
```

---

## 3. Đánh giá chất lượng hai mô hình

| Câu hỏi | Trạng thái |
|---|---|
| Hiệu suất thực | Sequence: AUROC 0,72–0,80, AP 2–4,6 lần base rate trên source-dev, nhưng số đo lạc quan vì checkpoint và ngưỡng chọn trên cùng tập [KIỂM]. Semantic: **chưa đo** |
| Hội tụ | Cả hai hội tụ về NLL; Sequence suy giảm khả năng phát hiện khi tiếp tục train [KIỂM] |
| Tổng quát hóa sang hệ thống chưa thấy | **Chưa có** metric đích; tạm suy từ việc source-dev nằm ngoài fold. SE Hanley–McNeil là 0,067 (16 mẫu dương) và 0,085 (10 mẫu dương) [KIỂM], tức sai số rất lớn |
| Bổ sung thông tin | **Chưa đo được** [KIỂM]. Theo cơ chế [GT]: cả hai chủ yếu đo "độ quen thuộc của nội dung". Dự kiến khác nhau ở *burst* (Semantic cao ở mọi lần lặp, Sequence gần 0 từ lần thứ hai) và *context break* (Sequence cao, Semantic thấp). Dự đoán Spearman ρ giữa các mẫu bình thường khoảng 0,3–0,6, nhưng vì chung backbone nên có thể cao hơn |
| Mô hình nào lấn át | Nếu cộng điểm thô, Semantic sẽ lấn át ở BGL do NLL lớn hơn khoảng 100 lần. Cần hiệu chỉnh theo hạng hoặc p-value [SUY] |
| Negative transfer | Gộp đều trọng số chỉ hơn expert mạnh A khi d′_B > d′_A(√(2(1+ρ)) − 1). Với A có AUROC 0,80: B cần AUROC > 0,64 khi ρ = 0 và > 0,73 khi ρ = 0,5 [SUY, C1 và V1 đã tính lại] |
| Rò rỉ / thiên lệch | Lỗ MID dùng chéo giữa fold (A7); chọn checkpoint và ngưỡng trên cùng 512 unit; buffer BGL có tỉ lệ alert tổng thể 7,3%, cao hơn giới hạn 5% |

**Trả lời câu hỏi quan trọng nhất:** chưa thể khẳng định hai mô hình bổ sung cho nhau. Theo mô hình nhị chuẩn (binormal) [SUY]:
- Nếu hai expert ngang nhau với AUROC 0,80, fusion chỉ lên 0,834 khi ρ = 0,5, và 0,806 khi ρ = 0,9.
- Ngay cả với so sánh ghép cặp, SE vẫn khoảng 0,03–0,05, lớn hơn mức lợi ích kỳ vọng.

Vì vậy kết quả có khả năng nhất là **lợi ích nhỏ hoặc không có**. Fusion chỉ đáng làm khi chấm điểm thật cho thấy ρ < 0,85 và hai expert bắt được *những mẫu dương khác nhau*.

---

## 4. Fusion Literature Review (đã kiểm nguồn)

Ký hiệu: PR = đã qua bình duyệt (peer-reviewed); PP = preprint. "Mức ưu tiên" là ưu tiên thử nghiệm cho hai expert này.

| # | Công trình | Cơ chế / công thức | Áp dụng cho Sem + Seq | Mức ưu tiên |
|---|---|---|---|---|
| 1 | Bates, Candès, Lei, Romano, Sesia, *Testing for outliers with conformal p-values*, Ann. Stat. 51(1):149–178, 2023 (PR) — [arXiv 2104.08279](https://arxiv.org/abs/2104.08279) | p̂ = (1 + #{cal: s ≥ s(x)})/(n + 1) (repo dùng quy ước điểm cao là bất thường); p-value marginal có tính PRDS nên BH kiểm soát FDR | Biến mỗi NLL thành p-value so được với nhau, không cần nhãn, dựa trên buffer đích. *Đính chính 2026-10-23:* Định lý 1 của Bates nói về nhiều điểm test dùng chung một calibration set, không phải về việc gộp hai expert trên cùng một unit. Trường hợp gộp hai expert được Vovk–Wang 2020 bao quát | **Cao** |
| 2 | Vovk & Wang, *Combining p-values via averaging*, Biometrika 107(4):791–808, 2020 (PR) — [arXiv 1212.4966](https://arxiv.org/abs/1212.4966) | 2·mean(p) hợp lệ dưới **mọi** dạng phụ thuộc | Luật gộp an toàn khi hai expert tương quan | **Cao** |
| 3 | Gupta et al., *Polysemantic Dropout: Conformal OOD Detection for Specialized LLMs*, EMNLP 2025 main (PR) — [arXiv 2509.04655](https://arxiv.org/abs/2509.04655) | ICAD theo từng tầng của LLM, gộp bằng trung bình lũy thừa có hệ số Vovk–Wang. Trong ablation, **trung bình số học tốt nhất, Bonferroni (K·min p) kém nhất** | Tiền lệ gần nhất: nhiều detector conformal trên cùng một LLM chuyên biệt. AUROC hơn baseline mạnh nhất khoảng 2–8 điểm (Bảng 1) | **Cao** |
| 4 | Liu & Xie, *Cauchy combination test*, JASA 115(529), 2020 (PR) — [arXiv 1808.09011](https://arxiv.org/abs/1808.09011) | T = Σwᵢ tan((0,5 − pᵢ)π) | Chỉ hợp lệ **tiệm cận** khi α → 0, và cần giả định cặp z-score có phân phối chuẩn hai chiều. Không đúng với p-value rời rạc dựa trên hạng [KIỂM V1] → chỉ dùng làm sensitivity | Trung bình |
| 5 | Ma, Zhao, Zhang, Akoglu, *The Need for Unsupervised Outlier Model Selection…*, SIGKDD Explor. 25(1), 2023 (PR) — [arXiv 2104.01422](https://arxiv.org/abs/2104.01422) | Tiêu chí nội tại không dùng nhãn để chọn mô hình gần như ngẫu nhiên | **Ràng buộc:** không chỉnh trọng số fusion bằng tiêu chí không nhãn; phải cố định luật trước | **Cao** (ràng buộc) |
| 6 | Serrà et al., *Input Complexity and Out-of-Distribution Detection with Likelihood-based Generative Models*, ICLR 2020 (PR) — [arXiv 1909.11480](https://arxiv.org/abs/1909.11480) | Likelihood bị độ phức tạp của đầu vào chi phối; dùng tỉ số với một mô hình tham chiếu để hiệu chỉnh | Lấy mô hình nền đóng băng làm tham chiếu: điểm = NLL_adapter − NLL_base. Có thể giải thích hiện tượng NLL giảm thì AUROC giảm | **Cao** |
| 7 | Kriegel, Kröger, Schubert, Zimek, *Interpreting and Unifying Outlier Scores*, SDM 2011 (PR) | Chuẩn hóa điểm về "xác suất outlier" rồi lấy trung bình | Baseline chuẩn hóa (z-score / erf / ECDF). Chi tiết regularization chưa đọc được bản gốc | Trung bình |
| 8 | Zhao et al., *LSCP*, SDM 2019 (PR) — [arXiv 1812.01528](https://arxiv.org/abs/1812.01528) | Chọn detector theo vùng lân cận, dùng giả nhãn từ max/avg | Cần không gian đặc trưng (hidden state); với 2 expert chỉ còn là công tắc theo từng unit | Thấp – trung bình |
| 9 | Meng et al., *LogAnomaly*, IJCAI 2019 (PR) | Ghép đặc trưng chuỗi (template2vec) và đặc trưng định lượng trong một LSTM | Động lực: hai góc nhìn chuỗi và định lượng bổ sung nhau (in-system, F1 BGL 0,96 / HDFS 0,95). Không phải late fusion | Động lực |
| 10 | Qi et al., *LogMoE*, ASE 2025 (PR, Distinguished Paper) | Các expert nhẹ theo từng hệ thống + gate học từ nhãn source | Baseline cross-system nên trích dẫn; gate cần nhãn | Trung bình (so sánh) |
| 11 | Zhao et al., *FusionLog*, arXiv 2511.05878 v3 (PP) | Router theo độ tương đồng không cần train + chưng cất LLM↔mô hình nhỏ bằng giả nhãn | Ý tưởng router theo độ mới của template; nhưng C1 cho rằng router đó trùng với chính baseline B0 | Thấp |
| 12 | Gộp/định tuyến LoRA: LoraHub (COLM 2024), MoLE (ICLR 2024), X-LoRA, AdapterFusion (EACL 2021), Arrow (ICML 2024), TIES (NeurIPS 2023), DARE (ICML 2024), LoRA Soups (COLING 2025) | Gộp có trọng số, gate học được, cắt tỉa / bầu dấu (trim/sign-elect) | **Loại.** Cần loss chung hoặc nhãn; hai adapter có prompt và hệ số khác nhau (2 so với 8); gộp lại sẽ triệt tiêu sự đa dạng cần thiết cho fusion | Thấp |
| 13 | Deep fusion: survey Baltrušaitis (TPAMI 2019), TFN (EMNLP 2017), LMF (ACL 2018), GMU, MulT (ACL 2019), MBT (NeurIPS 2021), sparse MoE (2017) | Tích ngoài, low-rank, gate nhân, cross-attention, bottleneck token | **Loại.** Cần đầu vào dạng vector/chuỗi và huấn luyện giám sát. Với khoảng 26 mẫu dương, ngân sách chỉ khoảng 2 tham số học từ nhãn (EPV ≥ 10) | Thấp |
| 14 | AnoFusion (KDD 2023), Hades (ICSE 2023) | Fusion đa phương thức metric + log + trace | Khác bài toán (hai góc nhìn trên cùng log, đầu ra vô hướng) | Thấp |

Phạm vi tìm kiếm:
- Có tìm có trọng tâm trên arXiv, ACL Anthology, Project Euclid, NeurIPS, IJCAI và researchr. Đây **không** phải rà soát hệ thống.
- Chưa mở được Aggarwal & Sathe 2015 (bị chặn 403). Chưa đọc được nội dung chi tiết của LogMoE.
- Venue của TIES, MBT, MulT, TFN và LMF chưa được mở lại trong phiên này.

---

## 5. So sánh và lựa chọn kiến trúc Fusion

| Tiêu chí | **K1. Calibrated Late Fusion (CLF)** | **K2. CLF + base likelihood ratio (LR-CLF)** | **K3. Mật độ 2D trên buffer (one-sided Gaussian copula)** | Gate / attention / MoE học được | Gộp LoRA |
|---|---|---|---|---|---|
| Khả năng cải thiện | Vừa (phụ thuộc ρ) | Vừa đến cao (loại phần phương sai chung do độ phức tạp đầu vào) | Bắt được vùng hai expert bất đồng | Không xác định được với 26 mẫu dương | Thấp |
| Khai thác phần bổ sung | Kiểu cộng (AND-mềm) | Như K1, trên điểm "sạch" hơn | Bắt được bất đồng (burst so với context break) | — | Mất đa dạng |
| Tương thích | Cao (điểm vô hướng, không đụng backbone) | Cao (mô hình nền có sẵn, cùng một lượt forward) | Cao | Thấp | Thấp |
| Độ phức tạp | Rất thấp | Thấp | Thấp – vừa | Cao | Vừa |
| Chi phí / VRAM | Chỉ CPU sau khi chấm điểm | Thêm 1 lượt forward của base (khoảng 10 GB VRAM) | CPU | GPU + train | GPU |
| Thời gian train fusion | 0 | 0 | 0 (ước lượng trên buffer) | Có | Có |
| Nguy cơ overfit | Rất thấp (0 tham số theo nhãn) | Rất thấp | Thấp (ước lượng trên buffer, không dùng nhãn) | Rất cao | Cao |
| Diễn giải được | Cao (p-value của từng expert) | Cao | Vừa | Thấp | Thấp |
| Bằng chứng khoa học | Bates 2023, Vovk–Wang 2020, Gupta 2025 | Serrà 2020 + #1–3 | Copula / one-class (suy luận, ít tiền lệ log) | Có ở bài toán giàu nhãn | Có ở bài toán đa nhiệm |
| Đóng góp nghiên cứu | Đo được, kể cả khi kết quả là "dư thừa" | **Cao** (giải thích được hiện tượng NLL suy giảm) | Vừa | — | — |

### Top 3: cách triển khai cụ thể

**K1. Calibrated Late Fusion (ưu tiên số 1)**
- *Vì sao phù hợp:* hai expert chỉ cho ra điểm NLL vô hướng, lệch thang đo khoảng 100 lần, không có nhãn đích và chỉ khoảng 26 mẫu dương ở source.
- *Nối ở tầng nào:* tầng quyết định (decision), sau khi đã gộp điểm về đơn vị đánh giá (BGL theo dòng; HDFS theo block, max là chính và top-3 mean là phụ; dùng **cùng** một luật cho cả hai expert và cho buffer).
- *Projection / alignment:* không cần projection. Cần căn unit (đã có join theo architecture/rank, không lệch bản ghi nào) và hiệu chỉnh ECDF theo buffer, có phân tầng theo độ dài.
- *Backbone:* đóng băng cả backbone lẫn adapter.
- *Các bước:*
  1. Chia buffer làm hai nửa không giao nhau: B1 và B2.
  2. Tính p_e = (1 + #{B1: s ≥ s_e(x)})/(|B1| + 1) cho mỗi expert, dùng mid-rank cho trường hợp hòa.
  3. Gộp: S = 2·mean(p_sem, p_seq) (Vovk–Wang).
  4. Conformal hóa lại S trên B2 để đặt ngưỡng theo FAR.
- *Loss:* không có, vì không có tham số nào được huấn luyện.
- *Rủi ro:*
  - Buffer nhiễm bất thường (BGL khoảng 7,3%) làm giảm recall với các loại bất thường lặp lại, và FAR chỉ đạt "danh nghĩa".
  - p-value bão hòa khi điểm vượt max của buffer.
  - Dữ liệu trôi theo thời gian (drift) phá giả định exchangeability.
- *Đo:* ΔAP và ΔAUROC so với expert đơn lẻ tốt nhất (chọn trên source); FAR thực tế so với danh nghĩa; recall@FAR.

**K2. LR-CLF: hiệu chỉnh bằng mô hình nền (ưu tiên số 2, chạy song song với K1 vì không tốn thêm chi phí đáng kể)**
- *Vì sao phù hợp:* Sequence càng train càng phát hiện kém; Serrà 2020 chỉ ra likelihood bị độ phức tạp đầu vào chi phối. Cả hai expert dùng chung backbone, nên mô hình nền là tham chiếu tự nhiên.
- *Đặc trưng đưa vào:* r_e(x) = NLL_adapter,e(x) − NLL_base,e(x), dùng cùng prompt và cùng mask. Sau đó áp dụng y nguyên pipeline K1.
- *Rủi ro:* nếu mô hình nền vốn đã phát hiện tốt thì r_e làm mất tín hiệu. Vì vậy phải báo cáo cả base đơn lẻ.
- *Đo:* thêm AUROC/AP của base, của r_e và của K1 với K2.

**K3. Mật độ đồng thời 2D trên buffer (ưu tiên số 3)**
- Ước lượng copula Gaussian của (Φ⁻¹(1 − p_sem), Φ⁻¹(1 − p_seq)) trên B1.
- Điểm = −log mật độ, nhưng **một phía**: chỉ tính khi ít nhất một expert vượt trung vị, để không gắn cờ các unit có cả hai điểm đều thấp.
- Cách này bắt được các mẫu mà hai expert bất đồng, đúng giả thuyết burst / context break.
- Rủi ro: buffer nhiễm bất thường, và tuyến bất thường không đơn điệu.

**Sensitivity và control (không phải ứng viên chính):**
- 2·min p (Bonferroni): Gupta 2025 thấy luật này kém nhất.
- Cauchy (chỉ hợp lệ tiệm cận).
- Một trọng số w fit bằng logistic: chỉ để tham khảo; không làm leave-one-source-out được ở fold HDFS.
- Mật độ kNN/Mahalanobis trên hidden state gộp (pooled): dùng như baseline lớp B0.

**Đề xuất bắt đầu với K1 + K2 trên fold HDFS-target**:
- Không có tham số học từ nhãn, nên không thể overfit 26 mẫu dương.
- Có cơ sở lý thuyết về tính hợp lệ (Bates; Vovk–Wang) và tiền lệ gần nhất (Gupta 2025).
- K2 cùng lúc kiểm tra cơ chế của hiện tượng suy giảm.

Đây là lựa chọn hợp lý nhất *trước* khi có dữ liệu, **không** phải khẳng định "tốt nhất tuyệt đối".

---

## 6. Experimental Design

**Baselines:**
- Semantic đơn lẻ và Sequence đơn lẻ, mỗi expert ở 3 phiên bản: base, best, latest.
- Base Llama không có adapter.
- B0 chỉ dùng buffer đích: template unseen, −log tần suất, Markov n-gram, IsolationForest trên vector đếm.
- Trung bình hạng (rank mean) đều trọng số.
- K1, K2, K3.

**Control để phân biệt "lợi ích do fusion" với "lợi ích do ensemble":**
- Seq-best ⊕ Seq-latest (ensemble cùng một expert).
- Seq ⊕ B0 và Sem ⊕ B0.
- Bộ so sánh = **max của các expert đơn lẻ**. Đây là so sánh với expert đơn tốt nhất kiểu oracle, nên mang tính bảo thủ.

**Ablation:**
- Checkpoint: base / best / latest.
- Calibration bật hoặc tắt (dùng điểm thô z-score theo source).
- Luật gộp: K1, K2, K3, min-p, Cauchy.
- Cách gộp về unit: max hoặc top-3 mean.
- Lượng tử: {0,99; 0,999}.
- Cắt bớt buffer (sensitivity về nhiễm bẩn).
- Theo độ phức tạp: 0 tham số → 1 tham số (F-D).

Phần "freeze so với fine-tune" và "vị trí fusion" **không áp dụng**, vì fusion nằm ở tầng điểm và không train lại.

**Dữ liệu và chia tập:**
- Source-dev mới: còn 1.536 unit chưa dùng trên tổng 2.048 mỗi nguồn. Chia thành D1 (dùng để chọn) và D2 (dùng để báo cáo) theo **khối thời gian**.
- Tập đích: **LATE là chính**. MID loại bỏ các unit dev và một vùng lân cận ±1 giờ, dùng làm phụ.
- Lấy mẫu đích **không nhìn nhãn** và đăng ký trước: khoảng 100 khối × 1.000 dòng BGL; khoảng 10.000 block HDFS.

**Metric:**
- AP (PR-AUC) là chính; AUROC; FAR thực tế tại ngưỡng lượng tử buffer; recall@FAR.
- Đơn vị: BGL theo dòng; HDFS theo block.

**Thống kê:**
- Bootstrap ghép cặp theo khối: BGL theo khối ≥ 1.000 dòng hoặc 1 giờ, ≥ 100 khối; HDFS theo khối block hằng giờ; 2.000 lần lấy mẫu.
- DeLong ghép cặp cho AUROC.
- Kiểm định theo thứ tự cố định K1 → K2 → K3 (hoặc Holm).

**Seed:**
- Hiện chỉ có S42. Muốn khẳng định xếp hạng giữa các biến thể LLM thì cần thêm 2 seed, khoảng 5 GPU-giờ mỗi seed, và **cần bạn đồng ý**.

**Gate (đã sửa theo C2 / V1):**
- **G-a:** ΔAUROC ghép cặp của từng expert so với base và so với B0 trên D1, cận dưới > −0,02. Nếu base thắng thì dùng base làm thành phần, không train lại.
- **G-b (trên buffer, không cần nhãn):** Spearman ρ < 0,85, và tỉ lệ đồng vượt ngưỡng ở đuôi q0,99 < 0,5. Trên D1: mức lợi ích dự đoán theo mô hình nhị chuẩn ≥ 0,01, và có các mẫu dương chỉ một expert bắt được.
- **G-c (khẳng định):** chỉ trên HDFS-target LATE. ΔAP một phía, khoảng tin cậy 97,5%, > 0 so với max của các expert đơn lẻ **và** so với Seq-best ⊕ Seq-latest; FAR không kém hơn. BGL chỉ là thứ cấp, và chỉ khi khôi phục được Semantic-BGL. Hadoop chỉ dùng để mô tả.

---

## 7. Implementation Roadmap

| Bước | Việc | Tài nguyên | Đầu ra | Ai quyết |
|---|---|---|---|---|
| R0 | Trích gói FULL + 5 ZIP target/recovery vào `00_inputs_immutable/`, kiểm sha; import `.pmem` của Colab vào collection chính, có kiểm xung đột; ghi Projmem về sai lệch Colab và về lần chạy Semantic mới | CPU | Kho đầu vào đã kiểm | Bạn duyệt, agent làm |
| R1 | Dọn Downloads theo mục 2 | — | Thu hồi khoảng 9–12 GB | **Chỉ bạn** |
| R2 | Bridge package mới (ngoài 5 thư mục đang bị hash): (a) nạp Semantic dựa trên `manifest['identity']` + sha adapter; (b) forward theo batch, có length bucketing; (c) cache theo sha256(input_ids); (d) Semantic dùng đúng forward/autocast như lúc validation. Kiểm batch so với single trên 200 unit (Spearman ≥ 0,9999, \|Δ\| < 1e-3) và kiểm lại digest `78a18851…` | CPU + test | Bridge đã version hóa | Agent làm, ghi Projmem |
| R3 | Khôi phục Semantic-BGL theo archive `d513dab2…`. Nếu không được thì **train lại** (khoảng 1 GPU-giờ) | GPU | Fold BGL dùng được cho fusion | **Bạn đồng ý** |
| R4 | B0 trên CPU; đếm số chuỗi (context, target) và số văn bản Semantic khác nhau để khử trùng lặp | CPU | Baseline đã đóng băng | Agent |
| R5 | Pre-registration ký và hash: checkpoint, thứ tự aggregate → calibrate → fuse, ≤ 3 luật, control, lượng tử, bootstrap, amendment LATE là chính, loại unit dev | — | `PREREGISTRATION.md` | **Bạn ký** |
| R6 | **Phase 0a GPU** (khoảng 1–4 giờ trên RTX PRO 6000): chấm base/best/latest × 2 expert trên 2.048 unit dev mỗi nguồn + mẫu buffer; lưu điểm theo unit, NLL theo token, NLL token đầu, hidden state gộp | Colab GPU | `02_scores/` | **Bạn đồng ý** |
| R7 | Gate G-a, G-b trên D1. **Dừng hoặc rẽ hướng** nếu: expert ≤ base hoặc ≤ B0 thì sửa expert (chấm Semantic với K seed mask, chọn checkpoint sớm hơn) trước khi fusion; nếu ρ ≥ 0,85 thì báo kết quả "dư thừa" và chuyển sang expert đơn + LR | CPU | Quyết định đi tiếp hay không | Lead đề xuất, bạn duyệt |
| R8 | K1, K2, K3 + control trên D2 (source) | CPU | Bảng nguồn | Agent |
| R9 | Phase 0b: chấm mẫu đích theo pre-registration (khoảng 7,5 giờ mỗi checkpoint với Sequence nếu không khử trùng lặp; Semantic khoảng 1,7 giờ mỗi checkpoint cho mọi bản ghi nhờ dedup) | GPU | Điểm trên tập đích | **Bạn đồng ý** |
| R10 | **Mở nhãn đích một lần**, chạy G-c, báo cáo đầy đủ mọi ablation | — | Kết quả cuối | **Bạn quyết** |

**Phương án dự phòng nếu fusion không cải thiện:**
1. Báo cáo kết quả âm có đủ power ("hai expert dư thừa sau khi hiệu chỉnh base-LR"). Kết quả này vẫn có giá trị khoa học, và theo C1 là kết quả có khả năng xảy ra hơn.
2. Dùng expert đơn tốt nhất + LR + hiệu chỉnh theo buffer.
3. Nâng expert: chấm Semantic với nhiều seed mask; chọn checkpoint Sequence không dùng nhãn (run `development_labels=None`, khoảng 1 GPU-giờ mỗi fold); loại burst khỏi ngữ cảnh.
4. Thêm góc nhìn thật sự khác: GTAT/đồ thị, hoặc mật độ hidden state.

---

## Phụ lục: những gì đã kiểm và chưa kiểm

**Đã chạy thật (chỉ đọc):**
- Kiểm CRC 12 ZIP Drive xuất về.
- Kiểm sha cho 12 artifact và 5 adapter.
- Kiểm checksum gói FULL và liệt kê nội dung.
- Diff collector Colab với gói READY.
- Đọc Projmem DB của lần chạy: 5 run, 0 failure row, 4 lần thử lỗi ở bước setup/prepare.
- Đọc learning curve từ `train.jsonl`.
- Đọc probe.
- V1 tính lại hash của lỗi loader, SE Hanley–McNeil và các ngưỡng F1.
- C1 tính lại các công thức binormal.

**Chưa làm (cần GPU hoặc cần bạn đồng ý):**
- Bất kỳ lần chấm điểm nào.
- Đo tương quan giữa hai expert.
- Đo step 0.
- Mọi metric trên tập đích.
- Khôi phục Semantic-BGL.

**Chưa đọc được bản gốc:** Kriegel 2011 (phần chi tiết), Aggarwal & Sathe 2015, LogMoE (toàn văn), Ren et al. NeurIPS 2019.
