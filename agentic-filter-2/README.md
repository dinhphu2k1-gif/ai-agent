# Filter Service

Lớp **bảo vệ truy cập dữ liệu** giữa agent layer và PostgreSQL / OpenSearch: FastAPI, catalog quyền (IAM), runtime authorize/filter/search, API admin.

Tài liệu kiến trúc: [docs/architecture_plan.md](docs/architecture_plan.md) · SRS: [my-docs/0_srs.md](my-docs/0_srs.md).

---

## Yêu cầu


| Thành phần | Phiên bản / ghi chú                         |
| ---------- | ------------------------------------------- |
| Python     | 3.11+                                       |
| Docker     | Khuyến nghị cho Postgres, OpenSearch, Redis |
| Git + pip  | Cài package editable                        |


Trên Windows, khi gọi HTTP từ PowerShell nên dùng `**curl.exe`** (tránh alias `curl` → `Invoke-WebRequest`).

---

## 1. Clone và cài dependency

```powershell
cd F:\data\src\agentic-filter-2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Bash / Git Bash:

```bash
cd /path/to/agentic-filter-2
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## 2. Khởi động Docker

File: `[docker-compose.yml](docker-compose.yml)`.

### Chỉ Postgres (SQL, catalog, filter query)

```powershell
docker compose up -d postgres
```

### Postgres + OpenSearch + Dashboards (SQL + search)

```powershell
docker compose up -d postgres opensearch opensearch-dashboards
```

### Thêm Redis (khi `USER_CONTEXT_CACHE_BACKEND=redis`)

```powershell
docker compose up -d postgres redis
# hoặc full stack:
docker compose up -d postgres opensearch opensearch-dashboards redis
```

### Cổng và URL mặc định


| Dịch vụ               | URL / cổng host                                               |
| --------------------- | ------------------------------------------------------------- |
| PostgreSQL            | `postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db` |
| OpenSearch HTTP       | [http://127.0.0.1:19200](http://127.0.0.1:19200)              |
| OpenSearch Dashboards | [http://127.0.0.1:5601](http://127.0.0.1:5601)                |
| Redis                 | `redis://127.0.0.1:6379/0`                                    |


Kiểm tra Postgres:

```powershell
docker compose ps
```

Kiểm tra OpenSearch (lần đầu có thể mất 30–60 giây):

```powershell
curl.exe -sS http://127.0.0.1:19200/
```

---

## 3. Cấu hình môi trường

```powershell
copy .env.example .env
```

Chỉnh `.env` cho local dev (tối thiểu):

```env
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db
RUNTIME_POSTGRES_URL=

REDIS_URL=redis://127.0.0.1:6379/0
USER_CONTEXT_CACHE_BACKEND=memory

IAM_BASE_URL=http://127.0.0.1:9999
IAM_TOKEN_VALIDATE_PATH=/v1/token/validate

# Bật khi đã docker compose up -d opensearch
OPENSEARCH_BASE_URL=http://127.0.0.1:19200

# Local FE: không cần mock IAM (chạy seed trước)
AUTH_BYPASS_ENABLED=true

# Tùy chọn: bảo vệ /api/v1/admin/*
# ADMIN_API_TOKEN=dev-admin-secret
```


| Biến                         | Ý nghĩa                                                 |
| ---------------------------- | ------------------------------------------------------- |
| `DATABASE_URL`               | Catalog IAM + permission (Alembic, seed)                |
| `RUNTIME_POSTGRES_URL`       | DB thực thi SQL runtime; để trống = dùng `DATABASE_URL` |
| `USER_CONTEXT_CACHE_BACKEND` | `memory` (không cần Redis) hoặc `redis`                 |
| `OPENSEARCH_BASE_URL`        | Bật executor search; để trống nếu không dùng OpenSearch |
| `AUTH_BYPASS_ENABLED`        | `true` chỉ local: mọi Bearer token → user demo sau seed |
| `IAM_BASE_URL`               | Cần khi tắt bypass và chạy `mock_iam_server.py`         |


---

## 4. Migration database

Chạy **trước** mọi script seed. Alembic lấy URL từ `**DATABASE_URL` trong file `.env`** (xem [alembic/env.py](alembic/env.py)) — **không cần** gõ `set DATABASE_URL=...` trên CMD hay `$env:DATABASE_URL` trên PowerShell.

Điều kiện:

1. Đã tạo `.env` (mục 3) với `DATABASE_URL=postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db`
2. Postgres đang chạy: `docker compose up -d postgres`
3. Mở terminal **tại thư mục gốc repo** (Cursor: *Terminal → New Terminal*; cwd = `agentic-filter-2`)

### Cách chạy (khuyến nghị)

```text
python scripts/run_migrate.py
```

Script in URL đang dùng (không in mật khẩu) rồi chạy `upgrade head`.

### Cách tương đương

```text
python -m alembic upgrade head
```

Cùng đọc `.env` qua `app.core.config.Settings` khi `alembic/env.py` được load.

> **Tránh:** chỉ gõ `alembic upgrade head` trong **CMD** nếu `alembic` không có trong PATH hoặc cwd không phải thư mục repo — dễ lỗi kết nối / không tìm thấy `.env`.

---

## 5. Seed dữ liệu

### 5.1 Demo runtime + admin wizard (`seed_demo_data.py`)

Tạo user demo, catalog `demo_db` / `public.orders` / `customers`, quyền SELECT + row filter, admin tree (`analytics_db`, `marketing_db`), bảng vật lý `public.orders`, và (nếu có `OPENSEARCH_BASE_URL`) index OpenSearch `customers`.

```powershell
$env:DATABASE_URL = "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
$env:OPENSEARCH_BASE_URL = "http://127.0.0.1:19200"
python scripts/seed_demo_data.py
```

Chỉ Postgres (bỏ OpenSearch):

```powershell
$env:DATABASE_URL = "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
Remove-Item Env:OPENSEARCH_BASE_URL -ErrorAction SilentlyContinue
python scripts/seed_demo_data.py
```

Giữ lại output `**ORDERS_TABLE_RESOURCE_ID**`, `**CUSTOMERS_TABLE_RESOURCE_ID**`, `**DEMO_USER_ID**` — dùng cho `/api/v1/runtime/authorize` và curl.

User demo cố định: `aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa`.

### 5.2 Catalog GL/CIF từ agentic-agri (`seed_gl_resource_dictionary.py`)

Nạp cây resource **COREDB** → schema **GL** / **CIF** → bảng & cột (metadata từ `agentic-agri/scripts/seed_data_dictionary.py`). Idempotent.

```powershell
$env:DATABASE_URL = "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
python scripts/seed_gl_resource_dictionary.py
```

Tùy chọn đường dẫn nguồn:

```powershell
$env:AGRI_DATA_DICTIONARY_SCRIPT = "F:\data\src\agentic-agri\scripts\seed_data_dictionary.py"
python scripts/seed_gl_resource_dictionary.py
```

Sau seed: `GET /api/v1/admin/resources/tree` — tìm `COREDB` với các bảng `GL_*`, `CIF_*`.

---

## 6. Xác thực runtime (chọn một)

### Cách A — Bypass IAM (khuyến nghị cho FE local)

Trong `.env`:

```env
AUTH_BYPASS_ENABLED=true
USER_CONTEXT_CACHE_BACKEND=memory
```

FE gửi `Authorization: Bearer <bất kỳ>`; service dùng user demo sau `seed_demo_data.py`. **Không** bật trên production.

### Cách B — Mock IAM (terminal riêng)

```powershell
python scripts/mock_iam_server.py
```

Mặc định: `http://127.0.0.1:9999/v1/token/validate`. Trong `.env`: tắt `AUTH_BYPASS_ENABLED`, đặt `IAM_BASE_URL=http://127.0.0.1:9999`.

---

## 7. Chạy API

```powershell
$env:DATABASE_URL = "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
$env:USER_CONTEXT_CACHE_BACKEND = "memory"
$env:OPENSEARCH_BASE_URL = "http://127.0.0.1:19200"
$env:AUTH_BYPASS_ENABLED = "true"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)  
- OpenAPI (nếu bật): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Nếu **không** set `OPENSEARCH_BASE_URL`, endpoint search có thể báo executor chưa cấu hình — bình thường khi chỉ test SQL.

---

## 8. Kiểm tra nhanh

```powershell
curl.exe -sS http://127.0.0.1:8000/health
curl.exe -sS http://127.0.0.1:8000/api/v1/runtime/user-context -H "Authorization: Bearer demo-token"
curl.exe -sS http://127.0.0.1:8000/api/v1/admin/resources/tree
```

Chuỗi **curl đầy đủ** (authorize, filter query, search, admin CRUD): [docs/huong-dan-chay-va-curl.md](docs/huong-dan-chay-va-curl.md).

---

## 9. Chạy test

### Unit / smoke (không cần Docker)

```powershell
python -m pytest -q
```

### Integration PostgreSQL

Postgres phải đang chạy (`docker compose up -d postgres`). Pytest tự probe `filter@127.0.0.1:5433/filter_db` nếu không set biến; có thể ghi đè:

```powershell
$env:FILTER_INTEGRATION_DATABASE_URL = "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
python -m pytest tests/integration -q -m integration
```

Mỗi test integration có thể `alembic downgrade base` + `upgrade head` — **chỉ dùng DB disposable**, không phải production.

### Integration OpenSearch + Postgres

```powershell
docker compose up -d postgres opensearch opensearch-dashboards
$env:FILTER_INTEGRATION_DATABASE_URL = "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
$env:FILTER_INTEGRATION_OPENSEARCH_URL = "http://127.0.0.1:19200"
python -m pytest tests/integration/test_opensearch_filter_search_integration.py -q -m integration
```

> **Lưu ý cổng OpenSearch:** `docker-compose.yml` map **19200→9200**. Đặt `OPENSEARCH_BASE_URL` / `FILTER_INTEGRATION_OPENSEARCH_URL` khớp cổng host (**19200**). Một số comment cũ trong repo có thể ghi 9201 — ưu tiên the file compose.

---

## 10. Thứ tự chạy lần đầu (checklist)

1. `pip install -e ".[dev]"`
2. `copy .env.example .env` → chỉnh URL Postgres / OpenSearch / bypass IAM
3. `docker compose up -d postgres opensearch opensearch-dashboards` *(hoặc chỉ postgres)*
4. `python scripts/run_migrate.py`
5. `python scripts/seed_demo_data.py` *(và tùy chọn `seed_gl_resource_dictionary.py`)*
6. *(Tùy chọn)* `python scripts/mock_iam_server.py` nếu không dùng bypass
7. `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
8. `curl.exe` / FE gọi `/health`, `/api/v1/runtime/`*, `/api/v1/admin/*`

---

## Tài liệu API


| Tài liệu                                                                 | Nội dung                                        |
| ------------------------------------------------------------------------ | ----------------------------------------------- |
| [docs/huong-dan-chay-va-curl.md](docs/huong-dan-chay-va-curl.md)         | Demo chi tiết, curl/PowerShell, troubleshooting |
| [docs/api-fe-integration.md](docs/api-fe-integration.md)                 | Runtime / filter cho frontend                   |
| [docs/api-reference.md](docs/api-reference.md)                           | Toàn bộ API admin + runtime                     |
| [docs/epic-01-project-foundation.md](docs/epic-01-project-foundation.md) | Epic 1 — foundation checklist                   |


---

## Agents / Cursor

Persona và subagent: [AGENTS.md](AGENTS.md).