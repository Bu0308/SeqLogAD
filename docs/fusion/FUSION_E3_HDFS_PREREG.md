# FUSION-E3-HDFS — Đăng ký trước (khóa 2026-10-23, trước khi có điểm nào)

## Vấn đề
Ở E1 và E2C, mỗi block HDFS chỉ được chấm khoảng 1 dòng lấy ngẫu nhiên. Nếu bất thường nằm ở dòng khác thì không thể phát hiện. Trên cohort độc lập E2C, mọi phương pháp cho kết quả gần ngẫu nhiên.

## Dữ liệu
- 3.000 block HDFS mới thuộc đoạn SOURCE_VALIDATION (MID), không trùng E1 và E2C (đã loại 4.046 block). Selection tag `FUSION-E3-HDFS-BLOCKS`, Projmem `run_adde1287c4f441b889248408f1e37fa8`.
- Chấm **mọi dòng** có ít nhất 1 dòng đứng trước, tối đa 32 dòng mỗi block: 44.752 cửa sổ.
- **65 block bất thường (2,2%).** Chỉ dùng nhãn source.

## Mô hình (đóng băng)
- Sequence V13R1 best của fold Hadoop-target.
- Semantic P2.1 best của fold Hadoop-target, 1 mask (seed 42); làm 8 mask quá tốn.
- B0: −log tần suất template.

## Tổng hợp theo block
- **max** (chính)
- top-3 mean, mean
- single: 1 dòng chọn theo hash, giả lập cách làm cũ

## Giả thuyết (bootstrap cụm 64 block, 2.000 lần, seed 42)

**Họ chính H5–H6** (Holm, α = 0,05 một phía):
- **H5a:** AUROC(Seq-max) > 0,5
- **H5b:** AP(Seq-max) > tỉ lệ bất thường
- **H6:** AP(Seq-max) > AP(Seq-single)

**Đứng riêng:**
- **H7:** Cauchy(Seq-max, B0-max) không kém max(Seq-max, B0-max), với cận dưới CI 95% > −0,02.

**Khám phá:** top-3 mean, mean, Semantic, VW, gộp 3 thành phần.

## Fail-closed
Parity của Sequence fold Hadoop trên cohort chọn checkpoint gốc: |ΔAUROC| và |ΔAP| ≤ 0,01.

## Hash đóng băng
```
8a7594d888e3b1b8af1dbdc9802586c68c6ae6d8df2b15502d89ffab1edfc48b  src/seqlogad/fusion/block_eval.py
3e3cdfc5af6a87755b2310ea76d6189631c82d306f337b4a043dda59e10cd3cc  src/seqlogad/fusion/evaluate.py
1757007dcec1e0386d82deac3f2b745ad92cdf06129b0581b6f5d5c3afe709a8  src/seqlogad/fusion/run_confirm.py
b5dd257d675b7a0152dc06c0f96190aad191af5d032c6e1e9eb5b2f83db73018  src/seqlogad/fusion/rules.py
8dca67b1802d8ccedf27d0164cbbdc849cd2625694446032403e55cc176b75ad  src/seqlogad/fusion/metrics.py
6bac9b6c59954c44f71f3bfd30f2ef65ff49cd73c4f37f540f9f6eda6d7ae9da  src/seqlogad/fusion/units.py
a9d166c5a513bd59a2e6355fac731c54ec4f5ef9a873388c8d0d874348857144  scripts/build_block_cohort.py
f5b3cf9e2ed926b2832e613e2d7ffcc490569df495cfa914a1efccfe937eff38  00_inputs_blocks/source_dev_blocks/manifest.json
ca6d40e32c7fe24affd52f875cac752919096eb8c28b591433591e5d459c0363  00_inputs_blocks/phase2_sequence_blocks/manifests/bundle.json
```
