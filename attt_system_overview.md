# Báo Cáo Phân Tích Hệ Thống ATTT (Agentic AI System)

Dựa trên quá trình rà soát toàn bộ thư mục `attt`, hệ thống được thiết kế theo một kiến trúc microservices/multi-tier hoàn chỉnh bao gồm 3 phân hệ chính: Frontend, AI Agent Backend, và Data Security/Filter Service.

Dưới đây là chi tiết vai trò và cách thức hoạt động của từng phân hệ:

---

## 1. Hệ Sinh Thái Các Phân Hệ (The 3 Pillars)

### 1.1. `agentic-agri` (Universal Supervisor - Bộ Não AI)
Đây là hệ thống **Multi-Agent Backend** cốt lõi được xây dựng trên **LangGraph**.
*   **Vai trò:** Đóng vai trò là "Bộ Não" phân tích ngôn ngữ tự nhiên từ người dùng và chuyển hóa thành câu lệnh truy vấn SQL (Text-to-SQL).
*   **Thành phần chính:**
    *   **Supervisor Agent:** Nhận lệnh, suy luận (ReAct) và điều phối công việc. Nếu thiếu thông tin, nó sẽ gọi node Human-In-The-Loop để hỏi lại người dùng.
    *   **Metadata Sub-graph:** Kết nối với OpenSearch (Hybrid Search: BM25 + Vector BGE-M3) để tra cứu Data Dictionary (cấu trúc bảng, cột, quan hệ).
    *   **SQL Writer Agent:** Dựa trên context từ Metadata Agent, tự động sinh mã PostgreSQL tuân thủ schema. (Có sử dụng Neo4j để tra cứu quan hệ các bảng).
*   **Công nghệ:** Python, LangGraph, LLM (Google / vLLM), OpenSearch, PostgreSQL, Neo4j, Redis (State/Checkpoint).

### 1.2. `agentic-filter-2` (Filter Service - Tấm Khiên Bảo Mật)
Đây là lớp **Data Protection & Authorization** nằm giữa Agent Layer và Database đích (PostgreSQL / OpenSearch).
*   **Vai trò:** Đảm bảo rằng dù Agent sinh ra bất kỳ câu SQL nào, nó cũng phải đi qua lớp kiểm duyệt quyền truy cập (IAM), lọc dữ liệu (Row-level filter), và che giấu dữ liệu nhạy cảm (Data masking) trước khi thực thi thực tế.
*   **Thành phần chính:**
    *   **Catalog IAM:** Quản lý quyền truy cập của User.
    *   **Runtime Authorize & Filter:** Đánh giá SQL sinh ra, viết lại câu query (SQL Rewrite) chèn thêm điều kiện WHERE dựa trên phân quyền người dùng.
    *   **Search Executor:** Mở rộng bảo mật cho cả OpenSearch query.
    *   **Admin API:** Quản lý quyền hạn và resource catalog.
*   **Công nghệ:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis (Caching context người dùng).

### 1.3. `agentic-ai-fe` (Frontend - Giao Diện Người Dùng)
Đây là giao diện tương tác cho người dùng cuối và quản trị viên.
*   **Vai trò:** Cung cấp ứng dụng Web Client để người dùng chat với AI (Agentic-Agri), xem kết quả truy vấn, cũng như giao diện Admin (có thể tích hợp với Admin API của Filter Service).
*   **Công nghệ:** React, TypeScript, Vite. Sử dụng ESLint strict (type-aware lint rules) để đảm bảo chất lượng code. Hệ thống cũng có khả năng tích hợp sẵn React Compiler.

---

## 2. Kiến Trúc Tương Tác (Architecture Flow)

1.  **Người dùng (User)** tương tác thông qua giao diện Web **(agentic-ai-fe)** (hoặc Telegram bot của agentic-agri).
2.  Yêu cầu dưới dạng văn bản (text) được gửi tới **Bộ Não AI (agentic-agri)**.
    *   Supervisor phân tích.
    *   Metadata Agent tra cứu lược đồ Database (OpenSearch).
    *   SQL Writer Agent tạo ra câu lệnh SQL PostgreSQL.
3.  Thay vì chạy thẳng SQL vào DB, câu SQL này được gửi qua **Tấm Khiên Bảo Mật (agentic-filter-2)**.
    *   Filter Service kiểm tra Token (Identity/IAM).
    *   Filter Service lấy user context và tự động viết lại câu SQL (chèn điều kiện bảo mật, mask cột nhạy cảm).
4.  Câu SQL an toàn cuối cùng được thực thi trên **PostgreSQL/OpenSearch**.
5.  Kết quả trả về qua các lớp và hiển thị lên **Frontend**.

---

## 3. Khởi Chạy Toàn Hệ Thống Cục Bộ (Local Development)

### Bước 1: Khởi động Hạ tầng Database chung
Hạ tầng dùng chung cho cả `agentic-agri` và `agentic-filter-2` bao gồm Postgres, OpenSearch, Neo4j, Redis. Nên sử dụng file `docker-compose.yml` ở một trong hai thư mục để khởi động. Lưu ý: Bạn cần phải `cd` vào đúng thư mục chứa file `docker-compose.yml` trước khi chạy lệnh.

Ví dụ khởi động bằng file docker-compose của thư mục `agentic-filter-2`:
```bash
cd agentic-filter-2
docker compose up -d postgres opensearch opensearch-dashboards redis
```

### Bước 2: Setup và Chạy `agentic-filter-2` (Cổng Bảo Mật)
```bash
cd agentic-filter-2
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Tạo .env, chạy migrate và seed dữ liệu
cp .env.example .env
python scripts/run_migrate.py
python scripts/seed_demo_data.py
python scripts/seed_gl_resource_dictionary.py  # Seed dictionary từ agentic-agri

# Chạy FastAPI Filter Server (Port 8000)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Bước 3: Setup và Chạy `agentic-agri` (Bộ Não AI)
```bash
cd agentic-agri
pip install -e . ".[dev]" ".[api]"

# Tạo .env và cấu hình SUPERVISOR_PROVIDER, LLM KEYS
cp env.example .env

# Chạy Seed Data để AI có Data Dictionary
python scripts/seed_data_dictionary.py
python scripts/seed_neo4j_relationships.py

# Chạy Chat HTTP API Server (Port 9001)
uvicorn api.app:app --host 0.0.0.0 --port 9001 --app-dir src
```

### Bước 4: Khởi chạy Giao diện `agentic-ai-fe`
```bash
cd agentic-ai-fe
npm install
# Cấu hình .env trỏ API về cổng 9001 (Chat) và 8000 (Filter/Admin)
npm run dev
```

---

## Tổng Kết
Ba dự án này tạo thành một giải pháp hoàn chỉnh cho **"Agentic SQL" có kiểm soát bảo mật**. Đây là một kiến trúc rất hiện đại, tách bạch rõ ràng giữa khả năng "Suy luận AI" (`agri`), khả năng "Kiểm soát an toàn/Phân quyền" (`filter-2`), và "Tương tác người dùng" (`ai-fe`).
