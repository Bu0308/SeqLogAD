# Fusion Literature Review cho SeqLogAD (Semantic expert + Sequence expert)

**Ngày:** 2026-10-23 · **Người viết:** research worker (phiên research-xhigh) · **Phạm vi:** chỉ đọc, tìm trên web công khai, không train, không mở nhãn đích.
**Đầu vào đã đọc trước khi viết:** `xh/AUDIT_BRIEF.md`, `xh/FUSION_CANDIDATES.md`, `docs/reports/FUSION-RESEARCH-TRAINING-AUDIT-2026-10-23.md` (mục 4 có 14 công trình đã kiểm).

## 0. Cách đọc tài liệu này

**Bối cảnh cần nhớ.** Hai expert dùng chung một Llama-3.1-8B đóng băng (QLoRA, LoRA r=16):
- **Semantic** chấm từng message bằng masked reconstruction NLL.
- **Sequence** chấm next-log NLL với tối đa 8 bản ghi đứng trước.

Thiết lập đánh giá:
- Cross-system theo leave-one-architecture-out (đích: BGL, HDFS, Hadoop; OpenStack chỉ làm source).
- **Không có nhãn đích nào.** Source chỉ có khoảng 26–114 mẫu dương.
- Mỗi expert cho ra một điểm vô hướng (scalar) trên mỗi unit.

Fusion chính dự kiến:
- Late fusion đã hiệu chỉnh, không dùng nhãn: ECDF/conformal p-value cho từng expert, rồi gộp bằng Vovk–Wang 2·mean(p).
- Một biến thể likelihood-ratio dùng base model làm tham chiếu.
- Mật độ copula 2-D một phía.
- Logistic học có nhãn chỉ làm comparator.

**Nhãn trạng thái của từng nguồn**

| Nhãn | Nghĩa |
|---|---|
| **PR** | Đã qua bình duyệt (peer-reviewed). Venue lấy từ chính PDF (header/footer, ACM Reference Format) hoặc từ trường journal-ref/comments trên arXiv mà tôi đã thấy |
| **PP** | Preprint. Chưa thấy bằng chứng bình duyệt |
| **[TOÀN VĂN]** | Đã mở PDF và đọc phần method + experiments (trích bằng pdftotext rồi đọc từng đoạn liên quan) |
| **[MỘT PHẦN]** | Đã mở PDF nhưng chỉ đọc một số đoạn. Các trường ghi "chưa trích" là chưa kiểm |
| **[ABSTRACT]** | Chỉ đọc được abstract hoặc trang chương trình hội nghị. Không dùng số liệu nào ngoài abstract |
| **[THƯ MỤC]** | Chỉ xác nhận được thông tin thư mục (tác giả, venue, DOI). Chưa đọc nội dung |

**Mức liên quan** (Cao / Trung bình / Thấp) được đánh giá cho **đúng bài toán này**: hai expert vô hướng trên cùng một backbone, zero target label, ít mẫu dương ở source. Đây không phải đánh giá chất lượng chung của bài báo.

**Phân biệt loại nhận định:**
- "Tác giả báo cáo" = số liệu hoặc khẳng định lấy nguyên từ bài.
- "Nhận xét" = suy luận của tôi.
- Mọi con số trong file đều do tác giả báo cáo, trừ chỗ ghi rõ là suy luận.

---

## 1. Bảng tổng hợp (27 mục)

| # | Công trình | Venue / trạng thái | Đã đọc | Nhóm | Liên quan |
|---|---|---|---|---|---|
| 1 | Guan et al., **LogLLM** | arXiv 2411.08561 v6 (PP) | TOÀN VĂN | (a) LLM log AD | Trung bình |
| 2 | Han, Yuan, Trabelsi, **LogGPT** | arXiv 2309.14482 v2 (PP; venue chưa xác minh) | MỘT PHẦN | (a) | Trung bình |
| 3 | Liu et al., **LogPrompt** (*Interpretable Online Log Analysis Using LLMs with Prompt Strategies*) | ICPC 2024 (PR, theo arXiv/researchr); bản ngắn là poster ICSE 2024 | MỘT PHẦN | (a) zero-shot | Trung bình |
| 4 | Pan, Wong, Yuan, **RAGLog** | arXiv 2311.05261 (PP; PDF có dòng "© 2023 IEEE", venue chưa xác minh) | TOÀN VĂN (bài ngắn) | (a) | Thấp |
| 5 | Zhao et al., **ZeroLog** | arXiv 2511.05862 v1 (PP) | MỘT PHẦN | (a) zero-label cross-system | Cao (về protocol) |
| 6 | Zhao et al., **FreeLog** (*From Few-Label to Zero-Label…*) | FSE Companion 2025 (PR, 5 trang), DOI 10.1145/3696630.3728519 | TOÀN VĂN | (a) | Trung bình |
| 7 | Zhao et al., **GeneralLog** (*Generality Is Not Enough…*) | arXiv 2511.05882 (PP; kết quả tìm kiếm liệt kê ở ICSE 2026 NIER nhưng tôi chưa mở trang đó) | MỘT PHẦN | (a) router | Trung bình |
| 8 | Zhao et al., **FusionLog** | arXiv 2511.05878 v3 (PP; header khuôn mẫu IEEE TSC "VOL. XX", chưa xác nhận được chấp nhận) | MỘT PHẦN | (a) fusion/router | Trung bình |
| 9 | **MetaLog** (ICSE 2024) | ICSE 2024 Research Track (PR) | ABSTRACT | (a) | Thấp – Trung bình |
| 10 | Qi et al., **LogMoE** | ASE 2025 (PR, Distinguished Paper) | ABSTRACT | (a) MoE cross-system | Trung bình (baseline) |
| 11 | Le & Zhang, *Log-based AD with DL: How Far Are We?* | ICSE 2022 (PR) | TOÀN VĂN (các phần liên quan) | (a) protocol | **Cao** |
| 12 | Meng et al., **LogAnomaly** | IJCAI 2019 (PR) | TOÀN VĂN | (a) hai view | Trung bình |
| 13 | Landauer, Skopik, Wurzenberger, *A Critical Review of Common Log Data Sets…* | Proc. ACM Softw. Eng. (FSE 2024), theo journal-ref trên arXiv 2309.02854 (PR) | MỘT PHẦN | (a) protocol / dataset | **Cao** |
| 14 | Bates, Candès, Lei, Romano, Sesia, *Testing for outliers with conformal p-values* | Ann. Statist. 51(1), 2023 (PR) | TOÀN VĂN | (b) conformal | **Cao** |
| 15 | Vovk & Wang, *Combining p-values via averaging* | Biometrika 107(4), 2020 (PR) | MỘT PHẦN | (b) p-merge | **Cao** |
| 16 | Liu & Xie, *Cauchy combination test* | JASA 115(529), 2020 (PR) | MỘT PHẦN | (b) p-merge | Trung bình |
| 17 | Gupta et al., *Polysemantic Dropout: Conformal OOD Detection for Specialized LLMs* | EMNLP 2025 (PR) | TOÀN VĂN | (b) conformal ensemble trên LLM | **Cao** |
| 18 | Kriegel, Kröger, Schubert, Zimek, *Interpreting and Unifying Outlier Scores* | SDM 2011 (PR) | MỘT PHẦN (bản preprint qua Wayback) | (b) chuẩn hóa điểm | Trung bình |
| 19 | Zhao, Nasrullah, Hryniewicki, Li, **LSCP** | SDM 2019 (PR) | MỘT PHẦN | (b) chọn cục bộ | Thấp – Trung bình |
| 20 | Ma, Zhao, Zhang, Akoglu, *The Need for Unsupervised Outlier Model Selection* | SIGKDD Explorations 25(1), 2023 (PR) | TOÀN VĂN | (b) ràng buộc | **Cao** |
| 21 | Ren et al., *Likelihood Ratios for OOD Detection* | NeurIPS 2019 (PR) | TOÀN VĂN | (b) likelihood ratio | **Cao** (cho K2) |
| 22 | Serrà et al., *Input Complexity and OOD Detection with Likelihood-based Generative Models* | ICLR 2020 (PR) | MỘT PHẦN | (b) likelihood ratio | **Cao** (cho K2) |
| 23 | Li, Zhao, Botta, Ionescu, Hu, **COPOD** | ICDM 2020 (PR, theo journal-ref arXiv) | MỘT PHẦN | (b) ECDF / copula | Trung bình (cho K3) |
| 24 | Li, Zhao, Hu, Botta, Ionescu, Chen, **ECOD** | IEEE TKDE 2022 (PR, theo comments arXiv) | MỘT PHẦN | (b) ECDF tail | Trung bình |
| 25 | Han et al., **ADBench** | NeurIPS 2022 Datasets & Benchmarks (PR) | MỘT PHẦN | (b) protocol | Trung bình (protocol) |
| 26 | Zhao et al., **AnoFusion** (*Robust Multimodal Failure Detection for Microservice Systems*) | KDD 2023 (PR) | MỘT PHẦN | (c) multimodal fusion | Thấp (để loại trừ) |
| 27 | Nhóm deep fusion và LoRA composition: TFN, LMF, MulT, MBT, AdapterFusion, TIES, DARE, LoraHub (cùng Hades, MoLE, X-LoRA, Arrow, LoRA Soups) | xem mục 4 | THƯ MỤC / review trước | (c) | Thấp (loại trừ) |

So với mục 4 của review trước, file này **thêm** #1–8, #11, #13, #21, #23–25 và đọc lại sâu hơn #14, #17, #18, #20. Ren et al. 2019 và Kriegel 2011 trước đây chưa đọc được, **nay đã đọc**.

---

## 2. Nhóm (a): Log AD dùng LLM / cross-system

### 2.1 LogLLM: Guan, Cao, Qian, Gao, Ouyang (PP, arXiv 2411.08561 v6). [TOÀN VĂN]
- **Mục tiêu:** phát hiện bất thường trên log sequence theo kiểu supervised, kết hợp một encoder LLM (ngữ nghĩa từng message) với một decoder LLM (phụ thuộc chuỗi).
- **Backbone:** BERT-base (LLM_E, 768-d) và Llama-3-8B (LLM_D, 4096-d), dùng QLoRA. LoRA rank 4 / α 32 cho BERT; rank 8 / α 16 cho Llama.
- **Fusion & vị trí:** fusion ở **tầng biểu diễn**.
  - Một *projector* tuyến tính map vector BERT của từng message sang embedding space của Llama.
  - Llama đọc chuỗi embedding đó rồi sinh ra câu trả lời "normal/anomalous".
  - Đây là **early/intermediate fusion có huấn luyện**, không phải late fusion.
- **Biểu diễn:** mỗi message → một vector (giảm số token so với đưa text thô vào). Preprocessing dùng regex, **không** dùng log parser.
- **Huấn luyện / loss:**
  - Cross-entropy trên câu trả lời. Train 3 giai đoạn: (1) chỉ fine-tune LLM_D cho đúng format, dùng 1.000 mẫu, lr 5e-4; (2) fine-tune embedder (BERT + projector); (3) fine-tune toàn bộ, 2 epoch, lr 5e-5.
  - Oversample lớp thiểu số lên tối thiểu β = 30%.
- **Dữ liệu:** HDFS (session theo block_id), BGL, Liberty, Thunderbird (cửa sổ 100 message, bước 100).
  - Train/test = 8:2. **HDFS chia ngẫu nhiên**; BGL, Liberty, Thunderbird chia theo thời gian (chronological).
- **Metric:** Precision / Recall / F1. Không có AUROC/AP.
- **Baseline:** DeepLog, LogAnomaly, PLELog, FastLogAD, LogBERT, LogRobust, CNN, LogLLaMA, EagerLog, NeuralLog, RAPID, BGE-Trans. Tất cả chạy bằng code gốc với hyperparameter như trong bài gốc.
- **Ablation:** bỏ Stage 1, bỏ Stage 2, bỏ cả Stage 1 & 2, bỏ Stage 3; thay oversampling bằng cost-sensitive loss; so sánh các cách preprocessing; đổi LLM (Qwen3, GLM-4).
- **Thống kê:** không thấy repeated runs, std hay kiểm định.
- **Compute:** một NVIDIA A40 48 GB (tác giả báo cáo).
- **Kết quả (tác giả báo cáo, Bảng II, v6):**

  | Dataset | P | R | F1 |
  |---|---|---|---|
  | HDFS | 0,994 | 1,000 | 0,997 |
  | BGL | 0,861 | 0,979 | 0,916 |
  | Liberty | 0,992 | 0,926 | 0,958 |

  F1 trung bình hơn baseline mạnh nhất (NeuralLog) 6,6%.
- **Hạn chế:**
  - Supervised, cần nhãn trong cùng hệ thống; không đánh giá cross-system.
  - HDFS chia ngẫu nhiên. Đây đúng là kiểu chia mà Le & Zhang 2022 cảnh báo là gây rò rỉ dữ liệu (data leakage).
  - Chạy một lần duy nhất.
- **Code:** https://github.com/guanwei49/LogLLM
- **Liên quan: Trung bình.** Là tiền lệ "semantic encoder + sequence decoder trên cùng một Llama-3-8B", nhưng fusion của họ cần nhãn và train end-to-end, nên **không** áp dụng được khi không có nhãn đích. Nên trích làm related work cho ý tưởng "hai góc nhìn semantic + sequence".

### 2.2 LogGPT: Han, Yuan, Trabelsi (PP, arXiv 2309.14482 v2; venue chưa xác minh). [MỘT PHẦN]
- **Mục tiêu:** semi-supervised log AD bằng next-log-key prediction, sau đó fine-tune bằng RL để thu hẹp khoảng cách giữa objective huấn luyện và objective phát hiện.
- **Backbone:** GPT-2 nhỏ (6 layer, 6 head, embedding 60-d), train từ đầu trên log key (Drain).
- **Fusion:** không có.
- **Công thức chính:**
  - Một sequence bị gắn bất thường nếu có ít nhất một log key thực tế **không** nằm trong Top-K dự đoán.
  - Reward RL = +1 nếu key thật nằm trong Top-K, −1 nếu không.
  - **K = 50% số log key của tập train, cố định**, không tune trên test.
- **Dữ liệu:**
  - HDFS (575.061 session, 16.838 bất thường), BGL (cửa sổ 1 phút; 36.927 sequence, 3.296 bất thường), Thunderbird (20 triệu dòng đầu; 112.959 sequence, 40.920 bất thường).
  - Train = **5.000 sequence bình thường lấy ngẫu nhiên**.
- **Metric:** P / R / F1, có mean ± std **qua 10 lần chạy**, kèm **paired t-test** so với baseline tốt nhất (p < 0,05).
- **Baseline:** PCA, iForest, OCSVM, LogCluster, DeepLog, LogAnomaly, OC4Seq, LogBERT, CAT.
- **Ablation:** có và không có RL (Bảng III).
- **Hạn chế:** chọn train ngẫu nhiên (không theo thời gian); K vẫn là một quyết định thiết kế; chỉ in-system.
- **Code:** https://github.com/nokia/LogGPT
- **Liên quan: Trung bình.** Cơ chế gần với Sequence expert (next-log likelihood). Đây là một trong số ít bài log AD có **10 lần chạy + kiểm định**. Tôi không chép số F1 vì bảng bị vỡ khi trích bằng pdftotext.

### 2.3 LogPrompt: Liu et al. (PR, ICPC 2024; arXiv 2308.07610). [MỘT PHẦN]
- **Mục tiêu:** dùng ChatGPT zero-shot (không train in-domain) cho log parsing và anomaly detection, kèm giải thích.
- **Backbone:** gpt-3.5-turbo-0301 qua API, temperature ban đầu thấp (tăng lên nếu format sai).
- **Cách làm:** prompt strategy (self-prompt, CoT-prompt, in-context). Ở anomaly detection, LLM gắn tag normal/abnormal cho **từng template** trong một session; session bị tính là bất thường nếu có ít nhất một tag abnormal.
- **Dữ liệu (AD):** BGL và Spirit. Session = cửa sổ cố định 100 template (Drain).
  - Baseline train trên **4.000 log đầu tiên**, sau đó test trên phần còn lại (kiểu online, chia theo thời gian).
- **Metric:** session-level P / R / F1. Với DeepLog và LogAnomaly, tác giả báo cáo "top-4 F1".
- **Kết quả (tác giả báo cáo, Bảng 3):**

  | Dataset | P | R | F1 | Baseline tốt nhất |
  |---|---|---|---|---|
  | BGL | 0,249 | 0,834 | 0,384 | DeepLog F1 0,268 |
  | Spirit | 0,290 | 0,999 | 0,450 | F1 ≤ 0,289 |

  Ghi chú: LogPrompt dùng 0 log để train.
- **Thống kê:** không thấy kiểm định hay số lần chạy.
- **Code:** https://github.com/lunyiliu/LogPrompt (link thấy trong kết quả tìm kiếm, chưa mở repo).
- **Liên quan: Trung bình.** Đây là baseline zero-shot LLM, không cần nhãn đích. Kết quả cho thấy bất thường mức session ở BGL vẫn rất khó khi không có nhãn: precision thấp, tức FAR cao.

### 2.4 RAGLog: Pan, Wong, Yuan (PP, arXiv 2311.05261). [TOÀN VĂN, bài ngắn]
- **Cơ chế:** vector DB chỉ chứa log **bình thường** (lấy ngẫu nhiên, hoặc lấy theo cụm k-means). GPT-3.5 (Davinci, temperature 0,1) được hỏi "normal/abnormal" kèm các log bình thường gần nhất truy xuất được.
- **Dữ liệu:** BGL, Thunderbird; 10.000 log mỗi cụm (5 cụm cho BGL, 4 cụm cho Thunderbird). **Test lấy mẫu ngẫu nhiên** từ 20% dữ liệu giữ lại, vì giới hạn chi phí API. Cỡ mẫu test không ghi rõ.
- **Kết quả (tác giả báo cáo):** P 0,91 / R 0,88 / F1 0,89, so với LogPrompt 0,25 / 0,83 / 0,38. Tuy nhiên đây là **so số liệu giữa hai bài khác nhau, trên hai mẫu test khác nhau**, và dataset của dòng này không được nêu rõ trong đoạn tôi đọc.
- **Liên quan: Thấp.** Chỉ đáng dẫn làm ví dụ "so sánh không cùng điều kiện" (mục 5 của EVAL_PROTOCOL_EVIDENCE).

### 2.5 ZeroLog (PP, arXiv 2511.05862) và FreeLog (PR, FSE Companion 2025): Zhao, Jia, He, (Wu), Li, Huang, ĐH Bắc Kinh. [MỘT PHẦN / TOÀN VĂN]
- **Mục tiêu:** cross-system log AD **không có nhãn đích** (zero-label). FreeLog là bản ngắn 5 trang; ZeroLog là bản đầy đủ của cùng ý tưởng.
- **Backbone:** mạng nhỏ trên semantic embedding 300-d của log event (embedding toàn cục theo kiểu MetaLog, parser Drain).
- **Cơ chế:** unsupervised domain adaptation dạng đối kháng (domain classifier phân biệt source/target) kết hợp meta-learning (meta-train / meta-test) trên các meta-task.
  - Loss = BCE phân loại trên source + loss đối kháng miền.
  - Có hyperparameter β, γ.
- **Fusion:** không có (một mô hình duy nhất).
- **Dữ liệu:** HDFS, BGL, OpenStack. Bốn cặp chuyển: HDFS→BGL, BGL→HDFS, OpenStack→HDFS, OpenStack→BGL.
- **Chi tiết protocol quan trọng (tác giả báo cáo):**
  - Với HDFS→BGL: dùng "tất cả log bất thường của HDFS và **một số lượng bằng nhau** log bình thường".
  - Với OpenStack→target: dùng "**một số lượng bằng nhau** log bình thường và bất thường **chưa gán nhãn** của HDFS và BGL" để train.
  - **Nhận xét:** như vậy tập đích "không nhãn" đã được lấy mẫu cân bằng lớp, mà muốn cân bằng thì phải biết nhãn. Tỉ lệ dương ≈ 50% khác xa thực tế (HDFS khoảng 2,9%), và F1 bị thổi phồng.
- **Metric:** P / R / F1.
- **Baseline:** PLELog, LogRobust (dùng nhãn đích 1% hoặc 100%); LogTAD, LogTransfer; MetaLog; DeepLog; NeuralLog (zero-shot).
- **Ablation (ZeroLog):** bỏ meta-learning làm F1 tụt xuống 61,74 / 62,81 / 53,70 / 66,84 trên bốn cặp. Có phân tích độ nhạy β, γ **trên F1 của đích** (ví dụ "83% khi β = 2, γ = 2,5"). Không thấy mô tả cách chọn β, γ mà không dùng nhãn.
- **Thống kê:** không thấy số lần chạy, std hay kiểm định.
- **Compute:** một RTX 3090, khoảng 9,5 phút train (ZeroLog, tác giả báo cáo).
- **Kết quả:** F1 > 80% ở thiết lập zero-label (abstract cả hai bài). ZeroLog: F1 82 (HDFS→BGL) và 79 (BGL→HDFS).
- **Liên quan: Cao về protocol, Trung bình về phương pháp.** Đây là nhóm bài gần nhất với thiết lập "zero target label, cross-system". Nhưng protocol của họ dùng tập đích cân bằng lớp và không có CI, nên **không nên so trực tiếp con số F1**. Nếu dẫn, phải nêu rõ khác biệt protocol.

### 2.6 GeneralLog (PP, arXiv 2511.05882) và FusionLog (PP, arXiv 2511.05878 v3): cùng nhóm tác giả. [MỘT PHẦN]
- **Mục tiêu:** zero-label cross-system bằng cách kết hợp LLM với small model và **định tuyến theo loại tri thức**.
- **Router (không cần train):**
  - Với mỗi event của chuỗi đích: sim_i = max_j cos(v_i, u_j), trong đó u_j là embedding các event của source.
  - Gộp lên mức chuỗi: x_sim = min_i sim_i.
  - Nếu x_sim ≥ τ thì chuỗi là "general log" và đi tới small model (meta-learning, FreeLog). Ngược lại là "proprietary log".
  - GeneralLog: proprietary đi tới LLM (Qwen3) kèm RAG.
  - FusionLog: proprietary đi qua **chưng cất nhiều vòng**. LLM (Qwen3-Plus, temperature 1,0, top-p 0,8) và small model cùng tạo pseudo-label; giữ các mẫu hai bên đồng thuận và vượt ngưỡng tin cậy động ε; dùng chúng fine-tune small model.
  - FusionLog đặt **τ = trung bình điểm similarity mức chuỗi**. Đây là cách chọn không dùng nhãn (điểm cộng về protocol).
- **Vị trí fusion:** định tuyến cứng ở mức chuỗi (decision-level routing), cộng với chưng cất tri thức (training-level).
- **Dữ liệu và protocol:** giống FreeLog, gồm cả việc lấy "số lượng bằng nhau log bình thường và bất thường" của đích.
- **Metric:** P / R / F1.
- **Kết quả (tác giả báo cáo):**
  - F1 > 90% (abstract cả hai bài).
  - FusionLog: thay Qwen3 bằng DeepSeek-V3.2 / GLM-4.6 / Gemini-2.5-Flash cho F1 95,71 / 92,50 / 91,12.
  - Ablation có phân tích độ nhạy theo τ: router cho F1 khoảng 93% trên general log nhưng khoảng 54% trên proprietary log (FusionLog, Hình 5).
- **Thống kê:** không thấy kiểm định hay số lần chạy.
- **Liên quan: Trung bình.**
  - Ý tưởng "định tuyến theo độ mới của template so với source" tương ứng với **F-B (novelty router)** của chúng ta.
  - Kết quả 93% so với 54% cho thấy **hai nhóm này khác nhau rất rõ về độ khó**. Đó là lý do nên báo cáo kết quả theo strata "template đã thấy / chưa thấy".
  - Nhưng mọi con số F1 đều chịu cùng vấn đề protocol như 2.5.

### 2.7 MetaLog (PR, ICSE 2024). [ABSTRACT]
- Theo abstract trên researchr: embedding ngữ nghĩa nhất quán toàn cục cộng với meta-learning. Đánh giá trên HDFS, BGL, OpenStack, Thunderbird. F1 > 80% khi có **1% nhãn đích**; hơn các mô hình transfer learning khoảng 20%.
- Chưa đọc được PDF (ACM DL trả về 403).
- Trang: https://conf.researchr.org/details/icse-2024/icse-2024-research-track/205/MetaLog-Generalizable-Cross-System-Anomaly-Detection-from-Logs-with-Meta-Learning
- **Liên quan: Thấp – Trung bình.** Cần nhãn đích; chỉ nên dùng làm related work.

### 2.8 LogMoE: Qi, Luan, Huang, Fung, Wang, Wang, Zhang, Yang, Qian (PR, ASE 2025, Distinguished Paper). [ABSTRACT]
- Theo abstract: nhiều expert nhẹ, mỗi expert train trên nhãn của một hệ thống trưởng thành; gộp bằng **gating MoE**; không cần log parsing.
- Đánh giá trên 8 dataset theo ba kịch bản: single-system, homogeneous, heterogeneous. Mạnh nhất khi đích có ít nhãn.
- Trang chương trình không có số liệu, PDF hay code.
- https://conf.researchr.org/details/ase-2025/ase-2025-papers/13/LogMoE-Lightweight-Expert-Mixture-for-Cross-System-Log-Anomaly-Detection
- **Liên quan: Trung bình (baseline cross-system nên dẫn).** Gate của họ học từ nhãn source, nên với 26–114 mẫu dương thì không học được gate tương tự.

### 2.9 Le & Zhang, *Log-based Anomaly Detection with Deep Learning: How Far Are We?* (PR, ICSE 2022; arXiv 2202.04301). [TOÀN VĂN, các phần liên quan]
- **Mục tiêu:** đánh giá lại 5 mô hình DL (DeepLog, LogAnomaly, PLELog, LogRobust, CNN) trên HDFS, BGL, Spirit, Thunderbird, trong điều kiện thí nghiệm được kiểm soát.
- **Phát hiện chính (tác giả báo cáo):**
  1. **Chia ngẫu nhiên hay theo thời gian** ảnh hưởng mạnh tới mô hình semi-supervised; chia ngẫu nhiên gây data leakage. Ví dụ: DeepLog trên BGL đạt F1 0,927 khi chia ngẫu nhiên, nhưng chỉ còn **0,426** khi chia theo thời gian.
     - HDFS không có timestamp nên không chia theo thời gian được.
     - Tác giả cho rằng LogAnomaly gốc dùng chia ngẫu nhiên. **Mâu thuẫn:** bài LogAnomaly (2.10) ghi "front 80% (according to the timestamps)". Đây là bất đồng giữa hai nguồn, tôi không giải quyết được.
  2. Cách nhóm log (window, session) ảnh hưởng nhiều tới kết quả; chuỗi ngắn làm giảm độ chính xác.
  3. Mất cân bằng lớp: "Precision, Recall, F-measure không đủ toàn diện". Tác giả đề xuất thêm **Specificity**.
  4. Một ít nhiễu nhãn hoặc lỗi parsing đã làm giảm hiệu năng; mô hình supervised nhạy hơn.
- **Protocol của chính họ:** train/test 80:20, chạy mỗi thí nghiệm **5 lần lấy trung bình**. Dùng hyperparameter của bài gốc, nếu bài gốc không có thì tune "empirically" (không nói rõ trên tập nào).
- **Code:** https://github.com/LogIntelligence/LogADEmpirical
- **Liên quan: Cao.** Là nguồn chính để biện minh cho split theo thời gian, cho việc báo cáo TNR/FAR, và cho việc chạy nhiều lần.

### 2.10 LogAnomaly: Meng et al. (PR, IJCAI 2019). [TOÀN VĂN]
- **Cơ chế:** template2vec (dùng từ đồng nghĩa/trái nghĩa) cho chuỗi template vector (sequential pattern), cộng với count vector (quantitative pattern). Cả hai cùng đi vào một LSTM; phát hiện bất thường theo top-k candidate.
- **Fusion:** **ghép đặc trưng (early fusion) trong cùng một mô hình**.
- **Dữ liệu:** BGL, HDFS; "front 80% (theo timestamp) để train, 20% còn lại để test". Window size 20, step 1.
- **Kết quả (tác giả báo cáo):**
  - F1 trung bình 0,96 (BGL) / 0,95 (HDFS).
  - Bỏ template vector sequence: precision còn 0,84 / 0,83, so với 0,97 / 0,96 khi đầy đủ.
  - Bỏ count vector cũng làm giảm cả P và R.
  - Online BGL: F1 0,8632, so với DeepLog 0,5489.
- **Protocol đáng chú ý:** "The parameters of these methods are all set best for accuracy". Tức tham số của baseline được đặt ở mức tốt nhất theo accuracy, mà không nói tune trên tập nào. Nhận xét: nhiều khả năng là tune trên test.
- **Liên quan: Trung bình (động lực).** Là bằng chứng sớm rằng hai góc nhìn chuỗi và nội dung bổ sung cho nhau. Nhưng đó là trong cùng hệ thống, có train chung, không phải late fusion.

### 2.11 Landauer, Skopik, Wurzenberger, *A Critical Review of Common Log Data Sets Used for Evaluation of Sequence-based Anomaly Detection Techniques* (PR theo journal-ref: Proc. ACM Softw. Eng., FSE 2024; arXiv 2309.02854). [MỘT PHẦN]
- **Mục tiêu:** kiểm tra xem 6 dataset log phổ biến (HDFS, BGL, Thunderbird, OpenStack, Hadoop, ADFA) có thực sự cần mô hình chuỗi hay không.
- **Phương pháp:** dùng các detector đơn giản (event mới, độ dài, ECVC = event count vector, edit distance, n-gram).
  - Ngưỡng được chọn bằng cách quét 0–1 bước 0,01 rồi **lấy ngưỡng tối đa hóa F1**. Tác giả nói rõ đây là ngưỡng tối ưu.
  - Chạy **25 lần** với mẫu train ngẫu nhiên; báo cáo trung bình và max.
  - **Không** làm kiểm định thống kê.
- **Kết quả chính (tác giả báo cáo):**
  - "Phần lớn bất thường không liên quan trực tiếp tới biểu hiện tuần tự".
  - HDFS: kết hợp "event mới + độ dài" cho F1 90,4% trên bản LogDeep, nhưng chỉ trung bình 72,0% trên bản gốc. Lý do: tập train của LogDeep không chứa event type 20, một event chỉ báo bất thường nhưng cũng xuất hiện ở 0,04% chuỗi bình thường.
  - BGL: chỉ cần phát hiện event type mới là đã có kết quả cạnh tranh.
  - **Hadoop:** F1 91,5% với TPR 100% nhưng **TNR 0%**, tức detector gắn cờ mọi chuỗi. Lý do: 82,9% chuỗi Hadoop là bất thường, và nhiều chuỗi bình thường giống hệt chuỗi bất thường.
  - Comparability giữa các bài bị hạn chế vì mỗi bài chia train/test khác nhau và "often only report the best scores achieved from multiple runs".
- **Liên quan: Cao.**
  1. Baseline B0 (template novelty, tần suất) là bắt buộc. Sequence expert có thể chỉ đang học lại B0, và probe V13R1 cũng gợi ý điều đó.
  2. Đích **Hadoop** có vấn đề nghiêm trọng về nhãn và tỉ lệ dương. Cần kiểm tra lại cách project định nghĩa unit Hadoop. Hadoop chỉ nên dùng để mô tả.
  3. Phải báo cáo TNR/FAR bên cạnh mọi chỉ số mạnh về recall.

---

## 3. Nhóm (b): Ensemble điểm outlier, chuẩn hóa điểm và gộp p-value

### 3.1 Bates, Candès, Lei, Romano, Sesia (PR, Ann. Statist. 2023; arXiv 2104.08279). [TOÀN VĂN]
- **Mục tiêu:** kiểm định outlier có đảm bảo, bằng conformal p-value tính trên một tập calibration sạch, cho bất kỳ one-class classifier nào.
- **Công thức (quy ước điểm cao = bất thường):** p̂(x) = (1 + #{i ∈ cal : ŝ(X_i) ≥ ŝ(x)}) / (n + 1).
  - p̂ marginally super-uniform dưới H0, tức hợp lệ nếu lấy trung bình trên các lần rút calibration set.
  - **Sàn của p̂ là 1/(n+1).** Điều này giải thích hiện tượng bão hòa khi điểm vượt max của buffer.
- **Định lý chính:**
  - **Thm 1:** khi gộp p-value của **nhiều điểm test cùng dùng một calibration set** để kiểm định global null bằng Fisher's combination, type-I error không còn đúng mức danh nghĩa.
  - **Thm 2:** các conformal p-value có tính PRDS, nên **BH kiểm soát FDR**.
  - Mục 3 đưa ra p-value *calibration-conditional* (CCV) qua hàm điều chỉnh h (Simes, DKWM, hoặc Monte Carlo); có trả giá bằng power.
- **Thí nghiệm:**
  - Dữ liệu mô phỏng: Gaussian mixture 50-d, n = 1.000.
  - 7 dataset thật: ALOI, Cover, Credit card, KDDCup99, Mammography, Digits, Shuttle. Base detector là isolation forest (thêm OCSVM và LOF ở phụ lục).
  - Metric: **FDR và power có điều kiện theo calibration set**, tính trên J "practitioner" độc lập.
  - Ở bài toán batch, harmonic mean và Simes không phát hiện được gì; Fisher có power cao hơn Stouffer.
- **Đính chính so với review trước:**
  - Review trước viết "gộp Fisher các p-value conformal dùng chung calibration set là không hợp lệ". Thm 1 nói về **gộp qua các điểm test** (batch) chứ không phải gộp **hai expert trên cùng một unit**.
  - Ở bài toán của chúng ta: p_sem(x) và p_seq(x) tính trên cùng buffer B1 cho cùng unit x, và chúng phụ thuộc nhau theo một cách tùy ý chưa biết. Vì vậy cần luật hợp lệ dưới **mọi** dạng phụ thuộc, tức Vovk–Wang (3.2).
  - Fisher hay Stouffer dạng thường (giả định độc lập) vẫn **không** dùng được, nhưng lý do là phụ thuộc giữa hai expert, không phải Thm 1.
  - Khi đặt ngưỡng FAR cho cả luồng log, nếu muốn kiểm soát FDR thì BH hợp lệ nhờ PRDS (Thm 2).
- **Liên quan: Cao.** Là nền tảng lý thuyết cho bước hiệu chỉnh của K1.

### 3.2 Vovk & Wang (PR, Biometrika 2020; arXiv 1212.4966). [MỘT PHẦN]
- **Kết quả chính (abstract và mục 1):**
  - Các p-value phụ thuộc tùy ý có thể gộp bằng cách **nhân trung bình cộng với 2**, và "no smaller factor is sufficient in general".
  - Trung bình nhân (geometric) nhân với e (kết quả của Mattner).
  - Trung bình điều hòa (harmonic) nhân với e·ln K.
  - Họ trung bình lũy thừa M_{r,K} với hằng số a_{r,K}.
  - Bonferroni (K·min p) là trường hợp r = −∞.
- **Nhận xét áp dụng (suy luận):**
  1. Với K = 2, cả 2·mean(p) lẫn 2·min(p) đều hợp lệ. Nhưng chúng **xếp hạng các unit khác nhau**: mean ứng với AND-mềm, min ứng với OR.
  2. Với các metric dựa trên thứ hạng (AP, AUROC), **hằng số 2 không ảnh hưởng gì**: xếp hạng theo 2·mean(p) giống hệt xếp hạng theo p_sem + p_seq. Hằng số chỉ quan trọng khi đặt ngưỡng FAR.
  3. Mean of p "chịu" kém một expert có p rất nhỏ (một p = 0,001 với p kia = 0,5 cho mean ≈ 0,25). Vì vậy nó **kém nhạy với bất thường chỉ một expert thấy**. Đây chính là lý do cần thêm biến thể min-p và copula một phía (K3).
- **Liên quan: Cao.**

### 3.3 Liu & Xie, Cauchy combination test (PR, JASA 2020; arXiv 1808.09011). [MỘT PHẦN]
- **Công thức:** T = Σ ω_i tan{(0,5 − p_i)π}.
- **Tính chất:** đuôi của T dưới H0 xấp xỉ Cauchy "under arbitrary dependency structures", với điều kiện (C.1) **bivariate normality** cho mọi cặp z-score; xấp xỉ càng chính xác khi α → 0.
- **Nhận xét:** p-value rời rạc dựa trên hạng (từ ECDF) không thỏa (C.1) một cách chặt chẽ. Do đó chỉ nên dùng làm sensitivity; review trước kết luận như vậy và đúng.
- **Liên quan: Trung bình.**

### 3.4 Gupta, Kaur, Roy, Cobb, Chellappa, Jha, *Polysemantic Dropout* (PR, EMNLP 2025; arXiv 2509.04655). [TOÀN VĂN]
- **Mục tiêu:** phát hiện OOD cho LLM chuyên ngành, có đảm bảo FAR.
- **Backbone:** EYE-LLaMA và MentaLLaMA-chat-7B (đều xây trên LLaMA-2).
- **Cơ chế:**
  - NCM = số neuron phải dropout (theo "polysemantic dropout") cho đến khi câu trả lời đổi nghĩa (GPT-4o-mini làm giám khảo).
  - Mỗi layer (7, 15, 22) cho một ICAD p-value.
  - Gộp K = 3 p-value bằng **valid merging function** của Vovk–Wang (họ trung bình lũy thừa, gồm HM, AM, GM, Bonferroni).
- **Vị trí fusion:** **tầng p-value (decision-level), không có tham số học**. Về cấu trúc, đây là tiền lệ gần nhất với K1: nhiều detector conformal trên **cùng một LLM**, gộp bằng hàm hợp lệ.
- **Dữ liệu:** iD gồm EyeQA và IMHI; OOD gồm CovidQA và MedMCQA.
- **Metric:** AUROC, đường ROC, và đường "FAR guarantee" theo ε ∈ {0, 0,05, …, 0,5}.
- **Protocol:** "averaged over five runs with random 80%−20% splits" giữa tập iD test và tập calibration; std khoảng 0,001.
- **Baseline:** base score (không dùng ICAD), single p-value cho từng layer, majority voting giữa các layer.
- **Ablation:** chọn merging function, số layer, giới hạn m số neuron dropout, step n.
- **Kết quả (tác giả báo cáo, Bảng 1, AUROC):**

  | Model | OOD | Ours (K = 3) | Single p-value tốt nhất (Layer 7) | Majority vote |
  |---|---|---|---|---|
  | EYE-LLaMA | CovidQA | 0,83 | 0,77 | 0,75 |
  | EYE-LLaMA | MedMCQA | 0,91 | 0,83 | 0,81 |
  | MentaLLaMA | CovidQA | 0,95 | 0,93 | 0,55 |
  | MentaLLaMA | MedMCQA | 0,96 | 0,94 | 0,55 |

  Với MentaLLaMA, FAR guarantee bị vi phạm ở ε lớn; tác giả cho là do calibration data không đủ đại diện.
- **Hạn chế:** không có kiểm định thống kê; OOD là dataset khác hẳn (dễ hơn bất thường log); không có metric AP.
- **Liên quan: Cao.** Lợi ích ensemble so với thành viên đơn tốt nhất là **+0,02 đến +0,08 AUROC**. Đây là kỳ vọng thực tế cho fusion của chúng ta, và nằm cùng cỡ với SE của AUROC trên source-dev (≈ 0,07–0,085). Hệ quả: chỉ có thể khẳng định trên tập đích lớn.

### 3.5 Kriegel, Kröger, Schubert, Zimek (PR, SDM 2011; DOI 10.1137/1.9781611972818.2). [MỘT PHẦN, preprint qua Wayback Machine]
- **Mục tiêu:** đưa các outlier score không cùng thang về "xác suất outlier" để có thể so sánh và gộp.
- **Bước 1, regularization:**
  - Baseline regularization: trừ đi giá trị kỳ vọng của inlier.
  - Linear inversion.
  - Logarithmic inversion: Reg(o) = −log(S(o)/S_max).
- **Bước 2, normalization:**
  - Linear.
  - **Gaussian scaling:** Norm(o) = max(0, erf((S(o) − μ_S)/(σ_S·√2))).
  - Gamma scaling.
- **Ensemble:** P(o) = (1/|OD|)·Σ prob_ODi(S_i(o)). Tác giả gọi đây là "a rather simple, baseline scheme".
- **Đánh giá:**
  - Giảm error-cost theo cost model cho dữ liệu mất cân bằng; ROC không dùng để đánh giá phép biến đổi, vì phép biến đổi giữ nguyên thứ hạng.
  - Ensemble trên KDDCup99 và ALOI (feature bagging, LOF với nhiều k, LOF/LDOF/kNN/aggregate-kNN), đo bằng ROC AUC. Cài đặt trong ELKI.
- **Nhận xét:** Gaussian scaling ước lượng μ, σ trên **chính dữ liệu đang chấm**, tức là transductive. Với chúng ta, cách tương đương là ước lượng trên buffer đích. ECDF/conformal (3.1) là phiên bản phi tham số và có đảm bảo của cùng ý tưởng.
- **Liên quan: Trung bình** (baseline chuẩn hóa z-score/erf trong ablation "có/không calibration").

### 3.6 LSCP: Zhao, Nasrullah, Hryniewicki, Li (PR, SDM 2019; arXiv 1812.01528). [MỘT PHẦN]
- **Cơ chế:**
  - Tạo pseudo ground truth = max hoặc mean của các detector.
  - Với mỗi điểm test, lấy vùng lân cận kNN trong không gian đặc trưng.
  - Chọn detector có Pearson correlation cao nhất với pseudo ground truth trong vùng đó. Biến thể LSCP_MOA và LSCP_AOM.
- **Protocol:** 20 dataset ODDS/DAMI; 60% train / 40% đánh giá; **30 trial độc lập**; ROC-AUC và mAP; **Friedman + Nemenyi** (p < 0,05). Base pool gồm 50 LOF.
- **Code:** https://github.com/yzhao062/LSCP
- **Liên quan: Thấp – Trung bình.** Cần không gian đặc trưng để định nghĩa vùng lân cận. Với 2 expert vô hướng, nó suy biến thành một công tắc theo từng unit, không ổn định.

### 3.7 Ma, Zhao, Zhang, Akoglu (PR, SIGKDD Explor. 25(1), 2023; arXiv 2104.01422). [TOÀN VĂN]
- **Mục tiêu:** đánh giá 7 họ tiêu chí *nội tại* (không dùng nhãn) để chọn mô hình outlier: IREOS, EM/MV, UDR, MC, clustering validation, HITS, ensemble.
- **Protocol:** 39 dataset (21 ODDS, 18 DAMI); 297 mô hình (8 detector × nhiều hyperparameter); metric chính là **AP**; kiểm định **one-sided paired Wilcoxon signed-rank** qua các dataset.
- **Kết quả (tác giả báo cáo):** các tiêu chí đứng riêng "không khác biệt có ý nghĩa so với chọn ngẫu nhiên"; các tiêu chí dựa trên consensus không hơn iForest với hyperparameter mặc định.
- **Liên quan: Cao (ràng buộc).**
  - Không được chọn trọng số hay luật fusion bằng tiêu chí không nhãn trên đích; phải **đăng ký trước** luật.
  - Ngoài ra, paper này dùng AP làm metric chính. Đây là tiền lệ trong cộng đồng outlier detection cho lựa chọn metric của chúng ta.

### 3.8 Ren, Liu, Fertig, Snoek, Poplin, DePristo, Dillon, Lakshminarayanan, *Likelihood Ratios for OOD Detection* (PR, NeurIPS 2019; arXiv 1906.02845). [TOÀN VĂN] (đã kiểm theo yêu cầu "verify!")
- **Mục tiêu:** khắc phục việc likelihood của generative model bị chi phối bởi "background statistics" (ví dụ tỉ lệ GC trong genome, nền ảnh).
- **Công thức:**
  - LLR(x) = log p_θ(x) − log p_θ0(x) ≈ log p_θ(x_S) − log p_θ0(x_S).
  - Với mô hình autoregressive, LLR được phân rã theo từng vị trí.
  - **p_θ0 là background model**: cùng kiến trúc, nhưng train trên **input bị nhiễu** (mutation rate μ) và tùy chọn thêm L2 (λ).
  - μ (và λ) được tune trên một tập **OOD validation riêng**, rời với tập OOD test; hoặc tune trên OOD mô phỏng.
- **Dữ liệu:** benchmark genomics mới (vi khuẩn; chia in/OOD theo năm phát hiện 2011/2016; đoạn 250 bp); Fashion-MNIST vs MNIST; CIFAR-10 vs SVHN.
- **Metric:** AUROC↑, AUPRC↑, FPR80↓. Mean (SE) qua **10 lần chạy độc lập**; ensemble dùng 10 bootstrap trên 30 lần chạy.
- **Kết quả (tác giả báo cáo):**

  | Thiết lập | Likelihood (AUROC) | LLR (AUROC) |
  |---|---|---|
  | Genomics (μ, λ) | 0,626 | 0,755 |
  | Fashion-MNIST vs MNIST | 0,091 | 0,996 |
  | CIFAR-10 vs SVHN | 0,095 | 0,931 |

  Với genomics, LLR có AUPRC 0,719 và FPR80 0,474.
- **Nhận xét áp dụng cho K2:**
  - Điểm r_e(x) = NLL_adapter(x) − NLL_base(x) của chúng ta **cùng dạng** LLR, nhưng **không giống hệt**.
  - Background model của Ren được train *riêng* để chỉ học thống kê nền. Frozen base Llama của chúng ta là mô hình ngôn ngữ chung, vốn cũng mã hóa phần lớn "ngữ nghĩa" của log.
  - Vì vậy hiệu ứng có thể yếu hơn, hoặc ngược chiều. Đây là lý do review trước yêu cầu báo cáo base đơn lẻ.
  - Một background "đúng nghĩa Ren" sẽ là adapter train trên log đã nhiễu. Cái đó cần train, nên chỉ để làm hướng mở rộng.
  - Lưu ý: Ren tune μ **dùng OOD validation có nhãn**. Chúng ta không có, nên K2 phải **không có hyperparameter**.
- **Code:** chưa kiểm repo.
- **Liên quan: Cao.**

### 3.9 Serrà, Álvarez, Gómez, Slizovskaia, Núñez, Luque (PR, ICLR 2020; arXiv 1909.11480). [MỘT PHẦN]
- **Công thức:**
  - S(x) = −ℓ_M(x) − L(x), trong đó L(x) là độ phức tạp ước lượng bằng số bit/chiều của một **lossless compressor** (PNG, JPEG2000, FLIF).
  - Viết dưới dạng likelihood ratio: S(x) = −log₂ p(x|M) + log₂ p(x|M₀), với M₀ là "universal model".
- **Đánh giá:** AUROC (theo thông lệ OOD). AUROC của likelihood thuần có thể < 0,1, và đảo ngược lại sau khi hiệu chỉnh bằng S.
- **Liên quan: Cao (cho K2).**
  - Biện minh cho việc hiệu chỉnh độ phức tạp đầu vào. Với log, M₀ có thể là base Llama hoặc thậm chí gzip/zstd. Đây là một **baseline 0 chi phí GPU** nên thêm vào B0.
  - Tác giả gợi ý dùng compressor khác cho text, nhưng với log thì chưa được kiểm chứng.

### 3.10 COPOD: Li, Zhao, Botta, Ionescu, Hu (PR, ICDM 2020; arXiv 2009.09463) và ECOD: Li, Zhao, Hu, Botta, Ionescu, Chen (PR, IEEE TKDE 2022; arXiv 2201.00382). [MỘT PHẦN]
- **Cơ chế:**
  - Ước lượng ECDF theo từng chiều, rồi tính tail probability trái và phải.
  - COPOD dựng **empirical copula** nhưng khi tính điểm thì lấy xấp xỉ tích các marginal, tức copula độc lập: −log Ĉ(u) = −Σ_j log P(Ũ_j ≤ u_j). Có thêm hiệu chỉnh skewness để chọn đuôi.
  - ECOD tương tự: tổng −log tail probability theo từng chiều.
- **Protocol:** 30 dataset; 60/40; **10 trial độc lập**; **ROC-AUC và AP**. ECOD dùng thêm Wilcoxon signed-rank có Holm correction.
- **Kết quả (tác giả báo cáo):** COPOD xếp hạng nhất trong 10 detector, ROC-AUC hơn 1,5% và AP hơn 2,7% so với detector đứng thứ hai.
- **Nhận xét:**
  - Đây là tiền lệ có bình duyệt cho việc "ECDF tail per dimension → gộp trong log space" trên dữ liệu không nhãn. Về bản chất, đó là Fisher-type với giả định độc lập.
  - K3 của chúng ta (Gaussian copula ước lượng tương quan ρ trên buffer, một phía) là bước tổng quát hóa: bỏ giả định độc lập, đúng điểm mà Bates/Vovk–Wang cảnh báo.
  - Với chỉ 2 "chiều", COPOD/ECOD có thể chạy trực tiếp làm **baseline fusion** (có sẵn trong PyOD: https://github.com/yzhao062/pyod).
- **Liên quan: Trung bình.**

### 3.11 ADBench: Han, Hu, Huang, Jiang, Zhao (PR, NeurIPS 2022 D&B; arXiv 2206.09426). [MỘT PHẦN]
- **Protocol:**
  - 57 dataset; 70% train / 30% test, stratified; **lặp 3 lần**.
  - Hyperparameter **mặc định** của bài gốc, không tune, để công bằng.
  - Metric: **AUCROC và AUCPR**.
  - Kiểm định: **critical difference diagram dựa trên Wilcoxon–Holm**, p ≤ 0,05.
- **Kết quả liên quan:** khi có anomaly bị lặp lại (duplicated anomalies), median ΔAUCROC của các phương pháp unsupervised là −16,43%. Điều này giống hiện tượng burst trong BGL và rủi ro buffer bị nhiễm.
- **Liên quan: Trung bình (về protocol).**

---

## 4. Nhóm (c): Deep fusion và LoRA composition (chỉ để biện minh cho việc loại)

| Công trình | Venue (đã xác minh trong phiên này) | Vì sao loại cho bài toán này |
|---|---|---|
| TFN (Zadeh et al.) | EMNLP 2017, ACL Anthology D17-1115 | Tích ngoài của các vector modality và train có giám sát. Ta chỉ có 2 điểm vô hướng và khoảng 26 mẫu dương |
| LMF (Liu et al.) | ACL 2018, P18-1209 | Như TFN, dạng low-rank. Vẫn cần nhãn |
| MulT (Tsai et al.) | ACL 2019, P19-1656 | Cross-modal attention trên chuỗi. Cần huấn luyện giám sát |
| MBT, *Attention Bottlenecks for Multimodal Fusion* | NeurIPS 2021 (arXiv 2107.00135, comments) | Bottleneck token trong Transformer. Phải train lại backbone |
| AdapterFusion (Pfeiffer et al.) | EACL 2021, 2021.eacl-main.39 | Attention học được trên các adapter. Cần loss chung + nhãn task |
| TIES-Merging | NeurIPS 2023 (arXiv 2306.01708) | Gộp trọng số. Hai adapter có prompt khác nhau và scale khác nhau (α/r = 2 so với rsLoRA α/√r = 8) |
| DARE (*Language Models are Super Mario*) | ICML 2024 (arXiv 2311.03099) | Như TIES. Gộp trọng số làm mất sự đa dạng mà fusion cần |
| LoraHub | COLM 2024 (arXiv 2307.13269) | Tìm trọng số tổ hợp LoRA dựa trên vài ví dụ có nhãn của task đích |
| MoLE, X-LoRA, Arrow, LoRA Soups, GMU, survey Baltrušaitis (TPAMI 2019) | Theo review trước; **không mở lại trong phiên này** | Gate/router học được, cần nhãn |
| **AnoFusion** (Zhao, Ma, et al.) | KDD 2023 (PR; arXiv 2305.18985). [MỘT PHẦN] | Xem bên dưới |
| Hades (Lee et al.), *semi-supervised cross-modal attention* | arXiv 2302.06914; venue ICSE 2023 theo review trước, lần này không xác minh lại | Cần một ít nhãn + pseudo-label; fusion log + metric. Tác giả báo cáo F1 trung bình 0,933 |

**AnoFusion (chi tiết vừa đủ dùng cho EVAL_PROTOCOL_EVIDENCE):**
- **Cơ chế:** unsupervised. Graph Transformer Network học tương quan giữa metric, log và trace; tiếp theo là GAT + GRU. Ngưỡng được đặt bằng **EVT** (Extreme Value Theory), không dùng nhãn.
- **Protocol:** chia theo thời gian, **60% đầu** của từng instance để train. Hai hệ microservice (10 và 28 instance).
- **Kết quả (tác giả báo cáo):** F1 0,857 / 0,922.
- **Ablation:** bỏ GTN, bỏ GAT, …
- **Điểm đáng chú ý:** baseline **JLT** là late fusion bằng **majority voting** của JumpStarter + LogAnomaly + TraceAnomaly. Nó kém vì precision thấp: các detector cùng bắt nhầm, nên ghép lại vẫn giữ FAR cao.
  - Nhận xét: đây là bằng chứng rằng **late fusion kiểu vote không có hiệu chỉnh** có thể *làm tăng* FAR. Ngược lại, luật p-value đã hiệu chỉnh (K1) kiểm soát FAR có chủ đích.
- **Code:** https://github.com/zcyyc/AnoFusion

**Kết luận nhóm (c):** mọi phương án deep fusion hoặc LoRA composition đều cần (i) đầu vào là vector hoặc chuỗi và (ii) một objective có nhãn hoặc một task loss chung. Cả hai điều kiện đều không có ở đây. Ngoài ra, với khoảng 26 mẫu dương ở source, ngân sách chỉ đủ cho khoảng 2 tham số học từ nhãn (EPV ≥ 10, xem review trước).

---

## 5. Tổng hợp: tài liệu ủng hộ gì cho F-A/K1, K2, K3, và còn trống ở đâu

**Bằng chứng ủng hộ (tác giả báo cáo, nhận xét của tôi trong ngoặc):**
1. **Hiệu chỉnh theo buffer bình thường rồi gộp p-value bằng hàm hợp lệ:**
   - Bates 2023 cho tính hợp lệ của từng p-value và việc kiểm soát FDR bằng BH.
   - Vovk–Wang 2020 cho tính hợp lệ dưới mọi dạng phụ thuộc.
   - Gupta 2025 cho thấy **trên cùng một LLM**, ensemble p-value hơn thành viên tốt nhất +0,02 đến +0,08 AUROC.
   - COPOD/ECOD cho thấy gộp ECDF-tail trong log space mạnh trên 30 benchmark.
2. **Hiệu chỉnh likelihood bằng mô hình tham chiếu:** Ren 2019 và Serrà 2020 cho thấy likelihood thuần có thể **đảo ngược** (AUROC < 0,1), và LLR sửa được hiện tượng này.
   - (Đây là giả thuyết cơ chế hợp lý cho hiện tượng "NLL giảm thì AUROC giảm" của Sequence V13R1, nhưng chưa được kiểm chứng.)
3. **Không chọn luật bằng tiêu chí không nhãn:** Ma 2023 cho thấy các tiêu chí nội tại xấp xỉ chọn ngẫu nhiên.
4. **Hai góc nhìn semantic và sequence bổ sung nhau:** LogAnomaly 2019 (ablation) và LogLLM; FusionLog cho thấy router theo độ tương đồng tách được nhóm dễ (F1 khoảng 93%) và nhóm khó (khoảng 54%).
   - (Cả ba đều trong điều kiện có nhãn hoặc dùng protocol đích cân bằng lớp. Chúng ủng hộ *giả thuyết* bổ sung, không phải *mức lợi ích*.)

**Thận trọng và phản chứng:**
- Landauer 2024: nhiều bất thường trong HDFS/BGL bắt được bằng event mới và độ dài. Fusion phải thắng **B0** chứ không chỉ thắng từng expert.
- ADBench: duplicated anomalies làm hỏng phương pháp unsupervised. Buffer đích bị nhiễm (BGL) có thể làm p-value của các bất thường lặp lại rất lớn, và fusion **không** sửa được lỗi này.
- AnoFusion/JLT: late fusion bằng vote làm tăng FAR khi các thành viên cùng sai.
- Gupta: FAR guarantee bị vi phạm khi calibration data không đại diện, tương ứng với drift và nhiễm trong buffer của chúng ta.

**Khoảng trống (có thể là đóng góp, cần diễn đạt khiêm tốn):** trong những gì tôi đã đọc, **chưa có** công trình log AD nào làm cả ba điều sau:
- (i) gộp hai detector likelihood trên **cùng một LLM đóng băng có hai adapter**;
- (ii) bằng p-value hiệu chỉnh trên **buffer đích không nhãn**;
- (iii) đánh giá bằng AP có CI theo cụm.

Các bài zero-label cross-system gần nhất (ZeroLog, FreeLog, GeneralLog, FusionLog) đều dùng mô hình đơn hoặc router cứng, chỉ báo cáo F1, và dùng tập đích cân bằng lớp. Đây **không phải** rà soát hệ thống, nên chỉ được viết "theo hiểu biết của chúng tôi".

---

## 6. Những gì chưa kiểm được

- **Chỉ đọc abstract:** MetaLog (ICSE 2024), LogMoE (ASE 2025).
- **Chỉ có thông tin thư mục:** DeLong 1988 (Biometrics 44(3):837–845, DOI 10.2307/2531595), Obuchowski 1997 (Biometrics 53:567–578), Künsch 1989 (Ann. Statist. 17(3):1217–1241). Ba bài này được dùng trong file EVAL_PROTOCOL_EVIDENCE.
- **Venue chưa xác minh:**
  - LogGPT (arXiv không có journal-ref; tìm kiếm không xác nhận được).
  - RAGLog (có dòng "© 2023 IEEE" nhưng không rõ hội nghị).
  - GeneralLog (ICSE 2026 NIER, chỉ thấy trong kết quả tìm kiếm).
  - FusionLog (header khuôn mẫu IEEE TSC, chưa xác nhận được chấp nhận).
  - Hades (ICSE 2023, theo review trước).
- **Bảng số liệu không trích được đáng tin cậy** (pdftotext làm vỡ bảng): LogGPT Bảng II; FreeLog / ZeroLog / GeneralLog / FusionLog Bảng 1–2. Tôi chỉ dùng các con số xuất hiện trong văn xuôi hoặc abstract.
- **Mâu thuẫn chưa giải quyết:** LogAnomaly tự mô tả là chia theo thời gian (front 80% theo timestamp), trong khi Le & Zhang 2022 nói LogAnomaly dùng chia ngẫu nhiên.
- Venue của MoLE, X-LoRA, Arrow, LoRA Soups, GMU và survey Baltrušaitis **không** được mở lại trong phiên này.
- Aggarwal & Sathe 2015 (*Theoretical foundations and algorithms for outlier ensembles*): vẫn chưa đọc được.
