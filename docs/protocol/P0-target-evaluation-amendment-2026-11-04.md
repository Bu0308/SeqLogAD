# P0 — Bản sửa đổi đánh giá hệ đích E6 (TARGET-EVAL-AMEND-001)

**Trạng thái (2026-11-04):** bản nháp, **chưa ký, chưa có hiệu lực**. Chưa đọc nhãn đích, chưa chấm điểm đích, seal TEST vẫn `open_count = 0`.
Nội dung ràng buộc nằm ở [`configs/protocols/target-evaluation-amendment-v1.yaml`](../../configs/protocols/target-evaluation-amendment-v1.yaml) (băm ở file `.sha256` cùng thư mục). File này giải thích lý do và bằng chứng.

## 1. Bạn đang ký điều gì

| | Quyết định | Hệ quả phải chấp nhận |
|---|---|---|
| TV-D1 | E6 chỉ đánh giá trên LATE, bỏ MID | Mất 15% dữ liệu. Chỉ gỡ được việc dùng lại unit, không gỡ được việc cấu hình đã được chọn trên chính BGL/HDFS. |
| TV-D2 | Bỏ Hadoop khỏi fold đích, báo cáo là đích bị từ chối (độ phủ 2/3) | Kết luận chỉ áp dụng cho hệ qua được kiểm tra sẵn sàng. Thu hẹp phạm vi 3 đích của P1.1. |
| C′ | Giai đoạn 1 đọc nhãn LATE trước mốc cắt; giai đoạn 2 mở TEST bằng công cụ, luôn thực hiện | TEST bị dùng hết, kể cả khi giai đoạn 1 xấu. Sau đó không còn dữ liệu niêm phong nào. |
| Protocol v2 | Giai đoạn 2 là lượt khóa duy nhất cho hệ luật cố định, không cần đạt G4 | Không tuyên bố fusion thích nghi. G1–G4 vẫn `NOT_PASSED`. |

## 2. Quy trình C′

1. Chạy lại phép kiểm danh tính TEST; dừng nếu lệch.
2. Chấm mọi unit của cả hai giai đoạn trong một lượt, băm điểm trước khi đọc bất kỳ nhãn nào.
3. **Giai đoạn 1 (nội bộ):** BGL 949.592 dòng; HDFS 117.703 block. Trình đọc nhãn chỉ nhận danh sách unit cho phép, vì nhãn BGL nằm ngay trong dòng raw.
4. Sửa lỗi code đã ghi log, nếu có. Lỗi nghĩa là lệch khỏi đặc tả đã đăng ký, chứng minh được bằng test tái lập. Đổi model, luật fusion, baseline, unit, calibration, ngưỡng hay metric **không** phải là sửa lỗi.
5. **Giai đoạn 2 (xác nhận):** bạn tự chạy `seqlogad-final-test-access unlock` cho từng dataset. BGL 4.747 parent (474.700 dòng); HDFS 68.243 block (1.105.256 dòng).

Ngoài hai giai đoạn: 97 dòng dư của BGL, và 2.661 block HDFS vắt qua mốc cắt (chỉ mô tả, sau giai đoạn 2). Không gộp p-value của hai giai đoạn.

## 3. Lý do chọn C′

- **A và C′ đều hợp lệ về thống kê** khi cấu hình đóng băng: đọc một lần không thêm sai lệch chọn lọc ([Mania et al.](https://arxiv.org/abs/1905.12580) về bậc của sai lệch khi dùng lại holdout). Khác biệt chính là khả năng phục hồi: đây là lần đầu chấm trên hệ đích, và dự án từng có lỗi thật (E3/E4 chỉ chấm 32 dòng đầu). Với C′, một lỗi phát hiện ở giai đoạn 1 vẫn còn TEST sạch.
- **Vì sao mở TEST vô điều kiện:** chỉ mở khi giai đoạn 1 đẹp là dừng tùy chọn, làm mất giá trị xác nhận.
- **Cái giá:** khoảng tin cậy trên TEST rộng hơn khoảng 1,73 lần so với cả LATE (ước tính, giả định đợt bất thường phân bố đều). TEST cũng có thể ít đợt bất thường, và chỉ biết sau khi mở nhãn.
- **Hai reviewer bất đồng:** C1 xếp A gia cố đầu tiên vì một ranh giới, một đại lượng ước lượng; C2 xếp C sửa đổi đầu tiên vì sống sót qua lỗi scorer. Researcher chọn C′ ngày 2026-11-04.
- **Phương án B bị loại:** seal sẽ ghi chưa mở trong khi nhãn đã bị đọc.

## 4. Các bài báo làm gì

Đọc 21 bài theo từ khóa ở phần thiết lập thí nghiệm, không đọc trọn từng bài; "không có" nghĩa là không tìm thấy.

- **Test niêm phong hoặc hai giai đoạn trên hệ đích:** 0/21. C′ chặt hơn mọi bài đã mở nên không có tiền lệ trực tiếp. Tìm kiếm bổ sung có giới hạn cũng không thấy.
- **Validation riêng rõ ràng:** 4/21 (PLELog, LogBERT, LogTAD, Ali et al.).
- **Số hệ đích trong bài cross-system:** 5/6 báo cáo 2 đích (ZeroLog, FreeLog, GeneralLog, LogTAD, CroSysLog); LogAction báo cáo 3.
- **Hadoop làm đích:** 0/21; ngoài nhóm đó, LogTransfer (2020) dùng HDFS→Hadoop và có fine-tune bằng nhãn đích. MetaLog chưa mở được toàn văn.
- **Khuyến nghị về phương pháp:** [Arp et al.](https://arxiv.org/abs/2010.09470) §2.2 (tách test tới lượt cuối); [DomainBed](https://arxiv.org/abs/2007.01434) §3 (chọn trên miền test là oracle, phải khai); [Landauer et al.](https://arxiv.org/abs/2309.02854) (khuyên không dùng Hadoop để đánh giá).

Quy trình: 5 vai do các agent riêng thực hiện (R1, R2, C1, C2, V1). Cùng một model nền nên vẫn có thể cùng sai.

## 5. Bằng chứng đã kiểm

- **Danh tính TEST:** tính lại `test_partition_hash` từ luật công khai khớp cả HDFS và BGL; bỏ một block thì lệch. Script và output: [`docs/fusion/evidence/P0-20261104/`](../fusion/evidence/P0-20261104/). Script không mở `sealed/*`, `partitions/*`, `exclusions` hay file nhãn; phần HDFS đọc `HDFS.log` (không chứa nhãn), phần BGL không đọc raw.
- **Rò rỉ:** C2 báo rank lớn nhất ở giai đoạn 1, tính cả ngữ cảnh, là BGL 4.273.165 và HDFS 10.058.030, đều trước mốc cắt.
- **Thời điểm ký Hadoop:** P1.6 ký 2026-09-06; không có điểm unit Hadoop nào được tính.

## 6. Khai báo liêm chính (đưa vào prereg E6)

- Phép kiểm trên thực chất dựng lại membership TEST bằng luật công khai, ngoài quy trình `seqlogad-final-test-access`. Không in membership, không có nhãn. Chạy ba lần ngày 2026-11-04 (C2 một lần, lead hai lần).
- Thống kê không nhãn của vùng TEST đã bị xem: BGL khoảng 86% dòng mang template chưa thấy so với khoảng 66% ở giai đoạn 1; tuổi thọ block HDFS trung vị 507 s so với 2.171 s; tự tương quan novelty theo chunk (số do C2 báo).
- Tỉ lệ nhãn tổng hợp của Hadoop (44/55 application) đã nằm trong registry và đã được đọc, nên không được gọi việc bỏ Hadoop là "outcome-neutral".
- Sự cố 2026-10-28 (in 400 byte `sealed/TEST.jsonl` của BGL) vẫn phải khai.

## 7. Chuyển sang prereg E6 (chữ ký này chưa chốt)

Đề xuất của C2, chưa kiểm chứng: cụm bootstrap BGL theo ngày và HDFS theo 10 phút; chỉ xác nhận khi có ít nhất 100 unit dương và 10 cụm dương, nếu không ghi `NOT_ESTIMABLE`; HDFS giai đoạn 1 dùng mẫu `in_sample` hiện có (12.496 block, phân tầng lại) còn giai đoạn 2 chấm toàn bộ. Ước tính khoảng 6,6 giờ A40 ở 29 window/s (chưa xác minh).

Cũng phải giải quyết trong prereg: thêm Sequence so với B0 vào giả thuyết chính, và khai các ablation bắt buộc của protocol v2 không thực hiện được (chưa có expert structural-time).

## 8. Việc phát sinh sau giai đoạn 2

`tests/test_active_state_contract.py` đang khẳng định `never_opened` và `open_count == 0`, nên sẽ fail sau khi mở TEST. Cần cập nhật có chủ đích khi đến bước đó; không sửa trước.
