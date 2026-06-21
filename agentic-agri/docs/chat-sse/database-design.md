# Chat API — Thiết kế database (PostgreSQL)

> Dùng trong **Phase 3**. DDL: `scripts/migrations/chat/001_init.sql`  
> Tổng quan kế hoạch: [chat-sse-implementation-plan.md](../chat-sse-implementation-plan.md) §4.3

## Tách store

| Store | Công nghệ | Lưu gì |
|-------|-----------|--------|
| Chat DB | PostgreSQL schema `chat` | Messages, channels, runs |
| Graph checkpoint | Redis `RedisSaver` | LangGraph state — **không** trong bảng chat |
| Warehouse | `PG_*` / `core_banking` | SQL execution — **không** trộn |

## ER (rút gọn)

```mermaid
erDiagram
  chat_channels ||--o{ chat_threads : has
  chat_threads ||--o{ chat_messages : contains
  chat_threads ||--o{ chat_runs : executes
  chat_runs ||--o{ chat_run_events : streams
```

## Bảng chính

### `chat.chat_channels`

Catalog `GET /channels`. Seed 4 slug spec §2.2.

### `chat.chat_threads`

- Unique `(channel_id, user_id)`
- `langgraph_thread_id` = `{user_id}:{channel_id}` (D1)
- `pending_prompt_message_id` → FK message HITL pending

### `chat.chat_messages`

| `sender` | JSONB |
|----------|-------|
| `user` / `system` | `content` |
| `agent` | `agent_data` |
| `action_prompt` | `prompt_data` |

**Status:** `final`, `pending`, `resolved`, `streaming`, `failed`  
**Rule:** tối đa 1 `action_prompt` + `pending` / thread.

### `chat.chat_runs`

Status: `queued` → `running` → `completed` | `failed` | `cancelled`  
Unique partial index: một run `queued|running` / thread (409).

### `chat.chat_run_events` (P1b)

Replay SSE: `BIGSERIAL id` → header `Last-Event-ID`.

### `chat.chat_channel_members` (P1b RBAC)

`(channel_id, user_id, role)`.

### `chat.chat_attachments` (Phase 5)

P2 backlog.

## DDL

Xem file migration đầy đủ trong [phase-3-persistence.md](./phase-3-persistence.md) hoặc copy từ implementation plan §4.3.12.

Chạy:

```bash
psql "$CHAT_DATABASE_URL" -f scripts/migrations/chat/001_init.sql
```

## Repository methods (bắt buộc implement Phase 3)

| Method | Mục đích |
|--------|----------|
| `ThreadRepository.get_or_create(channel_id, user_id)` | Trước mỗi POST |
| `MessageRepository.resolve_pending_prompts(thread_id)` | D2 |
| `MessageRepository.list_by_thread(thread_id, page, size)` | GET history |
| `MessageRepository.finalize_agent_message(id, agent_data)` | Sau `message.end` |
| `RunRepository.create_run(...)`, `get_active(thread_id)` | 409 |
| `RunEventRepository.append(run_id, event, payload)` | SSE replay |

**Transaction:** persist user + create run trong transaction ngắn; SSE **ngoài** transaction.

## Env

```bash
CHAT_DATABASE_URL=postgresql://admin:password123@localhost:5432/agentic_chat
CHAT_DB_POOL_MIN=2
CHAT_DB_POOL_MAX=10
CHAT_RUN_TIMEOUT_SEC=60
CHAT_RUN_EVENTS_RETENTION_DAYS=7
```

## JSONB examples

`agent_data` và `prompt_data` khớp [chat-sse-be-spec.md](../chat-sse-be-spec.md) §3 — field names camelCase trong JSON (API layer), có thể snake_case trong DB nếu mapper rõ ràng.
