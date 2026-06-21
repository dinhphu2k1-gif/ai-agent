# Phase 4 — Cứng hóa production

> **Ước lượng:** 2–4 ngày  
> **Phụ thuộc:** [phase-3-persistence.md](./phase-3-persistence.md)  
> **Tiếp theo:** [phase-5-backlog.md](./phase-5-backlog.md) (tùy product)

## Goal

API chat sẵn sàng môi trường staging/production: auth thật, ACL channel, rate limit, timeout, logging có `run_id`.

## Phạm vi

| Trong scope | Ngoài scope |
|-------------|-------------|
| JWT validation | Attachments |
| Channel ACL (`chat_channel_members`) | Token delta stream |
| HTTP 400/403/404/429 chuẩn | |
| Run timeout → SSE error | |
| Structured logging | |

## Tasks

### A. Authentication

- [x] **4.1** `middleware/auth.py` — parse JWT (PyJWT hoặc library team gateway)  
  - `CHAT_REQUIRE_AUTH=true` production  
  - Claims: `sub` → `user_id`  
  - 401 invalid/expired  
  → Verify: POST không token → 401; token hợp lệ → 200 stream

- [x] **4.2** `langgraph_thread_id` luôn `{user_id}:{channel_id}` khi auth bật (D1)

### B. Authorization

- [x] **4.3** Migration `002_channel_members.sql` hoặc mở rộng `001` — bảng `chat_channel_members`

- [x] **4.4** `ChannelRepository.list_for_user` — chỉ channel có membership

- [x] **4.5** `MessageService` / `RunService` — trước POST/GET: check user có quyền `participant` trên `channel_id`  
  - 403 nếu không  
  - 404 nếu channel không tồn tại (không leak existence nếu policy yêu cầu)

### C. Validation

- [x] **4.6** Pydantic validators chặt:  
  - `type: text` → `content` non-empty strip  
  - `type: action` → `actionId` + `label` required  
  - `replyToMessageId` tồn tại và thuộc thread  
  - `actionId` khớp prompt pending (nếu reply)  
  → Verify: POST `{}` → 422; empty content → 400

### D. Rate limit & concurrency

- [x] **4.7** Rate limit per `user_id` + `channel_id` (in-memory sliding window P0 prod, Redis P1)  
  - 429 + `Retry-After`  
  → Verify: burst > N requests → 429

- [x] **4.8** Đảm bảo 409 `RUN_IN_PROGRESS` body JSON consistent:

```json
{ "code": "RUN_IN_PROGRESS", "message": "..." }
```

### E. Timeout & errors

- [x] **4.9** `asyncio.wait_for` bọc stream generator — `CHAT_RUN_TIMEOUT_SEC` (default 60)  
  - Emit SSE `error` code `AGENT_TIMEOUT`  
  - Update run `failed` trong DB  
  → Verify: mock slow graph → timeout event

- [x] **4.10** Global exception handler — uncaught → `run.failed`, đóng stream sạch

### F. Observability

- [x] **4.11** Logging struct: `run_id`, `channel_id`, `user_id`, `thread_id` trên mọi log line trong RunService/Adapter

- [x] **4.12** *(Optional)* Sentry SDK — `capture_exception` trong except paths (không `print`)

- [x] **4.13** Deploy notes: nginx `proxy_buffering off`, `proxy_read_timeout` > run timeout

### G. Structured agent output (D4 partial)

- [x] **4.14** Mở rộng `PlannerDecision` hoặc mapper:  
  - `sql_result_preview` → SSE `table` + `action.buttons`  
  - Chỉ khi SQL writer đã populate state  
  → Verify: integration query trả table event (optional skip)

### H. Idempotency

- [x] **4.15** Header `Idempotency-Key` — unique `(thread_id, key)` trên `chat_runs`  
  - Trùng key → trả cùng `run_id` / replay stream policy (document: return 200 replay events hoặc 409)  
  → Verify: duplicate POST same key → không tạo 2 runs

## Done when

- [x] Staging deploy checklist pass: auth, ACL, 429, timeout, logs có correlation id
- [x] Security review: không log Bearer token, không SQL inject qua channel slug (parameterized queries)
- [x] `pytest` full chat tests pass với `CHAT_REQUIRE_AUTH=true` trong CI job tùy chọn

## Tham chiếu

- [chat-sse-be-spec.md](../chat-sse-be-spec.md) §7 Validation
- [chat-sse-implementation-plan.md](../chat-sse-implementation-plan.md) §5 Phase 4, §9 risks
