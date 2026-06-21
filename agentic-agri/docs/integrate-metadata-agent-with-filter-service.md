## Mục tiêu

Không cho `metadata_agent` truy cập trực tiếp OpenSearch/Data Dictionary. Thay vào đó, mọi truy vấn metadata phải đi qua **filter-service** để:

- **Kiểm tra quyền truy cập dữ liệu theo user/tenant/role**
- **Cảnh báo** khi user cố truy cập resource trái phép
- **Tự động loại bỏ** (filter) các resource chưa được phân quyền trước khi trả dữ liệu về cho agent

Tài liệu này mô tả:

- Kiến trúc tích hợp
- Contract API giữa `agentic-agri` (metadata_agent) và filter-service
- Hướng dẫn triển khai + lưu ý vận hành

---

## Phạm vi

- Áp dụng cho luồng **metadata discovery** (TABLE/COLUMN/RELATIONSHIP) phục vụ SQL Writer.
- Không thay đổi contract FE/Chat SSE; thay đổi chỉ nằm ở lớp metadata retrieval.

---

## Tổng quan kiến trúc

### Hiện trạng

`metadata_agent/opensearch_client.py` gọi trực tiếp OpenSearch bằng hybrid search (BM25 + kNN embedding).

### Đích đến

`metadata_agent` gọi **HTTP API filter-service**. Filter-service thực hiện:

1. Xác thực user (JWT / mTLS / internal auth)
2. Ánh xạ user → policy/entitlements
3. Thực thi truy vấn (hoặc forward sang OpenSearch/DB khác)
4. Lọc kết quả theo policy
5. Trả về kết quả đã được “sanitize” + cảnh báo

---

## Luồng xử lý (Sequence)

1. User gửi câu hỏi “mô tả bảng CIF_CUSTOMERS…”
2. Supervisor route sang `metadata_worker_node`
3. `query_analyzer_node` sinh `search_strategy`
4. `opensearch_retriever_node` **gọi filter-service** với `search_strategy` + user context
5. Filter-service trả `raw_results` (đã filter)
6. `result_synthesizer_node` tổng hợp schema report
7. Supervisor nhận `final_output`/`metadata_context` → gửi về chat/telegram

---

## Contract API: Metadata Retrieval (filter-service)

Mục tiêu của contract này là **map 1-1** với các method hiện có trong
`src/universal_agent/metadata_agent/opensearch_client.py` để phía `agentic-agri`
chỉ cần thay “OpenSearch direct call” bằng “HTTP call”, **không phải sửa nhiều**
ở `metadata_agent/nodes.py`.

> Nguyên tắc: mỗi endpoint trả về payload tương đương dữ liệu mà các method
> OpenSearchClient đang trả về (list hits hoặc text đã format).

---

### Auth headers (áp dụng cho mọi endpoint)

- `Authorization`: `Bearer <jwt>` (khuyến nghị)
- `X-Request-Id`: string (khuyến nghị, để trace)
- `Content-Type`: `application/json`

> `userId` nên được lấy từ JWT. Tuy nhiên để dễ tích hợp với hệ thống hiện tại,
> request body vẫn cho phép truyền `userId`/`threadId` để audit.

---

### 1) Hybrid semantic search (tương đương `OpenSearchClient.hybrid_search`)

`POST /v1/metadata/hybrid-search`

#### Headers

- (xem “Auth headers”)

#### Request body

```json
{
  "userId": "dev-user",
  "threadId": "dev-user:market-trends",
  "query": "Tìm kiếm thông tin chi tiết về bảng CIF_CUSTOMERS...",
  "size": 10
}
```

#### Response 200

Trả về **list hits** (tương đương `OpenSearchClient.hybrid_search(...)` trả về).

```json
{
  "success": true,
  "data": {
    "hits": [
      {
        "_id": "doc-id",
        "_score": 12.34,
        "_source": {
          "record_type": "TABLE",
          "table_name": "CIF_CUSTOMERS",
          "column_name": null,
          "description": "..."
        }
      }
    ],
    "filtered": {
      "removedTables": ["CIF_SSN_MAPPING"],
      "removedColumns": ["CIF_CUSTOMERS.national_id"],
      "removedRelationships": []
    },
    "warnings": [
      {
        "code": "ACCESS_FILTERED",
        "message": "Một số resource không đủ quyền đã bị loại bỏ khỏi kết quả.",
        "details": { "count": 2 }
      }
    ],
    "debug": {
      "tookMs": 123,
      "queryMode": "hybrid",
      "index": "data_dictionary"
    }
  }
}
```

---

### 2) Keyword search (tương đương `OpenSearchClient.search_by_keyword`)

`POST /v1/metadata/keyword-search`

#### Request body

```json
{
  "userId": "dev-user",
  "threadId": "dev-user:market-trends",
  "query": "customer CIF",
  "size": 5
}
```

#### Response 200

```json
{
  "success": true,
  "data": { "hits": [] }
}
```

---

### 3) Get table metadata (tương đương `OpenSearchClient.get_table_metadata`)

`GET /v1/metadata/tables/{tableName}`

#### Query params

- `userId` (optional nếu lấy từ JWT)
- `threadId` (optional)

#### Response 200

```json
{
  "success": true,
  "data": { "hits": [] }
}
```

---

### 4) Get table schema / columns (tương đương `OpenSearchClient.get_table_schema`)

`GET /v1/metadata/tables/{tableName}/columns`

#### Response 200

```json
{
  "success": true,
  "data": { "hits": [] }
}
```

---

### 5) Get relationships (tương đương `OpenSearchClient.get_relationships`)

`POST /v1/metadata/relationships`

#### Request body

```json
{
  "userId": "dev-user",
  "threadId": "dev-user:market-trends",
  "tableNames": ["CIF_CUSTOMERS", "CIF_ACCOUNTS"],
  "size": 20
}
```

#### Response 200

```json
{
  "success": true,
  "data": { "hits": [] }
}
```

---

### 6) Format search results (tương đương `OpenSearchClient.format_search_results`)

Filter-service nên cung cấp thêm endpoint helper để trả về **chuỗi format**
`[TABLE] / [COLUMN] / [RELATIONSHIP]` giống format hiện tại, để agent không đổi prompt.

`POST /v1/metadata/format-results`

#### Request body

```json
{
  "hits": [
    { "_id": "doc-id", "_score": 1.2, "_source": { "record_type": "TABLE" } }
  ]
}
```

#### Response 200

```json
{
  "success": true,
  "data": {
    "rawResults": "[TABLE] ...\\n[COLUMN] ..."
  }
}
```

> Nếu muốn tối giản hơn nữa, có thể cho các endpoint (1)-(5) nhận param
> `format=raw` để trả luôn `rawResults` thay vì `hits`. Nhưng mặc định vẫn giữ `hits`
> để giữ tương thích 1-1 với OpenSearchClient.

---

## Error contract

Tất cả lỗi trả JSON:

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED|FORBIDDEN|VALIDATION_ERROR|UPSTREAM_ERROR|TIMEOUT",
    "message": "Human-readable message",
    "data": {}
  }
}
```

### Mã lỗi tối thiểu

- `UNAUTHORIZED` (401): thiếu/invalid token
- `FORBIDDEN` (403): user không có quyền query bất kỳ resource nào
- `VALIDATION_ERROR` (400): thiếu field, sai type, size vượt giới hạn
- `UPSTREAM_ERROR` (502): filter-service không gọi được OpenSearch/DB upstream
- `TIMEOUT` (504): quá thời gian xử lý (tổng hoặc upstream)

---

## Auth & Trust boundary

Khuyến nghị 2 lớp:

1. **JWT** từ Chat API (đến filter-service)
2. **mTLS / network policy** nội bộ (service-to-service)

Nếu filter-service dùng JWT, nên validate:

- chữ ký (issuer/audience)
- expiry
- claims: `sub` (userId), `tenantId`, `roles/scopes`

---

## Timeouts / Retries / Idempotency

- Client (`agentic-agri`) timeout đề xuất: **3–10s** cho `/metadata/search`.
- Retries: chỉ retry với lỗi mạng/502/504, backoff (200ms → 1s), tối đa 2 lần.
- Idempotency: request không tạo side-effect, không cần idempotency key.

---

## Logging & Audit (bắt buộc)

Filter-service nên log tối thiểu:

- `requestId`, `userId`, `threadId`, `channelId`
- `target_tables`, `record_types`
- số lượng hits trước/sau filter
- danh sách resource bị loại bỏ (giới hạn độ dài; có thể hash)

---

## Hướng dẫn triển khai trong `agentic-agri` (plan)

### A) Cấu hình

Thêm env:

- `FILTER_SERVICE_BASE_URL` (vd: `http://filter-service:8080`)
- `FILTER_SERVICE_TIMEOUT_SEC` (vd: `10`)

### B) Thay đổi điểm gọi

- Trong `metadata_agent/opensearch_client.py`, thay toàn bộ method gọi OpenSearch trực tiếp
  bằng call sang các endpoint tương ứng:
  - `hybrid_search` → `POST /v1/metadata/hybrid-search`
  - `search_by_keyword` → `POST /v1/metadata/keyword-search`
  - `get_table_metadata` → `GET /v1/metadata/tables/{tableName}`
  - `get_table_schema` → `GET /v1/metadata/tables/{tableName}/columns`
  - `get_relationships` → `POST /v1/metadata/relationships`
- Dùng `POST /v1/metadata/format-results` để tạo `raw_results` string (nếu cần),
  giữ nguyên prompt của `result_synthesizer_node`.

### C) Fallback

Trong môi trường dev, cho phép fallback direct OpenSearch khi `FILTER_SERVICE_BASE_URL` chưa set (tùy policy).

---

## Checklist nghiệm thu

- [ ] Khi user hỏi bảng “nhạy cảm”, filter-service loại cột/tables trái phép và trả warning
- [ ] Không còn bất kỳ call trực tiếp OpenSearch từ metadata_agent (prod)
- [ ] `result_synthesizer_node` vẫn chạy đúng (rawResults format giữ nguyên)
- [ ] Log audit có đầy đủ `userId/threadId/requestId`

