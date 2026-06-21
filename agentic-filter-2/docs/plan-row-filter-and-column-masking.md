# Row filter + masking COLUMN — phân tích & plan triển khai

## Mục tiêu
Triển khai `POST /api/v1/sql/execute` trong filter-service để **thực thi SELECT có kiểm soát**: kiểm quyền theo `queryScope`, **inject row filter** (vd. tenant/org) và **mask cột nhạy cảm** trước khi trả preview cho agent.

Nguồn contract: `agentic-agri/docs/plan-writer-agent-filter-service.md` (mục “Contract API: SQL Execution”).

---

## Phân tích kiến trúc & phương án xử lý

### 1) Ranh giới trách nhiệm (trust boundary)
- **Agent không được** execute SQL trực tiếp lên PostgreSQL (đúng như `db_executor_client.py` đang làm). Từ phase này, agent chỉ gửi SQL sang filter-service.
- **Filter-service không tin SQL**: luôn normalize + parse + validate trước khi gọi DB.
- **Filter-service không tin tuyệt đối `queryScope`**: coi đây là “khai báo dự kiến” (dựa metadata session), phải cross-check với kết quả parse AST.
- **Row filter & masking là server-side policy**: agent không được tự “bù” filter/mask. Agent chỉ bật/tắt bằng `options.*` nếu cho phép.

### 2) Chuỗi xử lý request → execute (happy-path)
1. Nhận request, resolve `userId` → user context (reuse flow trusted user như metadata).
2. **Normalize SQL** (tham khảo `agentic-agri/.../db_executor_client.py`):
   - strip code fence / markdown
   - chỉ cho 1 câu SQL, cấm `;` giữa câu
   - chỉ cho phép `SELECT`
   - enforce `LIMIT` mặc định + cap (vd. 1000)
3. **Fail-fast entitlement** dựa trên `queryScope`:
   - check `SELECT` trên `queryScope.tables[]`
   - nếu có `columns[]` → check quyền cột sớm (để quyết định mask/deny)
4. Parse SQL (SQLGlot) → trích `parsedTables`, `parsedColumns`.
5. **Strict scope match**:
   - nếu `strictScopeMatch=true` và SQL tham chiếu bảng/cột ngoài `queryScope` → `403 POLICY_VIOLATION` kèm details.
6. **Row filter injection** (khi `applyRowFilter=true`):
   - tính predicate từ user context (vd. `tenant_id = :ctx_tenant_id`)
   - rewrite SQL an toàn bằng AST hoặc wrap subquery (ưu tiên) để không phá logic query.
7. **Column masking** (khi `applyColumnMasking=true`):
   - xác định cột cần mask theo policy/resource id
   - ưu tiên rewrite SELECT để mask ở SQL expression; fallback post-process rows nếu an toàn.
8. Execute bằng runtime DB executor (PostgresSqlExecutor) với timeout.
9. Trả response theo contract: `executedSql`, `columns`, `rows`, `rowCount`, `filtered{...}`, `warnings[]`.

### 3) Chiến lược rewrite (allowRewrite)
- `allowRewrite=true`: filter-service được quyền rewrite SQL để đảm bảo enforcement (row filter + mask).
- Row filter:
  - **ưu tiên** wrap subquery rồi áp `WHERE` ngoài cùng (tránh sai lệch join/aggregation).
- Masking:
  - nếu có function mask trong DB → dùng expression trong SELECT
  - nếu chưa có → post-process sau fetch (nhưng phải cẩn thận không leak qua aggregate/sort).

### 4) Mapping lỗi cho agent
- `400 VALIDATION_ERROR`: SQL không phải SELECT / multi-statement / thiếu queryScope → agent có thể repair.
- `403 FORBIDDEN`: thiếu quyền SELECT → agent không repair.
- `403 POLICY_VIOLATION`: scope mismatch → agent không repair.
- `200 success:false` + `EXECUTION_ERROR`: lỗi runtime DB (syntax/column missing) → agent repair loop.
- `502/504`: upstream/timeout → báo lỗi hệ thống.

### 5) Policy nền (row filter & masking)
- Row filter:
  - xuất phát từ user context (tenant/org/branch/cost_center)
  - nên thiết kế thành “policy generator” độc lập để sau này mở rộng nhiều rule.
- Masking:
  - policy theo COLUMN resource id (hoặc theo naming conventions giai đoạn đầu)
  - loại mask: redact/full, last4, hash, null, partial.

---

## Plan (cuối cùng)

## Goal
Xây endpoint `/api/v1/sql/execute` enforce `queryScope`, inject row filter, mask column theo policy, và trả preview an toàn cho writer agent.

## Tasks
- [ ] **T1: Khai báo contract & router** (`app/api/sql.py`, `app/schemas/sql_contract.py`) → Verify: OpenAPI hiển thị `POST /api/v1/sql/execute` có đủ `userId/threadId/sql/dialect/limit/queryScope/options`.
- [ ] **T2: Normalize + validate SQL** (strip fences, 1 câu, SELECT-only, enforce LIMIT + cap) → Verify: unit test non-SELECT/multi-statement/missing queryScope trả đúng `400 VALIDATION_ERROR`.
- [ ] **T3: Fail-fast entitlement theo `queryScope`** (check `SELECT` bảng/cột) → Verify: bảng/cột forbidden trả `403 FORBIDDEN` và không gọi DB executor.
- [ ] **T4: Parse SQL + strict scope match** (SQLGlot extract tables/columns) → Verify: SQL tham chiếu bảng ngoài scope trả `403 POLICY_VIOLATION` kèm `declaredTables/parsedTables/undeclaredTables`.
- [ ] **T5: Row filter injection** (policy từ user context + rewrite an toàn) → Verify: cùng SQL nhưng 2 user khác tenant trả rowCount khác; `executedSql` có predicate đã tiêm.
- [ ] **T6: Column masking** (rewrite hoặc post-process) → Verify: response có `filtered.maskedColumns[]` + warning `COLUMN_MASKED` và dữ liệu đã bị mask.
- [ ] **T7: Execute + response shaping** (executedSql/rows/filtered/scopeMatch/warnings, map lỗi) → Verify: happy-path + execution-error-path chạy đúng theo contract.
- [ ] **T8: Smoke với `agri_agent`** (seed + gọi thật) → Verify: có ít nhất 1 query chạy ra preview đã row-filter + masked; mismatch scope fail-fast.

## Done When
- [ ] `/api/v1/sql/execute` enforce `queryScope` + `strictScopeMatch`, inject row filter, mask column, và không leak dữ liệu thô.
- [ ] Unit tests pass + smoke `agri_agent` chạy được.

## Tham chiếu
- API contract: `agentic-agri/docs/plan-writer-agent-filter-service.md`
- SQL normalization reference: `agentic-agri/src/universal_agent/sql_writer_agent/db_executor_client.py`
