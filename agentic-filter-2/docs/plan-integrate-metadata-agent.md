# Kế hoạch: Tích hợp `metadata_agent` với Filter Service

## 1) Mục tiêu (Goal)
Chuyển toàn bộ luồng **metadata discovery** (TABLE/COLUMN/RELATIONSHIP) của `metadata_agent` sang gọi **HTTP API của filter-service** (thay vì gọi OpenSearch/Data Dictionary trực tiếp). Filter-service chịu trách nhiệm:

- **Thực thi search/query metadata upstream** (OpenSearch hoặc data dictionary index)
- **Lọc kết quả theo quyền truy cập** dựa trên policy hiện có
- **Chuẩn hoá response** để phía `agentic-agri` thay `OpenSearch direct call` bằng `HTTP call` với thay đổi tối thiểu

Ràng buộc quan trọng:

- **Giai đoạn này không cần check token** (không bắt `Authorization`).
- Quyền để xem metadata phải dựa trên **`PermissionType = 'DESCRIBE'`** (gate ở mức TABLE).

## 2) Bối cảnh & ranh giới dịch vụ (Service boundaries)

### 2.1 Hiện trạng
`metadata_agent/opensearch_client.py` gọi trực tiếp OpenSearch để:

- hybrid search (BM25 + kNN)
- keyword search
- get table metadata / schema / relationships
- format kết quả thành chuỗi prompt-friendly

### 2.2 Đích đến
`metadata_agent` gọi filter-service (HTTP). Filter-service:

- Nhận “search strategy” + “user context”
- Gọi upstream OpenSearch
- Map mỗi hit → resource trong catalog (`resources` table)
- Kiểm tra quyền `DESCRIBE` (table-level)
- Loại bỏ hit không đủ quyền + trả warnings + thống kê filtered

### 2.3 Trust boundary trong giai đoạn “không check token”
Vì không validate token, **request phải chạy trong boundary tin cậy** (internal network / service-to-service). Request body/headers truyền `userId` chỉ mang tính “đầu vào tin cậy”. Ở phase sau sẽ chuyển sang JWT/mTLS và derive `userId` từ token.

## 3) Contract API (đề xuất) cho metadata retrieval
Mục tiêu là “map 1-1” với method trong `OpenSearchClient` để phía `agentic-agri` không cần sửa nhiều ở `metadata_agent/nodes.py`.

### 3.1 Endpoints
Đề xuất router mới: `app/api/metadata.py` với prefix `/api/v1/metadata`

- `POST /hybrid-search`
- `POST /keyword-search`
- `GET /tables/{tableName}`
- `GET /tables/{tableName}/columns`
- `POST /relationships`
- `POST /format-results`

### 3.2 Input (không check token)
Mỗi request **nên** có:

- `userId` (bắt buộc) — để authorize + audit/log
- `threadId` (tuỳ chọn) — trace theo hội thoại
- `X-Request-Id` hoặc `requestId` (tuỳ chọn) — correlation

## 4) Quy tắc authorization cho metadata (DESCRIBE + kế thừa đệ quy)
Đây là điểm thiết kế cốt lõi để tránh “metadata leakage”. Metadata **không** dùng `SELECT`/`INSERT`/…; chỉ chấp nhận quyền mô tả schema.

### 4.1 Điều kiện permission (bắt buộc)
Một user được xem metadata của một resource **chỉ khi** PDP trả quyết định **ALLOW** cho action metadata, tương đương:

| Thuộc tính | Giá trị bắt buộc | Ghi chú |
|------------|------------------|---------|
| `permission_types.name` | **`DESCRIBE`** | Khớp seed/catalog (`app/core/permission_actions.py`: TABLE có action `DESCRIBE`) |
| `permissions.effect` | **`ALLOW`** | Phân biệt với `DENY` |
| Nguồn gán quyền | effective qua user / group / role | Cùng bundle runtime hiện tại |

**Không đủ quyền** nếu:

- Không có bất kỳ permission `DESCRIBE` + `ALLOW` nào khớp trên chuỗi tổ tiên (xem §4.2), hoặc
- Có **`DESCRIBE` + `DENY`** trên **bất kỳ** node nào trong chuỗi tổ tiên (ưu tiên DENY — giống runtime §7.2), hoặc
- Resource không tồn tại trong catalog (`get_ancestor_resource_ids` rỗng → fail-closed).

### 4.2 Kiểm tra đệ quy theo cây resource (inheritance lên cha)
Catalog là cây 4 tầng (mỗi node có một `resources.id`):

```text
DATABASE (gốc)
  └── SCHEMA
        └── TABLE
              └── COLUMN (lá)
```

**Nguyên tắc:** permission có thể gán ở **bất kỳ** tầng; quyền trên **cha** áp dụng cho **con** khi kiểm tra metadata. Nếu **cột** chưa có permission `DESCRIBE` riêng, phải **leo lên** TABLE → SCHEMA → DATABASE cho đến khi gặp `DESCRIBE` + `ALLOW` hoặc hết chuỗi (mặc định deny).

Chuỗi tổ tiên (từ node đích lên gốc) — **đã có sẵn** trong `ResourceRepository.get_ancestor_resource_ids`:

| Node đích | Thứ tự duyệt (self → … → gốc) |
|-----------|-------------------------------|
| COLUMN | `column_id` → `table_id` → `schema_id` → `database_id` |
| TABLE | `table_id` → `schema_id` → `database_id` |
| SCHEMA | `schema_id` → `database_id` |
| DATABASE | `database_id` |

**Thuật toán cho một `target_resource_id` (metadata PDP):**

1. Load **permission bundle** của user (một lần/request): `PolicyRepository.load_permission_bundle` (user + group + role kế thừa).
2. Lấy `ancestor_ids = get_ancestor_resource_ids(target_resource_id)` — danh sách **chính node + mọi cha** tới DATABASE.
3. Gọi **`resolve_from_bundle(bundle, frozenset(ancestor_ids), action="DESCRIBE")`** (`app/services/permission_resolver.py`):
   - Lọc candidate: `permission_type_name == 'DESCRIBE'` **và** `resource_id ∈ ancestor_ids` **và** `effect == 'ALLOW'` (sau bước loại DENY).
   - Nếu có bất kỳ candidate `DENY` trên chuỗi → **DENY** (`explicit_deny`).
   - Nếu không có candidate `ALLOW` → **DENY** (`default_deny`).
   - Nếu có `ALLOW` → **ALLOW** (metadata không cần row filter / column mask cho phase này).
4. Metadata hit **visible** iff bước 3 là ALLOW.

**Khuyến nghị triển khai:** tái sử dụng `resolve_access(..., action="DESCRIBE")` trong `authorization_service.py` thay vì viết PDP metadata riêng — hành vi kế thừa đệ quy đã thống nhất với `/api/v1/runtime/authorize` và filter runtime.

**Ví dụ (COLUMN):**

- User chỉ được grant `DESCRIBE` + `ALLOW` trên **TABLE** `GL.CIF_CUSTOMERS`, không grant trên cột `national_id`.
- Hit metadata là cột `national_id` → `target_resource_id` = column resource.
- Ancestors gồm column + table + schema + database → match permission trên **table** → **ALLOW** → cột vẫn hiện trong metadata.

**Ví dụ (DENY trên cha):**

- `DESCRIBE` + `DENY` trên SCHEMA `GL` → mọi table/column dưới schema đó **không** xem metadata, dù có ALLOW trên table con (DENY ưu tiên trong `resolve_from_bundle`).

### 4.3 Áp dụng theo loại hit metadata
Sau khi map hit → `target_resource_id` (§5):

| Loại hit | `target_resource_id` khi check | Điều kiện visible |
|----------|-------------------------------|-------------------|
| **TABLE** | `resources.id` của TABLE | `resolve_access(..., DESCRIBE)` = ALLOW trên chuỗi tổ tiên của table |
| **COLUMN** | `resources.id` của **COLUMN** (không rút gọn chỉ check table) | Cùng thuật toán §4.2: nếu cột không có grant riêng, **tự động** kế thừa từ table/schema/database |
| **RELATIONSHIP** | **Không check permission** | **Mặc định cho phép (always visible)** sau khi upstream trả hit — không gọi `resolve_access`, không cần `DESCRIBE` |

### 4.3.1 Ngoại lệ RELATIONSHIP (mặc định allow)
- Hit `record_type = RELATIONSHIP` **luôn giữ lại** trong `hits` (không lọc theo policy).
- **Không** resolve catalog, **không** kiểm tra quyền trên `left_table` / `right_table`.
- Lý do: relationship là metadata mô tả liên kết; phase này ưu tiên đơn giản hoá pipeline và tránh false-negative khi index thiếu `schema`/`database` cho hai đầu bảng.
- Vẫn ghi log/metrics đếm số RELATIONSHIP pass-through (không tính vào `no_describe_permission`).
- **Phase sau (tuỳ chọn):** nếu cần siết chặt, có thể bật flag `METADATA_FILTER_RELATIONSHIPS=true` để quay lại rule “cả hai endpoint table đều DESCRIBE+ALLOW”.

### 4.4 Khái niệm “effective” (nguồn quyền)
“Effective” = tổng hợp permission từ:

- `user_permissions` (gán trực tiếp user)
- `group_permissions` (qua nhóm user thuộc)
- `role_permissions` (role gán trực tiếp + role kế thừa qua `group_roles`)

Một lần load bundle / request; mọi hit dùng chung bundle + cache snapshot (nếu bật) giống runtime.

## 5) Mapping hit → resource (Catalog resolution)
Muốn check quyền thì phải map metadata hit (OpenSearch `_source`) về resource id trong DB.

### 5.1 Chuẩn hoá field nguồn
Chuẩn hoá cách hiểu `_source` cho 3 loại hit:

- TABLE: `database_name`, `schema_name`, `table_name`
- COLUMN: `database_name`, `schema_name`, `table_name`, `column_name`
- RELATIONSHIP: tối thiểu `left_table`, `right_table` (+ schema nếu có)

### 5.2 Resolver
Implement resolver theo chain:

`database` → `schema` → `table` → `column`

Sử dụng `ResourceRepository` để tìm `resource_id` tương ứng.

### 5.3 Safe default
Nếu **không map được** resource (không có trong catalog), mặc định:

- **TABLE / COLUMN:** coi như **không được phép** và filter khỏi kết quả (safe-by-default); ghi log `no_catalog_mapping`.
- **RELATIONSHIP:** **không áp dụng** safe-default mapping — hit vẫn trả về (§4.3.1), vì không đi qua bước authorize.

## 6) Filter pipeline (thực thi upstream + lọc + response)

### 6.1 Upstream execution
Tận dụng cùng executor (OpenSearch client) đang phục vụ `/api/v1/filter/search` để tránh trùng lặp hạ tầng.

### 6.2 Pipeline
1. Load user context + permission bundle (theo `userId` trong body).
2. Gọi upstream search/lookup → lấy `hits[]`.
3. Với mỗi hit:
   - Nếu `record_type == RELATIONSHIP` → **keep** (bỏ qua bước authorize, §4.3.1).
   - Ngược lại (TABLE/COLUMN):
     - resolve sang `target_resource_id`
     - `decision = resolve_access(..., "DESCRIBE")` — kế thừa đệ quy §4.2
     - keep nếu `decision != DENY`; drop và ghi reason (`no_describe_permission`, `explicit_deny`, `unknown_resource`, …)
4. Trả response gồm:
   - `hits` đã filter
   - `filtered`: thống kê bị loại (table/column/relationship), ưu tiên count + sample bounded
   - `warnings`: ít nhất 1 warning `ACCESS_FILTERED` khi có loại bỏ
   - `debug`: `tookMs`, queryMode, index (chỉ bật ở dev hoặc khi có flag)

## 7) Formatter compatibility (giữ nguyên prompt)
Để không phải đổi prompt và nodes trong agent:

- `POST /format-results`: input `hits[]`, output `rawResults` dạng:
  - `[TABLE] ...`
  - `[COLUMN] ...`
  - `[RELATIONSHIP] ...`

Formatter **không làm auth** (vì auth đã xảy ra ở các endpoint retrieval).

## 8) Observability & vận hành

### 8.1 Logging tối thiểu
Structured logs theo request:

- `requestId`, `userId`, `threadId`
- `hits_total`, `hits_kept`, `hits_dropped`
- `dropped_reason_counts`: `no_catalog_mapping`, `no_describe_permission`

### 8.2 Metrics (tuỳ chọn)
- counter: `metadata_requests_total`
- counter: `metadata_filtered_total`
- histogram: `metadata_upstream_latency_ms`

## 9) Rủi ro & trade-offs
- **RELATIONSHIP không lọc quyền**: user có thể thấy tên bảng/liên kết trong relationship dù không có `DESCRIBE` trên table — chấp nhận theo yêu cầu phase này; siết lại bằng feature flag nếu cần.
- **Rủi ro map sai resource (TABLE/COLUMN)**: hit không đủ field → resolver fail → bị filter (fail-closed). Cần đảm bảo index metadata có đủ `database/schema/table/column`.
- **Chi phí authorize per-hit**: nếu mỗi hit gọi DB nhiều lần sẽ chậm. Nên:
  - cache resolver theo `(db, schema, table)` trong request scope
  - batch load permission bundle 1 lần / request
  - batch resolve table resources theo set table_names nếu cần
- **Chưa check token**: yêu cầu boundary tin cậy. Phase sau phải harden.

## 10) Danh sách công việc (Tasks) + cách verify

- [ ] **Tạo metadata router + endpoint skeleton (không check token)** → Verify: `GET /docs` thấy `/api/v1/metadata/...`; curl không cần `Authorization` vẫn 200.
- [ ] **Chuẩn hoá schema request/response cho từng endpoint** → Verify: payload tương thích với `OpenSearchClient` (hits hoặc rawResults).
- [ ] **Implement resolver hit → resource id** → Verify: TABLE/COLUMN map được `resources.id`; thiếu mapping bị loại; RELATIONSHIP không cần map vẫn giữ hit.
- [ ] **Implement metadata authorization (DESCRIBE + ALLOW + đệ quy cha)** → Verify:
  - user có `SELECT` + `ALLOW` nhưng **không** có `DESCRIBE` + `ALLOW` trên chuỗi tổ tiên → không thấy metadata
  - user có `DESCRIBE` + `ALLOW` **chỉ trên TABLE** (không grant COLUMN) → vẫn thấy metadata **cột con** (kế thừa từ table)
  - user có `DESCRIBE` + `DENY` trên SCHEMA cha → table/column dưới schema bị ẩn dù có ALLOW trên table
  - RELATIONSHIP: user **không** có `DESCRIBE` trên bảng liên quan → relationship **vẫn** xuất hiện trong `hits`
- [ ] **Implement filtering + warnings + summary** → Verify: response có `filtered.*` và `warnings` khi có loại bỏ.
- [ ] **Implement formatter `/format-results`** → Verify: output string match format hiện tại của agent.
- [ ] **Tích hợp phía `agentic-agri`** → Verify: khi set `FILTER_SERVICE_BASE_URL`, không còn call trực tiếp OpenSearch trong metadata_agent.

## 11) Tiêu chí nghiệm thu (Done when)
- [ ] `metadata_agent` gọi filter-service lấy metadata và được filter theo **`DESCRIBE` + `ALLOW`**, có **kế thừa từ cha** (column → table → schema → database).
- [ ] Cột không có grant riêng vẫn hiện khi table/schema/database cha có `DESCRIBE` + `ALLOW`; `DENY` trên cha chặn toàn bộ nhánh con (TABLE/COLUMN).
- [ ] Hit **RELATIONSHIP** luôn được giữ, không phụ thuộc `DESCRIBE`.
- [ ] Resource không đủ quyền bị loại và có cảnh báo `ACCESS_FILTERED`.
- [ ] Log/metrics tối thiểu có số hits trước/sau lọc và `userId/requestId` để trace.


