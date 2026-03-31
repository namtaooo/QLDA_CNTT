# Kế hoạch Refactor Hệ thống (Architecture & Service Layer)

Qua rà soát dựa trên yêu cầu mới nhất (Refactor Architecture, Service Layer Separation, Duplicate Chunk Removal, Testing), dưới đây là kế hoạch điều chỉnh kiến trúc. Hầu hết các yêu cầu cốt lõi (Caching, Auth RBAC, Data Isolation, Sanitization, BackgroundTasks, Retries) đã được chúng ta triển khai trước đó, vì vậy đợt nâng cấp này sẽ **tập trung tối đa vào việc tách lớp (Decoupling) và dọn dẹp code**.

## User Review Required

> [!IMPORTANT]
> - Chúng ta sẽ di chuyển toàn bộ logic tương tác mạng (HTTP gọi AI) ra khỏi các Controller/API Router (`chat.py`, `documents.py`). 
> - Tạo một Service Model thuần túy: `server/app/services/ai_service.py` có nhiệm vụ làm "AI Client Layer" duy nhất của toàn hệ thống. Mọi API chỉ được phép gọi các hàm trong Service này.
> - Bổ sung lọc Chunk trùng lặp (Duplicate Chunk Removal) trực tiếp bằng Hash để tối ưu hóa context cho bộ Prompt RAG.

## Proposed Changes

### server/app/services/ai_service.py
- **[NEW]** Khởi tạo `AIEngineClient` class bao bọc `httpx.AsyncClient`.
- Đưa các hàm `chat()` và `index_document()` vào đây.
- Kế thừa thư viện `@retry` (tenacity) và áp dụng timeouts bên trong class này để che giấu độ phức tạp khỏi file Router.

### server/app/routes/chat.py
- **[MODIFY]** Xóa bỏ hàm `safe_call_ai_engine()`.
- **[MODIFY]** Thay vì gọi trực tiếp `httpx`, router giờ đây chỉ gọi `ai_service.chat(payload)`.

### server/app/routes/documents.py
- **[MODIFY]** Cập nhật `process_document_background()` để gọi `ai_service.index_document(content, metadata)` thay vì code block `httpx` rườm rà.

### ai-engine/embeddings.py
- **[MODIFY]** Cập nhật thuật toán RAG: Duyệt tập kết quả `filtered`, sử dụng tập hợp (Set) lưu trữ nội dung hash tóm tắt (hoặc full content) để **loại bỏ Duplicate Chunks** trước khi tính điểm Re-ranking, tránh việc gửi LLM nhiều đoạn text trùng lặp y hệt nhau.

### server/tests/test_ai_service.py
- **[NEW]** Khởi tạo một unit test sử dụng `pytest` và `respx` (hoặc magic mock) để test tính năng Retry/Timeout của `AIEngineClient` đảm bảo hệ thống phản hồi duyên dáng (Graceful degradation) khi AI Server sập.

## Lộ trình tích hợp (Integration Guide)
1. Cơ cấu lại folder `server/app/services/` với file `ai_service.py`.
2. Gắn kết service vào `chat.py` và `documents.py`.
3. Cập nhật `embeddings.py` loại bỏ duplicate.
4. Chạy `pytest` test_ai_service.py để nghiệm thu.

## Open Questions

> [!WARNING]
> Kiến trúc Controller - Service - AI Client Layer sẽ thay đổi cấu trúc import đáng kể trong BackgroundTasks. Việc tái cấu trúc này sẽ giúp hệ thống dễ dàng migrate sang kiến trúc Celery Task Queue sau này nếu hệ thống phát triển phình to.
> 
> Bạn có đồng ý với lộ trình cấu trúc lại mã nguồn theo Layered Architecture này không?
