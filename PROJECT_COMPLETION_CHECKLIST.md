# Project Completion Checklist (AI Office Assistant)

Tài liệu này tổng hợp những việc cần làm thêm để dự án có thể **chạy ổn định** và tiến tới **production-ready**.

## 1) Mức tối thiểu để chạy được (MVP kỹ thuật)

- [x] Bổ sung SQLAlchemy models để các route `auth/chat/tasks/documents` hoạt động.
- [x] Bổ sung `__init__.py` cho `app.schemas` và export trong `app` để tránh lỗi import.
- [x] Bổ sung `Dockerfile` cho `server` và `ai-engine` để `docker-compose.yml` build thành công.
- [ ] Tạo thư mục `storage/documents`, `storage/reports` trên server thật (hoặc mount volume tương ứng).
- [ ] Chạy migration/init DB tự động theo môi trường (dev/prod tách biệt).
- [ ] Xác nhận health-check end-to-end:
  1. `POST /api/v1/auth/register`
  2. `POST /api/v1/auth/login/access-token`
  3. `POST /api/v1/chat/send`

## 2) Những điểm đang là scaffold/mock, cần hoàn thiện

- [ ] `server/app/routes/chat.py` hiện trả về phản hồi giả lập, chưa gọi AI Engine thực tế.
- [ ] `office/generate-macro` mới là logic mẫu, cần prompt + guardrail theo từng app Word/Excel/PPT.
- [ ] Upload document mới lưu file + metadata, chưa trigger indexing thật vào vector store.
- [ ] Chưa có cơ chế queue/background worker (Celery/RQ/FastAPI background task nâng cao).

## 3) Bảo mật trước khi đưa vào nội bộ doanh nghiệp

- [ ] Thay `SECRET_KEY` mặc định bằng secret mạnh từ biến môi trường.
- [ ] Siết `CORS` theo domain nội bộ thay vì `*`.
- [ ] Mã hóa HTTPS cho backend/public endpoints (qua reverse proxy).
- [ ] Bật logging/audit cho đăng nhập, gọi AI, upload tài liệu.
- [ ] Giới hạn loại file upload + quét file độc hại.
- [ ] Phân quyền theo vai trò rõ hơn (`admin/manager/user`) ở tất cả endpoint.

## 4) Vận hành & độ ổn định

- [ ] Thêm `.env.example` đầy đủ cho server và ai-engine.
- [ ] Bổ sung healthcheck trong `docker-compose.yml`.
- [ ] Tạo script backup/restore PostgreSQL + retention policy.
- [ ] Thêm observability: metrics (Prometheus), logs tập trung, alerting.
- [ ] Thiết lập timeout/retry/circuit-breaker khi server gọi AI Engine.

## 5) Chất lượng phần mềm

- [ ] Unit test cho service và route quan trọng (auth/chat/tasks/documents).
- [ ] Integration test cho luồng đăng nhập -> chat -> lưu hội thoại.
- [ ] Pre-commit: ruff/black/isort + CI pipeline.
- [ ] API contract docs + ví dụ request/response cho client team.

## 6) Lộ trình đề xuất

1. **Sprint 1 (Run ổn định):** harden auth + DB + AI call thật + upload/index docs.
2. **Sprint 2 (An toàn nội bộ):** RBAC đầy đủ, HTTPS, audit log, backup/monitor.
3. **Sprint 3 (Nâng cấp nghiệp vụ):** macro generator theo ngữ cảnh Office, task automation sâu, báo cáo quản trị.

