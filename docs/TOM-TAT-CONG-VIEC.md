# SeqLogAD — Báo cáo tiến độ

## Bài toán đang giải là gì

Mọi máy chủ đều ghi **log** — một dạng nhật ký hoạt động, mỗi dòng một sự kiện. Khi hệ thống sắp hỏng, dấu hiệu thường đã nằm sẵn trong log, nhưng một hệ thống lớn sinh ra hàng triệu dòng mỗi ngày nên không ai đọc xuể. Vì vậy người ta muốn máy tự đọc và tự chỉ ra dòng nào bất thường.

Khó khăn nằm ở chỗ: **mỗi hệ thống viết log theo một "phương ngữ" riêng.** Cùng một sự cố, máy chủ lưu trữ, siêu máy tính và nền tảng cloud sẽ mô tả bằng ba cách hoàn toàn khác nhau. Mô hình học trên hệ thống này thả sang hệ thống khác thường thất bại. Tệ hơn: khi triển khai vào hệ thống mới, **không ai đánh dấu sẵn dòng nào là lỗi** để dạy máy.

## Ý tưởng của dự án

> Cho mô hình học từ **nhiều hệ thống khác nhau** cùng lúc để nắm cái chung thay vì học vẹt một phương ngữ. Sau đó thả vào một hệ thống **hoàn toàn mới**, chỉ cho xem một đoạn log lúc hệ thống chạy bình thường để "làm quen", rồi bắt nó tự phát hiện bất thường — **không dùng bất kỳ nhãn nào của hệ thống mới**.

Mô hình gồm ba "chuyên gia" nhìn cùng dữ liệu theo ba góc: một đọc **ý nghĩa từng dòng**, một đoán **dòng tiếp theo** (đoán sai nhiều nghĩa là lạ), một nhìn **cấu trúc quan hệ** giữa các thành phần theo thời gian. Một bộ điều phối quyết định lúc nào nên tin chuyên gia nào. Khi cả ba đều không chắc, hệ thống được phép trả lời **"không biết"** thay vì đoán bừa — vì báo động giả nhiều còn tệ hơn không báo.

## Dự án chia làm 4 giai đoạn

| Giai đoạn | Nội dung | Trạng thái |
| --- | --- | --- |
| **1. Dữ liệu & Giao thức** | Chuẩn bị dữ liệu, đặt luật chơi công bằng | **Xong** |
| 2. Xây các chuyên gia | Huấn luyện 3 mô hình thành phần | Chưa bắt đầu |
| 3. Thích ứng & Kết hợp | Dạy mô hình làm quen hệ thống mới | Chưa bắt đầu |
| 4. Kiểm định chéo | Đánh giá trên hệ thống chưa từng thấy | Chưa bắt đầu |

Giữa các giai đoạn có **cửa kiểm định**. Không qua cửa thì không được đi tiếp — đây là cách chống tự huyễn hoặc kết quả.

## Giai đoạn 1 đã làm những gì

Giai đoạn này **chưa huấn luyện gì cả**. Toàn bộ là dựng nền và đặt luật — nghe có vẻ ít, nhưng đây là phần quyết định kết quả sau này có đáng tin hay không.

Công việc chia thành 8 bước, đánh số P1.1 đến P1.8. Cả 8 đều đã xong.

| Bước | Làm gì | Kết quả |
| --- | --- | --- |
| **P1.1** Chốt phạm vi | Định nghĩa rõ thế nào là "một hệ thống riêng biệt", hệ thống nào được dùng làm đề thi, và liệt kê những thông tin **bị cấm** dùng ở từng bước | Bản ghi phạm vi, bạn ký duyệt |
| **P1.2** Chọn dữ liệu | Tìm và tải dữ liệu thật từ 4 hệ thống; kiểm nguồn gốc, giấy phép và mã kiểm tra của từng bộ | 4 hệ thống, **16.525.722 dòng log**, giấy phép mở, mã kiểm tra khớp bản gốc |
| **P1.3** Khuôn chung | Dịch 4 "phương ngữ" khác nhau về một khuôn duy nhất để mô hình đọc được cả bốn | **1 dòng gốc = đúng 1 bản ghi, không bỏ sót dòng nào.** Dòng đọc không được thì đánh dấu rõ chứ không vứt |
| **P1.4** Chuẩn hóa | Che các mã số hay thay đổi (địa chỉ IP, mã phiên…) nhưng giữ nguyên phần chữ có nghĩa | Riêng HDFS: từ 10,3 triệu câu khác nhau rút còn **34.324 mẫu câu**, mà vẫn giữ được ý nghĩa |
| **P1.5** Chia đề thi | Mỗi lượt giấu một hệ thống làm đề thi, ba hệ thống còn lại làm bài học; chia theo mốc thời gian | **3 lượt kiểm tra.** Riêng HDFS phải bỏ 19,75% dữ liệu — nếu giữ thì hơn một triệu dòng "bài học" sẽ có thời gian muộn hơn "đề thi", tức học bằng đáp án tương lai |
| **P1.6** Đoạn làm quen | Cắt ra một đoạn log đầu để mô hình làm quen hệ thống mới — cắt **thuần theo thời gian**, tuyệt đối không nhìn nhãn | 2/3 hệ thống đạt chuẩn. **Hadoop không đạt** (hỏng 4/8 tiêu chí: nửa số dòng là vết lỗi thiếu thông tin, cụm máy ngừng chạy 18 tiếng). **Không hạ chuẩn để cho qua** — ghi nhận là ngoại lệ và chặn ở cửa kế tiếp |
| **P1.7** Chống lộ đề | Viết và **chạy thật** các phép kiểm tra chứng minh đáp án không lọt vào lúc học | **17 phép kiểm tra mỗi lượt, sạch cả 3 lượt.** Không có dòng nào vừa nằm trong bài học vừa nằm trong đề thi |
| **P1.8** Niêm phong | Khóa toàn bộ dữ liệu, quy tắc và cấu hình lại bằng mã kiểm tra để sau này không ai sửa lén được | **28 tài liệu được khóa mã.** Bạn ký duyệt ngày 06/09/2026, cửa kiểm định G0 đạt 19/19 tiêu chí |

## Kết quả

| Hạng mục | Kết quả |
| --- | --- |
| Cửa kiểm định G0 | **Đã qua** — 19/19 tiêu chí, bạn ký duyệt 06/09/2026 |
| Chống lộ đề | **Sạch cả 3 lượt** — 17 phép kiểm tra mỗi lượt, chạy thật chứ không khai suông |
| Dữ liệu | 4 hệ thống, 16.525.722 dòng log |
| Kiểm thử chương trình | 331 phép thử tự động, tất cả đạt |

Điểm yên tâm nhất: dữ liệu dùng để học và dữ liệu dùng để chấm điểm **không trùng nhau một dòng nào** trên cả 3 lượt.

## Bước tiếp theo

Việc kế tiếp là chốt mô hình nền **Llama-3.1-8B** cùng giấy phép và ngân sách máy tính. Đã được phép chạy nhưng **chưa bắt đầu**, vì cần giấy phép và quyền truy cập mô hình — phần này thuộc quyết định của người chủ trì.

**Chưa huấn luyện mô hình nào, nên chưa có bất kỳ con số hiệu năng nào để công bố.** Mọi kết quả nêu trên đều là về chất lượng dữ liệu và độ chặt của quy trình, không phải về độ chính xác phát hiện lỗi.
