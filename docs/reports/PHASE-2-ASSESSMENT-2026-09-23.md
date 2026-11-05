# Đánh giá Phase 2 — Semantic Expert

**Ngày rà soát:** 23/09/2026  
**Phạm vi:** kế hoạch sáu phase hiện hành; Phase 2 gồm P2.PRE và P2.1. Sequence thuộc Phase 3.  
**Kết luận:** Phase 2 **đã hoàn thành ở mức xây dựng và chạy Semantic Expert seed 42** theo mốc của kế hoạch. Chưa có bằng chứng để kết luận Semantic phát hiện bất thường tốt, vượt baseline bài báo, hoặc đạt kết quả khoa học cuối cùng.

## 1. Việc đã hoàn thành

| Hạng mục | Kết quả được ghi nhận | Đánh giá |
| --- | --- | --- |
| P2.PRE — cố định nền tảng | Đóng băng `meta-llama/Llama-3.1-8B` và tokenizer tại revision `d04e592bb4f6aa9cfee91e2e20afa771667e1d4b`; quy định base bất biến, adapter LoRA riêng, QLoRA và môi trường thực thi. | **PASS về metadata/protocol**; bản thân P2.PRE không phải một lượt huấn luyện GPU. |
| P2.1 — phương pháp Semantic | Cài đặt mục tiêu tái dựng từng `normalized_message`: che từ trong một thông điệp rồi tính NLL trên token của thông điệp gốc. Đầu vào không chứa chuỗi sự kiện liền trước. | Có Semantic Expert độc lập và điểm reconstruction NLL thô để dùng trong các bước đánh giá/fusion sau. |
| Dữ liệu và đóng gói | Chuẩn bị, kiểm tra ba fold có hệ đích HDFS, BGL, Hadoop; OpenStack chỉ làm miền nguồn. Báo cáo chuẩn bị ghi nhận kiểm tra fold và gói dữ liệu/mã; gói final code/data có kiểm tra giải nén. | Có đầu vào tái lập cho huấn luyện nguồn, nhưng các kiểm tra gói không thay thế kiểm định khoa học. |
| Thực thi seed 42 | Notebook RunPod được cung cấp ghi `COMPLETED` cho HDFS và Hadoop trên NVIDIA A40/BF16, `REGISTERED_EXTERNALLY` cho BGL. Metrics HDFS/Hadoop khớp notebook. Bản phục hồi của run **BGL final riêng** ghi best NLL `0,029459` tại step 800, chạy trên Tesla T4/FP16; ID và digest checkpoint khớp phiếu đăng ký BGL trong ZIP cuối. | **Đạt mốc Phase 2 của kế hoạch sáu phase**. BGL không được chạy lại trong notebook này; metrics BGL đến từ gói phục hồi cũ, không phải output trực tiếp của notebook. |
| Lưu kết quả | Notebook báo ZIP cuối `seqlogad_outputs_P2.1_S42_FINAL.zip`, kích thước 301.371.038 byte, SHA-256 `d04b5dd4c218934dcd8d17853f02282329c89bb5d5f433f72e7a941f45a0bf0e` và `SAFE_TO_STOP_RUNTIME=YES`. | Ngày 23/09/2026, đã băm lại bản ZIP lưu tại `outputs/runpod/P2.1-S42-A40-upload/`: SHA-256 khớp, kiểm tra CRC toàn ZIP đạt. ZIP này chỉ chứa **phiếu đăng ký BGL**, không nhúng artifact huấn luyện BGL. |

## 2. Kết quả huấn luyện đọc được

NLL dưới đây là **reconstruction NLL trên tập validation của các miền nguồn**, dùng để chọn checkpoint. Hệ ghi ở cột đầu là *hệ đích được giữ ngoài lúc huấn luyện*, không phải tập đã được đánh giá phát hiện bất thường.

| Fold giữ ngoài | Miền nguồn trong validation | NLL đầu tiên (step 100) | NLL tốt nhất / checkpoint | Thay đổi so với step 100 | Dừng sớm |
| --- | --- | ---: | ---: | ---: | --- |
| HDFS | BGL, Hadoop, OpenStack | 0,43769 | **0,31493 / step 600** | Giảm 28,0% | Step 900 |
| Hadoop | BGL, HDFS, OpenStack | 0,45715 | **0,29204 / step 500** | Giảm 36,1% | Step 800 |
| BGL | HDFS, Hadoop, OpenStack | 0,09708 | **0,02946 / step 800** | Giảm 69,7% | Step 1100 |

Ba đường validation đi xuống so với lần đo đầu và quy tắc dừng sớm đã hoạt động. Riêng BGL final, log ghi NLL `0,029459` tại checkpoint được chọn (step 800); giá trị ở step 1100 khi dừng là `0,029993`, không phải điểm tốt nhất. Đây là dấu hiệu quá trình tối ưu tác vụ tái dựng đã học được trên nguồn. **Không được diễn giải các tỷ lệ giảm là mức cải thiện so với mô hình chưa fine-tune, baseline khác, hoặc điểm phát hiện anomaly.** Các fold có tập nguồn khác nhau; BGL còn chạy trên loại GPU/precision khác HDFS/Hadoop. Không dùng NLL tổng hợp để xếp hạng năng lực trên từng hệ đích.

Tại checkpoint được chọn, NLL theo miền nguồn chênh lệch đáng kể: fold HDFS có BGL `0,87685`, Hadoop `0,05957`, OpenStack `0,00788`; fold Hadoop có BGL `0,83685`, HDFS `0,02972`, OpenStack `0,00954`; fold BGL có Hadoop `0,05641`, HDFS `0,02505`, OpenStack `0,00697`. Vì vậy số NLL tổng hợp che khuất việc tái dựng log BGL khó hơn nhiều khi BGL là *nguồn* trong hai fold khác. Fold giữ BGL ngoài lúc train chưa cho biết tỷ lệ phát hiện bất thường của BGL.

## 3. Đánh giá mức độ đạt mục tiêu

| Câu hỏi | Kết luận hiện tại |
| --- | --- |
| Đã có một Semantic Expert được huấn luyện và lưu artifact chưa? | **Có, ở mốc phát triển seed 42** theo notebook và hồ sơ phục hồi; HDFS/Hadoop có trace trực tiếp, BGL có log/metrics riêng trong gói phục hồi cũ và được đăng ký bằng digest trong ZIP cuối. Artifact nhị phân BGL không nằm trong ZIP cuối hoặc bản handoff cũ đã đọc. |
| NLL này có tốt không? | **Tốt theo nghĩa hẹp:** source-validation NLL giảm trong cả ba lượt chạy đã đọc, checkpoint được chọn có căn cứ. Chưa có ngưỡng hay đối chứng để gọi nó là NLL “tốt” theo nghĩa chất lượng phát hiện bất thường. |
| Có tốt hơn bài báo/baseline không? | **Chưa xác định.** Các bài báo thường báo AP/PR-AUC, F1, AUROC, FAR trên nhãn anomaly. NLL tái dựng trên nguồn là đại lượng khác. Ngay cả hai NLL cũng chỉ so sánh công bằng khi cùng dữ liệu, tokenizer, objective, masking, cách tính loss và split. Chưa có baseline được chạy theo cùng protocol trong hồ sơ Phase 2 này. |
| Đã hoàn thành đánh giá khoa học chưa? | **Chưa.** Notebook tự ghi `run_mode=development`, `scientific_result=NOT_EVALUATED`, `multi_seed_stability=NOT_CLAIMED`. Mới có seed 42; protocol final có thêm seed 3407 và 8675309. G1–G4 chưa qua. |
| Nguồn dữ liệu có chắc chắn toàn log bình thường không? | **Không.** Protocol ghi nguồn không nhãn, có thể lẫn bất thường; `SOURCE_LABEL_STATUS=UNRESOLVED_DENY`. NLL thấp không chứng minh mô hình phân biệt log bất thường, và tác vụ tái dựng có thể học mẫu phổ biến hoặc lối tắt sao chép. |

**Giá trị thực của Phase 2:** tạo một tín hiệu *ngữ nghĩa ở mức từng log message* và một adapter/checkpoint độc lập, có thể đem vào thí nghiệm so sánh single expert và fusion về sau. NLL là chỉ số huấn luyện/chọn checkpoint và ứng viên anomaly score; nó chưa phải kết luận benchmark. Semantic không mã hóa thứ tự giữa các sự kiện, nên Sequence Expert ở Phase 3 vẫn có vai trò khoa học rõ ràng.

## 4. Việc còn thiếu và hướng tiếp theo

1. **Tiếp tục P3.1 Sequence Reference** theo kế hoạch hiện hành, dùng adapter riêng và tác vụ dự đoán log kế tiếp từ ngữ cảnh cùng session. Trước lượt GPU mới, đối chiếu lại quy tắc cắt ngữ cảnh trong tài liệu Sequence với code: tài liệu yêu cầu bỏ các predecessor cũ trước rồi mới rút tiền tố target; hồ sơ bàn giao hiện ghi nhận code làm thứ tự ngược lại.
2. **Khi đến gate đánh giá thích hợp**, chạy Semantic và các baseline trên cùng fold, quyền truy cập nhãn, đơn vị phát hiện, split và metric; báo AP/PR-AUC, F1/FAR và độ phủ, cùng độ dao động nhiều seed. Không dùng NLL nguồn để thay bảng benchmark anomaly. Việc dùng nhãn phải theo quyết định C2/gate hiện hành.
3. **Giữ ranh giới provenance:** nếu công bố kết quả seed 42, lấy artifact nhị phân BGL từ kho lịch sử và kiểm tra theo digest đã đăng ký; bản ZIP cuối hiện chỉ có phiếu đăng ký BGL. BGL final `0,02946` tại step 800 khác với *BGL pilot* `0,05086` tại step 300; hai lượt có ngân sách/protocol khác nhau nên không xem chênh lệch đó là một phép so sánh chất lượng công bằng.

**Quyết định đánh giá:** ghi “Phase 2 hoàn thành: Semantic Expert seed 42 được xây dựng và chạy”; ghi riêng “hiệu quả anomaly/cross-system chưa được đánh giá”. Chưa có lý do từ các số NLL hiện tại để huấn luyện lại Semantic ngay hoặc bỏ Sequence Expert.

## 5. Nguồn kiểm tra và giới hạn rà soát

- [Kế hoạch sáu phase](../migration/SIX-PHASE-2026-09-20.md), [trạng thái dự án](../../configs/active-state.yaml), [đóng băng base](../protocol/P2.PRE-base-model-freeze.md), [hợp đồng Semantic](../protocol/P2.1-semantic-expert.md).
- [Notebook RunPod do người nghiên cứu cung cấp](../../outputs/runpod/P2.1_run_all_semantic_s42.ipynb), SHA-256 của chính notebook: `5f9b8d0273df24c3b7b532256f2078075c41943051a8f46f27d67e764a0dc6f2`. Đã đọc output lưu trong notebook; **không chạy lại GPU**.
- [ZIP kết quả cuối lưu tại RunPod upload](../../outputs/runpod/P2.1-S42-A40-upload/seqlogad_outputs_P2.1_S42_FINAL.zip) được băm lại và kiểm tra CRC ngày 23/09/2026. Phiếu BGL trong ZIP ghi run ID `P2.1-FINAL-BGL-S42`, checkpoint `step-800`, digest adapter `63b17c16bb7ed1ee4e4b6f0696d8f02bee05e41b37125e92f0793b032857e0eb`.
- [Báo cáo chuẩn bị Semantic](P2.1-semantic-preparation.json), [kiểm tra gói final](P2.1-final-packages.json), [ma trận run đăng ký trước](P2.1-final-run-matrix.json), [BGL pilot](P2.1-bgl-pilot-closeout.json). Trạng thái `NOT_STARTED` trong ma trận là ảnh chụp trước thực thi, không phải trạng thái seed 42 hiện nay.
- Hai JSON metrics phục hồi ở `aletheia_minh_quan_case_20260921/06_RUN_EVIDENCE/run_metrics/` được dùng để đối chiếu best checkpoint HDFS/Hadoop. Chúng là bản phục hồi; hồ sơ gốc RunPod không được tái thực thi trong lần rà soát này.
- Metrics và log BGL final riêng nằm trong gói phục hồi trước khi rút gọn phạm vi: [metrics.json](</Users/apple/study/long-term job/SEQLOGAD_BAN_GIAO_20260920_R03/DU_LIEU_PRE_P5/06_RUN_EVIDENCE/runs/P2.1-FINAL-BGL-S42/metrics.json>) và [train.jsonl](</Users/apple/study/long-term job/SEQLOGAD_BAN_GIAO_20260920_R03/DU_LIEU_PRE_P5/06_RUN_EVIDENCE/runs/P2.1-FINAL-BGL-S42/logs/train.jsonl>). `metrics.json` khớp bản R02 theo SHA-256 `6bd471d25b71a698a03d719baadc428ba303b10b27a0bfab6069ad568d1ca769`; digest checkpoint trong manifest khớp phiếu BGL của ZIP cuối. Đây là bằng chứng phục hồi lịch sử, không phải một lượt train mới.
