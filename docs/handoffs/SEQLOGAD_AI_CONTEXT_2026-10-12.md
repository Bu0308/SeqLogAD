# SeqLogAD — bản bàn giao context cho AI tiếp theo

**Ngày chốt:** 2026-10-12 (Asia/Ho_Chi_Minh)  
**Workspace hiện tại:** `/Users/apple/study/DACNTT`  
**Trạng thái:** V13R1 đã được đóng gói và kiểm tra cục bộ; chưa chạy huấn luyện GPU thật. Bản ghi này là hướng dẫn tiếp tục công việc, không phải bằng chứng mô hình đã train hay đạt benchmark.

## 1. Chỉ dẫn ngắn cho AI nhận bàn giao

Đọc tài liệu này trước, sau đó đối chiếu repo và Projmem hiện hành. Không mặc định máy/AI mới có quyền truy cập các đường dẫn tuyệt đối, GitHub, RunPod hoặc DB riêng. Không xóa hoặc ghi đè phiên bản, run, lỗi hay dữ liệu lịch sử. Người dùng yêu cầu mọi thay đổi mô hình, lần train/test và lỗi quan trọng phải được ghi bằng `pmem run`/Projmem vào collection hiện có. Chưa được train trên máy hiện tại, push GitHub, mở nhãn target, hay tuyên bố kết quả tốt hơn bài báo nếu chưa có ủy quyền/kết quả tương ứng.

Người dùng muốn chuẩn bị bộ chạy để bạn của họ train trên RunPod. Việc tiếp theo là người chạy upload bộ `V13R1-READY`, train một lần trên A40, trả về FULL archive cùng checksum và toàn bộ persistence `.pmem`; sau đó kiểm tra bằng chứng. Fusion Semantic + Sequence chưa chạy được vì còn lỗi tương thích checkpoint Semantic và thiếu adapter BGL. Cần giải quyết các trở ngại này trước khi báo cáo fusion.

## 2. Mục tiêu nghiên cứu và protocol

SeqLogAD nghiên cứu phát hiện bất thường log khi **kiến trúc/hệ thống target là unseen**. Ý tưởng dài hạn gồm expert Semantic, expert Sequence, expert cấu trúc/đồ thị (GTAT) và fusion có xét drift/độ bất định. Mục tiêu là đánh giá tổng quát hóa cross-system, không phải random row split.

Quy tắc khoa học đã thống nhất:

- Trong train, chọn checkpoint, hiệu chỉnh hoặc chọn fusion cho target, không dùng nhãn target. Nhãn target chỉ được mở sau khi đóng băng mô hình, cấu hình, score/fusion và protocol đánh giá cuối.
- Nhãn công khai của **source** được phép dùng trong tập development riêng để chọn checkpoint; metric đó phải gọi là source-development, không phải target benchmark.
- BGL đánh giá theo line; HDFS theo block. Không được tráo đơn vị đánh giá hay so metric từ split/protocol khác nhau như thể tương đương.
- Muốn báo cáo F1/accuracy/precision/recall/AUROC/AP phải có nhãn hợp lệ và split/đơn vị xác định. Thiếu tập nhãn development được phép thì không bịa/chép metric của bài báo vào làm metric của mô hình mình.
- So với bài báo chỉ công bằng khi dataset, nhãn, split, đơn vị, preprocessing, metric và protocol khớp. NLL của hai objective khác nhau không so trực tiếp được.

## 3. Trạng thái repo và artifact tại thời điểm bàn giao

- Git repo: `https://github.com/Bu0308/SeqLogAD.git`
- Nhánh local: `codex/sequence-v13r1`; HEAD: `b1172d0` (`Prepare Sequence V13R1 and RunPod collection workflow`).
- Working tree **dirty** với 16 mục theo `git status` tại phiên bàn giao; có các file bị đánh dấu deleted và nhiều file untracked. Vì vậy HEAD không đại diện toàn bộ artifact mới nhất. Không kết luận rằng nhánh này đã push lên GitHub; assistant chưa push.
- Bản RunPod khuyến nghị:
  `/Users/apple/study/DACNTT/outputs/runpod/P2.2-S42-A40-V13R1-READY.zip`
- SHA-256 của ZIP: `a17a0949bd7743a263267460d35ff9182fccc9b601420f6edb923b465076c14c` (đối chiếu file `.sha256`).
- Thư mục READY: `/Users/apple/study/DACNTT/outputs/runpod/P2.2-S42-A40-V13R1-READY/`
- Notebook chạy: `P2.2_run_all_sequence_lora_s42_v13r1_collect.ipynb`; hướng dẫn tiếng Việt: `HUONG_DAN_RUNPOD_V13R1_VI.md`; manifest upload: `RUNPOD_UPLOAD_MANIFEST.json`.

READY gồm notebook collect, hướng dẫn, manifest, hai collector Python, wheel Projmem 0.4.0a1 và ba ZIP code/data/source-development. Tải đúng bộ chín file theo manifest/hướng dẫn; đừng chỉ tải notebook. ZIP source-development chứa source labels được cho phép theo protocol và phải được giữ restricted. Không chia sẻ FULL archive công khai vì có thể chứa logs/dữ liệu restricted.

Một ZIP handoff khác có checksum là `P2.2-S42-A40-V13R1-handoff-collect-20261005.zip`; bộ READY trên là khuyến nghị hiện tại. Nếu có khác biệt giữa các bản, kiểm tra checksum/manifest trước khi dùng.

## 4. Sequence Expert V13R1 thực tế

- Variant/alias: `LORA-SEQ-003-R1-v1.3.1`; seed 42.
- Base: frozen `meta-llama/Llama-3.1-8B` **BASE** (không phải Instruct), revision `d04e592bb4f6aa9cfee91e2e20afa771667e1d4b`; quyền truy cập gated HF cần secret `HF_TOKEN`.
- 4-bit NF4 QLoRA, double quantization, BF16 compute; chỉ train adapter `sequence`, rsLoRA rank 16, alpha 32, dropout 0.05 trên q/k/v/o. Semantic adapter không nạp vào Sequence.
- Causal next-log prediction: teacher forcing, token-average NLL cho log kế tiếp. Context tối đa 512 token; tối đa 8 predecessor tương thích cùng architecture/partition/group. Không nối ngữ cảnh qua biên kiến trúc/partition/group. Khi train dùng suffix context nhiều độ dài 1/2/4/full (full với xác suất 0.5); validation/inference dùng toàn bộ ngữ cảnh khả dụng.
- Train theo thứ tự BGL → HDFS → HADOOP; mỗi fold giữ ngoài một target architecture. Hyperparameters chính: LR `1e-4`, warmup 100, microbatch 1, grad accumulation 16, tối đa 1536 optimizer steps, eval/checkpoint mỗi 100, patience 3, grad norm 1, weight decay 0.
- Checkpoint selection/early stopping dùng **source-development macro F1**. NLL cùng accuracy, precision, recall, F1, AUROC và average precision được ghi cho source development. Không diễn giải chúng là metric target.
- Source labels được chọn: BGL 16 positive/496 negative; HDFS 10 positive/501 negative. Ít mẫu dương khiến macro-F1 selection nhiễu/không ổn định. Hadoop không đưa vào nguồn chọn F1 vì chỉ có 5 app trong candidate pool.
- HDFS block metric được tổng hợp từ các cửa sổ được lấy mẫu; không đại diện mọi log của block. Một ablation với thứ tự/ngữ cảnh log thực tế vẫn cần thiết để xác định lợi ích riêng của Sequence.
- GPU đích: RunPod A40 48GB, yêu cầu tối thiểu khoảng 40 GiB VRAM; image `runpod/pytorch:1.0.3-cu1281-torch291-ubuntu2404`; Network Volume mount `/workspace`.

Phương pháp được tham khảo gồm causal next-event như DeepLog, multi-scale temporal context như hướng nghiên cứu TLAN, NF4/QLoRA, rsLoRA. Đây là động lực thiết kế; không chứng minh mô hình SeqLogAD vượt các paper. V13R1 không phải bản sao nguyên trạng của các kiến trúc đó.

## 5. Kiểm tra đã có và chưa có

Đã hoàn tất kiểm tra cục bộ, không GPU:

- Regression Sequence/Phase 2: 70 passed, 1 deselected; Projmem run `run_d4771570702d4af6a6ce0b72b9b7485a`. Deselected là test notebook Semantic cũ không có trong checkout.
- V13R1 package, ZIP/checksum, source-only sidecar, notebook cells và code identity được xác minh; có log trong Projmem, gồm `run_1ea8ff84c26f42e59719fd9a7bdefd02` và `run_474e48ec754c4964b6b093d9d760fb91`.
- Synthetic collector integration run `run_62ec6fceee1e4e20904d89f9c2942d6a` kiểm tra trước/sau train, thiếu run/recall, checksum hỏng, success/failure index, SQLite snapshot và archive hidden `.pmem`. Đây chỉ là mô phỏng integration, không phải train GPU.
- READY release run `run_06e111be25424750895828de7ed5cea8`.

Chưa có: GPU A40 execution, Sequence target metrics, scientific comparison với baseline, fusion result, G1–G4 acceptance hoặc Aletheia acceptance. `COLLECT_READY=YES` chỉ chứng nhận gói capture training đã qua các kiểm tra collector; không đồng nghĩa nghiên cứu/collection được nghiệm thu.

## 6. RunPod và thu thập kết quả

Đọc trọn hướng dẫn `HUONG_DAN_RUNPOD_V13R1_VI.md`. Tóm tắt:

1. Mở đúng Pod A40, image/Network Volume như trên; truyền `HF_TOKEN` qua secret, không ghi token vào notebook/log.
2. Upload đủ chín file của thư mục READY vào `/workspace/uploads`, xác minh checksum.
3. Chạy notebook `_collect.ipynb` bằng Run All; giữ volume và logs nếu có lỗi/gián đoạn. Không bỏ qua identity/metrics guard.
4. Chỉ khi có `COLLECT_READY=YES`, tải `SeqLogAD_sequence-v13r1_FULL_<id>.tar.gz` **và** `.sha256` từ `/workspace/exports`. Gửi thêm GPU, native Projmem run IDs, log, tình trạng resume/gián đoạn. Nếu lỗi thì giữ và trả gói FAILED/INTERRUPTED, không xóa DB hay chạy lại mù quáng.
5. Đối chiếu checksum trước khi giải phóng Pod/volume. Gói FULL restricted.
6. DB RunPod là DB riêng. Import/merge vào collection Mac phải kiểm tra provenance/conflict; tuyệt đối không ghi đè DB collection gốc.

Collector trước train chụp config/input hashes; sau train kiểm tra native Projmem success, metrics từng fold, identity code/data/fold, checkpoint bytes/hash, fold ZIPs và tạo export + SQLite online snapshot + archive toàn bộ persistence `.pmem`/logs/configs/input/checkpoints có thể thu được. Trường hợp Pod bị hard-kill có thể còn journal/checkpoint mà thiếu row SQLite; lần setup sau có cơ chế đăng ký journal, vẫn phải audit.

## 7. Projmem bắt buộc và dữ liệu bền vững

Collection canonical hiện ở:
`/Users/apple/study/long-term job/seqlogad-projmem-collection/.pmem/pmem.db`

DB này đã được kiểm tra integrity trước đây; giữ nguyên lịch sử, bao gồm failures. Dùng wheel đã pin (máy host có thể có Projmem cũ hơn):

```bash
cd "/Users/apple/study/long-term job/seqlogad-projmem-collection"
env PYTHONPATH=/Users/apple/study/DACNTT/outputs/colab/projmem-0.4.0a1-py3-none-any.whl \
  python3 -m pmem run --name "<ten-run>" --seed 42 \
  --config "/duong/dan/config.json" --metrics "/duong/dan/metrics.json" \
  -- python3 "/duong/dan/script.py"
```

Xác nhận syntax bằng `python3 -m pmem run --help`/guide trước run thực tế. `pmem run` ghi argv, status, exit code, stdout/stderr, runtime và Git state; `--config`, `--metrics`, `--artifact` khai báo thêm dữ liệu. Projmem không tự hiểu leakage, đúng/sai khoa học hoặc nội dung dataset. Sau run, nối native run ID với manifest IDs, track artifact và log failure/deviation. Không sửa/xóa dòng JSONL append-only; correction bằng record mới.

## 8. Semantic P2.1 và vấn đề fusion

Semantic S42 source development có best validation NLL từng fold: HDFS `0.31493` ở step 600; Hadoop `0.29204` ở step 500; BGL `0.029459` ở step 800. Đây là reconstruction NLL trên source validation, không phải anomaly F1/AUROC/AP target và không thể trực tiếp so với Sequence next-log NLL hoặc paper có objective khác.

Fusion chưa sẵn sàng:

- `SemanticExpert.from_checkpoint` tính lại config hash sau khi `real_training_completed=True`, làm loader bác checkpoint HDFS/Hadoop hợp lệ.
- BGL adapter bytes thiếu trong ZIP semantic cuối; checkpoint lịch sử FP16 cũng không khớp BF16 guard của loader A40.
- Semantic source views và Sequence source views đã align theo architecture/rank/normalized message, nhưng đó chỉ chứng minh alignment dữ liệu, không phải lợi ích fusion.
- Không cộng trực tiếp hai NLL khác nghĩa/thang đo. Hướng khởi đầu sau khi sửa bridge là empirical target-normal percentiles và late fusion equal-weight; so với từng single expert trên source-held-out. Chỉ nghiên cứu learned gate nếu có bằng chứng bổ trợ/robustness. Không dùng target labels để chọn.

Bước tiếp theo sau khi nhận training: (a) audit archive/DB/checkpoint/metrics của A40; (b) giải quyết Semantic loader bằng bridge phiên bản riêng, tìm/khôi phục BGL adapter; (c) tạo score view tương thích và kiểm tra source-fold complementarity; (d) so từng expert, equal-weight và ablations; (e) đóng băng protocol rồi mới xin/mở target final evaluation. Không sửa source code trong V13R1 mà vẫn giữ cùng code identity; thay đổi fusion bridge phải version/hash riêng và ghi Projmem.

## 9. Lịch sử xóa, Git và sở thích người dùng

Người dùng từng cho phép xóa các bộ upload cũ rồi sau đó đổi ý “đừng xóa gì hết”. Trước khi đổi ý, chín mục cũ đã được chuyển vào macOS Trash và hash/path được ghi trong Projmem; **không có xóa thêm sau khi người dùng rút yêu cầu**. Không nói rằng các mục cũ đã được restore. Giữ lại mọi phiên bản hiện có, cả lỗi và cải tiến.

Người dùng hỏi hướng dẫn push GitHub và quyền clone, nhưng assistant chưa push. Repo có commit local nêu trên; working tree bẩn. Trước khi push phải rà soát file D/untracked, nhạy cảm/dataset/model và chỉ stage danh sách tường minh; không `git add .`. Push chỉ sau khi user yêu cầu rõ.

Phong cách làm việc: trả lời tiếng Việt, đi thẳng vào kết luận; người dùng muốn artifacts hoàn chỉnh, reproducible, không chắp vá, giữ dữ liệu để collect; cập nhật Projmem cho mọi thay đổi/run/lỗi quan trọng. Không tự ý xóa/commit/push/train hay mở nhãn target.

## 10. Tài liệu gốc cần đọc tiếp

- Hướng dẫn vận hành RunPod: `outputs/runpod/P2.2-S42-A40-V13R1-READY/HUONG_DAN_RUNPOD_V13R1_VI.md`
- Kiểm toán Sequence V13R1: `docs/reports/SEQUENCE-V13R1-INDEPENDENT-AUDIT-2026-10-04.md`
- Rà soát phương pháp/bài báo: `docs/reports/SEQUENCE-EXPERT-METHOD-REVIEW-2026-09-26.md`
- Đánh giá Phase 2: `docs/reports/PHASE-2-ASSESSMENT-2026-09-23.md`
- Handoff/fusion findings và Next step: `_agent_ops/CURRENT_TASK.md`
- Protocol thu thập: `/Users/apple/study/long-term job/seqlogad-projmem-collection/COLLECTION_GUIDE.md` và `SOURCE_DATA_COLLECTION_GUIDE.md`
- Repo instructions: `AGENTS.md`; continuity: `_agent_ops/SESSION_BRIEF.md`, `_agent_ops/OPERATING_RULES.md`, `_agent_ops/PROJECT_CONTEXT_CARD.md`.

### Hash tham chiếu payload trong READY

- Code ZIP: `ad0f313b1b2e482f75eb2f5d10800fe59c451a2d1adc0c9e85aa0f1b0d01efb3`
- Sequence data ZIP: `4ed76b92e4b001138b28b4b3d3017d6ff7f30dd31e8cca0649bfdf34ede781`
- Source-development ZIP: `c765eb88a4feebc8ceb157110e5a6bd28dec942a7fb9343d7f6b969b3e79b295`
- Projmem wheel: `637964eed3af38c6170c5571bbc02338268cf31bddb15eaf3cc6d883c6b3ce4f`
- READY full ZIP: `a17a0949bd7743a263267460d35ff9182fccc9b601420f6edb923b465076c14c`

---

**Tóm tắt trạng thái cuối:** gói train đã chuẩn bị và kiểm tra cục bộ; chưa có GPU training hay kết quả target. Đầu tiên nhận archive + checksum + `.pmem` của lần RunPod thật, rồi audit; sau đó mới làm fusion bridge Semantic/Sequence.
