# Writer Agent: Sub-graph + Filter-Service SQL Execution

## Goal

Hoàn thiện `writer_agent` thành LangGraph sub-graph (giống `metadata_agent`), **bỏ Neo4j** (metadata đã có JOIN/schema đầy đủ), và **thay thực thi SQL trực tiếp PostgreSQL** bằng gọi **filter-service** để kiểm quyền, masking cột nhạy cảm và row filter trước khi trả kết quả.

## Hiện trạng

| Thành phần | Vấn đề |
|------------|--------|
| `supervisor/graph.py` | Gọi `sql_writer_agent.nodes.sql_writer_worker_node` (monolithic), **không** dùng `writer_agent` sub-graph |
| `writer_agent/graph.py` | WIP: có `neo4j_enrichment`, conditional edge sai (`should_continue_repair` là node thay vì router function; map `"retry"` vs return `"repair"`) |
| `writer_agent/nodes.py` | Vẫn gọi Neo4j + `db_executor_client` trực tiếp |
| `writer_agent/state.py` | Class `SQLWriterState`, graph import `WriterState` — không khớp |
| `sql_writer_agent/prompts.py` | Prompt phụ thuộc `neo4j_context` |
| Metadata agent | Đã có Neo4j JOIN + schema trong `synthesized_schema` / `metadata_context` |

## Kiến trúc đích

```
Supervisor sql_writer_worker_node
    → writer_subgraph.invoke(...)
        sql_generation_node      (LLM, chỉ metadata_context)
        → sql_execution_node     (filter-service POST /api/v1/sql/execute)
        → [conditional] sql_repair_node → sql_execution_node (loop)
        → END → final_output + investigation_log
```

Filter-service chịu trách nhiệm: **check quyền theo `queryScope` (bảng/cột agent khai báo)** → cross-validate với SQL parse → inject row filter → execute → mask → trả preview.

Agent truyền danh sách bảng từ metadata session (`expanded_tables` / `list_tables`) để filter-service **fail-fast** trước khi parse SQL.

---

## Contract API: SQL Execution (filter-service)

Prefix: **`/api/v1/sql`** (đồng bộ với metadata `/api/v1/metadata`).

### Auth / headers (mọi endpoint)

| Header | Bắt buộc | Mô tả |
|--------|----------|--------|
| `Content-Type` | Có | `application/json` |
| `Authorization` | Phase sau | `Bearer <jwt>` |
| `X-Request-Id` | Khuyến nghị | UUID trace |

Body luôn có `userId` (+ `threadId` optional) cho audit và test (giống metadata).

---

### `POST /api/v1/sql/execute`

Thay thế `PostgresExecutorClient.execute_query()` / `writer_agent/db_executor_client.py`.

#### Request

```json
{
  "userId": "845069b7-a70f-58f5-b8df-1e0c5682f3e0",
  "threadId": "845069b7-a70f-58f5-b8df-1e0c5682f3e0:market-trends",
  "sql": "SELECT c.customer_name, a.account_number FROM cif_customers c JOIN cif_accounts a ON ...",
  "dialect": "postgresql",
  "limit": 100,
  "queryScope": {
    "source": "metadata_agent",
    "tables": [
      {
        "name": "CIF_CUSTOMERS",
        "schema": "public",
        "columns": ["customer_id", "customer_name", "tenant_id"]
      },
      {
        "name": "CIF_ACCOUNTS",
        "schema": "public",
        "columns": ["account_id", "account_number", "customer_id", "tenant_id"]
      }
    ]
  },
  "options": {
    "applyRowFilter": true,
    "applyColumnMasking": true,
    "allowRewrite": true,
    "strictScopeMatch": true
  }
}
```

| Field | Kiểu | Mô tả |
|-------|------|--------|
| `userId` | string | User entitlement (bắt buộc) |
| `threadId` | string? | Audit / session |
| `sql` | string | Một câu `SELECT` duy nhất (agent đã strip markdown) |
| `dialect` | enum | `postgresql` \| `oracle` (phase 1: postgres) |
| `limit` | int | Max rows trả về (default 100, cap 1000) |
| `queryScope` | object | **Bắt buộc** — phạm vi bảng/cột cần check quyền (xem bên dưới) |
| `options.applyRowFilter` | bool | Inject RLS / tenant filter vào query hoặc WHERE |
| `options.applyColumnMasking` | bool | Mask cột nhạy cảm (SSN, số tài khoản, …) |
| `options.allowRewrite` | bool | Cho phép filter-service rewrite SQL an toàn (thêm filter/mask subquery) |
| `options.strictScopeMatch` | bool | `true` (default): SQL parse thấy bảng/cột ngoài `queryScope` → `POLICY_VIOLATION` |

#### `queryScope` — phạm vi truy vấn (bắt buộc)

Filter-service dùng field này làm **danh sách chính** để check entitlement `SELECT` trước khi execute. Agent lấy từ output metadata sub-graph (`expanded_tables` + cột đã retrieve).

| Field | Kiểu | Mô tả |
|-------|------|--------|
| `queryScope.source` | enum | `metadata_agent` \| `sql_parser` \| `manual` — nguồn khai báo (audit) |
| `queryScope.tables` | array | Danh sách bảng dự kiến truy vấn (≥ 1 phần tử) |
| `queryScope.tables[].name` | string | Tên bảng UPPER_SNAKE (vd. `CIF_CUSTOMERS`) — khớp data dictionary |
| `queryScope.tables[].schema` | string? | Schema DB (default `public`) |
| `queryScope.tables[].columns` | string[]? | Cột agent/ metadata đã expose; nếu có → check quyền cột + masking sớm |
| `queryScope.tables[].alias` | string? | Alias trong SQL (`c`, `a`) — hỗ trợ map lỗi, không dùng thay `name` |

**Nguồn dữ liệu phía agentic-agri:**

```
metadata_worker_node output
  → expanded_tables / list_tables
  → columns từ raw retrieval hits ([COLUMN] records)
  → supervisor state: query_scope (mới)
  → writer sql_execution_node gửi kèm queryScope
```

**Quy tắc filter-service:**

1. Check `SELECT` trên mọi `queryScope.tables[].name` (và `columns` nếu có).
2. Parse SQL → lấy `parsedTables` / `parsedColumns`.
3. Nếu `strictScopeMatch=true`:
   - `parsedTables ⊄ queryScope.tables` → `403 POLICY_VIOLATION` (SQL tham chiếu bảng không được metadata phép).
   - `parsedColumns` ngoài scope → `403` hoặc mask/deny theo policy.
4. Nếu `strictScopeMatch=false`: union `queryScope` + `parsedTables` rồi check (fallback dev).

**Ví dụ lỗi scope mismatch:**

```json
{
  "success": false,
  "error": {
    "code": "POLICY_VIOLATION",
    "message": "SQL references table GL_JOURNAL_LINES not declared in queryScope",
    "details": {
      "declaredTables": ["CIF_CUSTOMERS", "CIF_ACCOUNTS"],
      "parsedTables": ["CIF_CUSTOMERS", "CIF_ACCOUNTS", "GL_JOURNAL_LINES"],
      "undeclaredTables": ["GL_JOURNAL_LINES"]
    }
  }
}
```

#### Response 200 — thành công

```json
{
  "success": true,
  "data": {
    "executedSql": "SELECT ... WHERE tenant_id = $1 ...",
    "columns": ["customer_name", "account_number"],
    "rows": [["Nguyen Van A", "****1234"]],
    "rowCount": 42,
    "truncated": true,
    "filtered": {
      "checkedTables": ["CIF_CUSTOMERS", "CIF_ACCOUNTS"],
      "checkedColumns": ["CIF_CUSTOMERS.customer_name", "CIF_ACCOUNTS.account_number"],
      "deniedTables": [],
      "deniedColumns": [],
      "maskedColumns": ["account_number"],
      "appliedRowFilters": ["tenant_id = :ctx_tenant_id"],
      "scopeMatch": {
        "declaredTables": ["CIF_CUSTOMERS", "CIF_ACCOUNTS"],
        "parsedTables": ["CIF_CUSTOMERS", "CIF_ACCOUNTS"],
        "strictScopeMatch": true
      }
    },
    "warnings": [
      {
        "code": "COLUMN_MASKED",
        "message": "Column account_number masked per policy POL-MASK-001",
        "resource": "CIF_ACCOUNTS.account_number"
      }
    ]
  }
}
```

#### Response 200 — `success: false` (lỗi nghiệp vụ, agent có thể repair)

```json
{
  "success": false,
  "error": {
    "code": "EXECUTION_ERROR",
    "message": "column \"foo\" does not exist",
    "sqlState": "42703",
    "dialect": "postgresql"
  }
}
```

#### HTTP / error codes

| Code | HTTP | Ý nghĩa | Agent xử lý |
|------|------|---------|-------------|
| `FORBIDDEN` | 403 | Không có quyền `SELECT` trên bảng/cột | Không repair; trả user-facing message |
| `POLICY_VIOLATION` | 403 | SQL tham chiếu resource ngoài entitlement | Không repair |
| `VALIDATION_ERROR` | 400 | Không phải SELECT / nhiều câu / DDL / **thiếu `queryScope`** | Repair nếu LLM sinh sai |
| `EXECUTION_ERROR` | 200 + success false | Lỗi DB runtime/syntax | Vào `sql_repair_node` |
| `TIMEOUT` | 504 | Query quá thời gian | Retry hoặc báo user |
| `UPSTREAM_ERROR` | 502 | DB upstream lỗi | Log + fallback message |

---

### `POST /api/v1/sql/validate` (khuyến nghị, phase 1.5)

Kiểm tra quyền **trước** khi execute (optional cho agent).

```json
{
  "userId": "...",
  "sql": "SELECT ...",
  "dialect": "postgresql",
  "queryScope": {
    "source": "metadata_agent",
    "tables": [
      { "name": "CIF_CUSTOMERS", "schema": "public", "columns": ["customer_name"] }
    ]
  }
}
```

Response:

```json
{
  "success": true,
  "data": {
    "allowed": true,
    "checkedTables": ["CIF_CUSTOMERS"],
    "deniedResources": [],
    "scopeMatch": { "declaredTables": ["CIF_CUSTOMERS"], "parsedTables": ["CIF_CUSTOMERS"], "undeclaredTables": [] },
    "warnings": []
  }
}
```

→ Verify: user không có `SELECT` trên bảng trong `queryScope` → `allowed: false`, agent không gọi execute.

---

### Quyền filter-service (gợi ý mapping)

| Metadata (đã có) | SQL execution (mới) |
|------------------|---------------------|
| `DESCRIBE` trên TABLE/COLUMN | `SELECT` trên TABLE/COLUMN |
| Deny trên SCHEMA | Chặn mọi bảng trong schema |
| Warning khi thiếu quyền | `warnings[]` + loại cột mask |

Row filter: policy theo `userId` (tenant, branch, cost_center) — filter-service inject vào AST/WHERE, **không** tin agent tự thêm filter.

---

## Tasks (agentic-agri)

- [x] **Task 1: Chuẩn hóa `WriterState` + sửa `graph.py`**  
  File: `writer_agent/state.py`, `graph.py`.  
  - State: `user_input`, `metadata_context`, `query_scope`, `user_id`, `thread_id`, `generated_sql`, `sql_result_preview`, `sql_execution_error`, `sql_repair_attempts`, `final_output` — **không** `neo4j_context`.  
  - `query_scope`: `{ source, tables: [{ name, schema?, columns? }] }` — copy từ supervisor (metadata session).  
  - Graph: `START → sql_generation → sql_execution → conditional(sql_repair) → END`.  
  → Verify: `writer_subgraph = WriterAgentGraph().compile()` import OK, `get_graph().draw_ascii()` (optional) hiển thị 3–4 node.

- [x] **Task 2: Bỏ Neo4j khỏi writer**  
  File: `writer_agent/nodes.py`, xóa/deprecate `neo4j_client.py` usage; `prompts.py` (move từ `sql_writer_agent/prompts.py`, bỏ block Neo4j).  
  → Verify: grep `neo4j` trong `writer_agent/` = 0; prompt chỉ dùng `{metadata}`.

- [x] **Task 3: `FilterServiceSqlClient` + factory**  
  File mới: `writer_agent/filter_service_sql_client.py`, `writer_agent/sql_execution_client.py`.  
  - `execute_sql(user_id, sql, query_scope, dialect, limit)` — body gồm `queryScope` bắt buộc.  
  - Helper `build_query_scope(expanded_tables, raw_hits)` từ metadata retriever output.  
  - `create_sql_execution_client(user_id, thread_id)` — filter-service khi `SQL_USE_FILTER_SERVICE=true`, else `PostgresExecutorClient` (dev fallback).  
  - Reuse `FILTER_SERVICE_BASE_URL`, `resolve_metadata_user_context()` cho `userId`.  
  → Verify: `pytest tests/test_filter_service_sql_client.py -v`.

- [x] **Task 4: Refactor nodes dùng filter client**  
  `sql_execution_node` gọi factory thay `create_db_executor()`. Map `EXECUTION_ERROR` → repair; `FORBIDDEN`/`POLICY_VIOLATION` → không repair.  
  → Verify: mock client, repair loop chạy đúng `MAX_SQL_REPAIR_ATTEMPTS`.

- [x] **Task 5: Supervisor wiring**  
  File: `supervisor/nodes.py`, `supervisor/graph.py`.  
  - `sql_writer_worker_node` invoke `writer_subgraph` (pattern giống `metadata_worker_node`).  
  - Truyền `user_id`/`thread_id`/`query_scope` từ supervisor state.  
  - `metadata_worker_node` persist `query_scope` vào supervisor state (build từ `expanded_tables` + column hits).  
  - Map output → `final_output`, `generated_sql`, `investigation_log`.  
  → Verify: `tests/test_metadata_agent.py` style test cho worker; supervisor monitor chạy được.

- [x] **Task 6: Config + env**  
  File: `config.py`, `env.example`.  
  ```env
  SQL_USE_FILTER_SERVICE=true
  # FILTER_SERVICE_BASE_URL=http://127.0.0.1:8000  (shared với metadata)
  SQL_EXECUTOR_DIALECT=postgresql
  MAX_SQL_REPAIR_ATTEMPTS=2
  SQL_EXECUTION_TIMEOUT_SEC=60
  ```  
  → Verify: dev fallback khi `SQL_USE_FILTER_SERVICE=false` vẫn chạy postgres local.

- [x] **Task 7: Tests + deprecate `sql_writer_agent`**  
  - Port/update `tests/test_sql_writer_agent.py` → `tests/test_writer_agent.py`.  
  - Giữ `sql_writer_agent/` thin re-export hoặc xóa sau migration (1 PR).  
  → Verify: `pytest tests/test_writer_agent.py tests/test_filter_service_sql_client.py -v`.

---

## Tasks (filter-service — repo `agentic-filter-2`)

- [ ] **F1: Implement `POST /api/v1/sql/execute`** theo contract trên → Verify: curl 3 userId khác nhau, cùng SQL → rowCount / masked columns khác nhau.

- [ ] **F2: Entitlement check theo `queryScope` + cross-validate SQL** — check `SELECT` trên `queryScope.tables` trước; parse AST so khớp scope (`strictScopeMatch`) → Verify: bảng forbidden → 403; SQL thêm bảng lạ → `POLICY_VIOLATION`.

- [ ] **F3: Row filter injection** — policy per user/tenant → Verify: user A chỉ thấy rows tenant A.

- [ ] **F4: Column masking** — mask theo policy → Verify: `national_id` → `***` trong response.

- [ ] **F5: Seed permission test users** (reuse 3 user metadata test) → Verify: integration test trong `tests/test_sql_api.py`.

---

## Done When

- [ ] Supervisor dùng `writer_agent` sub-graph, không còn Neo4j trong luồng SQL.
- [ ] Production path: SQL **chỉ** qua filter-service khi `SQL_USE_FILTER_SERVICE=true`.
- [ ] User thiếu quyền `SELECT` nhận lỗi rõ ràng, không leak data.
- [ ] Cột nhạy cảm được mask; row filter áp dụng theo policy.
- [ ] Repair loop hoạt động với lỗi `EXECUTION_ERROR` từ filter-service.
- [ ] Unit tests pass; E2E manual: chat query → SQL + preview masked.

## Ghi chú

- **Metadata đủ JOIN**: `metadata_context` từ metadata agent đã gồm Neo4j paths — SQL Writer prompt chỉ cần `{metadata}`, không duplicate graph context.
- **`queryScope` bắt buộc**: mọi call `/sql/execute` phải khai báo bảng từ metadata session; filter-service không chỉ dựa parse SQL. Thiếu `queryScope` → `400 VALIDATION_ERROR`.
- **Build `query_scope`**: `supervisor/state.py` thêm field; `metadata_worker_node` set sau retriever; `build_query_scope()` map `expanded_tables` + `[COLUMN]` hits → `{ name, columns[] }`.
- **Placeholder userId**: reuse logic `dev-user` → `METADATA_TEST_USER_ID` từ `metadata_retrieval_client` (shared helper).
- **Giới hạn agent**: agent vẫn chỉ sinh `SELECT`; filter-service là lớp enforcement cuối (validate + rewrite).
- **Phase sau**: JWT bắt buộc; `POST /api/v1/sql/explain`; Oracle dialect.

## Phụ thuộc

- Filter-service metadata đã chạy (`FILTER_SERVICE_BASE_URL`)
- PostgreSQL sample data (`seed_postgres_data.py`) — **chỉ** filter-service connect trực tiếp DB, agentic-agri không cần `PG_*` khi filter bật
- Contract doc tham chiếu: [integrate-metadata-agent-with-filter-service.md](./integrate-metadata-agent-with-filter-service.md)
