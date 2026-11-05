# Bằng chứng về Evaluation Protocol (nội dung bắt buộc của Phase 4)

**Ngày:** 2026-10-23 · **Đi kèm:** `xh/FUSION_LITERATURE_REVIEW.md` (thẻ chi tiết và link của từng bài).
**Mục đích:** ghi lại các công trình tương đương thực sự *đánh giá* như thế nào, rồi suy ra protocol cho fusion Semantic + Sequence của SeqLogAD.

**Quy ước:**
- Mục 1–3 là **"tác giả báo cáo"**: chỉ chép những gì tôi đọc được trong PDF.
  - "không nêu" = tôi không tìm thấy thông tin này trong phần đã đọc.
  - "chưa trích" = tôi chưa đọc tới phần đó.
- Mục 4–5 là **"khuyến nghị của chúng tôi"**: suy luận có dẫn nguồn.
- PR = peer-reviewed; PP = preprint.

---

## 1. Trích xuất protocol theo từng bài (tác giả báo cáo)

### 1a. Log AD: LLM và cross-system

| Bài | Unit | Split | Metric chính | Số lần chạy / seed | CV | Tune hyperparameter | Chọn checkpoint | Ngưỡng có dùng nhãn test? | Kiểm định / CI |
|---|---|---|---|---|---|---|---|---|---|
| **Le & Zhang**, ICSE'22 (PR) | Cửa sổ cố định (1 h, 0,5 h, …), session | So sánh ngẫu nhiên 80:20 với theo thời gian 80:20. HDFS chỉ chia ngẫu nhiên được (không có timestamp) | P, R, F1, **Specificity** | **5 lần, lấy trung bình** | Không | Theo bài gốc; nếu không có thì tune "empirically" (không nói trên tập nào) | Không nêu | Không nêu rõ (dùng cơ chế của từng mô hình) | Không |
| **LogLLM**, arXiv (PP) | HDFS: session theo block; các tập khác: cửa sổ 100 message | **HDFS ngẫu nhiên**; BGL, Liberty, Thunderbird theo thời gian; 8:2 | P, R, F1 | **1** (không có std) | Không | Cố định (β = 30%, lr, 2 epoch) | Train số epoch cố định | Không có ngưỡng (LLM sinh nhãn) | Không |
| **LogGPT**, arXiv (PP) | Session (HDFS), cửa sổ 1 phút (BGL, Thunderbird) | Train = 5.000 sequence bình thường lấy **ngẫu nhiên** | P, R, F1 | **10 lần, mean ± std** | Không | K = 50% số key, cố định | "early stop criteria" (không nói trên tập nào) | Không (K cố định từ trước) | **Paired t-test** so với baseline tốt nhất, p < 0,05 |
| **LogPrompt**, ICPC'24 (PR) | Session = 100 template | Theo thời gian: baseline train trên 4.000 log đầu, test phần còn lại; LogPrompt dùng 0 log train | Session-level P, R, F1 | Không nêu | Không | Chọn prompt strategy dựa trên một dataset (Android) | — | DeepLog, LogAnomaly báo cáo "top-4 F1" | Không |
| **RAGLog**, arXiv (PP) | Từng log entry | Test = mẫu ngẫu nhiên từ 20% giữ lại (cỡ mẫu không nêu) | P, R, F1 | Không nêu | Không | Số cụm k-means chọn bằng elbow | — | Không (LLM sinh nhãn) | Không. So với số của LogPrompt trên mẫu khác |
| **ZeroLog**, arXiv (PP) | Session (Drain, theo code PLELog) | Source có nhãn; đích "không nhãn" nhưng **lấy số lượng bằng nhau giữa bình thường và bất thường**. Đánh giá phụ trên source: 80/20 | P, R, F1 | Không nêu | Không | β, γ: có độ nhạy **trên F1 của đích**; không có quy tắc chọn không dùng nhãn | Không nêu | Không nêu ngưỡng phân loại | Không |
| **FreeLog**, FSE-Comp'25 (PR) | Session | Như ZeroLog (target "half unlabeled", cân bằng lớp) | P, R, F1 | Không nêu | Không | Không nêu | Không nêu | Không nêu | Không |
| **FusionLog / GeneralLog**, arXiv (PP) | Session | Như FreeLog | P, R, F1 | Không nêu | Không | **τ = trung bình similarity** (không dùng nhãn, FusionLog); ε động | Không nêu | Không. Router dùng τ cố định; LLM cho nhãn | Không |
| **LogAnomaly**, IJCAI'19 (PR) | Cửa sổ 20 log (BGL), block (HDFS) | Theo thời gian: 80% đầu / 20% | P, R, F1 | Không nêu | Không | Baseline: "parameters … all set best for accuracy" | — | **Có khả năng** (tune baseline theo accuracy, không nói trên tập nào) | Không |
| **Landauer et al.**, FSE'24 (PR) | Sequence theo từng dataset | Mẫu train ngẫu nhiên, lặp lại | F1 (kèm TPR, precision, TNR) | **25 lần**, báo cáo trung bình và max | Không | — | — | **Có, công khai**: chọn ngưỡng tối đa hóa F1 (quét 0–1, bước 0,01) | Không ("opted against statistical tests") |
| **AnoFusion**, KDD'23 (PR) | Thời điểm × instance | **Theo thời gian, 60% đầu** để train | P, R, F1 | Chưa trích | Không | Chưa trích | Chưa trích | **Không**: dùng EVT để đặt ngưỡng tự động | Chưa trích |

### 1b. Ensemble, conformal và likelihood ratio (để đối chiếu protocol)

| Bài | Unit | Split | Metric chính | Số lần chạy | Tune hyperparameter | Ngưỡng có dùng nhãn test? | Kiểm định / CI |
|---|---|---|---|---|---|---|---|
| **Gupta et al.**, EMNLP'25 (PR) | Từng query | Chia ngẫu nhiên 80/20 giữa iD test và calibration | **AUROC** + đường FAR guarantee theo ε | **5 lần chia ngẫu nhiên** (std khoảng 0,001) | Layer 7/15/22 chọn theo lý do kiến trúc; m = 30, n = 5 | Không: dùng ICAD với ε cho trước | Không có kiểm định; chỉ có std |
| **Ren et al.**, NeurIPS'19 (PR) | Từng chuỗi / ảnh | Genomics: chia theo thời gian (năm phát hiện 2011/2016); có tập OOD validation riêng, rời với test | **AUROC, AUPRC, FPR80** | **10 lần chạy độc lập**, mean (SE) | μ, λ tune trên **OOD validation có nhãn** (hoặc OOD mô phỏng) | Không (threshold-free) | SE qua các lần chạy |
| **Bates et al.**, AoS'23 (PR) | Từng điểm | J practitioner độc lập × L tập test | **FDR, power** (có điều kiện theo calibration) | Mô phỏng lặp nhiều lần | Isolation forest với tham số mặc định (contamination = 0,1) | Không | Đảm bảo lý thuyết + mô phỏng |
| **LSCP**, SDM'19 (PR) | Từng điểm | 60/40 | **ROC-AUC, mAP** | **30 trial** | Phạm vi k của LOF ngẫu nhiên | Không (threshold-free) | **Friedman + Nemenyi** |
| **Ma et al.**, SIGKDD Expl.'23 (PR) | Từng điểm | Toàn bộ dataset (đánh giá việc chọn mô hình) | **AP** (cùng ROC) | Pool 297 mô hình × 39 dataset | Đối tượng nghiên cứu là chính việc chọn mô hình | Không | **One-sided paired Wilcoxon** qua các dataset |
| **COPOD / ECOD**, ICDM'20 / TKDE'22 (PR) | Từng điểm | 60/40 | **ROC-AUC, AP** | **10 trial** | Không có (parameter-free) | Không | ECOD: **Wilcoxon + Holm** |
| **ADBench**, NeurIPS'22 (PR) | Từng điểm | 70/30, stratified | **AUCROC, AUCPR** | **3 lần** | **Mặc định** của bài gốc, cố ý không tune | Không | **CD diagram, Wilcoxon–Holm** |

---

## 2. Ma trận bắt buộc (tác giả báo cáo, trừ cột Relevance)

| Paper | Venue | Fusion Method | Dataset | Primary Metric | Baselines | Ablation | Statistical Test | Relevance |
|---|---|---|---|---|---|---|---|---|
| Le & Zhang, *How Far Are We?* | ICSE 2022 (PR) | — (nghiên cứu đánh giá) | HDFS, BGL, Spirit, Thunderbird | P / R / F1 + Specificity | DeepLog, LogAnomaly, PLELog, LogRobust, CNN | Theo yếu tố: split, cách nhóm, mất cân bằng, nhiễu, early detection | Không (5 lần chạy, lấy trung bình) | **Cao** |
| Landauer et al., *Critical Review of Log Data Sets* | FSE 2024 / PACMSE (PR) | Kết hợp OR các detector đơn giản (event mới + độ dài, …) | HDFS, BGL, Thunderbird, OpenStack, Hadoop, ADFA | F1 (+ TPR, TNR, precision) | So với số SOTA lấy từ các bài khác | Theo từng loại detector | Không (25 lần chạy) | **Cao** |
| LogLLM | arXiv (PP) | BERT → projector → Llama-3-8B (intermediate fusion, có train) | HDFS, BGL, Liberty, Thunderbird | P / R / F1 | 12 phương pháp (DeepLog … BGE-Trans) | Các stage, MCO/CSL, preprocessing, đổi LLM | Không | Trung bình |
| LogGPT | arXiv (PP) | — | HDFS, BGL, Thunderbird | P / R / F1 | PCA, iForest, OCSVM, LogCluster, DeepLog, LogAnomaly, OC4Seq, LogBERT, CAT | Có / không RL | **Paired t-test** (10 lần chạy) | Trung bình |
| LogPrompt | ICPC 2024 (PR) | — (zero-shot LLM) | BGL, Spirit (AD) | Session P / R / F1 | DeepLog, LogAnomaly, LogRobust | Các prompt strategy | Không | Trung bình |
| RAGLog | arXiv (PP) | — (RAG với log bình thường) | BGL, Thunderbird | P / R / F1 | LogPrompt (số lấy từ bài khác) | Lấy mẫu ngẫu nhiên so với theo cụm | Không | Thấp |
| ZeroLog / FreeLog | arXiv (PP) / FSE-Comp 2025 (PR) | — (UDA + meta-learning) | HDFS, BGL, OpenStack (4 cặp chuyển) | P / R / F1 | PLELog, LogRobust, LogTAD, LogTransfer, MetaLog, DeepLog, NeuralLog | Bỏ meta-learning; độ nhạy β, γ | Không | Cao (protocol) |
| FusionLog / GeneralLog | arXiv (PP) | **Router** theo similarity (decision-level) + chưng cất LLM↔small model | HDFS, BGL, OpenStack | P / R / F1 | Như trên + RAGLog | Độ nhạy τ, ε; đổi LLM | Không | Trung bình |
| LogAnomaly | IJCAI 2019 (PR) | Ghép đặc trưng chuỗi + định lượng trong một LSTM (early fusion) | BGL, HDFS | P / R / F1 | LogCluster, PCA, IM, DeepLog | Bỏ chuỗi; bỏ count vector | Không | Trung bình |
| Gupta et al., *Polysemantic Dropout* | EMNLP 2025 (PR) | **Gộp p-value hợp lệ (Vovk–Wang) giữa các layer của một LLM** | EyeQA / IMHI so với CovidQA / MedMCQA | AUROC + FAR guarantee | Base score, single p-value, majority vote | Merging function, K, m, n | Không (5 lần chia, std) | **Cao** |
| Ren et al., *Likelihood Ratios* | NeurIPS 2019 (PR) | **Likelihood ratio** với background model | Genomics OOD, Fashion-MNIST/MNIST, CIFAR/SVHN | AUROC, AUPRC, FPR80 | p(ŷ\|x), entropy, ODIN, Mahalanobis, ensemble, WAIC, … | μ, λ; chỉ dùng μ so với dùng (μ, λ) | SE qua 10 lần chạy | **Cao** |
| Bates et al., *Conformal p-values* | Ann. Statist. 2023 (PR) | Marginal và calibration-conditional p-value + BH / Fisher / Stouffer / Simes | Mô phỏng + 7 dataset outlier | FDR, power | So sánh các cách hiệu chỉnh | Simes, DKWM, Monte Carlo | Đảm bảo lý thuyết | **Cao** |
| LSCP | SDM 2019 (PR) | Chọn detector cục bộ (pseudo ground truth) | 20 ODDS/DAMI | ROC-AUC, mAP | 7 luật gộp toàn cục (mean, max, AOM, MOA, …) | 4 biến thể LSCP | Friedman + Nemenyi | Thấp – Trung bình |
| Ma et al., *Unsupervised Model Selection* | SIGKDD Expl. 2023 (PR) | (Đối tượng là việc chọn mô hình) | 39 ODDS/DAMI | **AP** | Random, iForest mặc định | 7 họ tiêu chí | One-sided paired Wilcoxon | **Cao** (ràng buộc) |
| COPOD / ECOD | ICDM 2020 / TKDE 2022 (PR) | Tổng −log tail-ECDF giữa các chiều (copula độc lập) | 30 benchmark | ROC-AUC, AP | 10–11 detector của PyOD | Skewness correction, chọn đuôi | ECOD: Wilcoxon + Holm | Trung bình |
| AnoFusion | KDD 2023 (PR) | GTN + GAT + GRU (deep multimodal); baseline JLT = **late fusion bằng majority vote** | 2 hệ microservice | P / R / F1 | JumpStarter, LogAnomaly, TraceAnomaly, JLT, … | Bỏ GTN, bỏ GAT, … | Chưa trích | Thấp (để loại trừ; JLT là phản chứng) |
| ADBench | NeurIPS 2022 D&B (PR) | (Benchmark; có cả ensemble) | 57 dataset | AUCROC, AUCPR | Nhiều thuật toán unsupervised, semi-supervised và supervised (chưa trích số lượng) | Loại anomaly, nhiễu, mức giám sát | CD diagram, Wilcoxon–Holm | Trung bình (protocol) |

---

## 3. Mẫu hình quan sát được (đếm trên các bài ở mục 1a, tác giả báo cáo)

- **Metric chính:** cả 11 bài log AD hoặc multimodal ở 1a đều dùng **P/R/F1 làm metric chính**; Le & Zhang thêm Specificity, Landauer thêm TNR. Ngược lại, ở 1b có 6/7 bài dùng **metric không cần ngưỡng** (AUROC; AP/AUCPR trong 5/7 bài). Bài còn lại là Bates, dùng FDR và power tại mức α cho trước.
- **Split:** chia theo thời gian xuất hiện ở Le & Zhang (so sánh), LogAnomaly, LogPrompt, LogLLM (trừ HDFS) và AnoFusion. Chia ngẫu nhiên ở LogGPT, LogLLM-HDFS và RAGLog. Nhóm zero-label (ZeroLog, FreeLog, FusionLog) **lấy mẫu đích cân bằng lớp**.
- **Lặp lại:** có ở Le & Zhang (5), LogGPT (10), Landauer (25). Không có ở LogLLM, LogPrompt, RAGLog, ZeroLog, FreeLog, FusionLog, LogAnomaly. Trong 1b: Gupta (5 lần chia), Ren (10), LSCP (30), COPOD/ECOD (10), ADBench (3).
- **Kiểm định thống kê:** trong 1a, chỉ **LogGPT** (paired t-test qua các lần chạy). Trong 1b: LSCP, Ma, ECOD, ADBench (tất cả là kiểm định **qua nhiều dataset**: 20–57 dataset).
- **Không bài nào** trong danh sách báo cáo **CI bằng bootstrap theo cụm (cluster/block bootstrap)** trên tập test. Phương sai chỉ đến từ seed hoặc từ cách chia, không đến từ việc lấy mẫu các unit test có tương quan.

---

## 4. Những lỗi phổ biến trong tài liệu (có dẫn chứng)

1. **Chia ngẫu nhiên gây rò rỉ thời gian.** Le & Zhang: DeepLog trên BGL đạt F1 0,927 khi chia ngẫu nhiên, nhưng chỉ còn 0,426 khi chia theo thời gian. Dù vậy, LogLLM (HDFS) và LogGPT vẫn chia ngẫu nhiên.
2. **Chọn ngưỡng hoặc hyperparameter bằng nhãn test.**
   - Landauer chọn ngưỡng tối đa hóa F1 (có công khai, coi là cận trên).
   - LogAnomaly đặt tham số baseline "best for accuracy".
   - ZeroLog trình bày độ nhạy β, γ trên F1 của đích mà không có quy tắc chọn không dùng nhãn.
   - Ren tune μ trên một tập **OOD validation có nhãn**. Cách này hợp lệ trong thiết lập của họ, nhưng **không** chuyển được sang thiết lập zero target label.
   - Phản ví dụ tốt: FusionLog đặt τ = trung bình similarity; AnoFusion dùng EVT; Gupta và Bates dùng ε/α cho trước.
3. **Chạy một seed, không có CI.** LogLLM, ZeroLog, FreeLog, FusionLog, LogPrompt.
   - Ngay cả LogGPT có paired t-test thì đó cũng là kiểm định **qua 10 lần train** (phương sai do seed), không phải trên phương sai do lấy mẫu test.
   - Landauer chỉ ra một mặt khác: nhiều bài "often only report the best scores achieved from multiple runs".
4. **Chỉ dùng F1 khi dữ liệu mất cân bằng nặng.**
   - Le & Zhang: P/R/F1 "not comprehensive enough".
   - Landauer, Hadoop: F1 91,5% nhưng TNR 0%.
   - Saito & Rehmsmeier 2015 và Davis & Goadrich 2006: ROC có thể quá lạc quan khi phân phối lớp lệch mạnh (mục 5.1).
5. **Tập đích "không nhãn" nhưng được lấy mẫu bằng nhãn.** ZeroLog, FreeLog, FusionLog lấy số lượng bằng nhau giữa log bình thường và bất thường của đích, tức tỉ lệ dương khoảng 50%. Tỉ lệ thật ở HDFS khoảng 2,9% (16.838 / 575.061 block theo LogGPT/LogAnomaly). Thiết kế này vừa rò rỉ thông tin nhãn vào bước lấy mẫu, vừa thổi phồng precision và F1.
6. **So số liệu giữa các bài khác điều kiện.** RAGLog so số của mình với số trong bài LogPrompt trên một mẫu test khác. Landauer cảnh báo khả năng so sánh bị hạn chế vì mỗi bài dùng split khác nhau.
7. **Bệnh lý của dataset.**
   - Hadoop: 82,9% chuỗi bất thường, và nhiều chuỗi bình thường giống hệt chuỗi bất thường (Landauer).
   - HDFS: kết quả khác nhau giữa bản LogDeep và bản gốc, 90,4% so với 72,0% (Landauer).
   - Duplicated anomalies làm hỏng phương pháp unsupervised (ADBench: median ΔAUCROC −16,43%).
8. **Late fusion không hiệu chỉnh.** JLT (majority vote) trong AnoFusion có precision thấp vì các detector cùng bắt nhầm.

---

## 5. Khuyến nghị của chúng tôi (không phải số liệu tác giả báo cáo)

### 5.1 Metric chính: **AP (Average Precision, tức PR-AUC dạng bậc thang)**, tính riêng cho từng target fold

**Lý do:**
- **Mất cân bằng nặng.** Tỉ lệ dương khoảng 2–3% (HDFS) đến khoảng 7% (BGL, mức dòng, theo review trước). Saito & Rehmsmeier (PLoS ONE 10(3):e0118432, 2015; [TOÀN VĂN]):
  - ROC plot "can be deceptive" với dữ liệu mất cân bằng.
  - Baseline của PRC là y = P/(P+N), nên AUC(PRC) của bộ phân loại ngẫu nhiên đúng bằng tỉ lệ dương.
  - Kết luận của họ: PRC "more informative" khi dữ liệu mất cân bằng.
- Davis & Goadrich (ICML 2006, DOI 10.1145/1143844.1143874; [TOÀN VĂN qua bản UW FTP]):
  - ROC "can present an overly optimistic view" khi phân phối lớp lệch nhiều.
  - Một đường cong dominate trong ROC space **khi và chỉ khi** nó dominate trong PR space.
  - **Không được nội suy tuyến tính** trong PR space.
  - Tối ưu AUC-ROC không bảo đảm tối ưu AUC-PR.
- **Không cần ngưỡng:** tránh hoàn toàn lỗi số 2 ở mục 4. Cộng đồng outlier detection dùng AP làm metric chính (Ma 2023) hoặc đi kèm ROC (LSCP, COPOD, ECOD, ADBench, Ren).
- **Gắn với vận hành:** AP phản ánh precision ở vùng đầu bảng xếp hạng (top-of-ranking), tức là gánh nặng cảnh báo cho operator.

**Cách tính:**
- Dùng **step-wise AP** (ví dụ `sklearn.metrics.average_precision_score`), **không** dùng PR-AUC theo quy tắc hình thang (vì Davis & Goadrich đã chỉ ra không được nội suy tuyến tính).
- Báo cáo **tỉ lệ ties**: p-value có sàn 1/(n+1) (Bates), nên nhiều unit có thể bị trùng điểm ở đuôi. Dùng điểm thô NLL làm tie-breaker đã đăng ký trước, hoặc dùng phần đuôi GPD như review trước đề xuất.

**Lưu ý bắt buộc:** AP phụ thuộc vào tỉ lệ dương π_t, nên:
- Luôn báo cáo kèm π_t và **AP lift = AP/π_t**.
- **Không** lấy trung bình AP thô giữa các target có π khác nhau mà không ghi chú.
- **Hadoop:** Landauer báo cáo 82,9% chuỗi Hadoop là bất thường. Nếu unit Hadoop của repo có π cao như vậy thì AP gần như vô nghĩa. Cần kiểm tra lại định nghĩa unit (việc này chưa làm), và Hadoop chỉ dùng để mô tả.

### 5.2 Metric phụ
1. **AUROC:** không phụ thuộc π, nên so được giữa các target; là chuẩn trong OOD (Gupta, Ren, Serrà); kiểm định được bằng phương pháp ghép cặp (paired).
2. **Recall@FAR và FAR thực tế:**
   - Ngưỡng = lượng tử của **buffer bình thường không nhãn** (q ∈ {0,99; 0,999}, đăng ký trước). Không dùng nhãn.
   - Báo cáo FAR thực đo trên các unit bình thường của đích so với FAR danh nghĩa, giống "FAR guarantee curve" của Gupta 2025 và việc kiểm FDR / power của Bates 2023.
   - Đây là metric **triển khai được**, tương ứng với yêu cầu Specificity/TNR của Le & Zhang và Landauer.
3. **FPR@TPR80** (như FPR80 của Ren): một con số để so với tài liệu OOD.
4. **F1 tại ngưỡng không dùng nhãn** (ngưỡng buffer) để so được với tài liệu log AD.
   - **Best-F1 trên nhãn test** chỉ được báo cáo dưới tên "oracle upper bound" (như Landauer), tuyệt đối không dùng làm kết quả chính.
5. **Chẩn đoán độ bổ sung** (không phải metric thành công):
   - Spearman ρ giữa hai expert trên buffer bình thường.
   - Tỉ lệ cùng vượt ngưỡng ở đuôi q0,99.
   - Sau khi mở nhãn: tỉ lệ mẫu dương **chỉ một expert bắt được** tại FAR cố định.

### 5.3 Unit, split và chọn checkpoint
- **Unit cố định trước khi chấm:** BGL theo dòng; HDFS theo block (max là chính, top-3 mean là phụ; **cùng một luật** cho cả hai expert, cho buffer và cho fusion); Hadoop chỉ mô tả.
- **Split theo thời gian** (Le & Zhang).
  - Buffer lấy từ đoạn đầu; đánh giá trên đoạn **LATE** của đích.
  - Loại các unit source-dev bị dùng chéo giữa các fold, cùng một vùng đệm thời gian quanh chúng (theo review trước).
  - **Không** lấy mẫu đích theo nhãn (lỗi số 5).
- **Checkpoint:**
  - Chốt trước khi mở nhãn đích; chỉ dùng tiêu chí source hoặc tiêu chí không nhãn.
  - Báo cáo cả base / best / latest cho từng expert.
  - Ghi rõ: Sequence V13R1 chọn checkpoint bằng macro-F1 trên 10–16 mẫu dương của source, nên số source-dev đã bị lạc quan. Chỉ dùng source-dev **mới** (1.536 unit còn lại mỗi source) cho mọi so sánh mới.
- **Luật fusion:** đăng ký trước tối đa 3 luật (K1, K2, K3) cộng các control. Không chọn luật trên đích bằng tiêu chí không nhãn (Ma 2023).

### 5.4 Định nghĩa Fusion Gain (đăng ký trước)

Ký hiệu AP_t(·) là AP trên target t, tính trên **cùng một tập unit**.
- **FG_oracle(t) = AP_t(F) − max{AP_t(Sem), AP_t(Seq)}**
  - So với expert đơn tốt nhất *nhìn từ phía test*. Đây là so sánh bảo thủ, và là con số chính để khẳng định "fusion có ích".
- **FG_deploy(t) = AP_t(F) − AP_t(e\*)**
  - e\* = expert được chọn **trên source-dev mới D1** trước khi mở đích. Đây là so sánh mà người triển khai thực sự gặp.
- **FG_ens(t) = AP_t(F) − AP_t(Seq_best ⊕ Seq_latest)**, cùng một luật gộp.
  - Tách "lợi ích do kết hợp hai *góc nhìn*" khỏi "lợi ích do ensemble đơn thuần".
- **FG_B0(t) = AP_t(F) − max_b AP_t(B0_b)**
  - B0 gồm: template mới, −log tần suất, n-gram, và một baseline nén (gzip) theo tinh thần Serrà 2020.
  - Lý do: theo Landauer, phần lớn bất thường bắt được bằng các phương pháp rất đơn giản.
- Báo cáo thêm ΔAUROC tương ứng, ΔRecall@FAR, và chênh lệch FAR thực tế (fusion **không** được làm FAR xấu hơn).
- **Tiêu chí "fusion thắng"** (khớp gate G-c của review trước):
  - Cận dưới một phía 97,5% của FG_oracle > 0 **và** của FG_ens > 0 trên HDFS-target LATE.
  - FAR thực tế ≤ danh nghĩa + dung sai đã đăng ký.
  - BGL là thứ cấp, và chỉ khi khôi phục được Semantic-BGL.

### 5.5 Kiểm định thống kê
1. **Paired cluster (block) bootstrap** là phương pháp chính.
   - Lấy mẫu lại **theo cụm**: BGL theo khối thời gian liên tiếp (≥ 1.000 dòng hoặc 1 giờ, ≥ 100 khối); HDFS theo nhóm block liền nhau theo thứ tự xuất hiện hoặc thời gian của protocol repo.
   - Dùng **cùng một tập chỉ số resample** cho mọi phương pháp, vì đây là so sánh ghép cặp.
   - B ≥ 2.000; CI percentile (có thể dùng BCa); tính cho ΔAP, ΔAUROC và FAR.
   - Lý do: các dòng trong cùng một burst tương quan với nhau, nên bootstrap iid sẽ cho CI quá hẹp. Nền tảng là block bootstrap cho dữ liệu phụ thuộc (Künsch 1989, Ann. Statist. 17(3):1217–1241). **Tôi chỉ xác nhận được thông tin thư mục và tóm tắt** của bài này.
2. **DeLong 1988** (Biometrics 44(3):837–845, DOI 10.2307/2531595; **chỉ xác nhận được thông tin thư mục**).
   - Là kiểm định phi tham số cho hai AUC tương quan trên **cùng một tập đối tượng** (paired).
   - Nhận xét: DeLong giả định các đối tượng độc lập, nên với dòng log thì vi phạm giả định. Chỉ dùng như sanity check, chủ yếu ở mức block HDFS.
   - Bản cho dữ liệu theo cụm là Obuchowski 1997 (Biometrics 53:567–578; **chỉ thông tin thư mục**). Có thể dùng thay DeLong nếu muốn một kiểm định giải tích.
3. **Đa so sánh:** thứ tự cố định K1 → K2 → K3 (fixed-sequence), hoặc Holm, đăng ký trước.
4. **Qua các target:** chỉ có 2–3 target, nên **không** dùng được Wilcoxon / Friedman / CD diagram như ADBench, LSCP, Ma, ECOD (các bài đó cần 20–57 dataset). Báo cáo từng target riêng, kèm tính nhất quán về dấu.
5. **Seed:**
   - Fusion bản thân là tất định (deterministic).
   - Để phản ánh phương sai do calibration: lặp lại việc chia buffer B1/B2 một cách ngẫu nhiên (≥ 5 lần, như 5 lần chia calibration của Gupta 2025).
   - Phương sai do huấn luyện expert: hiện chỉ có S42, nên **phải ghi là hạn chế**. Muốn khẳng định xếp hạng giữa các biến thể LLM thì cần ≥ 3 seed (LogGPT dùng 10, Ren dùng 10, Le & Zhang dùng 5); việc này cần người dùng đồng ý vì tốn GPU.
6. **Độ lớn hiệu ứng kỳ vọng:**
   - Gupta 2025 báo cáo lợi ích ensemble +0,02 đến +0,08 AUROC so với thành viên tốt nhất.
   - SE của AUROC trên source-dev khoảng 0,07–0,085 (review trước, Hanley–McNeil).
   - Hệ quả: **source-dev không thể phân giải** được lợi ích fusion; chỉ có tập đích lớn mới phân giải được. Phải chấp nhận khả năng kết quả là "không khác biệt có ý nghĩa", và báo cáo cả trường hợp đó.

### 5.6 Danh sách báo cáo tối thiểu (checklist)
- [ ] π_t, số unit, số cụm bootstrap cho từng target.
- [ ] AP, AP lift, AUROC, Recall@FAR(q), FAR thực tế, FPR@TPR80 cho: Sem, Seq (base / best / latest), base Llama, B0, K1, K2, K3, Seq_best ⊕ Seq_latest, logistic F-D (chỉ làm comparator).
- [ ] FG_oracle, FG_deploy, FG_ens, FG_B0 kèm CI 95% theo cluster bootstrap.
- [ ] Spearman ρ và tỉ lệ cùng vượt ngưỡng trên buffer; số mẫu dương chỉ một expert bắt được.
- [ ] Best-F1 (nếu có) dán nhãn **oracle**.
- [ ] Các mục chưa làm và hạn chế: một seed, Hadoop chỉ mô tả, buffer có thể nhiễm, chưa có Semantic-BGL.

---

## 6. Nguồn đã mở cho file này (ngoài các nguồn ở FUSION_LITERATURE_REVIEW.md)

- Saito & Rehmsmeier 2015, PLoS ONE: https://doi.org/10.1371/journal.pone.0118432 ([TOÀN VĂN])
- Davis & Goadrich 2006, ICML: http://ftp.cs.wisc.edu/machine-learning/shavlik-group/davis.icml06.pdf ([TOÀN VĂN]); DOI 10.1145/1143844.1143874
- ADBench: https://arxiv.org/abs/2206.09426 ([MỘT PHẦN])
- **Chỉ thông tin thư mục:**
  - DeLong, DeLong & Clarke-Pearson 1988, Biometrics 44(3):837–845, DOI 10.2307/2531595
  - Obuchowski 1997, Biometrics 53:567–578
  - Künsch 1989, Ann. Statist. 17(3):1217–1241, DOI 10.1214/aos/1176347265
