# Phase 1 — REST read-only + channel catalog

> **Ước lượng:** 1–2 ngày  
> **Phụ thuộc:** [phase-0-prep.md](./phase-0-prep.md)  
> **Tiếp theo:** [phase-2-sse-core.md](./phase-2-sse-core.md)

## Goal

FE gọi `GET /api/v1/chat/channels` và `GET /api/v1/chat/channels/{channelId}/messages` — thay mock local; persistence **in-memory** + fixture golden.

## Phạm vi

| Trong scope | Ngoài scope |
|-------------|-------------|
| Pydantic schemas khớp spec §3 | `POST` SSE |
| `InMemory*` repositories | Postgres |
| Auth stub (optional Bearer) | LangGraph invoke |

## Kiến trúc (phase này)

```
Router → Service → Repository (in-memory)
```

Không gọi `supervisor.graph.app` trong phase 1.

## Tasks

- [x] **1.1** `src/api/schemas/common.py` — `ApiResponse[T]`, `PageableResponse[T]` (`success`, `message`, `data`, `currentPage`, `totalItems`, `totalPages`)

- [x] **1.2** `src/api/schemas/chat.py` — models khớp [chat-sse-be-spec.md](../chat-sse-be-spec.md) §3:  
  `Message`, `MessageSender`, `AgentMessageData`, `ExecutionTraceStep`, `TableRow`, `ActionPromptData`, `Channel`

- [x] **1.3** `src/chat/repositories/channel_repository.py` — interface + `InMemoryChannelRepository`  
  Seed 4 channel (spec §2.2): `threat-intel`, `network-anomaly`, `insider-risk`, `market-trends`

- [x] **1.4** `src/chat/repositories/message_repository.py` — `InMemoryMessageRepository`  
  - Key: `channel_id` → list messages  
  - Seed fixture Q4 revenue conversation (spec §12 / mock `getInitialMessages`)  
  - Methods: `list_by_channel(channel_id, page, page_size)`, `channel_exists(id)`

- [x] **1.5** `src/chat/services/channel_service.py`, `message_service.py` — orchestration mỏng

- [x] **1.6** `src/api/routers/chat/channels.py` — `GET /api/v1/chat/channels` → `ApiResponse[list[Channel]]`

- [x] **1.7** `src/api/routers/chat/messages.py` — `GET /api/v1/chat/channels/{channel_id}/messages?page=1&pageSize=50`  
  - 404 nếu channel không tồn tại  
  - Pagination (page 1-based)

- [x] **1.8** `src/api/deps.py` — wire repositories (singleton in-memory cho dev)

- [x] **1.9** `src/api/middleware/auth.py` — nếu `CHAT_REQUIRE_AUTH=true` → 401 khi thiếu `Authorization: Bearer`; P0 default false, optional parse token stub → `user_id = "dev-user"`

- [x] **1.10** Register routers trong `app.py` prefix `/api/v1/chat`

- [x] **1.11** Tests:  
  - `tests/test_chat_api_channels.py` — list channels, shape fields  
  - `tests/test_chat_api_messages_history.py` — pagination, 404 unknown channel, agent message có `agentData`  
  → Verify: `pytest tests/test_chat_api_channels.py tests/test_chat_api_messages_history.py -v`

## API contract (tóm tắt)

```
GET /api/v1/chat/channels
GET /api/v1/chat/channels/{channelId}/messages?page=1&pageSize=50
```

Envelope: `ApiResponse` / `PageableResponse` — **không** dùng cho SSE sau này.

## Files tạo mới

```
src/api/
  deps.py
  middleware/auth.py
  schemas/common.py
  schemas/chat.py
  routers/chat/channels.py
  routers/chat/messages.py
src/chat/
  __init__.py
  repositories/channel_repository.py
  repositories/message_repository.py
  services/channel_service.py
  services/message_service.py
tests/
  test_chat_api_channels.py
  test_chat_api_messages_history.py
```

## Done when

- [x] `curl http://localhost:8080/api/v1/chat/channels` trả 4 channel
- [x] `curl ".../market-trends/messages?page=1&pageSize=50"` trả history có user + agent + action_prompt
- [x] `curl ".../unknown/messages"` → 404
- [x] Tests pass không cần OpenSearch/LLM

## Ghi chú cho FE

- `timestamp` trả ISO8601 (khuyến nghị), FE vẫn format local
- Một `action_prompt` với `status` logic in-memory: chỉ seed một pending trong fixture

## Tham chiếu

- [chat-sse-be-spec.md](../chat-sse-be-spec.md) §2, §3, §4.1–4.2
- [chat-sse-implementation-plan.md](../chat-sse-implementation-plan.md) §4.1 cấu trúc thư mục
