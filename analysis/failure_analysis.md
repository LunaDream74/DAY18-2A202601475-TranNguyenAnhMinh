# Phân tích lỗi cá nhân Lab 18: Production RAG

- **Họ tên:** Trần Nguyễn Anh Minh
- **Mã học viên:** 2A202601475
- **Ngày phân tích:** 18/08/2026

## Phạm vi và giới hạn dữ liệu

Phân tích này dùng `reports/ragas_report.json`, `reports/naive_baseline_report.json`, `test_set.json` và các tài liệu trong `data/`. Báo cáo production chỉ lưu điểm tổng hợp cùng danh sách lỗi. Câu trả lời do model sinh và các context của từng câu không được lưu, nên tôi không thể khẳng định model đã trả lời gì hoặc chunk nào đã được truy xuất. Các nguyên nhân dưới đây được tách thành phần đã xác nhận và giả thuyết cần kiểm tra.

## So sánh RAGAS

| Metric | Naive baseline | Production | Chênh lệch |
|---|---:|---:|---:|
| Faithfulness | 0.8208 | 0.4833 | -0.3375 |
| Answer relevancy | 0.7074 | 0.5696 | -0.1378 |
| Context precision | 0.9250 | 0.9458 | +0.0208 |
| Context recall | 0.9250 | 0.8333 | -0.0917 |

Production lọc context chính xác hơn một chút, nhưng faithfulness và answer relevancy giảm rõ rệt. Kết quả này cho thấy retrieval tốt chưa đủ. Cần kiểm tra context cuối cùng và câu trả lời trước khi quy lỗi riêng cho retrieval hoặc generation.

## Năm câu có điểm thấp nhất

### 1. Thiết bị trị giá 55 triệu

- Kỳ vọng: đơn hàng trên 50 triệu cần Tổng Giám đốc (CEO) phê duyệt.
- Kết quả ghi nhận: điểm trung bình 0.2500, faithfulness 0. Câu trả lời thực tế và context không có trong file báo cáo.
- Error tree: output không được RAGAS xác nhận là bám context; context đúng hay thiếu chưa xác định; pipeline không có bước rewrite nên query gốc được dùng trực tiếp.
- Giả thuyết: chunk chứa bảng thẩm quyền có thể không nằm trong ba kết quả cuối, hoặc câu trả lời đã thêm thông tin không có trong context.
- Cách kiểm tra và sửa: lưu answer cùng top-3 context, sau đó xác nhận chunk chứa ngưỡng `trên 50.000.000 VNĐ`. Nếu context đã đúng, siết prompt để model chỉ nêu người phê duyệt từ tài liệu.

### 2. Lương thử việc Junior cao nhất

- Kỳ vọng: `85% x 20.000.000 = 17.000.000 VNĐ/tháng`.
- Kết quả ghi nhận: điểm trung bình 0.3958, faithfulness 0; answer và context không được lưu.
- Error tree: chưa thể biết model sai ở mức lương trần, tỷ lệ thử việc hay phép tính.
- Giả thuyết: đây là câu hỏi cần ghép bảng lương Junior trong `bang_luong_2024.md` với tỷ lệ 85% trong chính sách thử việc. Top-3 có thể không giữ đủ hai dữ kiện.
- Cách kiểm tra và sửa: truy xuất theo từng ý, lấy cả chunk mức lương và chunk tỷ lệ thử việc, rồi yêu cầu model trình bày phép tính trước khi kết luận.

### 3. Mua laptop 30 triệu

- Kỳ vọng: Giám đốc phòng ban phê duyệt, phòng CNTT xác nhận cấu hình kỹ thuật, và hồ sơ có ít nhất ba báo giá.
- Kết quả ghi nhận: điểm trung bình 0.4167, faithfulness 0; answer và context không được lưu.
- Error tree: câu hỏi có ba điều kiện, nhưng chưa xác định context cuối có đủ cả ba phần hay không.
- Giả thuyết: các quy định nằm ở nhiều mục trong `mua_sam.md`. Reranker chọn ba child chunk độc lập có thể bỏ sót một mục dù tài liệu đúng đã được tìm thấy.
- Cách kiểm tra và sửa: sau khi retrieve child chunk, mở rộng sang parent hoặc các chunk lân cận cùng nguồn. Prompt cũng cần đối chiếu lần lượt giá trị đơn hàng, loại thiết bị và yêu cầu báo giá.

### 4. Chu kỳ đổi mật khẩu

- Kỳ vọng: chính sách v2.0 hiện hành yêu cầu đổi mỗi 120 ngày; quy định 90 ngày của v1.0 đã bị thay thế.
- Kết quả ghi nhận: điểm trung bình 0.4583, faithfulness 0; answer và context không được lưu.
- Error tree: chưa biết pipeline lấy v1.0, v2.0 hay cả hai.
- Giả thuyết: corpus giữ đồng thời phiên bản cũ và hiện hành. Reranking theo độ liên quan nội dung không bảo đảm ưu tiên trạng thái hiệu lực.
- Cách kiểm tra và sửa: trích metadata `version`, `effective_date` và `status`; lọc văn bản đã bị thay thế hoặc ưu tiên phiên bản mới nhất trước khi tạo câu trả lời.

### 5. Độ dài tối thiểu của mật khẩu

- Kỳ vọng: tối thiểu 12 ký tự theo v2.0; mức 8 ký tự của v1.0 không còn hiệu lực.
- Kết quả ghi nhận: điểm trung bình 0.5000, faithfulness 0; answer và context không được lưu.
- Error tree: giống câu 4, xung đột phiên bản là rủi ro rõ nhất trong nguồn, nhưng chưa phải nguyên nhân đã được chứng minh.
- Cách kiểm tra và sửa: áp dụng cùng bộ lọc phiên bản, đồng thời yêu cầu câu trả lời nêu phiên bản chính sách làm căn cứ.

## Case study ưu tiên

Chọn câu mua laptop 30 triệu vì nó kiểm tra nhiều phần của pipeline cùng lúc. Retrieval phải tìm đúng tài liệu; chunking phải giữ được bảng thẩm quyền, yêu cầu báo giá và lưu ý dành cho thiết bị CNTT; reranking phải giữ đủ các chunk; generation phải trả lời đủ ba ý mà không thêm quy định ngoài nguồn.

Nếu có thêm một giờ: sẽ sửa `save_report()` để lưu question, answer, ground truth, từng context và 4 điểm theo câu. Sau đó chạy lại riêng 5 câu trên, kiểm tra parent expansion cho câu laptop và salary, rồi thử metadata filtering cho hai câu mật khẩu. Đây là bước cần thiết để biến các giả thuyết thành nguyên nhân có bằng chứng.
