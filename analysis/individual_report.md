# Báo cáo cá nhân Lab 18: Production RAG

- **Họ tên:** Trần Nguyễn Anh Minh
- **Mã học viên:** 2A202601475
- **Ngày thực hiện:** 18/08/2026

## Phạm vi thực hiện

Triển khai đủ năm module của pipeline RAG và nối chúng thành luồng chạy hoàn chỉnh. Hệ thống đọc tài liệu tiếng Việt, chia nhỏ nội dung, làm giàu chunk, tìm kiếm bằng BM25 kết hợp dense retrieval, rerank kết quả, sinh câu trả lời và đánh giá bằng RAGAS.

| Module | Nội dung | Kết quả kiểm thử |
|---|---|---:|
| M1 | Semantic, hierarchical và structure-aware chunking | 13/13 |
| M2 | Vietnamese BM25, dense search trên Qdrant và RRF | 5/5 |
| M3 | Cross-encoder reranking | 5/5 |
| M4 | RAGAS evaluation và failure analysis | 4/4 |
| M5 | Summary, HyQA, contextual prepend và metadata | 10/10 |

Tổng cộng 37/37 test đã pass trong môi trường Python 3.11.9. Hai model `BAAI/bge-m3` và `BAAI/bge-reranker-v2-m3` đã được tải đầy đủ và kiểm tra ở chế độ offline.

## Cách pipeline hoạt động

Pipeline đọc được 26 tài liệu và bỏ qua 2 PDF scan không có text layer. M1 tạo 116 child chunks theo cấu trúc parent-child. M5 bổ sung context và metadata trước khi index. M2 dùng BM25 để bắt từ khóa, số liệu và tên chính sách; dense search dùng embedding 1024 chiều để tìm theo ngữ nghĩa. Reciprocal Rank Fusion gộp 2 danh sách kết quả. M3 sau đó dùng cross-encoder để chọn ra 3 context tốt nhất cho câu trả lời.

Khi có `OPENAI_API_KEY`, hệ thống gọi OpenAI để enrich chunk và sinh câu trả lời từ context. M4 chạy bốn metric RAGAS trên 20 câu hỏi trong test set và ghi kết quả vào `reports/ragas_report.json`.

## Kết quả RAGAS

| Metric | Naive baseline | Production | Chênh lệch |
|---|---:|---:|---:|
| Faithfulness | 0.8208 | 0.4833 | -0.3375 |
| Answer relevancy | 0.7074 | 0.5696 | -0.1378 |
| Context precision | 0.9250 | 0.9458 | +0.0208 |
| Context recall | 0.9250 | 0.8333 | -0.0917 |

Context precision là metric duy nhất tăng, cho thấy hybrid search và reranking lọc context khá chính xác, nhưng pipeline production không tạo câu trả lời tốt hơn baseline. Faithfulness giảm mạnh dù context precision đạt 0.9458. Vì vậy, vấn đề chính nằm sau bước retrieval: cách chọn ba context cuối cùng, cách đưa context đã enrich vào prompt, hoặc cách model diễn đạt câu trả lời.

Context recall giảm 0.0917 cũng đáng chú ý. Pipeline hiện index child chunk và giữ `parent_id`, nhưng chưa lấy lại toàn bộ parent text sau khi tìm thấy child. Với câu hỏi cần nhiều điều kiện hoặc nhiều nguồn, ba child chunks có thể đúng nhưng chưa đủ thông tin để trả lời trọn vẹn.

## Key Findings

1. **Biggest improvement:** Context precision tăng từ 0.9250 lên 0.9458, tương đương 0.0208. Đây là metric duy nhất tốt hơn baseline và cho thấy các context được giữ lại nhìn chung có liên quan đến câu hỏi.
2. **Biggest challenge:** Faithfulness giảm từ 0.8208 xuống 0.4833. Cả năm câu có điểm trung bình thấp nhất đều nhận faithfulness bằng 0, nên ưu tiên tiếp theo là kiểm tra answer và top-3 context của từng câu.
3. **Surprise finding:** Pipeline production phức tạp hơn và có context precision cao hơn nhưng vẫn thua baseline ở ba metric còn lại. Kết quả này cho thấy thêm hybrid search, reranking và enrichment không tự động làm câu trả lời tốt hơn nếu context cuối chưa đủ hoặc prompt chưa kiểm soát chặt thông tin được sinh ra.

## Các failure đáng chú ý

Năm câu có điểm trung bình thấp nhất đều có faithfulness bằng 0:

| Câu hỏi | Điểm trung bình |
|---|---:|
| Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt? | 0.2500 |
| Lương thử việc của nhân viên Junior mức cao nhất là bao nhiêu? | 0.3958 |
| Nếu cần mua laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT? | 0.4167 |
| Bao lâu phải đổi mật khẩu một lần? | 0.4583 |
| Mật khẩu phải có tối thiểu bao nhiêu ký tự? | 0.5000 |

Các failure tập trung vào số liệu, quy trình phê duyệt và chính sách có phiên bản cũ, mới. Chỉ số tổng hợp chưa đủ để kết luận chính xác lỗi phát sinh ở retrieval hay generation cho từng câu. Cần mở context và answer tương ứng trước khi sửa pipeline.

## Điều sẽ sửa tiếp

Ưu tiên đầu tiên là dùng `parent_id` đúng mục đích: retrieve child để có độ chính xác, sau đó trả parent cho LLM để tăng context recall. Tăng thêm metadata về phiên bản và trạng thái hiệu lực để tránh trộn chính sách cũ với chính sách hiện hành.

Prompt trả lời nên yêu cầu model trích đúng số liệu và nêu nguồn trước khi kết luận. Với câu hỏi nhiều phần, pipeline cần kiểm tra xem context có đủ dữ kiện cho từng phần hay chưa. Sau mỗi thay đổi, tôi sẽ chạy lại cùng test set và so sánh cả bốn metric, thay vì chỉ nhìn context precision.

2 PDF scan vẫn chưa tham gia retrieval. Muốn dùng các tài liệu này, bước load dữ liệu cần thêm OCR và kiểm tra chất lượng văn bản sau OCR.
