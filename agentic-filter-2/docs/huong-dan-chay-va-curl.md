# Hướng dẫn chạy local, seed demo, và curl test luồng

Tài liệu này mô tả cách chạy Filter Service với **PostgreSQL** (catalog + bảng vật lý `public.orders`), tùy chọn **OpenSearch** (index `customers`), **mock IAM**, script **seed**, và chuỗi **curl** để tự kiểm tra runtime (Postgres + OpenSearch).

**API cho FE:** runtime/filter [api-fe-integration.md](./api-fe-integration.md) · **danh mục đầy đủ** [api-reference.md](./api-reference.md).

## Điều kiện

- Python 3.11+ (khớp với dự án).
- Docker (khuyến nghị) cho Postgres / Redis / OpenSearch tùy chọn.
- Trên Windows, dùng `curl.exe` (binary thật) thay vì alias `curl` của PowerShell nếu cần.

## 1. Khởi động Docker (Postgres; OpenSearch + Redis nếu cần)

**Tối thiểu Postgres + OpenSearch** (đủ test cả SQL và search):

```powershell
cd F:\data\src\agentic-filter-2
docker compose up -d postgres opensearch opensearch-dashboards
```

**Giao diện OpenSearch Dashboards** (xem index, chạy query trong Dev Tools): mở trình duyệt **http://127.0.0.1:5601** — không đăng nhập khi chạy stack dev (security tắt). Lần đầu Dashboards có thể cần thêm vài chục giây sau khi OpenSearch đã **green/yellow**.

Chỉ Postgres (bỏ qua mục OpenSearch trong tài liệu):

```powershell
docker compose up -d postgres
```

OpenSearch lần đầu có thể cần **30–60 giây**; kiểm tra:

```powershell
curl.exe -sS http://127.0.0.1:9201/
```

Chuỗi Postgres mặc định (khớp `docker-compose.yml`):

`postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db`

HTTP OpenSearch trong compose: **http://127.0.0.1:9201** (cổng host 9201 → container 9200).  
OpenSearch Dashboards: **http://127.0.0.1:5601** (menu **Management → Index Management** hoặc **Dev Tools** để gửi `_search`).

## 2. Cấu hình `.env`

```powershell
copy .env.example .env
```

Sửa (hoặc thêm) các biến tối thiểu sau cho luồng demo:

| Biến | Gợi ý demo |
|------|------------|
| `DATABASE_URL` | `postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db` |
| `RUNTIME_POSTGRES_URL` | *(để trống)* — mặc định dùng cùng DB với catalog; seed tạo bảng `public.orders` trên DB này. |
| `IAM_BASE_URL` | `http://127.0.0.1:9999` |
| `IAM_TOKEN_VALIDATE_PATH` | `/v1/token/validate` |
| `USER_CONTEXT_CACHE_BACKEND` | `memory` *(không cần Redis)* hoặc `redis` nếu đã `docker compose up -d redis`. |
| `ADMIN_API_TOKEN` | *(để trống)* — gọi admin không cần header; nếu set thì mọi request `/api/v1/admin/*` cần `X-Admin-Token`. |
| `OPENSEARCH_BASE_URL` | `http://127.0.0.1:9201` khi đã `docker compose up -d opensearch`. Để trống nếu không test search. |
| `AUTH_BYPASS_ENABLED` | `true` — **chỉ local**: bỏ qua IAM; mọi `Authorization: Bearer <bất kỳ>` hợp lệ map user `AUTH_BYPASS_USER_ID` (mặc định user demo sau seed). Không cần chạy mock IAM. |

Cài package:

```powershell
pip install -e ".[dev]"
```

## 3. Migration Alembic

Phải chạy **trước** seed (bảng catalog, `permission_types`, v.v.):

```powershell
$env:DATABASE_URL = "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
alembic upgrade head
```

## 4. Seed dữ liệu demo (Postgres catalog + tùy chọn OpenSearch)

Script: `scripts/seed_demo_data.py`

- User cố định: `aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa` (trùng mock IAM).
- Catalog **Postgres**: database logic `demo_db`, schema `public`, bảng `orders` (cột `id`, `name`, `tenant_id`) + bảng **`customers`** (cột `name`, `tenant_id`) dùng cho OpenSearch (tên index = tên bảng logic: `customers`).
- Quyền SELECT trên từng bảng và cột; row filter `tenant_id = 1` trên **cả** `orders` và `customers`.
- Vật lý Postgres: **`DROP` + `CREATE` `public.orders`**, chèn 2 dòng `(Alice,1)` và `(Bob,2)`.
- **OpenSearch**: nếu biến môi trường `OPENSEARCH_BASE_URL` có giá trị (hoặc đọc từ `.env` qua `Settings`), script tạo lại index `customers`, bulk 2 document (Alice/Bob), `_refresh`.

```powershell
$env:DATABASE_URL = "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
$env:OPENSEARCH_BASE_URL = "http://127.0.0.1:9201"
python scripts/seed_demo_data.py
```

Chỉ seed Postgres (không gọi OpenSearch):

```powershell
$env:DATABASE_URL = "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
Remove-Item Env:OPENSEARCH_BASE_URL -ErrorAction SilentlyContinue
python scripts/seed_demo_data.py
```

Giữ lại các dòng in **`ORDERS_TABLE_RESOURCE_ID`** và **`CUSTOMERS_TABLE_RESOURCE_ID`** — dùng cho `/api/v1/runtime/authorize`. Index search luôn là **`customers`** (trùng `OPENSEARCH_INDEX` in ra).

## 5. Xác thực runtime (chọn một)

### 5a. Ghép FE nhanh — bỏ qua IAM (`AUTH_BYPASS_ENABLED`)

Sau khi đã `alembic upgrade head` và `python scripts/seed_demo_data.py`, thêm vào `.env`:

```env
AUTH_BYPASS_ENABLED=true
USER_CONTEXT_CACHE_BACKEND=memory
```

FE vẫn gửi header như production, ví dụ `Authorization: Bearer <token-từ-FE>` — Filter Service **không** gọi IAM, luôn dùng user demo `aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa` (hoặc `AUTH_BYPASS_USER_ID` nếu bạn đổi). **Không** bật trên production.

### 5b. Mock IAM (terminal thứ hai)

```powershell
python scripts/mock_iam_server.py
```

Mặc định: `http://127.0.0.1:9999/v1/token/validate` (GET, header `Authorization: Bearer ...`). Trên Windows script bind **`127.0.0.1`** (tránh `WinError 10013` với `0.0.0.0`); có thể ghi đè: `$env:MOCK_IAM_BIND = "0.0.0.0"`.

## 6. Chạy API (bật OpenSearch executor khi có URL)

```powershell
$env:DATABASE_URL = "postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
$env:USER_CONTEXT_CACHE_BACKEND = "memory"
$env:OPENSEARCH_BASE_URL = "http://127.0.0.1:9201"
# Chọn một: bypass IAM (FE) hoặc mock IAM
$env:AUTH_BYPASS_ENABLED = "true"
# $env:IAM_BASE_URL = "http://127.0.0.1:9999"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Nếu không test OpenSearch, bỏ dòng `OPENSEARCH_BASE_URL` (endpoint `/api/v1/filter/search` sẽ trả 500 *executor not configured*).

## 7. Biến môi trường shell (Bash hoặc Git Bash)

```bash
export BASE=http://127.0.0.1:8000
export TOK=demo-token
export TBL='<DÁN_ORDERS_TABLE_RESOURCE_ID_TỪ_SEED>'
export TCUST='<DÁN_CUSTOMERS_TABLE_RESOURCE_ID_TỪ_SEED>'
export IDX=customers
```

## 8. Chuỗi lệnh `curl` (Bash / Git Bash)

Linux/macOS/Git Bash: dùng lệnh `curl`. Trên **PowerShell thuần** Windows, gọi `curl.exe` để tránh alias `curl` → `Invoke-WebRequest`.

### 8.1 Health

```bash
curl -sS "$BASE/health"
```

### 8.2 User context

```bash
curl -sS "$BASE/api/v1/runtime/user-context" -H "Authorization: Bearer $TOK"
```

### 8.3 Authorize ALLOW (bảng `orders`)

```bash
curl -sS "$BASE/api/v1/runtime/authorize" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d "{\"resource_id\":\"$TBL\",\"action\":\"SELECT\"}"
```

### 8.3b Authorize ALLOW (bảng catalog `customers` / index OpenSearch)

```bash
curl -sS "$BASE/api/v1/runtime/authorize" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d "{\"resource_id\":\"$TCUST\",\"action\":\"SELECT\"}"
```

### 8.4 Authorize DENY

```bash
curl -sS "$BASE/api/v1/runtime/authorize" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"resource_id":"00000000-0000-4000-8000-000000000001","action":"SELECT"}'
```

### 8.5 Filter query (row filter `tenant_id = 1`)

```bash
curl -sS "$BASE/api/v1/filter/query" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"backend":"postgres","database":"demo_db","query":"SELECT id, name, tenant_id FROM public.orders"}'
```

### 8.6 Filter query — database không có trong catalog (422)

```bash
curl -sS -w "\nHTTP %{http_code}\n" "$BASE/api/v1/filter/query" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"backend":"postgres","database":"khong_ton_tai","query":"SELECT id FROM public.orders"}'
```

### 8.7 Access logs (admin, không token nếu `ADMIN_API_TOKEN` trống)

```bash
curl -sS "$BASE/api/v1/admin/audit/access-logs?limit=20"
```

Nếu đã bật `ADMIN_API_TOKEN`:

```bash
curl -sS "$BASE/api/v1/admin/audit/access-logs?limit=20" -H "X-Admin-Token: YOUR_TOKEN"
```

### 8.8 Thiếu Bearer (401)

```bash
curl -sS -w "\nHTTP %{http_code}\n" "$BASE/api/v1/runtime/user-context"
```

### 8.9 Filter search OpenSearch (`match_all`, row filter → 1 hit)

Cần API đã bật `OPENSEARCH_BASE_URL` và đã chạy seed có OpenSearch.

```bash
curl -sS "$BASE/api/v1/filter/search" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d "{\"backend\":\"opensearch\",\"index\":\"$IDX\",\"query\":{\"match_all\":{}},\"size\":20}"
```

Kỳ vọng: HTTP 200, `policy.decision` = `ALLOW_WITH_FILTER`, `hits.hits` có **1** phần tử, `_source.name` = `Alice`, `_source.tenant_id` = 1.

### 8.10 Filter search — index không có trong catalog (422)

```bash
curl -sS -w "\nHTTP %{http_code}\n" "$BASE/api/v1/filter/search" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"backend":"opensearch","index":"unknown_index_xyz","query":{"match_all":{}},"size":5}'
```

---

## 9. Biến tiện dụng (PowerShell) + `Invoke-RestMethod`

```powershell
$BASE = "http://127.0.0.1:8000"
$TOK  = "bat-ky-chuoi-nao"
$HDR  = @{ Authorization = "Bearer $TOK" }
$TBL  = "<ORDERS_TABLE_RESOURCE_ID>"
$TCUST = "<CUSTOMERS_TABLE_RESOURCE_ID>"
$IDX  = "customers"
```

### 9.1 Health

```powershell
Invoke-RestMethod -Uri "$BASE/health" -Method Get
```

Kỳ vọng: `{ "status": "ok" }`.

### 9.2 User context (IAM → cache → DB user)

```powershell
Invoke-RestMethod -Uri "$BASE/api/v1/runtime/user-context" -Headers $HDR -Method Get
```

Kỳ vọng: `user_id` = `aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa`, `username` = `demo_user`.

### 9.3 Authorize SELECT trên resource bảng `orders`

```powershell
$body = @{ resource_id = $TBL; action = "SELECT" } | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE/api/v1/runtime/authorize" -Headers $HDR -Method Post -Body $body -ContentType "application/json"
```

Kỳ vọng: `decision` = `ALLOW`, `combined_row_filter` chứa `tenant_id = 1`.

### 9.3b Authorize trên bảng `customers` (OpenSearch)

```powershell
$body = @{ resource_id = $TCUST; action = "SELECT" } | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE/api/v1/runtime/authorize" -Headers $HDR -Method Post -Body $body -ContentType "application/json"
```

### 9.4 Authorize DENY (resource không có quyền)

```powershell
$badId = "00000000-0000-4000-8000-000000000001"
$body = @{ resource_id = $badId; action = "SELECT" } | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE/api/v1/runtime/authorize" -Headers $HDR -Method Post -Body $body -ContentType "application/json"
```

Kỳ vọng: `decision` = `DENY` (UUID không gắn quyền demo).

### 9.5 Filter query Postgres (SELECT có row filter)

```powershell
$fq = @{
  backend  = "postgres"
  database = "demo_db"
  query    = "SELECT id, name, tenant_id FROM public.orders"
} | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE/api/v1/filter/query" -Headers $HDR -Method Post -Body $fq -ContentType "application/json"
```

Kỳ vọng: chỉ một dòng (`Alice`, `tenant_id` = 1); `policy.decision` dạng `ALLOW_WITH_FILTER` hoặc tương tự.

### 9.6 Filter query — database không tồn tại trong catalog (422)

```powershell
$fq = @{
  backend  = "postgres"
  database = "khong_ton_tai"
  query    = "SELECT id FROM public.orders"
} | ConvertTo-Json
try {
  Invoke-RestMethod -Uri "$BASE/api/v1/filter/query" -Headers $HDR -Method Post -Body $fq -ContentType "application/json"
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Kỳ vọng: HTTP 422, thông báo unknown database.

### 9.7 Audit — access logs (admin)

Nếu `ADMIN_API_TOKEN` **chưa** set:

```powershell
Invoke-RestMethod -Uri "$BASE/api/v1/admin/audit/access-logs?limit=20" -Method Get
```

Nếu đã set token trong `.env`:

```powershell
Invoke-RestMethod -Uri "$BASE/api/v1/admin/audit/access-logs?limit=20" -Headers @{ "X-Admin-Token" = "YOUR_TOKEN" } -Method Get
```

Sau các bước runtime ở trên, log sẽ có các dòng `AUTHORIZE`, `POSTGRES_FILTER_QUERY`, `OPENSEARCH_FILTER_SEARCH`, v.v.

### 9.9 Filter search OpenSearch

```powershell
$fs = @{
  backend = "opensearch"
  index     = $IDX
  query     = @{ match_all = @{} }
  size      = 20
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "$BASE/api/v1/filter/search" -Headers $HDR -Method Post -Body $fs -ContentType "application/json"
```

Kỳ vọng: một hit (Alice); `policy.decision` = `ALLOW_WITH_FILTER`.

### 9.10 Index không tồn tại trong catalog (422)

```powershell
$fs = @{
  backend = "opensearch"
  index     = "unknown_index_xyz"
  query     = @{ match_all = @{} }
  size      = 5
} | ConvertTo-Json -Depth 5
try {
  Invoke-RestMethod -Uri "$BASE/api/v1/filter/search" -Headers $HDR -Method Post -Body $fs -ContentType "application/json"
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Kỳ vọng: HTTP 422 (unknown index trong catalog).

### 9.11 Bearer thiếu / sai định dạng (401)

```powershell
try {
  Invoke-RestMethod -Uri "$BASE/api/v1/runtime/user-context" -Method Get
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Kỳ vọng: 401.

## 10. Ghi chú OpenSearch

- Index mẫu: **`customers`** (đúng bằng tên bảng logic trong catalog; xem `resolve_opensearch_index_to_table_resource_id`).
- Code tạo index + bulk: `scripts/opensearch_customers_seed.py` (dùng chung với pytest integration).
- **OpenSearch Dashboards** (Docker service `opensearch-dashboards`): **http://127.0.0.1:5601** — khởi động cùng: `docker compose up -d opensearch opensearch-dashboards`.
- Nếu không set `OPENSEARCH_BASE_URL` khi chạy uvicorn, `POST /api/v1/filter/search` trả **500** `"OpenSearch executor not configured"`.
- Row filter SQL-style `tenant_id = 1` được chuyển thành mệnh đề `term` trên OpenSearch (MVP); field phải tồn tại trong mapping.

## 11. Admin User / Role / Group API (contract §H)

**Prefix thống nhất:** mọi API (runtime, filter, admin) dùng **`/api/v1/...`**.

| Nhóm | Prefix | Ví dụ |
|------|--------|--------|
| Runtime / Filter | `/api/v1/runtime`, `/api/v1/filter` | `GET /api/v1/runtime/user-context` |
| Admin contract (envelope `success` / `data`) | `/api/v1/admin` | `GET /api/v1/admin/users` |
| Admin MVP (permission CRUD, resource CRUD, audit) | `/api/v1/admin/permissions`, `/resources`, `/audit` | `POST /api/v1/admin/permissions` |
| Gán permission/role đã có (theo UUID) | `/api/v1/admin/assignments` | `POST /api/v1/admin/assignments/users/{id}/permissions` |

**Đặt tên JSON:** contract endpoints dùng **camelCase** (`pageSize`, `isPrimaryKey`). Cây Epic 3 (`GET .../resources/mvp-tree`) dùng **snake_case** (`resource_id`, `databases[]`).

**Auth:** giống mục 2 — nếu `ADMIN_API_TOKEN` được set thì thêm header `X-Admin-Token`.

```powershell
$ADMIN = "http://127.0.0.1:8000/api/v1/admin"
# Resource tree (permission wizard, §G.1)
curl.exe -sS "$ADMIN/resources/tree" | jq '.data[0].type, .data[0].children[0].name'
# Users (trang 1)
curl.exe -sS "$ADMIN/users?page=1&pageSize=10" | jq '.success, .data.totalItems'
# Roles + permissions mặc định demo
$ROLE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaa101"  # role-data-scientist-eu — xem seed uuid5
curl.exe -sS "$ADMIN/roles/$ROLE/permissions" | jq '.data | length'
# Group effective permissions
$GRP = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaa201"    # grp-de-core
curl.exe -sS "$ADMIN/groups/$GRP/effective-permissions" | jq '.data.summary, .data.inheritedSummary'
```

Sau `python scripts/seed_demo_data.py`, chạy regression:

```powershell
pytest tests/test_admin_contract_foundation.py tests/test_admin_users_api.py `
  tests/test_admin_roles_api.py tests/test_admin_groups_api.py `
  tests/test_admin_contract_snapshot.py tests/test_epic3_admin_api.py -q
```

Danh sách đủ 41 endpoint: [my-docs/admin-api-contracts-user-role-group.md](../my-docs/admin-api-contracts-user-role-group.md) mục **H**.

### 11.1 Add Permission wizard — grant TABLE + row filter, COLUMN + mask

Yêu cầu: đã chạy `python scripts/seed_demo_data.py` (có `seed_permission_wizard_resource_tree`: `analytics_db` → `public` → `users` / cột `email`). Role demo: `role-data-scientist-eu` = `aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaa101`.

**Bash (jq)** — lấy UUID từ cây rồi grant:

```bash
export BASE=http://127.0.0.1:8000
export ADMIN="$BASE/api/v1/admin"
export ROLE=aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaa101

# Cây catalog
curl -sS "$ADMIN/resources/tree" | jq '.data[] | select(.name=="analytics_db") | {id, name, schemas: [.children[]? | {id, name, tables: [.children[]? | {id, name}]}]}'

# IDs (điều chỉnh nếu DB khác seed)
DB_ID=$(curl -sS "$ADMIN/resources/tree" | jq -r '.data[] | select(.name=="analytics_db") | .id')
SCH_ID=$(curl -sS "$ADMIN/resources/tree" | jq -r '.data[] | select(.name=="analytics_db") | .children[] | select(.name=="public") | .id')
TBL_ID=$(curl -sS "$ADMIN/resources/tree" | jq -r '.data[] | select(.name=="analytics_db") | .children[] | select(.name=="public") | .children[] | select(.name=="users") | .id')
COL_ID=$(curl -sS "$ADMIN/resources/tree" | jq -r '.data[] | select(.name=="analytics_db") | .children[] | select(.name=="public") | .children[] | select(.name=="users") | .children[] | select(.name=="email") | .id')

# Grant TABLE + row filter → data.created[0] có modifier ROW_FILTER
curl -sS -X POST "$ADMIN/roles/$ROLE/permissions" \
  -H "Content-Type: application/json" \
  -d "{
    \"resourcePath\": [
      {\"id\": \"$DB_ID\", \"name\": \"analytics_db\", \"type\": \"database\"},
      {\"id\": \"$SCH_ID\", \"name\": \"public\", \"type\": \"schema\"},
      {\"id\": \"$TBL_ID\", \"name\": \"users\", \"type\": \"table\"}
    ],
    \"resourceType\": \"TABLE\",
    \"actions\": [\"SELECT\"],
    \"effect\": \"ALLOW\",
    \"rowFilter\": {\"enabled\": true, \"conditionExpression\": \"tenant_id = 1\"}
  }" | jq '.success, .data.created[0].modifier'

# Grant COLUMN + PARTIAL mask
curl -sS -X POST "$ADMIN/roles/$ROLE/permissions" \
  -H "Content-Type: application/json" \
  -d "{
    \"resourcePath\": [
      {\"id\": \"$DB_ID\", \"name\": \"analytics_db\", \"type\": \"database\"},
      {\"id\": \"$SCH_ID\", \"name\": \"public\", \"type\": \"schema\"},
      {\"id\": \"$TBL_ID\", \"name\": \"users\", \"type\": \"table\"},
      {\"id\": \"$COL_ID\", \"name\": \"email\", \"type\": \"column\"}
    ],
    \"resourceType\": \"COLUMN\",
    \"actions\": [\"SELECT\"],
    \"effect\": \"ALLOW\",
    \"columnMask\": {\"enabled\": true, \"maskType\": \"PARTIAL\", \"maskPattern\": \"***@***\"}
  }" | jq '.success, .data.created[0].path | length, .data.created[0].modifier'

# Multi-action → 2 phần tử created
curl -sS -X POST "$ADMIN/roles/$ROLE/permissions" \
  -H "Content-Type: application/json" \
  -d "{
    \"resourcePath\": [
      {\"id\": \"$DB_ID\", \"name\": \"analytics_db\", \"type\": \"database\"},
      {\"id\": \"$SCH_ID\", \"name\": \"public\", \"type\": \"schema\"},
      {\"id\": \"$TBL_ID\", \"name\": \"users\", \"type\": \"table\"}
    ],
    \"resourceType\": \"TABLE\",
    \"actions\": [\"SELECT\", \"DESCRIBE\"],
    \"effect\": \"ALLOW\"
  }" | jq '.data.created | length'

# List sau grant
curl -sS "$ADMIN/roles/$ROLE/permissions" | jq '.data.summary, (.data.permissions | length)'
```

**PowerShell** — cùng logic (cần `analytics_db` trong tree):

```powershell
$ADMIN = "http://127.0.0.1:8000/api/v1/admin"
$ROLE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaa101"
$tree = Invoke-RestMethod -Uri "$ADMIN/resources/tree" -Method Get
$db = $tree.data | Where-Object { $_.name -eq "analytics_db" }
$sch = $db.children | Where-Object { $_.name -eq "public" }
$tbl = $sch.children | Where-Object { $_.name -eq "users" }
$col = $tbl.children | Where-Object { $_.name -eq "email" }

$bodyTable = @{
  resourcePath = @(
    @{ id = $db.id; name = "analytics_db"; type = "database" },
    @{ id = $sch.id; name = "public"; type = "schema" },
    @{ id = $tbl.id; name = "users"; type = "table" }
  )
  resourceType = "TABLE"
  actions = @("SELECT")
  effect = "ALLOW"
  rowFilter = @{ enabled = $true; conditionExpression = "tenant_id = 1" }
} | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri "$ADMIN/roles/$ROLE/permissions" -Method Post -Body $bodyTable -ContentType "application/json"
```

Regression wizard (Phase 3):

```powershell
pytest tests/test_admin_permission_grant.py tests/test_admin_roles_api.py `
  tests/test_admin_groups_api.py tests/test_resource_tree_service.py -q
```

Tài liệu FE: [api-fe-integration.md §9.1](./api-fe-integration.md), [api-reference.md §9.1](./api-reference.md).

## 12. Ghi chú nhanh

- **Dữ liệu vật lý Postgres**: script **drop** bảng `public.orders` rồi tạo lại và chèn 2 dòng mẫu (không dùng trên DB production).
- **OpenSearch**: seed **xóa và tạo lại** index `customers` + bulk 2 document; không dùng trên cluster production có dữ liệu thật trên index trùng tên.
- **User demo** và **mock IAM** phải cùng `user_id` — xem `scripts/demo_constants.py`.
- Production: không dùng mock IAM; cấu hình `IAM_BASE_URL` thật và token hợp lệ.
