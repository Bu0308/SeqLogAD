# FUSION-E2-CONFIRM — Đăng ký trước (khóa 2026-10-23, trước khi có điểm xác nhận nào)

## Mục đích
Kiểm lại trên **dữ liệu độc lập** các phát hiện khám phá của E1.1. Đây là bước xác nhận trên source-dev, chưa phải trên hệ đích.

## Dữ liệu
- Cohort mới: Projmem `run_f19da51ccb29487dbebf098ab66b00af`, selection tag `FUSION-E2-CONFIRM-seed2`.
- Cùng đoạn SOURCE_VALIDATION (MID), loại toàn bộ 2.048 cửa sổ/nguồn của E1/E1.1.
- BGL: 2.048 dòng, 89 bất thường.
- HDFS: 2.048 cửa sổ = 2.026 block, 20 bất thường.
- **Đăng ký trước:** loại 57 block HDFS đã có trong cohort E1 (2 block bất thường), còn khoảng 1.969 block và 18 bất thường. BGL không có unit nào trùng.
- Không đọc bản ghi hay nhãn nào của hệ đích.

## Mô hình (đóng băng, không train)
- Sequence V13R1 best theo từng fold.
- Semantic P2.1 best theo fold (HDFS, Hadoop), **trung bình NLL qua 8 seed mask (42–49)**, đúng như chốt ở D-17.
- B0 = −log tần suất template trên SOURCE_TRAIN của cùng nguồn.
- Calibration: p-value ECDF transductive (không dùng nhãn) theo từng nguồn.

## Giả thuyết

**Họ chính:** BGL, fold HDFS-target và fold Hadoop-target, tổng 4 phép kiểm. Hiệu chỉnh Holm, α = 0,05 một phía.
- **H1:** VW(Seq, B0) có gain AP so với max(Seq, B0) lớn hơn 0.
- **H2:** VW(Sem-mk8, Seq) có gain AP so với max(Sem-mk8, Seq) lớn hơn 0.

**Phụ** (báo cáo, không hiệu chỉnh):
- **H3:** AP(Sem-mk8) > AP(Sem seed 42).
- **H3b:** AP(Sem-mk8) > AP(B0).
- **H4** (HDFS, cả hai fold): Cauchy(Seq, B0) không kém Seq, tức cận dưới CI 95% của ΔAP > −0,02.

**Khám phá:** VW 3 thành phần (Sem-mk8, Seq, B0), so với max của ba thành phần.

## Thống kê
- Metric chính: AP.
- Báo cáo thêm AUROC, P/R/F1 ở ngân sách 1% và 5%.
- Paired cluster bootstrap theo khối 64 cửa sổ liên tiếp, 2.000 lần lấy mẫu, seed 42.
- p một phía = (#{gain ≤ 0} + 1)/(B + 1).

## Fail-closed
Chấm lại 256 cửa sổ E1 bằng Sequence (fold HDFS) và so với điểm E1R. Nếu |Δ| > 2e-3 thì dừng, không đánh giá.

## Hash đóng băng
```
47a08e99b6cb08b2e205d44ecca0e607f8c835a7d3c5027064f8965f8099fee5  src/seqlogad/fusion/confirm_eval.py
e64fbb6273109457679d91fc8f9cf5abcd242d868d8a171b6adea4718eb17e36  src/seqlogad/fusion/run_confirm.py
b5dd257d675b7a0152dc06c0f96190aad191af5d032c6e1e9eb5b2f83db73018  src/seqlogad/fusion/rules.py
700a8acd1099c1be2a6dfb2cdb88e8e493c503d3ff55aac11cccf564acc5eaf0  src/seqlogad/fusion/calibration.py
8dca67b1802d8ccedf27d0164cbbdc849cd2625694446032403e55cc176b75ad  src/seqlogad/fusion/metrics.py
69b8f7eacc77fb9eb1493c2f44a5049188f77e5aca407e930e84f0d2711dffe7  src/seqlogad/fusion/evaluate.py
6bac9b6c59954c44f71f3bfd30f2ef65ff49cd73c4f37f540f9f6eda6d7ae9da  src/seqlogad/fusion/units.py
a66567270ba9b65927bf19e77989e72ffeb7a2b838b6448dfa439abac75b59d9  src/seqlogad/fusion/baselines.py
d98e83a33f0aa02570ae3f4cd8cf8991c1d8d59990311c30251bc21de5c6e59c  src/seqlogad/fusion/run_multimask.py
d738b4b49c81cb254dfbeb7c4e0036f3dd8a2a3c0cef82d785bafcb13526979b  scripts/build_confirm_cohort.py
a7139225a01e3b21bd7150cd6fa7f0f861aa964fccc54cd51672fa391ef010d4  00_inputs_confirm/source_dev_confirm/manifest.json
c7fa6d894b7274f7742bb80900e94bac56d30b5248086ebbca32959bb87a5901  00_inputs_confirm/phase2_sequence_confirm/manifests/bundle.json
```

## Phụ lục sai lệch D-18 (ghi trước khi có điểm xác nhận)

Thời điểm: 2026-10-23 13:55 UTC.

- **Lý do:** pod `a3xfs2sf1zj0fu` không bật lại được vì máy chủ hết GPU. File điểm E1R dùng cho anchor nằm trên volume của pod đó.
- **Thay đổi:** anchor fail-closed chuyển sang parity gốc. Chấm lại 512 unit đã dùng chọn checkpoint của fold HDFS bằng Sequence best; |ΔAUROC| và |ΔAP| phải ≤ 0,01 so với số đã ghi lúc train.
- **Không đổi:** giả thuyết, dữ liệu, luật, thống kê và bộ đánh giá.
- Hash mới của `run_confirm.py` được ghi trong decision log.
