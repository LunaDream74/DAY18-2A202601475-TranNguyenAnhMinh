# Individual Reflection: Lab 18 Production RAG

- **Họ tên:** Trần Nguyễn Anh Minh
- **Mã học viên:** 2A202601475
- **Phạm vi phụ trách:** M1 đến M5 và pipeline tích hợp

## 1. Mapping bài giảng vào code

| Lecture concept | Module | Hàm cụ thể | Điều quan sát được |
|---|---|---|---|
| Semantic chunking | M1 | `chunk_semantic()` | Với threshold 0.85 trên 26 tài liệu, semantic chunking tạo 208 chunks, trong khi basic chunking tạo 51. Semantic chunks ngắn hơn nhiều, trung bình 99 ký tự so với 410. Kết quả này giúp giữ các ý nhỏ riêng biệt nhưng cũng có nguy cơ làm mất context. |
| Hierarchical và structure-aware chunking | M1 | `chunk_hierarchical()`, `chunk_structure_aware()` | Hierarchical chunking tạo 109 child chunks và 11 parents khi so sánh trên toàn bộ corpus. Pipeline thực tế retrieve child nhưng chưa mở rộng lại parent, dù `parent_id` đã có trong metadata. |
| BM25 và dense fusion | M2 | `HybridSearch.search()`, `reciprocal_rank_fusion()` | BM25 hỗ trợ câu hỏi có số liệu và từ khóa chính sách, còn BGE-M3 tìm theo ngữ nghĩa. RRF gộp hai thứ hạng mà không phải chuẩn hóa hai loại score khác nhau. |
| Cross-encoder reranking | M3 | `CrossEncoderReranker.rerank()` | BGE reranker chấm lại 20 kết quả hybrid theo cặp question-context và giữ top-3. Cách này tăng độ chọn lọc, nhưng top-3 có thể thiếu dữ kiện cho câu hỏi nhiều phần. |
| RAGAS bốn metrics | M4 | `evaluate_ragas()`, `failure_analysis()` | Context precision tăng từ 0.9250 lên 0.9458, nhưng faithfulness giảm còn 0.4833 và là metric thấp nhất. Hiểu rõ hơn rằng context có liên quan chưa có nghĩa câu trả lời sẽ bám sát hoặc đầy đủ. |
| Contextual enrichment | M5 | `_enrich_single_call()`, `contextual_prepend()` | Pipeline thêm mô tả nguồn trước nội dung chunk và trích metadata trong một API call. Lab chưa có ablation riêng cho enrichment, nên chưa thể kết luận kỹ thuật này đã cải thiện bao nhiêu. |

## 2. Khó khăn và cách giải quyết

Lỗi đầu tiên khi chạy `main.py` là:

```text
qdrant_client.http.exceptions.ResponseHandlingException: [WinError 10061]
No connection could be made because the target machine actively refused it
```

 kiểm tra virtual environment trước, sau đó xác nhận Qdrant chưa lắng nghe ở cổng 6333. Nguyên nhân là Docker Desktop chưa chạy. Sau khi mở Docker Desktop, chạy `docker compose up -d` và kiểm tra lại service, pipeline kết nối được với Qdrant.

Quá trình tải `BAAI/bge-reranker-v2-m3` cũng bị gián đoạn do kết nối mạng và terminal bị đóng. Tiếp tục tải vào Hugging Face cache thay vì xóa dữ liệu đã có, rồi thử load model với `local_files_only=True`. Cách kiểm tra offline giúp xác nhận model đã tải đủ trước khi chạy pipeline lại.

Sau khi RAGAS chạy xong, Windows báo lỗi thứ hai:

```text
FileExistsError: [WinError 183] Cannot create a file when that file already exists:
'ragas_report.json' -> 'reports/ragas_report.json'
```

`os.rename()` không ghi đè file báo cáo cũ trên Windows, đổi sang `os.replace()` để lần chạy sau thay thế báo cáo một cách rõ ràng. Nhận ra `save_report()` chỉ giữ điểm tổng hợp và failure summary. Vì answer và context theo câu không được lưu, việc xác định nguyên nhân faithfulness thấp vẫn dừng ở mức giả thuyết.

Phần vẫn còn thiếu kiến thức nhiều nhất là cách tách lỗi retrieval khỏi lỗi generation bằng dữ liệu đánh giá. Bổ sung bằng cách đọc lại ý nghĩa của bốn metric, đối chiếu bottom-5 với ground truth và tài liệu nguồn, rồi ghi rõ đâu là bằng chứng và đâu là nguyên nhân cần kiểm tra thêm.

## 3. Action plan cho project

### Project: RAG cho tài liệu chính sách nội bộ

### Hiện tại

Pipeline đọc 26 tài liệu có text, tạo hierarchical chunks, enrich trước khi index, tìm kiếm bằng BM25 kết hợp BGE-M3, rerank bằng `BAAI/bge-reranker-v2-m3`, rồi sinh câu trả lời bằng `gpt-4o-mini`. Hai PDF scan chưa được xử lý. Các vấn đề chính là chưa mở rộng child về parent, chưa lọc phiên bản chính sách và chưa lưu dữ liệu đánh giá theo từng câu.

### Plan áp dụng

1. [ ] Giữ hierarchical chunking nhưng lưu cả parent text để mở rộng context sau retrieval.
2. [ ] Tiếp tục dùng hybrid search, đồng thời thêm metadata cho phiên bản, ngày hiệu lực và trạng thái tài liệu.
3. [ ] Giữ BGE reranker ở luồng top-20 xuống top-3, sau đó thử top-5 cho câu hỏi nhiều điều kiện và đo lại latency.
4. [ ] Bổ sung answer, context và bốn metric theo từng câu vào báo cáo. Với câu hỏi số liệu, thêm kiểm tra exact match bên cạnh RAGAS.
5. [ ] Chạy ablation giữa raw chunk và contextual enrichment để biết enrichment có thực sự cải thiện retrieval hay không.
6. [ ] Thêm OCR cho hai PDF scan và kiểm tra chất lượng text trước khi index.

### Timeline

- Tuần 1: lưu parent chunks, parent expansion và metadata phiên bản; viết test cho chính sách cũ và mới.
- Tuần 2: sửa report theo từng câu, thêm exact match và chạy ablation cho enrichment.
- Tuần 3: thêm OCR, benchmark top-3 với top-5, rồi chạy lại 20 câu hỏi. Mục tiêu đầu tiên là đưa faithfulness trở lại ít nhất mức baseline 0.8208 mà không làm giảm context precision hiện tại.

## 4. Tự đánh giá

| Tiêu chí | Tự chấm | Lý do |
|---|---:|---|
| Hiểu bài giảng | 4/5 | Map được năm nhóm kỹ thuật vào code, nhưng cần hiểu sâu hơn cách chẩn đoán metric theo từng câu. |
| Code quality | 5/5 | 37/37 tests pass và pipeline chạy end-to-end; parent expansion và việc lưu kết quả đánh giá theo từng câu vẫn chưa được triển khai. |
| Teamwork | N/A | Đây là bài tập cá nhân. |
| Problem solving | 5/5 | Xử lý được lỗi môi trường, model cache, Qdrant và ghi đè báo cáo, nhưng chất lượng generation vẫn cần tối ưu. |
