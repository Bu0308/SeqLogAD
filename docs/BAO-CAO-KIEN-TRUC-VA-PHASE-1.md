# SeqLogAD — Kiến trúc hệ thống và báo cáo Phase 1

| Mục | Giá trị |
| --- | --- |
| Kế hoạch chuẩn | `Bang_ke_hoach_SeqLogAD.xlsx` (SHA-256 `c33aad33…d174d56b`) |
| Ngày báo cáo | 2026-09-07 |
| Trạng thái Phase 1 | **HOÀN THÀNH** — P1.1 đến P1.8 đều `DONE` |
| Cổng G0 | **PASSED** — 19/19 tiêu chí, ký ngày 2026-09-06 |
| Kết quả khoa học | **CHƯA CHẠY** — chưa train bất kỳ model nào |
| Việc tiếp theo | P2.1 — đã được phép, **chưa khởi động** |

---

# PHẦN 1 — Dự án này là gì

## 1.1 Bài toán

Hệ thống phần mềm sinh ra log. Trong log có những bất thường báo hiệu sự cố. Vấn đề
thực tế là: **mỗi hệ thống viết log theo một kiểu hoàn toàn khác nhau**, và khi triển
khai vào một hệ thống mới thì *không có nhãn* để huấn luyện.

So sánh cụ thể 4 hệ thống đang dùng:

```
HDFS      081109 203615 148 INFO dfs.DataNode$PacketResponder: Receiving block blk_-16089996...
BGL       - 1117838570 2005.06.03 R02-M1-N0-C:J12-U11 ... RAS KERNEL INFO instruction cache parity error
Hadoop    2015-10-17 21:47:48,288 INFO [main] org.apache.hadoop.mapreduce.v2.app.MRAppMaster: Created ...
OpenStack nova-api.log.1... 2017-05-16 00:00:00.008 25746 INFO nova.osapi_compute.wsgi.server [req-3810...
```

Bốn cú pháp, bốn từ vựng, bốn cách đánh nhãn. Model học trên HDFS không tự nhiên chạy
được trên OpenStack.

## 1.2 Câu hỏi nghiên cứu

> **Liệu một hệ thống fusion có thể học kiến thức từ nhiều kiến trúc nguồn, tự hiệu
> chỉnh sang một kiến trúc đích chưa từng thấy chỉ bằng một buffer log bình thường
> không nhãn, rồi phát hiện bất thường kèm bằng chứng và độ tin cậy đã hiệu chỉnh?**

Workbook chia thành 5 câu hỏi con (RQ1–RQ5):

| RQ | Câu hỏi | Đo bằng |
| --- | --- | --- |
| RQ1 | Biểu diễn có tổng quát hóa qua các cú pháp log khác nhau không? | AP/PR-AUC theo từng target + CI |
| RQ2 | Hiệu chỉnh chỉ bằng dữ liệu bình thường của target có hoạt động không? | FAR, calibration, tỉ lệ abstain |
| RQ3 | Fusion thích ứng có thực sự tốt hơn không? | AP/FAR so với baseline |
| RQ4 | Chuyện gì xảy ra khi drift / cold start / nhiễm bẩn buffer? | Mức suy giảm + độ trễ |
| RQ5 | Kết luận có tái lập được không? | Audit hash/config/seed |

**Ranh giới tuyên bố:** chỉ kết luận trong phạm vi các kiến trúc đã thực sự đánh giá.
Không tuyên bố tổng quát hóa phổ quát, không tuyên bố phát hiện được khi chưa có đủ
buffer.

---

# PHẦN 2 — Kiến trúc mô hình (hoạt động như thế nào)

## 2.1 Sơ đồ tổng thể

```
                    ┌─────────────── 3 KIẾN TRÚC NGUỒN ───────────────┐
                    │  log thô → canonical view → chuẩn hóa           │
                    └────────────────────┬────────────────────────────┘
                                         │  huấn luyện (P2)
              ┌──────────────────────────┼──────────────────────────┐
              ▼                          ▼                          ▼
    ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
    │ SEMANTIC EXPERT   │    │ SEQUENCE EXPERT   │    │ STRUCTURAL EXPERT │
    │ Llama-3.1-8B      │    │ Llama-3.1-8B      │    │ Temporal Graph    │
    │ + LoRA-Semantic   │    │ + LoRA-Sequence   │    │ Transformer(GTAT) │
    │ "câu log này lạ?" │    │ "log kế tiếp bất  │    │ "cấu trúc         │
    │                   │    │  ngờ không?"      │    │  event/service    │
    │                   │    │                   │    │  /time có lạ?"    │
    └─────────┬─────────┘    └─────────┬─────────┘    └─────────┬─────────┘
              │                        │                        │
              └────────────┬───────────┴────────────┬───────────┘
                           ▼                        ▼
              ┌────────────────────────────────────────────┐
              │  MỖI EXPERT XUẤT RA (chuẩn EVID-CS-001):   │
              │  score_raw · score_calibrated · uncertainty │
              │  coverage · localisation · evidence · version│
              └────────────────────┬───────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │   TARGET ADAPTATION (P3) — chỉ dùng burn-in buffer   │
        │   không nhãn của kiến trúc đích                      │
        │   • target memory (prototype/thống kê)              │
        │   • calibration bằng quantile của buffer            │
        │   • đo drift + coverage                             │
        └──────────────────────────┬──────────────────────────┘
                                   ▼
              ┌────────────────────────────────────────────┐
              │  ADAPTIVE GATE — MLP 8→32→16→3 Softmax     │
              │  Đầu vào: drift, uncertainty, coverage,     │
              │           context (KHÔNG có nhãn target)    │
              │  Đầu ra:  trọng số cho 3 expert             │
              └────────────────────┬───────────────────────┘
                                   ▼
              ┌────────────────────────────────────────────┐
              │  KẾT QUẢ: NORMAL / ANOMALY / UNKNOWN-REVIEW│
              │  kèm expert weights + evidence + lý do     │
              └────────────────────────────────────────────┘
```

## 2.2 Giải thích từng thành phần

**Canonical view** — Đưa 4 cú pháp log về một khuôn chung, che (mask) các định danh
(IP, UUID, block ID…) nhưng **giữ nguyên văn bản gốc**. Nhãn không bao giờ được dùng.

**Semantic expert** — Llama-3.1-8B đóng băng + adapter LoRA-Semantic riêng. Nhìn *nội
dung* một dòng log và đánh giá mức bất thường ngữ nghĩa.

**Sequence expert** — Cùng base Llama, nhưng **adapter LoRA-Sequence hoàn toàn riêng
biệt** (không chia sẻ trọng số với adapter kia). Dự đoán log kế tiếp; log thực tế càng
"bất ngờ" thì điểm bất thường càng cao.

**Structural expert (GTAT)** — Graph Transformer trên đồ thị event–service–component–
time. Bắt các bất thường *cấu trúc* mà đọc từng dòng không thấy. Nếu thiếu metadata
topology thì báo **coverage thấp và abstain**, chứ không bịa điểm số.

**Target adaptation** — Đây là điểm mấu chốt. Model không được xem nhãn của hệ thống
đích. Nó chỉ được xem một đoạn log đầu (burn-in buffer) và tự học "bình thường ở hệ
thống này trông ra sao", rồi hiệu chỉnh thang điểm theo đó.

**Adaptive gate** — Không phải cộng điểm 3 expert một cách tùy tiện. Gate học cách
đánh trọng số dựa trên độ trôi dữ liệu, độ bất định và độ phủ. Quan trọng: gate được
huấn luyện **chỉ trên các episode nguồn**, đóng băng trước khi đánh giá target.

**Abstain** — `UNKNOWN / REVIEW` là một đầu ra hợp lệ hạng nhất. Khi coverage thấp,
hệ thống được phép nói "tôi không biết" thay vì bị ép chọn normal/anomaly.

## 2.3 Quy tắc cứng: cô lập nhãn

Nhãn bất thường của kiến trúc đích **bị cấm** ở: huấn luyện, adaptation, calibration,
routing, fit fusion, chọn model, fit normalizer, fit parser.

Chỉ được mở ở **biên đánh giá cuối cùng**.

---

# PHẦN 3 — Kiến trúc phần mềm (Phase 1 được cài đặt ra sao)

## 3.1 Các module

Toàn bộ Phase 1 nằm trong `src/seqlogad/protocol/` — **3.846 dòng**, 12 module:

| Module | Dòng | Nhiệm vụ |
| --- | ---: | --- |
| `architectures.py` | 456 | Registry 4 kiến trúc + adapter đọc log thô của từng loại |
| `nul.py` | 157 | Codec an toàn byte `seqlogad-nul-escape-v1` |
| `normalizer.py` | 190 | Bộ chuẩn hóa `NORM-CS-001` (nạp bảng luật từ YAML) |
| `schema.py` | 269 | Contract bản ghi chung `LOG-UNIFY-001` |
| `chronology.py` | 628 | Quét stream, sắp theo thời gian, cắt segment |
| `folds.py` | 298 | Sinh fold LOAO `CS-SPLIT-001` |
| `buffer.py` | 267 | Buffer burn-in `ADAPT-INPUT-001` + luật từ chối |
| `labels.py` | 244 | **Biên nhãn — chỉ dùng khi đánh giá** |
| `audit.py` | 449 | Audit rò rỉ `LEAK-CS-001` (17 kiểm tra) |
| `registry.py` | 298 | Registry dataset `DATA-REG-001` |
| `freeze.py` | 567 | Biên lai G0 + xác minh chữ ký |

## 3.2 Luồng dữ liệu

```
log thô (2,4 GB)
   │
   ├─ adapter theo kiến trúc → tách metadata, VỨT BỎ nhãn inline (BGL cột 0)
   │
   ├─ codec NUL → text an toàn, có thể đảo ngược, băm SHA-256 bytes gốc
   │
   ├─ normalizer → che định danh, GIỮ raw
   │
   ├─ sắp xếp theo thời gian → cắt EARLY / GUARD / MID / LATE
   │
   └─ ghi ra stream index (Parquet + JSON, ~157 MB)
              │
              ├─ folds.py    → 3 fold LOAO
              ├─ buffer.py   → 3 buffer burn-in
              ├─ audit.py    → 3 báo cáo rò rỉ
              └─ freeze.py   → biên lai G0 (băm 28 artifact)
```

**Điểm thiết kế quan trọng:** bản ghi canonical **không được vật chất hóa ra đĩa**.
Chúng được sinh lại theo yêu cầu từ byte gốc bằng một hàm tất định. Lý do: 16,5 triệu
bản ghi JSON sẽ vượt dung lượng đĩa còn trống. Manifest chỉ lưu ID, biên, số đếm, hash.

## 3.3 Cô lập nhãn được cài đặt thế nào

Không phải bằng lời hứa trong tài liệu, mà bằng 3 cơ chế:

1. **Bản ghi canonical không có trường nhãn.** Schema từ chối bất kỳ trường nào có tên
   giống nhãn (`label`, `anomaly`, `groundtruth`…).
2. **Adapter vứt nhãn inline ngay tại nguồn.** BGL để nhãn ở cột 0; adapter loại bỏ
   trước khi bản ghi tồn tại.
3. **`labels.py` là module duy nhất mở được nhãn.** Nó từ chối 10 scope bị cấm và ghi
   log mọi lần truy cập. **Không module nào trên đường adaptation import nó** — kiểm
   tra `L09` dựng lại import graph mỗi lần chạy để chứng minh.

---

# PHẦN 4 — Từng task Phase 1 làm như thế nào

## P1.1 — Chốt phạm vi nghiên cứu ✅ `DONE`

**Đã làm:** Định nghĩa "kiến trúc" = **một hệ thống sinh log riêng biệt**, không phải
tập con của một dataset, không phải nhóm theo EventID. Vẽ sơ đồ fold. Lập bảng trường
bị cấm ở từng bước.

**Kết quả:** `docs/protocol/P1.1-research-scope.md`. Đã ký.

---

## P1.2 — Danh mục dataset ✅ `DONE`

**Đã làm:** Tải thêm OpenStack và Hadoop từ Zenodo, kiểm MD5 khớp đúng bản công bố,
ghi provenance/license/chronology/nhãn cho từng bộ.

**Kết quả — 4 kiến trúc, 16.525.722 bản ghi:**

| Kiến trúc | Hệ thống | Bản ghi | Vai trò | Nhãn |
| --- | --- | ---: | --- | --- |
| `ARCH-HDFS` | HDFS v1 (lưu trữ phân tán) | 11.175.629 | nguồn + đích | 16.838/575.061 block bất thường |
| `ARCH-BGL` | Blue Gene/L (siêu máy tính) | 4.747.963 | nguồn + đích | 348.460 dòng alert |
| `ARCH-HADOOP` | Hadoop YARN (tính toán lô) | 394.310 | nguồn + đích | 44/55 app lỗi |
| `ARCH-OPENSTACK` | OpenStack Nova (cloud) | 207.820 | **chỉ nguồn** | 4 VM instance |

**Vì sao OpenStack chỉ làm nguồn:** Dữ liệu gồm 3 phiên chụp riêng. Cách duy nhất sắp
xếp mà **không dùng nhãn** là theo đồng hồ, và đồng hồ đặt toàn bộ phiên chứa bất
thường (14/05) **trước** cả hai phiên bình thường (16–17/05). Nếu cắt burn-in theo thời
gian thì nó nuốt sạch bất thường, cửa sổ đánh giá không còn positive nào. Sắp xếp kiểu
khác = dùng tên file normal/abnormal = dùng ground truth. Nên chọn phương án trung
thực: dùng làm nguồn thôi. → `EXC-004`

**Thunderbird bị loại:** kiến trúc HPC khác biệt thật, nhưng bản nén ~2,0 GB giải nén
ra hàng chục GB, trong khi ổ chỉ còn 2,2 GB. Dataset không xác minh được thì không được
vào registry. → `EXC-006`

**License:** CC-BY-4.0, open access — đọc trực tiếp từ metadata của Zenodo.

---

## P1.3 — Schema chung `LOG-UNIFY-001` ✅ `DONE`

**Đã làm:** Thiết kế một khuôn bản ghi cho cả 4 nguồn, có contract ánh xạ riêng cho
từng kiến trúc (trường nào có, trường nào khai báo là thiếu, trường nào suy ra từ đâu).

**Ba tính chất được ép buộc bằng code:**
1. Văn bản gốc sống sót — `raw_message_sha256` khóa đúng byte gốc
2. Thiếu dữ liệu được gõ kiểu, không bịa — mọi bản ghi có `parse_status`/`timestamp_status`
3. Không có nhãn — schema từ chối trường trông giống nhãn

**Kết quả — 1 dòng log thô = đúng 1 bản ghi, KHÔNG BỎ dòng nào:**

| Kiến trúc | `OK` | `CONTINUATION` | `MALFORMED` | Bỏ |
| --- | ---: | ---: | ---: | ---: |
| HDFS | 11.175.629 | 0 | 0 | **0** |
| BGL | 4.747.963 | 0 | 0 | **0** |
| Hadoop | 180.896 | 213.414 | 0 | **0** |
| OpenStack | 207.812 | 0 | 8 | **0** |

213.414 dòng `CONTINUATION` của Hadoop là stack trace và diagnostic của YARN không có
header log. Chúng được **giữ lại như bản ghi hạng nhất** với timestamp null và trạng
thái trung thực, thay vì bị vứt đi.

---

## P1.4 — Chuẩn hóa `NORM-CS-001` ✅ `DONE`

**Đã làm:** Bảng luật đặt trong file YAML có version (`configs/parsing/normalizer-cs-v1.yaml`)
— 17 luật che + 5 mẫu bảo tồn. Hash của file được khóa vào mọi manifest.

**Ví dụ thật:**

| Gốc | Sau chuẩn hóa |
| --- | --- |
| `Receiving block blk_-1608999687919862906 src: /10.251.31.5:56682` | `Receiving block <BLK> src: /<IP>:<PORT>` |
| `2015-10-17 21:47:48,288 INFO ... appattempt_1445087491445_0005_000001` | `<TS> INFO ... <YARNID>` |
| `checksum deadbeefcafe1234 over IPv4 TCP on x86_64 using SHA-256` | `checksum <HEX> over IPv4 TCP on x86_64 using SHA-256` |

Dòng cuối là lý do có danh sách bảo tồn: nếu không, `HTTP/1.1`, `SHA-256`, `IPv4`,
`x86_64` đều biến thành `<NUM>` và câu log mất hết ý nghĩa.

**Hiệu quả đo được:**

| Kiến trúc | Message thô khác nhau | Sau chuẩn hóa | Giảm |
| --- | ---: | ---: | ---: |
| HDFS | 10.335.015 | 34.324 | 99,67% |
| BGL | 358.357 | 20.338 | 94,32% |
| Hadoop | 62.468 | 25.812 | 58,68% |
| OpenStack | 151.409 | 4.605 | 96,96% |

**2 bug thật đã tìm ra và sửa** khi viết golden test:
- Placeholder bảo tồn chứa chữ số → bị chính luật số che mất → làm hỏng toàn bộ token
  được bảo tồn. Đã đổi sang ký tự private-use không luật nào khớp.
- `\d+` backtrack biến `54fadb` thành `<NUM>4fadb`. Đã sửa lookaround.

**Chính sách NUL:** tái sử dụng **nguyên văn** quyết định `CANONICAL-NUL-DECISION-001`
đã có sẵn trong repo, không phát minh lại.

---

## P1.5 — Chia fold LOAO `CS-SPLIT-001` ✅ `DONE`

**Cách chia:** Mỗi kiến trúc được cắt theo thời gian thành 4 đoạn:

```
│◄──── EARLY 50% ────►│GUARD 5%│◄─ MID 15% ─►│◄──── LATE 30% ────►│
        │                            │              │
  nguồn: SOURCE_TRAIN         SOURCE_VALIDATION    (không dùng)
  đích : TARGET_BURN_IN       ◄──── TARGET_EVALUATION ────►
```

Cùng một cách cắt dù kiến trúc đóng vai nguồn hay đích → loại bỏ hẳn một lớp rò rỉ phụ
thuộc vai trò. `GUARD` không bao giờ được dùng, nó là vùng đệm thời gian.

**Xử lý đơn vị nhóm (block HDFS / application Hadoop / instance OpenStack):**
- **Toàn vẹn:** một đơn vị đi theo đoạn của bản ghi *cuối cùng* của nó → không bị xé đôi
- **Biên:** đơn vị nào có vòng đời *cắt ngang* mốc cắt thì bị loại khỏi mọi partition

**Luật chọn mốc cắt** (được khai báo trước): có 2 cách đạt được biên sạch — giữ mốc
danh nghĩa rồi loại các đơn vị đang sống, hoặc dời mốc tới một "khoảnh khắc yên tĩnh"
khi không đơn vị nào đang chạy. Cả hai đều tốn bản ghi. **Luật là chọn cách rẻ hơn**,
đo bằng số bản ghi bị dịch khỏi đoạn danh nghĩa.

**Chi phí thực tế:**

| Kiến trúc | Chiến lược | Bản ghi bị loại |
| --- | --- | ---: |
| HDFS | giữ mốc + loại đơn vị (×3) | 2.207.427 (19,75%) |
| BGL | giữ mốc (không có đơn vị nhóm) | 0 |
| Hadoop | dời tới khoảng nghỉ | **0** |
| OpenStack | giữ mốc + loại đơn vị | 75 (0,04%) |

**3 fold sinh ra:**

| Fold (đích) | `SOURCE_TRAIN` | `SOURCE_VALIDATION` | `TARGET_BURN_IN` | `TARGET_EVALUATION` |
| --- | ---: | ---: | ---: | ---: |
| HDFS | 2.715.308 | 853.440 | 4.746.575 | 4.191.330 |
| BGL | 5.087.902 | 1.167.140 | 2.373.981 | 2.136.584 |
| Hadoop | 7.224.454 | 1.769.225 | 237.429 | 156.881 |

Mỗi fold đúng **3 kiến trúc nguồn** — đạt yêu cầu tối thiểu của G0. Hoàn toàn tất
định, **không dùng seed ngẫu nhiên nào**.

---

## P1.6 — Buffer burn-in `ADAPT-INPUT-001` ✅ `DONE` (có 1 buffer bị từ chối)

**Cách lấy:** Buffer chính là đoạn `EARLY`, không gì khác — chọn thuần bằng thời gian.
Thao tác bị cấm `select records where label == normal` là **không thể chạm tới**: module
buffer không import code nhãn và bản ghi buffer không có trường nhãn.

**Nhiễm bẩn là một GIẢ ĐỊNH (bound 5%), không phải số đo.** Đo thật cần nhãn của
target → đó là việc của P4.

**Kết quả kiểm tra sẵn sàng (8 tiêu chí, ngưỡng khai báo TRƯỚC khi đo):**

| Buffer | Bản ghi | Khoảng thời gian | Kết luận |
| --- | ---: | ---: | --- |
| `BUFFER-ARCH-HDFS` | 4.746.575 | 26,2 h | `READY` → `ACCEPTED` |
| `BUFFER-ARCH-BGL` | 2.373.981 | 1.044,7 h | `READY` → `ACCEPTED` |
| `BUFFER-ARCH-HADOOP` | 237.429 | 26,8 h | **`NOT_READY` → `REJECTED`** |

**Hadoop hỏng 4/8 tiêu chí:** khoảng trống thời gian 0,677 > 0,25 · parse-OK 0,506 <
0,95 · coverage level 0,506 < 0,90 · coverage component 0,506 < 0,90.

Nguyên nhân đã kiểm chứng bằng cách lấy mẫu: ~54% dòng là continuation không có
level/component, và cụm máy nghỉ ~18 tiếng trong cửa sổ burn-in. **Đây là tính chất
thật của dữ liệu, không phải bug của adapter.**

**Tôi KHÔNG hạ ngưỡng để nó qua.** Luật `BUFFER-REJECT-001` quy định: buffer bị từ chối
thì không được dùng để xây target memory, calibrate, fit drift hay đặt ngưỡng abstain,
và **G1 không được tuyên bố cho fold đó**. Hạ ngưỡng là "phương án khắc phục bị cấm".
→ `EXC-003`

---

## P1.7 — Audit cô lập & rò rỉ `LEAK-CS-001` ✅ `DONE`

**17 kiểm tra được CHẠY THẬT trên từng fold**, không phải khẳng định suông:

`L01` trùng kiến trúc · `L02` trùng message thô · `L03` trùng message chuẩn hóa · `L04`
trùng bản ghi giữa partition · `L05` đơn vị bị xé · `L06` đảo thứ tự thời gian · `L07`
rò rỉ tương lai qua biên thời gian · `L08` chồng lấn burn-in/eval · `L09` lộ nhãn trên
đường adaptation · `L10` normalizer fit trên eval · `L11` parser/template fit · `L12`
sở hữu feature-fitting · `L13` đụng độ manifest · `L14` nhiễm nguồn↔đích · `L15` lộ
đường dẫn tuyệt đối · `L16` GUARD bị dùng · `L17` sổ ngoại lệ đầy đủ

**Kết quả: cả 3 fold `PASS` — 15 pass, 0 fail, 2 informational.**

`L02`/`L03` báo `INFORMATIONAL` vì không có ngưỡng khai báo trước, và **informational
không bao giờ được tính là pass**. Nhưng con số đo được rất đáng nói: **0** message
(thô lẫn chuẩn hóa) của `TARGET_EVALUATION` xuất hiện trong `SOURCE_TRAIN`, trên cả 3
fold. Các kiến trúc thực sự tách biệt về nội dung.

---

## P1.8 — Đóng băng và biên lai G0 ✅ `DONE`

**Đã làm:** Khóa schema, normalizer, registry, split manifest, env lockfile. Ghi lệnh
tái tạo và SHA-256 cho từng artifact.

**Biên lai khóa 28 artifact hash**, gồm cả chính workbook, 4 file contract, registry,
mọi stream index/parquet, mọi fold/buffer/audit.

```
G0 = PROTOCOL_READY — 19/19 tiêu chí PASS, 0 FAIL, 0 PENDING
```

**Cơ chế chữ ký:** Phase 1 cần **4 chữ ký** (P1.1, P1.6, P1.7, P1.8/G0). Cổng không bật
bằng một cờ trạng thái — tiêu chí `G0-15` và `G0-19` **so khớp từng byte** giữa sổ chữ
ký và payload mà từng contract khai báo, tính lại mỗi lần build.

**Đã kiểm chứng fail-closed:** đổi 1 ký tự trong payload (`Phase 1` → `Phase 2`) →
cổng lập tức quay về `PENDING_RESEARCHER_SIGNATURE` và chỉ đúng chữ ký bị lệch.

---

# PHẦN 5 — Tổng kết

## 5.1 Đã xong hết chưa?

**Phase 1: XONG.** Cả 8 task `DONE`, G0 `PASSED`, đã ký.

| Task | Trạng thái | Sản phẩm |
| --- | --- | --- |
| P1.1 Phạm vi | ✅ | `docs/protocol/P1.1-research-scope.md` |
| P1.2 Dataset | ✅ | `data/registry/dataset_registry.{csv,json}` |
| P1.3 Schema | ✅ | `LOG-UNIFY-001` |
| P1.4 Chuẩn hóa | ✅ | `NORM-CS-001` + bảng luật YAML |
| P1.5 Fold | ✅ | 3 fold LOAO |
| P1.6 Buffer | ✅ | 3 buffer (1 bị từ chối, đã ghi nhận) |
| P1.7 Audit | ✅ | 3 báo cáo, đều PASS |
| P1.8 Freeze | ✅ | Biên lai G0 |

**Kiểm thử:** 331 test pass (khởi điểm 199).

## 5.2 Những gì CÒN LẠI (ngoại lệ đã ký nhưng chưa giải quyết)

Ký duyệt sổ ngoại lệ = **ghi nhận**, không phải **giải quyết**:

| ID | Vấn đề | Chặn cái gì |
| --- | --- | --- |
| `EXC-001` | HDFS mất 19,75% bản ghi do loại trừ biên; ảnh hưởng tới phân bố bất thường **chưa đo** | Tuyên bố P4 về HDFS |
| `EXC-002` | Bằng chứng purge audit cũ **không chuyển giao được** sang tập loại trừ mới (Jaccard chỉ 0,42) | Không được viện dẫn audit cũ |
| `EXC-003` | Buffer Hadoop bị từ chối | **G1 cho fold Hadoop** |
| `EXC-004` | OpenStack chỉ làm nguồn → 3 fold thay vì 4 | Phạm vi kết luận |
| `EXC-006` | Thiếu Thunderbird (do dung lượng đĩa) | Phạm vi kết luận |
| `RSG-001` | Workbook gọi expert đồ thị là "GTAT" nhưng nguồn S6 không hề định nghĩa "GTAT" | Cần xử lý trước khi viết P2.7 |

## 5.3 Bước tiếp theo

```
NEXT_AUTHORIZED_TASK = P2.1 — LLM-BASE-001
Nội dung: khóa base Llama-3.1-8B, tokenizer, license và ngân sách GPU
Chủ sở hữu: Người nghiên cứu
Trạng thái: ĐÃ ĐƯỢC PHÉP, CHƯA KHỞI ĐỘNG
```

Việc này cần license và quyền truy cập model → thuộc quyết định của bạn.

## 5.4 Trạng thái các cổng

```
G0 Protocol Ready     ✅ PASSED (19/19, ký 06/09/2026)
G1 Adaptation Ready   ⬜ chưa qua — EXC-003 chặn fold Hadoop
G2 Expert Diversity   ⬜ chưa qua
G3 Fusion Justified   ⬜ chưa qua
G4 Final Evaluation   ⬜ chưa qua
```

**Chưa train model nào. Chưa commit. Chưa push.**

---

## Cách tái tạo toàn bộ

```bash
python scripts/extract_excel_roadmap.py    # workbook → kế hoạch máy đọc được
python scripts/build_streams.py            # quét log thô (~11 phút)
python scripts/build_protocol.py           # registry, fold, buffer, audit, G0
python -m pytest -q                        # 331 test
```
