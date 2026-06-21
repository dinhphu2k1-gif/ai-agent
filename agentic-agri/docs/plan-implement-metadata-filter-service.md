# Plan triển khai: Metadata Agent ↔ Filter Service

## Goal

Chuyển `metadata_agent` từ gọi OpenSearch trực tiếp sang gọi **filter-service** (`agentic-filter-2`), lọc metadata theo quyền **`DESCRIBE` + `ALLOW`** (kế thừa cây resource), với khả năng **truyền `userId` để test** nhiều profile quyền mà không cần JWT (phase 1).

**Tài liệu tham chiếu**

| Repo | File |
|------|------|
| agentic-agri | [integrate-metadata-agent-with-filter-service.md](./integrate-metadata-agent-with-filter-service.md) |
| agentic-filter-2 | `docs/plan-integrate-metadata-agent.md` |

**Lưu ý đồng bộ contract:** filter-service dùng prefix **`/api/v1/metadata`**. Doc agentic-agri ghi `/v1/metadata` — client phải gọi đúng `/api/v1/metadata/...`.

**Hiện trạng code (2026-05):**

- **filter-service:** đã có `app/api/metadata.py`, schemas, `metadata_service.py`, test `tests/test_metadata_api.py`.
- **agentic-agri:** ✅ đã tích hợp `FilterServiceClient` + factory; truyền `userId`/`threadId` qua chat → supervisor → metadata subgraph.

---

## Kiến trúc sau triển khai

```text
Chat API (userId từ JWT / dev header)
  → SupervisorStreamAdapter (thread_id = userId:channelId)
    → metadata_worker_node
      → metadata subgraph (opensearch_retriever)
        → FilterServiceClient (HTTP)
          → filter-service /api/v1/metadata/*
            → OpenSearch + PDP DESCRIBE
```

---

## Phase 1 — Filter-service (agentic-filter-2)

Mục tiêu: endpoint ổn định, filter đúng policy, sẵn sàng cho agent gọi.

- [ ] **1.1 Xác nhận contract response khớp agent** → Verify: `POST /api/v1/metadata/hybrid-search` body `{"userId":"u1","query":"CIF_CUSTOMERS","size":5}` trả `success`, `data.hits[]` có `_id`, `_score`, `_source`; khi có lọc có `data.filtered` + `data.warnings`.
- [ ] **1.2 Hoàn thiện authorize DESCRIBE + kế thừa cha** (TABLE/COLUMN) theo §4 plan filter-service → Verify: user chỉ có `SELECT` không thấy metadata; user có `DESCRIBE` trên TABLE vẫn thấy cột con; `DENY` trên SCHEMA chặn nhánh con.
- [ ] **1.3 RELATIONSHIP pass-through** (không lọc quyền phase 1) → Verify: user không có DESCRIBE trên bảng liên quan vẫn nhận hit `record_type=RELATIONSHIP`.
- [ ] **1.4 `/format-results`** output giống `OpenSearchClient.format_search_results` → Verify: chuỗi có prefix `[TABLE]`, `[COLUMN]`, `[RELATIONSHIP]`.
- [ ] **1.5 Seed user + permission test** trong DB filter-service (ít nhất 3 user) → Verify: curl cùng query, 3 `userId` khác nhau → số `hits` / nội dung khác nhau.

**User test trên filter-service (không JWT):**

```bash
curl -s -X POST http://localhost:8080/api/v1/metadata/hybrid-search \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: test-req-1" \
  -d '{"userId":"analyst-gl","threadId":"analyst-gl:demo","query":"CIF_CUSTOMERS","size":10}'
```

---

## Phase 2 — Agentic-agri: HTTP client + cấu hình ✅

- [x] **2.1 Thêm env** — `src/universal_agent/config.py`, `env.example`:

  ```bash
  FILTER_SERVICE_BASE_URL=http://localhost:8080
  FILTER_SERVICE_TIMEOUT_SEC=10
  METADATA_USE_FILTER_SERVICE=true
  METADATA_TEST_USER_ID=
  ```

- [x] **2.2 `filter_service_client.py`** — map 1-1 endpoint `/api/v1/metadata/*`, parse `data.hits`, retry 502/504.

- [x] **2.3 Facade `create_metadata_retrieval_client()`** — `metadata_retrieval_client.py`: filter-service khi `METADATA_USE_FILTER_SERVICE=true` + URL; ngược lại `OpenSearchClient`.

**Files:** `filter_service_client.py`, `metadata_retrieval_client.py`, `config.py`

---

## Phase 3 — Truyền `userId` / `threadId` xuyên suốt graph ✅

- [x] **3.1** `MetadataState`: `user_id`, `thread_id`; `resolve_metadata_user_context()`.
- [x] **3.2** `metadata_worker_node` truyền context + `config` vào subgraph.
- [x] **3.3** `SupervisorStreamAdapter`: `configurable.user_id` + `thread_id`.
- [x] **3.4** `opensearch_retriever_node` dùng factory; sửa bug `unique_hits` dùng trước khi khai báo.

**Files:** `state.py`, `nodes.py`, `supervisor/nodes.py`, `supervisor_stream.py`

---

## Phase 4 — Option test `user_id` (dev / QA) ✅

| Cách | Trạng thái |
|------|------------|
| **A. Chat Bearer = userId** (dev, no JWT secret) | ✅ có sẵn |
| **B. `METADATA_TEST_USER_ID` env** | ✅ |
| **C. LangGraph `configurable`** | ✅ |
| **D. `X-Metadata-Test-User` header** | ✅ khi `API_ALLOW_TEST_USER_HEADER=true` |
| **E. curl filter-service** | ✅ (Phase 1) |

**Test nhanh agent:**

```bash
set METADATA_USE_FILTER_SERVICE=true
set FILTER_SERVICE_BASE_URL=http://localhost:8080
set METADATA_TEST_USER_ID=analyst-gl
pytest tests/test_filter_service_client.py tests/test_metadata_agent.py -v
```

---

## Phase 5 — Tests & nghiệm thu

- [x] **5.1 Unit (agentic-agri):** `tests/test_filter_service_client.py` — client parse, factory, retriever user context.
- [ ] **5.2 Integration (filter-service):** `tests/test_metadata_api.py` cover DESCRIBE deny/allow + 3 userId.
- [ ] **5.3 E2E (tùy chọn):** OpenSearch + filter DB seeded + chat query.
- [x] **5.4 Regression:** synthesizer prompt không đổi; format `[TABLE]/[COLUMN]/[RELATIONSHIP]` giữ local.

---

## Done when

- [x] Với `METADATA_USE_FILTER_SERVICE=true`, retriever dùng HTTP client (không gọi OpenSearch trực tiếp).
- [x] Mọi request metadata gửi **`userId`** (+ **`threadId`**) tới filter-service.
- [x] Dev có **≥2 cách** đổi `userId` (env + Bearer/configurable/header).
- [ ] User thiếu `DESCRIBE` không thấy TABLE/COLUMN — **cần verify E2E với filter-service + seed permission**.
- [ ] RELATIONSHIP pass-through — **verify trên filter-service**.
- [x] Log retriever in `userId`; filter-service log `requestId`/`userId` (phía filter-service).

---

## Bật tích hợp (local)

```bash
# .env
METADATA_USE_FILTER_SERVICE=true
FILTER_SERVICE_BASE_URL=http://localhost:8080
FILTER_SERVICE_TIMEOUT_SEC=10
# METADATA_TEST_USER_ID=analyst-gl
# API_ALLOW_TEST_USER_HEADER=true
```

Filter-service chạy riêng (`agentic-filter-2`); OpenSearch + catalog permission phải được seed trước khi test policy.

---

## Rủi ro / ghi chú

- **Prefix URL:** `/api/v1/metadata/...`
- **Telegram `main.py`:** dùng `METADATA_TEST_USER_ID` hoặc mở rộng `configurable` tương tự chat.
- **Phase sau:** JWT bắt buộc trên filter-service.
