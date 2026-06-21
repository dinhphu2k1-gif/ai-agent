# Phase 3 — Persistence & checkpoint

> **Ước lượng:** 2–3 ngày  
> **Phụ thuộc:** [phase-2-sse-core.md](./phase-2-sse-core.md)  
> **Tiếp theo:** [phase-4-production.md](./phase-4-production.md)  
> **DB:** [database-design.md](./database-design.md) (đọc trước)

## Goal

Lịch sử chat và run metadata sống sót sau restart API; LangGraph state trên Redis; hỗ trợ reconnect SSE (P1b).

## Phạm vi

| Trong scope | Ngoài scope |
|-------------|-------------|
| Migration schema `chat` | Attachments |
| Postgres repositories | JWT gateway đầy đủ (Phase 4) |
| Thay in-memory repos | `content.delta` |
| Redis `RedisSaver` khi `REDIS_URL` set | |
| `seed_chat_fixture.py` | |

## Tasks

### A. Migration & connection

- [x] **3.1** Tạo `scripts/migrations/chat/001_init.sql` — copy DDL từ [database-design.md](./database-design.md) / implementation plan §4.3.12

- [x] **3.2** `src/chat/db.py` — connection pool `psycopg2` hoặc `asyncpg` (chọn một, khớp FastAPI async nếu dùng async routes)  
  - Đọc `CHAT_DATABASE_URL`  
  → Verify: `psql -f 001_init.sql` → `\dt chat.*` liệt kê bảng

- [x] **3.3** Document tạo DB `agentic_chat` trên docker postgres (hoặc dùng `my_database` + schema `chat`)

  ```bash
  # Docker example
  docker exec -it <postgres_container> psql -U admin -c "CREATE DATABASE agentic_chat;"
  psql "postgresql://admin:password123@localhost:5432/agentic_chat" -f scripts/migrations/chat/001_init.sql
  \dt chat.*
  ```

### B. Repositories (Postgres)

- [x] **3.4** `PostgresChannelRepository` — `list_for_user` (P1b: JOIN members; P0 migration: all active channels)

- [x] **3.5** `PostgresThreadRepository` — `get_or_create(channel_id, user_id)` → `langgraph_thread_id`

- [x] **3.6** `PostgresMessageRepository`  
  - `insert_user_message`, `insert_agent_message`, `insert_prompt`  
  - `resolve_pending_prompts(thread_id)` — UPDATE status resolved (D2)  
  - `list_by_thread` paginated  
  - `finalize_agent_message(id, agent_data json)`

- [x] **3.7** `PostgresRunRepository`  
  - `create` status `queued` → `running` → `completed`/`failed`  
  - `get_active(thread_id)` → None hoặc run → 409  
  - `update_last_event_id`

- [x] **3.8** `PostgresRunEventRepository` (P1b) — `append`, `list_after(run_id, last_id)`

- [x] **3.9** Wire `deps.py` — chọn Postgres vs InMemory qua env `CHAT_USE_MEMORY=false` (default postgres khi URL set)

### C. RunService integration

- [x] **3.10** Refactor `RunService.start_run` — transaction:
  1. `resolve_pending_prompts`
  2. insert user message
  3. insert run `queued`
  4. commit
  5. stream (no transaction)

- [x] **3.11** On `message.end`: finalize agent message JSONB + `run.status = completed` + `finished_at`

- [x] **3.12** On `action.prompt`: insert message `sender=action_prompt`, `status=pending`, set `threads.pending_prompt_message_id`

- [x] **3.13** Persist each SSE event to `chat_run_events` (optional flag `CHAT_PERSIST_SSE_EVENTS=true`)

### D. Redis LangGraph checkpoint

- [x] **3.14** `supervisor/graph.py` — khi `REDIS_URL` có giá trị:

```python
from langgraph.checkpoint.redis import RedisSaver
# checkpointer = RedisSaver(redis_url=os.environ["REDIS_URL"])
```

Giữ `MemorySaver` fallback dev.

- [x] **3.15** Verify `thread_id` ổn định qua restart: POST → restart API → POST tiếp (HITL) vẫn nhớ context  
  → Verify: manual hoặc integration test với Redis container

### E. Reconnect endpoint (P1b)

- [x] **3.16** `GET /api/v1/chat/runs/{run_id}/stream`  
  - Query `lastEventId` hoặc header `Last-Event-ID`  
  - Replay từ `chat_run_events`  
  - Chỉ khi run `running` hoặc policy cho phép replay completed  
  → Verify: curl disconnect giữa chừng, reconnect nhận event sau `lastEventId`

### F. Seed & tests

- [x] **3.17** `scripts/seed_chat_fixture.py` — import golden conversation vào `chat_messages` cho `market-trends`

- [x] **3.18** `tests/test_chat_db_repositories.py` — pytest với Postgres testcontainer hoặc skip nếu `CHAT_DATABASE_URL` unset

- [x] **3.19** Update `tests/conftest.py` — fixture db session, truncate schema `chat` between tests

## Done when

- [x] Restart uvicorn — GET history vẫn có messages trước đó
- [x] Active run 409 enforced bởi DB unique index (không chỉ dict)
- [x] Redis enabled → graph state survive process restart
- [x] `seed_chat_fixture.py` chạy được sau migration
- [x] Phase 2 tests vẫn pass (repos swappable)

## Env (bổ sung)

```bash
CHAT_DATABASE_URL=postgresql://admin:password123@localhost:5432/agentic_chat
CHAT_USE_MEMORY=false
REDIS_URL=redis://localhost:6379/0
CHAT_PERSIST_SSE_EVENTS=true
```

## Tham chiếu

- [database-design.md](./database-design.md)
- [chat-sse-implementation-plan.md](../chat-sse-implementation-plan.md) §4.3, §5 Phase 3
- `src/universal_agent/supervisor/graph.py` — Redis scaffold comment
