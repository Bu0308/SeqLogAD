# TRAINING_AUDIT_REPORT — Hai expert đã train của SeqLogAD

**Ngày:** 2026-10-23.

**Nguồn dữ liệu:**
- Bản xuất ZIP của Google Drive `SeqLogAD` (ID `1VcD3vx0…`, chủ sở hữu `luuquocviet005@…`) trong `~/Downloads`. Có 286 mục và tất cả qua kiểm tra CRC.
- Repository `codex/sequence-v13r1`.

Ký hiệu mức độ chắc chắn:
- **[KIỂM]**: đã kiểm trực tiếp trên artifact hoặc code.
- **[SUY]**: suy luận hoặc tính toán.
- **[GT]**: giả thuyết, cần thực nghiệm.

> **Giới hạn truy cập.** Connector Google Drive đọc được metadata của thư mục nhưng **không liệt kê được file con**: `search parentId` trả rỗng, connector thứ hai lỗi xác thực OAuth. Toàn bộ kiểm kê dưới đây dựa trên bản ZIP mà Drive tự xuất. Ba "part" thiếu (semantic 002, 005, 006) là 3 shard trọng số Llama. Drive tải các shard này thẳng dưới dạng file thô, không đóng ZIP.

## 1. Hai mô hình

| | Model A — **Semantic expert** (P2.1, `LORA-SEM-001`) | Model B — **Sequence expert** (P2.2 V13R1, `LORA-SEQ-003-R1 v1.3.1`) |
|---|---|---|
| Backbone (chung) | `meta-llama/Llama-3.1-8B` BASE, revision `d04e592b`, đóng băng. 32 layer, hidden 4096, 32 head, 8 KV head (KV dim 1024), FFN 14336, vocab 128.256 [KIỂM: config.json trong HF cache] | như Model A |
| Quantization | NF4 4-bit QLoRA, double quant, compute BF16 | như Model A |
| Adapter | LoRA r16, α32, dropout 0,05, q/k/v/o, **LoRA thường** (scale α/r = 2) | LoRA r16, α32, q/k/v/o, **rsLoRA** (α/√r = 8) |
| Tham số adapter | 13.631.488 FP32: A (16×4096); B (4096×16) cho q, o; B (1024×16) cho k, v; × 32 layer [KIỂM: header safetensors] | 13.631.488 FP32 [KIỂM] |
| Đầu vào | 1 `normalized_message`; che 30% số từ theo seed sha256(text, 42); prompt `Restore the log message:` | tối đa 8 bản ghi trước cùng boundary + log kế tiếp; prompt `Previous log messages… Next log message:`; ≤ 512 token |
| Mục tiêu / loss | causal denoising reconstruction; CE trên **mọi** token thông điệp + EOS | causal next-log; CE trên token của log kế tiếp; ngữ cảnh đa thang 1/2/4/full |
| Đầu ra dùng cho fusion | NLL trung bình token: **vô hướng** theo bản ghi | NLL trung bình token: **vô hướng** theo cửa sổ |
| Optimizer | LR 1e-4, warmup 100, microbatch 1 × grad accum 16, clip 1,0, WD 0, tối đa 1.536 step | như Model A |
| Chọn checkpoint | NLL tái tạo thấp nhất trên source-val (không dùng nhãn; min_delta 0,001; patience 3) | **macro F1 lớn nhất trên nhãn source** (min_delta 0; patience 3) |
| Lần chạy | Colab, RTX PRO 6000 Blackwell 96 GB, torch 2.9.1+cu128, code `db79892b…` | Colab, RTX PRO 6000 Blackwell, 2026-10-22, 8.233 giây cho 3 fold; code `ad0f313b…`, implementation `78a18851…` |

## 2. Checkpoint (đã kiểm sha256)

| Expert / fold | Best | Latest | Ghi chú |
|---|---|---|---|
| Sequence / BGL-target | step-300 `ee42f1ec…` | step-600 | dừng ở 600 |
| Sequence / HDFS-target | step-100 `b6012c13…` | step-400 | dừng ở 400 |
| Sequence / Hadoop-target | step-100 `51fbb71c…` | step-400 | dừng ở 400 |
| Semantic / HDFS-target | step-600 `5ca88f60…` | step-900 | dừng ở 900 |
| Semantic / Hadoop-target | step-500 `73d6734e…` | step-800 | dừng ở 800 |
| Semantic / BGL-target | **không có byte** | — | chỉ có `BGL-REGISTERED_EXTERNALLY.json` (sha `63b17c16…`) |

Tất cả 12 ZIP target, recovery và FINAL khớp `.sha256`. Gói FULL `cdc29963…` khớp. Mỗi recovery ZIP chỉ giữ best + latest; các checkpoint trung gian không còn [KIỂM].

## 3. Log và learning curve

**Sequence:** đánh giá source-dev mỗi 100 step. Bảng lấy từ `logs/train.jsonl` [KIỂM].

| Fold (nguồn dev) | val NLL / AUROC / AP theo step | Best |
|---|---|---|
| BGL-target (HDFS) | 100: .239/.756/.053 · 200: .152/.776/.055 · **300: .114/.774/.095** · 400: .113/.739/.046 · 500: .090/.781/.056 · 600: .095/.711/.063 | F1 .167 = **1 TP**/10 |
| HDFS-target (BGL) | **100: .207/.803/.089** · 200: .126/.727/.070 · 300: .108/.659/.062 · 400: .093/.610/.059 | F1 .176 |
| Hadoop-target (BGL + HDFS) | **100:** BGL .804/.087, HDFS .724/.040 · 400: BGL .690/.065, HDFS .712/.043 | macro F1 .143 |

**Semantic:** chỉ có NLL tái tạo [KIỂM].

| Fold | Val NLL theo step |
|---|---|
| HDFS-target | .438 → .296 (step 600) → .310 (step 900) |
| Hadoop-target | .448 → .295 (step 500) → .307 (step 800) |

NLL theo nguồn: BGL khoảng 0,82–0,84; Hadoop/HDFS 0,03–0,06; OpenStack khoảng 0,007.

**Overfit / underfit:**
- Về mô hình ngôn ngữ thì không underfit.
- Sequence có hiện tượng **"overfit với mục tiêu phát hiện"**: NLL tiếp tục giảm nhưng AUROC và AP giảm theo.
- Ngưỡng có F1 tốt nhất trên BGL nhảy từ ≤ 0,025 (step 100–200) lên 0,25–0,36 (step 300–400) [KIỂM, V1]. Như vậy điểm của các mẫu dương đã tụt xuống dưới nhiều mẫu âm.
- Giải thích được ưu tiên [GT]: dữ liệu train ở source không sạch (`clean_normal_claim: false`), nên mô hình học dự đoán luôn cả bất thường, cộng thêm việc copy trong ngữ cảnh khi gặp burst.
- Chưa đo step 0.

## 4. Feature, embedding, tương thích

- Chưa lưu embedding nào. Đầu ra của cả hai expert là **một số vô hướng trên mỗi unit**.
- Hidden state cuối có kích thước 4096 nhưng phải chạy lại inference mới lấy được.
- Hai expert căn khớp đơn vị: mỗi cửa sổ Sequence nối đúng một bản ghi Semantic theo (architecture, rank), không lệch bản ghi nào. Đơn vị đánh giá: BGL theo dòng, HDFS theo block [KIỂM].
- Cohort dev dựng lại khớp hoàn toàn số liệu đã ghi. Mỗi nguồn có 2.048 cửa sổ:

  | Nguồn | Cụm dùng để chọn checkpoint | Phần mới (chưa dùng) |
  |---|---|---|
  | BGL | 16 dương / 496 âm | **67 / 1.469** |
  | HDFS | 10 / 502 | **21 / 1.515** (2.020 block) |

  [KIỂM: `tests/fusion/test_fusion_cohort.py`]

## 5. Vấn đề ảnh hưởng tới Fusion

| # | Vấn đề | Ảnh hưởng | Đã xử lý trong code |
|---|---|---|---|
| A1 | Không lưu điểm theo unit | Không đo được độ bổ sung khi chưa chạy inference | `fusion/scorer.py` lưu điểm theo unit và theo token, cùng hidden state |
| A2 | Semantic chưa có AUROC/AP | Không biết chất lượng của Semantic | E1 chấm Semantic trên cohort dev |
| A3 | `SemanticExpert.from_checkpoint` từ chối checkpoint hợp lệ (manifest `6a1baa87…`, tính lại ra `866364ba…`) | Không nạp được Semantic | `fusion/artifacts.py` tin `manifest.identity` + sổ checksum, giống cách Sequence làm |
| A4 | Bẫy implementation digest | Sửa nhầm thư mục thì Sequence từ chối nạp | Code mới nằm ở `src/seqlogad/fusion/`, ngoài 5 thư mục đang bị hash; digest vẫn `78a18851…` (có test) |
| A5 | Thiếu adapter Semantic-BGL | Fold BGL không có Semantic đã train | E1 dùng Semantic base cho fold BGL và đánh dấu là exploratory |
| A6 | Buffer Hadoop bị từ chối | Không hiệu chỉnh được theo buffer cho Hadoop | E1 không dùng buffer đích |
| A7 | Unit dev nằm trong MID của tập đánh giá đích ở fold khác | Rò rỉ khi đánh giá đích | E1 **không** chạm dữ liệu đích; giai đoạn đích cần amendment LATE |
| A8 | Code gốc forward batch 1 | Chậm | Scorer batch theo token budget; test chứng minh batch = single |
| A9 | 512 unit dùng để chọn checkpoint Sequence | Metric lạc quan | E1 chỉ báo cáo trên **unit mới** |
| A10 | Chạy trên Colab thay vì A40; Semantic là lần chạy mới, không có Projmem DB; cảnh báo không tất định của CuBLAS | Provenance | Đã ghi lại; E1 kiểm parity với số đã ghi trước khi tính fusion |

## 6. Kết luận về checkpoint

Checkpoint **hợp lệ về toàn vẹn** (sha256, sổ checksum, identity). Về **mức phù hợp cho fusion**:
- Sequence dùng được nhưng yếu và nhạy với việc chọn checkpoint.
- Semantic **chưa có bằng chứng** là phát hiện được bất thường.

Cả best và latest đều được chấm. Checkpoint chọn cho fusion là best, theo đúng tiêu chí mà mỗi run đã đăng ký trên source-validation, **không** dựa vào tập test. Latest được dùng làm ablation và control.
