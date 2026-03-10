# 🤖 AI Office Assistant

Hệ thống trợ lý AI nội bộ dành cho doanh nghiệp, tích hợp vào Microsoft Office và Web Chat.

## ✅ Tính năng chính

- Hỏi đáp cách dùng Microsoft Word
- Hướng dẫn & tự động hoá trong Microsoft Excel
- Hỗ trợ làm slide trong Microsoft PowerPoint
- Phân tích dữ liệu & gợi ý quyết định
- Phân công công việc nội bộ
- Trợ lý chuyên môn (thay vì phải Google)
- Dùng nội bộ trong hệ thống eOffice

---

## � Kiến trúc Client - Server

```
  ┌─── MÁY CHỦ (Server) ──────────────────────────┐
  │                                                 │
  │  ┌─────────────────────────────────────────┐    │
  │  │     Backend API (FastAPI) - port 8000    │    │
  │  │  Auth │ Chat │ Tasks │ Office │ Docs     │    │
  │  └──────────────┬──────────────────────────┘    │
  │                 │                               │
  │         ┌───────┴────────┐                      │
  │         ▼                ▼                      │
  │  ┌─────────────┐  ┌─────────────┐              │
  │  │  PostgreSQL │  │  AI Engine  │              │
  │  │  (Database) │  │  (LLM+RAG) │              │
  │  │  port 5432  │  │  port 8001  │              │
  │  └─────────────┘  └──────┬──────┘              │
  │                          │                      │
  │                   ┌──────┴──────┐               │
  │                   ▼             ▼               │
  │             ┌──────────┐ ┌───────────┐          │
  │             │  Models  │ │   FAISS   │          │
  │             │(Qwen/...)│ │VectorStore│          │
  │             └──────────┘ └───────────┘          │
  └─────────────────────────────────────────────────┘
                        ▲
                        │  HTTP API (gọi qua mạng LAN/Internet)
                        │
  ┌─── MÁY NHÂN VIÊN (Client) ────────────────────┐
  │                                                 │
  │  ┌──────────────┐     ┌───────────────────┐     │
  │  │  Web Chat    │     │  Office Add-in    │     │
  │  │ (Trình duyệt)│     │ (Word/Excel/PPT)  │     │
  │  └──────────────┘     └───────────────────┘     │
  │                                                 │
  └─────────────────────────────────────────────────┘
```

---

## 🖥️ PHẦN 1: CHẠY SERVER (Trên máy chủ)

> Máy chủ chạy Backend API + AI Engine + Database.
> Chỉ cần 1 máy duy nhất, các máy nhân viên sẽ gọi API tới máy này.

### Bước 1: Cài PostgreSQL

Tải và cài đặt PostgreSQL: https://www.postgresql.org/download/

Tạo database:
```bash
psql -U postgres -c "CREATE DATABASE ai_office_db;"
psql -U postgres -d ai_office_db -f database/init.sql
```

### Bước 2: Chạy Backend API Server

```bash
cd server
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- `--host 0.0.0.0` cho phép các máy khác trong mạng LAN truy cập
- Sau khi chạy, test thử: `http://<IP_MÁY_CHỦ>:8000/docs`

### Bước 3: Chạy AI Engine

```bash
cd ai-engine
pip install -r requirements.txt
uvicorn llm_server:app --host 0.0.0.0 --port 8001
```

- Kiểm tra: `http://<IP_MÁY_CHỦ>:8001/health`

### Bước 4: Tải Model AI (chỉ lần đầu)

```bash
cd ai-engine
pip install huggingface_hub
huggingface-cli download Qwen/Qwen2-1.5B-Instruct --local-dir ./models/qwen2-1.5b
```

> Xem thêm model gợi ý tại `ai-engine/models/README.md`

### ✅ Kết quả: Server đang lắng nghe

| Service | URL | Mô tả |
|---------|-----|-------|
| Backend API | `http://<IP_MÁY_CHỦ>:8000` | Nhận request từ client |
| AI Engine | `http://<IP_MÁY_CHỦ>:8001` | Xử lý AI (nội bộ, client không gọi trực tiếp) |
| PostgreSQL | `<IP_MÁY_CHỦ>:5432` | Database (nội bộ) |

---

## 💻 PHẦN 2: CHẠY CLIENT (Trên máy nhân viên)

> Mỗi nhân viên sẽ truy cập AI Assistant qua 1 trong 2 cách dưới đây.
> Client KHÔNG cần cài Python hay Database, chỉ cần trình duyệt.

### ⚠️ QUAN TRỌNG: Cấu hình địa chỉ Server

Trước khi dùng client, cần sửa IP máy chủ trong code:

**File `client/web-chat/app.js` (dòng 1):**
```javascript
const API_BASE_URL = "http://<IP_MÁY_CHỦ>:8000/api/v1";
// Ví dụ: const API_BASE_URL = "http://192.168.1.100:8000/api/v1";
```

**File `client/office-addin/taskpane.js` (dòng 2):**
```javascript
const API_BASE_URL = "http://<IP_MÁY_CHỦ>:8000/api/v1";
// Ví dụ: const API_BASE_URL = "http://192.168.1.100:8000/api/v1";
```

---

### Cách 1: Web Chat (mở trên trình duyệt)

1. Copy thư mục `client/web-chat/` sang máy nhân viên (hoặc đặt trên shared folder)
2. Mở file `index.html` bằng trình duyệt (Chrome / Edge)
3. Bắt đầu chat với AI!

> **Hoặc** host bằng HTTP server để nhiều người truy cập cùng lúc:
> ```bash
> cd client/web-chat
> npx -y http-server -p 3000
> ```
> Truy cập: `http://<IP_MÁY_WEB>:3000`

---

### Cách 2: Office Add-in (nhúng vào Word / Excel / PowerPoint)

#### Bước 1: Host Add-in qua HTTPS

```bash
cd client/office-addin
npx -y office-addin-dev-certs install
npx -y http-server -S -p 3000
```

#### Bước 2: Sideload vào Office

1. Mở **Microsoft Word** (hoặc Excel / PowerPoint)
2. Vào **Insert** → **My Add-ins** → **Upload My Add-in**
3. Chọn file `client/office-addin/manifest.xml`
4. Panel **AI Office Assistant** xuất hiện bên phải cửa sổ
5. Gõ câu hỏi → nhấn **Gửi** → AI trả lời ngay trong Office

---

## 🔌 Bảng API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/api/v1/auth/register` | Đăng ký tài khoản |
| `POST` | `/api/v1/auth/login/access-token` | Đăng nhập lấy JWT token |
| `POST` | `/api/v1/chat/send` | Gửi tin nhắn cho AI |
| `GET`  | `/api/v1/chat/conversations` | Lấy danh sách hội thoại |
| `POST` | `/api/v1/tasks/` | Tạo công việc mới |
| `GET`  | `/api/v1/tasks/` | Xem danh sách công việc |
| `POST` | `/api/v1/documents/upload/` | Upload tài liệu cho RAG |
| `POST` | `/api/v1/office/generate-macro` | Sinh macro cho Office |

> Swagger docs đầy đủ: `http://<IP_MÁY_CHỦ>:8000/docs`

---

## 🔧 Biến môi trường (Server)

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `POSTGRES_SERVER` | `localhost` | Địa chỉ PostgreSQL |
| `POSTGRES_USER` | `postgres` | User PostgreSQL |
| `POSTGRES_PASSWORD` | `postgres` | Mật khẩu PostgreSQL |
| `POSTGRES_DB` | `ai_office_db` | Tên database |
| `AI_ENGINE_URL` | `http://localhost:8001` | URL AI Engine |
| `SECRET_KEY` | (auto) | JWT Secret Key |

---

## � Cấu trúc thư mục

```
QLDA_CNTT/
│
├── client/                     # ← COPY SANG MÁY NHÂN VIÊN
│   ├── office-addin/           # Add-in nhúng vào Word/Excel/PPT
│   │   ├── manifest.xml
│   │   ├── taskpane.html
│   │   ├── taskpane.js
│   │   └── taskpane.css
│   └── web-chat/               # Web Chat trên trình duyệt
│       ├── index.html
│       ├── app.js
│       └── style.css
│
├── server/                     # ← CHẠY TRÊN MÁY CHỦ
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # Khởi động FastAPI
│       ├── core/               # Config & Security
│       ├── models/             # Database models
│       ├── schemas/            # Data validation
│       ├── routes/             # API endpoints
│       ├── services/           # Business logic
│       └── utils/              # Tiện ích
│
├── ai-engine/                  # ← CHẠY TRÊN MÁY CHỦ
│   ├── requirements.txt
│   ├── llm_server.py
│   ├── rag_pipeline.py
│   ├── embeddings.py
│   ├── models/                 # Lưu model AI
│   └── vector_store/           # Lưu FAISS index
│
├── database/                   # ← CHẠY TRÊN MÁY CHỦ
│   ├── init.sql
│   └── migrations/
│
├── storage/                    # ← TRÊN MÁY CHỦ
│   ├── documents/
│   └── reports/
│
├── docker-compose.yml
└── README.md
```

---

## 👥 Đội ngũ phát triển

- QLDA AI Team

## 📝 License

Internal Use Only - Dùng nội bộ trong hệ thống eOffice.
