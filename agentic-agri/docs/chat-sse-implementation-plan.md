# Kế hoạch triển khai Backend — Chat Agent (SSE)

> **Phiên bản:** 2026-05-21  
> **Tham chiếu:** [CLAUDE.md](../CLAUDE.md), [chat-sse-be-spec.md](./chat-sse-be-spec.md)  
> **Trạng thái repo:** Chưa có HTTP API — runtime chính là Telegram (`src/main.py`) + LangGraph supervisor (`src/universal_agent/supervisor/graph.py`)

Tài liệu này là **kế hoạch triển khai** (who / what / when / how), không thay thế hợp đồng API trong `chat-sse-be-spec.md`.

### Tài liệu giao việc theo phase (dev)

| Phase | File chi tiết |
|-------|----------------|
| 0 | [chat-sse/phase-0-prep.md](./chat-sse/phase-0-prep.md) |
| 1 | [chat-sse/phase-1-rest-readonly.md](./chat-sse/phase-1-rest-readonly.md) |
| 2 | [chat-sse/phase-2-sse-core.md](./chat-sse/phase-2-sse-core.md) |
| 3 | [chat-sse/phase-3-persistence.md](./chat-sse/phase-3-persistence.md) |
| 4 | [chat-sse/phase-4-production.md](./chat-sse/phase-4-production.md) |
| 5 | [chat-sse/phase-5-backlog.md](./chat-sse/phase-5-backlog.md) |
| DB | [chat-sse/database-design.md](./chat-sse/database-design.md) |
| Index | [chat-sse/README.md](./chat-sse/README.md) |

---

## 1. Mục tiêu

| Mục tiêu | Mô tả |
|----------|--------|
| **Giao diện web** | FE chat (`/chat`, `/chat/:channelId`) gọi REST + SSE thay mock |
| **Tái sử dụng agent** | Cùng supervisor graph, checkpointer, HITL như Telegram |
| **Hợp đồng ổn định** | Message shape và event SSE khớp spec §3–§5 |
| **Vận hành** | Auth Bearer, một run active / channel, lỗi có event `error` / `run.failed` |

**Không nằm trong phạm vi P0:** upload attachment (§4.5), system message UI, tách POST/GET stream (§4.4).

---

## 2. Đánh giá khả thi (BFRI — áp dụng nguyên tắc layered backend)

Áp dụng khung BFRI từ backend guidelines, điều chỉnh cho Python/FastAPI (không phải Express).

| Chiều | Điểm (1–5) | Ghi chú |
|-------|------------|---------|
| Architectural fit | 4 | Thêm lớp HTTP tách khỏi graph; pattern routes → handlers → services → adapters đã có tiền lệ trong repo (nodes/graph) |
| Business logic complexity | 4 | Map LangGraph + HITL → SSE nhiều trạng thái; format `AgentMessageData` có thể cần LLM structured output |
| Data risk | 3 | Lịch sử chat + thread state; cần persistence và quyền channel |
| Operational risk | 3 | SSE dài, timeout LLM/OpenSearch; cần Redis checkpointer nếu scale |
| Testability | 4 | Mock graph + test SSE parser; fixture từ mock FE |

**BFRI ≈ (4+4) − (4+3+3) = 8 − 10 = −2 → thực tế sau khi tách phase: P0 chỉ in-memory + adapter đơn giản → ~4 (Moderate, tiến hành có test + giám sát).**

**Kết luận:** Triển khai theo **phase**, không big-bang. P0 chứng minh luồng end-to-end; P1 persistence + Redis; P2 attachment.

---

## 3. Hiện trạng codebase (anchor)

```mermaid
flowchart LR
  subgraph today [Hiện tại]
    TG[Telegram main.py]
    G[SupervisorGraph MemorySaver]
    OS[OpenSearch]
    LLM[LLM vLLM / Google]
    TG -->|thread_id = chat_id| G
    G --> OS
    G --> LLM
  end

  subgraph target [Mục tiêu]
    FE[Web Chat FE]
    API[FastAPI /api/v1/chat]
    FE --> API
    API --> G
  end
```

| Thành phần | Vị trí | Liên quan chat SSE |
|------------|--------|-------------------|
| Supervisor graph | `supervisor/graph.py` | `interrupt_before=["clarification_node"]` = HITL |
| State | `supervisor/state.py` | `user_input`, `message_to_user`, `final_output`, `investigation_log` |
| Telegram loop | `main.py` | `astream_events` + `get_state` — **mẫu map sang SSE** |
| Checkpointer | `MemorySaver` | Cần `thread_id` = `channelId` (hoặc `channelId:userId`) |
| Config | `universal_agent/config.py` | Mở rộng cho API host, JWT, Redis |
| HTTP | *Chưa có* | Thêm FastAPI + uvicorn |

**Mapping domain FE ↔ LangGraph:**

| FE (spec) | Runtime hiện tại |
|-----------|------------------|
| `channelId` | `configurable.thread_id` |
| User text | `user_input` + `investigation_log` |
| `action` / option | Resume HITL: `update_state` + `astream_events(None)` (như `main.py` L63–68) |
| `action_prompt` | `snapshot.next` chứa `clarification_node` + `message_to_user` |
| Execution trace | `on_chain_start` trong `astream_events` (`node_status_map`) |
| Agent answer | `final_output` (thường SQL markdown) → tách `paragraphs` / optional table |

---

## 4. Kiến trúc đích

### 4.1 Cấu trúc thư mục đề xuất

```
src/
├── api/                          # NEW — HTTP boundary
│   ├── app.py                    # FastAPI factory, lifespan
│   ├── deps.py                   # Auth, DB session, graph app singleton
│   ├── middleware/
│   │   └── auth.py               # Bearer JWT (hoặc stub P0)
│   ├── routers/
│   │   └── chat/
│   │       ├── channels.py       # GET /channels
│   │       └── messages.py       # GET history, POST + SSE
│   ├── schemas/
│   │   ├── common.py             # ApiResponse, PageableResponse
│   │   └── chat.py               # Message, AgentMessageData, POST body
│   └── streaming/
│       └── sse.py                # format_sse(event, data), heartbeat
├── chat/                         # NEW — domain (framework-agnostic)
│   ├── services/
│   │   ├── channel_service.py
│   │   ├── message_service.py
│   │   └── run_service.py        # concurrency, idempotency
│   ├── adapters/
│   │   └── supervisor_stream.py  # LangGraph → SSE events
│   ├── repositories/
│   │   ├── channel_repository.py
│   │   ├── message_repository.py   # P0: in-memory; P1: Postgres §4.3
│   │   ├── run_repository.py
│   │   ├── thread_repository.py
│   │   └── run_event_repository.py # P1b reconnect
│   └── mappers/
│       └── agent_message_mapper.py # final_output / state → agentData
└── universal_agent/              # existing — không đổi contract graph
```

**Nguyên tắc:** Router không gọi `app.astream_events` trực tiếp; chỉ `SupervisorStreamAdapter` / `RunService`.

### 4.2 Luồng request POST (happy path)

```mermaid
sequenceDiagram
  participant FE
  participant Router as messages.router
  participant RunSvc as RunService
  participant Adapter as SupervisorStreamAdapter
  participant LG as LangGraph app

  FE->>Router: POST /channels/{id}/messages + Bearer
  Router->>RunSvc: start_run(channelId, body)
  RunSvc->>RunSvc: lock channel, persist user msg
  Router-->>FE: 200 text/event-stream
  loop SSE
    RunSvc->>Adapter: stream_run(...)
    Adapter->>LG: astream_events / get_state
    Adapter-->>Router: ChatSseEvent
    Router-->>FE: event + data JSON
  end
```

### 4.3 Thiết kế database

Phần này mô tả **lưu trữ chat API** (lịch sử tin, channel, run). **Không** thay thế:

| Store | Vai trò | Công nghệ |
|-------|---------|-----------|
| **Chat DB** | Message history, channel catalog, run metadata, idempotency | PostgreSQL (schema `chat`) |
| **Graph checkpoint** | State LangGraph theo `thread_id` (HITL, investigation_log) | Redis (`RedisSaver`) — Phase 3 |
| **Data warehouse** | GL/CIF, SQL execution | PostgreSQL `core_banking` — đã có trong repo |

Tách DB chat khỏi warehouse tránh lock/contention và cho phép migrate độc lập. P0 dùng in-memory; P1 áp dụng schema dưới đây.

#### 4.3.1 Sơ đồ quan hệ (ER)

```mermaid
erDiagram
  chat_channels ||--o{ chat_threads : has
  chat_channels ||--o{ chat_channel_members : grants
  chat_threads ||--o{ chat_messages : contains
  chat_threads ||--o{ chat_runs : executes
  chat_runs ||--o{ chat_messages : produces
  chat_runs ||--o{ chat_run_events : streams
  chat_messages ||--o| chat_messages : replies_to
  chat_runs ||--o| chat_idempotency_keys : dedupes
  chat_channels ||--o{ chat_attachments : stores

  chat_channels {
    varchar id PK
    varchar title
    varchar icon
    varchar category
    boolean is_active
    timestamptz created_at
  }

  chat_threads {
    uuid id PK
    varchar channel_id FK
    varchar user_id
    varchar langgraph_thread_id UK
    timestamptz created_at
    timestamptz updated_at
  }

  chat_messages {
    uuid id PK
    uuid thread_id FK
    uuid run_id FK
    varchar sender
    text content
    jsonb agent_data
    jsonb prompt_data
    varchar status
    timestamptz created_at
    uuid reply_to_message_id FK
  }

  chat_runs {
    uuid id PK
    uuid thread_id FK
    varchar status
    varchar trigger_type
    jsonb request_payload
    varchar last_event_id
    timestamptz started_at
    timestamptz finished_at
    text error_code
  }
```

#### 4.3.2 Quy ước chung

| Quy ước | Giá trị |
|---------|---------|
| Schema PostgreSQL | `chat` (tách namespace, tránh trùng bảng warehouse) |
| PK message / run | `UUID` v4, expose ra API là string (`msg-...` hoặc raw UUID) |
| `channel_id` | `VARCHAR(64)` — slug URL (`threat-intel`, `market-trends`) |
| `user_id` | `VARCHAR(128)` — subject JWT hoặc `anonymous` (P0) |
| `langgraph_thread_id` | `{user_id}:{channel_id}` (D1) — unique per thread row |
| Timestamp API | `TIMESTAMPTZ` UTC; serialize ISO8601 cho FE |
| Payload phức tạp | `JSONB` — khớp `agentData` / `promptData` spec §3 |

#### 4.3.3 Bảng `chat.chat_channels`

Catalog channel cho `GET /channels`. Seed từ spec §2.2.

| Cột | Kiểu | Null | Mô tả |
|-----|------|------|--------|
| `id` | `VARCHAR(64)` | NO | PK — `channelId` URL |
| `title` | `VARCHAR(255)` | NO | Tên hiển thị |
| `icon` | `VARCHAR(64)` | NO | Material icon name |
| `category` | `VARCHAR(128)` | YES | Nhóm sidebar |
| `sort_order` | `INT` | NO | Default `0` |
| `is_active` | `BOOLEAN` | NO | Default `TRUE` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` |
| `updated_at` | `TIMESTAMPTZ` | NO | |

**Index:** PK (`id`), partial `(is_active, sort_order)` WHERE `is_active`.

#### 4.3.4 Bảng `chat.chat_channel_members` (P1 — RBAC)

| Cột | Kiểu | Mô tả |
|-----|------|--------|
| `channel_id` | `VARCHAR(64)` FK → `chat_channels` | |
| `user_id` | `VARCHAR(128)` | |
| `role` | `VARCHAR(32)` | `viewer` \| `participant` \| `admin` |
| `created_at` | `TIMESTAMPTZ` | |

**PK:** `(channel_id, user_id)`. **Rule:** `GET /channels` chỉ trả channel user có membership (hoặc public channel flag — mở rộng sau).

#### 4.3.5 Bảng `chat.chat_threads`

Một user × một channel = một conversation + một LangGraph thread.

| Cột | Kiểu | Null | Mô tả |
|-----|------|------|--------|
| `id` | `UUID` | NO | PK nội bộ |
| `channel_id` | `VARCHAR(64)` | NO | FK |
| `user_id` | `VARCHAR(128)` | NO | |
| `langgraph_thread_id` | `VARCHAR(256)` | NO | Unique — truyền vào `configurable.thread_id` |
| `pending_prompt_message_id` | `UUID` | YES | FK → `chat_messages` — prompt HITL đang chờ (D2) |
| `created_at` | `TIMESTAMPTZ` | NO | |
| `updated_at` | `TIMESTAMPTZ` | NO | |

**Unique:** `(channel_id, user_id)`, `(langgraph_thread_id)`.

**Repository:** `get_or_create_thread(channel_id, user_id)` trước mỗi POST.

#### 4.3.6 Bảng `chat.chat_messages`

Lưu đủ shape `Message` cho `GET .../messages` — không cần re-stream SSE để xem lại.

| Cột | Kiểu | Null | Mô tả |
|-----|------|------|--------|
| `id` | `UUID` | NO | PK — `messageId` SSE/API |
| `thread_id` | `UUID` | NO | FK |
| `run_id` | `UUID` | YES | FK — run sinh ra message (user msg gắn run kích hoạt) |
| `sender` | `VARCHAR(32)` | NO | `user` \| `agent` \| `system` \| `action_prompt` |
| `content` | `TEXT` | YES | User/system plain text |
| `agent_data` | `JSONB` | YES | `AgentMessageData` khi `sender = agent` |
| `prompt_data` | `JSONB` | YES | `ActionPromptData` khi `sender = action_prompt` |
| `status` | `VARCHAR(32)` | NO | Xem §4.3.8 |
| `reply_to_message_id` | `UUID` | YES | FK self — `replyToMessageId` từ POST |
| `client_request_id` | `VARCHAR(64)` | YES | Idempotency / optimistic UI |
| `created_at` | `TIMESTAMPTZ` | NO | Thứ tự timeline |
| `updated_at` | `TIMESTAMPTZ` | YES | Khi stream hoàn tất / patch JSONB |

**Index:**

- `(thread_id, created_at DESC)` — pagination history
- `(thread_id, sender, status)` WHERE `sender = 'action_prompt' AND status = 'pending'` — enforce một prompt pending
- `(run_id)` — lookup theo run

**Map JSONB → API:**

```json
// agent_data
{
  "executionTrace": [{ "title": "...", "description": "...", "icon": "search" }],
  "paragraphs": ["..."],
  "tableHeader": "optional",
  "tableRows": [{ "region": "...", "actual": "...", "projected": "...", "variance": "...", "isPositive": true }],
  "actionButtons": [{ "label": "...", "icon": "...", "actionId": "..." }]
}

// prompt_data
{
  "title": "...",
  "description": "...",
  "options": [{ "label": "...", "actionId": "..." }],
  "customOptionLabel": "optional",
  "expectsTextInput": false
}
```

**Ghi chú streaming P1:** Trong lúc SSE, adapter có thể chỉ cập nhật Redis/memory; khi `message.end`, `MessageRepository.finalize_agent_message(id, agent_data)` ghi một lần vào JSONB (hoặc merge incremental nếu cần `content.delta`).

#### 4.3.7 Bảng `chat.chat_runs`

Một POST → một run; hỗ trợ 409, reconnect, audit.

| Cột | Kiểu | Null | Mô tả |
|-----|------|------|--------|
| `id` | `UUID` | NO | PK — `runId` |
| `thread_id` | `UUID` | NO | FK |
| `status` | `VARCHAR(32)` | NO | `queued` \| `running` \| `completed` \| `failed` \| `cancelled` |
| `trigger_type` | `VARCHAR(16)` | NO | `text` \| `action` |
| `request_payload` | `JSONB` | NO | Body POST (redact secrets) |
| `user_message_id` | `UUID` | YES | FK — tin user đã lưu |
| `agent_message_id` | `UUID` | YES | FK — tin agent/prompt chính |
| `last_event_id` | `VARCHAR(64)` | YES | SSE `id:` cuối — reconnect |
| `idempotency_key` | `VARCHAR(128)` | YES | Header `Idempotency-Key` |
| `started_at` | `TIMESTAMPTZ` | NO | |
| `finished_at` | `TIMESTAMPTZ` | YES | |
| `error_code` | `VARCHAR(64)` | YES | `AGENT_TIMEOUT`, `RUN_FAILED`, ... |
| `error_message` | `TEXT` | YES | |

**Index:**

- `(thread_id, status)` WHERE `status IN ('queued','running')` — **tối đa một run active** / thread (409)
- Unique `(thread_id, idempotency_key)` WHERE `idempotency_key IS NOT NULL`

**State machine:**

```mermaid
stateDiagram-v2
  [*] --> queued: POST accepted
  queued --> running: SSE opened
  running --> completed: message.end
  running --> failed: error / run.failed
  running --> cancelled: client disconnect policy
  failed --> [*]
  completed --> [*]
```

#### 4.3.8 Trạng thái `chat_messages.status`

| `status` | `sender` | Ý nghĩa |
|----------|----------|---------|
| `final` | user, agent, system | Hiển thị lịch sử |
| `pending` | action_prompt | Đang chờ user — **tối đa 1** / `thread_id` |
| `resolved` | action_prompt | User đã trả lời — ẩn khỏi UI (FE cũng xóa local) |
| `streaming` | agent | Đang SSE (optional; P1 có thể chỉ dùng in-memory đến `final`) |
| `failed` | agent | Run lỗi; có thể có `agent_data` partial |

**Rule D2 (DB):** Khi POST mới:

1. `UPDATE chat_messages SET status = 'resolved' WHERE thread_id = ? AND sender = 'action_prompt' AND status = 'pending'`
2. `UPDATE chat_threads SET pending_prompt_message_id = NULL`
3. Insert user message + tạo run

#### 4.3.9 Bảng `chat.chat_run_events` (khuyến nghị P1 — reconnect SSE)

Lưu từng event SSE để `Last-Event-ID` replay (spec §5.6).

| Cột | Kiểu | Mô tả |
|-----|------|--------|
| `id` | `BIGSERIAL` | PK — map sang SSE `id:` |
| `run_id` | `UUID` FK | |
| `event_name` | `VARCHAR(64)` | `trace.step`, `content.delta`, ... |
| `payload` | `JSONB` | Một dòng JSON |
| `created_at` | `TIMESTAMPTZ` | |

**Index:** `(run_id, id)`. **Retention:** xóa event > 7 ngày hoặc sau khi run `completed` + TTL (job cron).

**P0:** Bỏ qua bảng này; reconnect không supported.

#### 4.3.10 Bảng `chat.chat_idempotency_keys` (tùy chọn)

Nếu không muốn cột trên `chat_runs`:

| Cột | Kiểu |
|-----|------|
| `idempotency_key` | `VARCHAR(128)` PK |
| `thread_id` | `UUID` |
| `run_id` | `UUID` |
| `response_snapshot` | `JSONB` |
| `expires_at` | `TIMESTAMPTZ` |

TTL 24h.

#### 4.3.11 Bảng `chat.chat_attachments` (P2)

| Cột | Kiểu | Mô tả |
|-----|------|--------|
| `id` | `UUID` PK | `attachmentId` |
| `channel_id` | `VARCHAR(64)` | |
| `thread_id` | `UUID` | |
| `uploader_id` | `VARCHAR(128)` | |
| `file_name` | `VARCHAR(512)` | |
| `mime_type` | `VARCHAR(128)` | |
| `size_bytes` | `BIGINT` | |
| `storage_path` | `TEXT` | S3/local path |
| `created_at` | `TIMESTAMPTZ` | |

Bảng nối `chat_message_attachments(message_id, attachment_id)` nếu một tin nhiều file.

#### 4.3.12 DDL tham chiếu (PostgreSQL 16)

File migration đề xuất: `scripts/migrations/chat/001_init.sql`

```sql
CREATE SCHEMA IF NOT EXISTS chat;

CREATE TABLE chat.chat_channels (
    id              VARCHAR(64) PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    icon            VARCHAR(64) NOT NULL DEFAULT 'chat',
    category        VARCHAR(128),
    sort_order      INT NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chat.chat_threads (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id                  VARCHAR(64) NOT NULL REFERENCES chat.chat_channels(id),
    user_id                     VARCHAR(128) NOT NULL,
    langgraph_thread_id         VARCHAR(256) NOT NULL,
    pending_prompt_message_id   UUID,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_thread_user_channel UNIQUE (channel_id, user_id),
    CONSTRAINT uq_langgraph_thread UNIQUE (langgraph_thread_id)
);

CREATE TABLE chat.chat_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id           UUID NOT NULL REFERENCES chat.chat_threads(id) ON DELETE CASCADE,
    status              VARCHAR(32) NOT NULL,
    trigger_type        VARCHAR(16) NOT NULL,
    request_payload     JSONB NOT NULL DEFAULT '{}',
    user_message_id     UUID,
    agent_message_id    UUID,
    last_event_id       VARCHAR(64),
    idempotency_key     VARCHAR(128),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ,
    error_code          VARCHAR(64),
    error_message       TEXT,
    CONSTRAINT chk_run_status CHECK (
        status IN ('queued','running','completed','failed','cancelled')
    )
);

CREATE UNIQUE INDEX uq_run_active_per_thread
    ON chat.chat_runs (thread_id)
    WHERE status IN ('queued', 'running');

CREATE UNIQUE INDEX uq_run_idempotency
    ON chat.chat_runs (thread_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE chat.chat_messages (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id               UUID NOT NULL REFERENCES chat.chat_threads(id) ON DELETE CASCADE,
    run_id                  UUID REFERENCES chat.chat_runs(id) ON DELETE SET NULL,
    sender                  VARCHAR(32) NOT NULL,
    content                 TEXT,
    agent_data              JSONB,
    prompt_data             JSONB,
    status                  VARCHAR(32) NOT NULL DEFAULT 'final',
    reply_to_message_id     UUID REFERENCES chat.chat_messages(id) ON DELETE SET NULL,
    client_request_id       VARCHAR(64),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ,
    CONSTRAINT chk_sender CHECK (
        sender IN ('user','agent','system','action_prompt')
    ),
    CONSTRAINT chk_message_status CHECK (
        status IN ('final','pending','resolved','streaming','failed')
    ),
    CONSTRAINT chk_payload_shape CHECK (
        (sender IN ('user','system') AND agent_data IS NULL AND prompt_data IS NULL)
        OR (sender = 'agent' AND agent_data IS NOT NULL)
        OR (sender = 'action_prompt' AND prompt_data IS NOT NULL)
        OR (sender = 'user')
    )
);

CREATE INDEX idx_messages_thread_created
    ON chat.chat_messages (thread_id, created_at DESC);

CREATE INDEX idx_messages_pending_prompt
    ON chat.chat_messages (thread_id)
    WHERE sender = 'action_prompt' AND status = 'pending';

ALTER TABLE chat.chat_threads
    ADD CONSTRAINT fk_pending_prompt
    FOREIGN KEY (pending_prompt_message_id)
    REFERENCES chat.chat_messages(id) ON DELETE SET NULL;

ALTER TABLE chat.chat_runs
    ADD CONSTRAINT fk_run_user_message
    FOREIGN KEY (user_message_id) REFERENCES chat.chat_messages(id) ON DELETE SET NULL;

ALTER TABLE chat.chat_runs
    ADD CONSTRAINT fk_run_agent_message
    FOREIGN KEY (agent_message_id) REFERENCES chat.chat_messages(id) ON DELETE SET NULL;

CREATE TABLE chat.chat_run_events (
    id              BIGSERIAL PRIMARY KEY,
    run_id          UUID NOT NULL REFERENCES chat.chat_runs(id) ON DELETE CASCADE,
    event_name      VARCHAR(64) NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_run_events_run_id ON chat.chat_run_events (run_id, id);

-- Seed channels (spec §2.2)
INSERT INTO chat.chat_channels (id, title, icon, category, sort_order) VALUES
    ('threat-intel', 'threat-intel-global', 'shield', 'Active Channels', 10),
    ('network-anomaly', 'network-anomaly-detect', 'hub', 'Active Channels', 20),
    ('insider-risk', 'insider-risk-alerts', 'person_alert', 'Active Channels', 30),
    ('market-trends', 'Market Trends', 'trending_up', NULL, 0)
ON CONFLICT (id) DO NOTHING;
```

#### 4.3.13 Repository ↔ API (truy vấn chính)

| Use case | Repository method | SQL / ghi chú |
|----------|-------------------|---------------|
| List channels | `ChannelRepository.list_for_user(user_id)` | JOIN `chat_channel_members` hoặc all active P0 |
| History | `MessageRepository.list_by_thread(thread_id, page, size)` | `ORDER BY created_at DESC LIMIT/OFFSET` |
| Start POST | `RunService.start_run` | Transaction: resolve prompts → insert user msg → insert run `queued` → commit → stream |
| Active run check | `RunRepository.get_active(thread_id)` | `status IN ('queued','running')` → 409 |
| Finalize agent | `MessageRepository.update_agent_data(id, jsonb)` | `status = 'final'` |
| Save prompt | `MessageRepository.insert_prompt(...)` | `status = 'pending'` + set `threads.pending_prompt_message_id` |
| Reconnect | `RunEventRepository.list_after(run_id, last_id)` | `id > ? ORDER BY id` |

**Transaction boundary:** Một POST nên bọc “persist user + create run” trong transaction ngắn; SSE stream **ngoài** transaction (tránh giữ lock lâu).

#### 4.3.14 Seed & fixture

| Nguồn | Mục đích |
|-------|----------|
| `INSERT` channels §4.3.12 | Menu sidebar |
| Script `scripts/seed_chat_fixture.py` | Import golden conversation từ spec §12 vào `chat_messages` cho dev/CI |
| `tests/conftest.py` | DB test container hoặc SQLite in-memory *chỉ unit* — integration dùng Postgres |

#### 4.3.15 Lộ trình DB theo phase

| Phase | Persistence |
|-------|-------------|
| **P0** | `InMemoryMessageRepository` — không migration |
| **P1** | Chạy `001_init.sql`; `PostgresMessageRepository` + connection pool |
| **P1b** | `chat_channel_members`, `chat_run_events` |
| **P2** | `chat_attachments`, retention job `chat_run_events` |

#### 4.3.16 Cấu hình kết nối (bổ sung §7)

```bash
# Chat persistence (schema chat) — có thể cùng instance Postgres, khác database
CHAT_DATABASE_URL=postgresql://admin:password123@localhost:5432/agentic_chat
# hoặc dùng chung my_database:
# CHAT_DATABASE_URL=postgresql://admin:password123@localhost:5432/my_database

CHAT_DB_POOL_MIN=2
CHAT_DB_POOL_MAX=10
CHAT_RUN_TIMEOUT_SEC=60
CHAT_RUN_EVENTS_RETENTION_DAYS=7
```

**Không** nhầm với `PG_*` / `core_banking` dùng cho SQL writer execution.

---

## 5. Phân phase triển khai

> Chi tiết task, file paths, verify criteria: xem từng file trong [docs/chat-sse/](./chat-sse/README.md).

### Phase 0 — Chuẩn bị (0.5–1 ngày)

→ **[phase-0-prep.md](./chat-sse/phase-0-prep.md)**

| # | Việc | Deliverable |
|---|------|-------------|
| 0.1 | Thêm dependency: `fastapi`, `uvicorn[standard]`, `python-multipart` (P2) | `pyproject.toml` |
| 0.2 | Entrypoint: `python -m api` hoặc `uvicorn api.app:app` | `src/api/app.py` |
| 0.3 | Health: `GET /health` | Smoke deploy |
| 0.4 | CORS cho `VITE_APP_API_URL` origin | Config env |
| 0.5 | Document env mới: `API_HOST`, `API_PORT`, `CHAT_JWT_SECRET` (optional P0) | `.env.example` |

**Tiêu chí xong:** Server chạy độc lập Telegram; không đổi graph.

---

### Phase 1 — REST read-only + channel catalog (1–2 ngày)

→ **[phase-1-rest-readonly.md](./chat-sse/phase-1-rest-readonly.md)**

| # | API | Logic |
|---|-----|--------|
| 1.1 | `GET /api/v1/chat/channels` | Trả danh sách channel (P0: static map từ spec §2.2; P1: DB + RBAC) |
| 1.2 | `GET /api/v1/chat/channels/{channelId}/messages` | Pagination `page`, `pageSize`; envelope `ApiResponse` / `PageableResponse` |
| 1.3 | Pydantic schemas | Khớp `Message`, `AgentMessageData`, `ActionPromptData` (spec §3) |
| 1.4 | Auth middleware P0 | Bearer optional hoặc fixed dev token; 401 nếu thiếu khi bật |

**Persistence P0:** `InMemoryMessageRepository` — seed fixture từ mô tả `getInitialMessages()` (spec §12) để FE integration sớm.

**Tiêu chí xong:** FE load channel + history không mock local.

**Test:** `pytest tests/test_chat_api_channels.py`, `test_chat_api_messages_history.py` (TestClient, không LLM).

---

### Phase 2 — POST + SSE core (3–5 ngày) — **critical path**

→ **[phase-2-sse-core.md](./chat-sse/phase-2-sse-core.md)**

#### 2.1 `RunService`

- `thread_id = f"{user_id}:{channel_id}"` hoặc `channel_id` nếu single-tenant P0.
- **409 `RUN_IN_PROGRESS`:** dict in-memory `active_runs[channel_id]`.
- **Idempotency:** header `Idempotency-Key` → cache response run_id (optional P1).
- Persist user message trước khi stream; emit `user.ack` với `messageId` thật.

#### 2.2 `SupervisorStreamAdapter`

Bảng map sự kiện LangGraph → SSE (bổ sung spec §5.3):

| SSE event | Nguồn |
|-----------|--------|
| `run.start` | Đầu `astream_events` |
| `user.ack` | Sau khi lưu user message |
| `message.start` | Trước khi stream agent output |
| `trace.step` | `on_chain_start` + `node_status_map` (tái dùng `main.py`) |
| `content.delta` | *Optional P1* — token stream từ worker LLM |
| `content.paragraph` | Khi có đoạn text hoàn chỉnh (planner reasoning / final_output chunk) |
| `table` | *P1* — parse từ `sql_result_preview` hoặc structured tool output |
| `action.buttons` | *P1* — planner/tool định nghĩa `actionId` |
| `action.prompt` | `get_state`: `clarification_node` in `snapshot.next` → `promptData` từ `message_to_user` + options (cần mở rộng planner hoặc map tạm 1 option “Trả lời tự do”) |
| `message.end` | Sau `final_output` hoặc sau khi emit prompt |
| `error` / `run.failed` | Exception, timeout, parse JSON planner fail |

**Input graph:**

```python
# Text mới (giống main.py L72-75)
current_input = {
    "user_input": content,
    "investigation_log": [f"Nhận yêu cầu: {content}"],
}

# HITL resume (giống main.py L63-68)
if snapshot.next and "clarification_node" in snapshot.next:
    app.update_state(config, {"investigation_log": [f"Người dùng trả lời (HITL): {label}"]})
    current_input = None
```

**`type: action`:** map `actionId` → text gửi vào `investigation_log`; `replyToMessageId` validate với prompt pending.

#### 2.3 Router `POST /channels/{channelId}/messages`

- `Accept: text/event-stream` → `StreamingResponse` generator async.
- Headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive`.
- Mỗi chunk: `sse.format_sse("trace.step", payload)` + `id:` monotonic (reconnect P1).
- **Không** bọc body trong `ApiResponse`.

#### 2.4 `AgentMessageMapper`

P0 tối thiểu:

- `final_output` → một phần tử `paragraphs[]`.
- Nếu chứa khối SQL fenced → paragraph riêng + `executionTrace` bước `sql_writer_worker_node`.
- HITL: `message_to_user` → `action.prompt` với `options[]` sinh từ parser đơn giản hoặc single free-text option.

P1: structured `PlannerDecision` mở rộng field `ui_options: list[{label, actionId}]` để khớp mock FE.

**Tiêu chí xong:** FE gửi text → nhận đủ chuỗi event §5.5; HITL hiện `action.prompt`; trả lời tiếp → resume graph.

**Test:**

- Unit: `SupervisorStreamAdapter` với graph mock / recorded events.
- Integration: `tests/test_chat_sse_integration.py` — mock LLM hoặc skip nếu không có vLLM (pattern các test hiện có).

---

### Phase 3 — Persistence & checkpoint (2–3 ngày)

→ **[phase-3-persistence.md](./chat-sse/phase-3-persistence.md)** · DB: **[database-design.md](./chat-sse/database-design.md)**

> **Schema chi tiết:** §4.3 Thiết kế database (bản đầy đủ cũng trong `database-design.md`)

| # | Việc |
|---|------|
| 3.1 | Migration `scripts/migrations/chat/001_init.sql` — schema `chat` (§4.3.12) |
| 3.2 | `PostgresChannelRepository` + `PostgresMessageRepository` + `PostgresRunRepository` |
| 3.3 | `get_or_create_thread`, resolve pending prompts (§4.3.8), unique active run (§4.3.7) |
| 3.4 | Sau `message.end`, `finalize_agent_message` + `run.status = completed` |
| 3.5 | `chat_run_events` + `GET /runs/{runId}/stream?lastEventId=` (§4.3.9) |
| 3.6 | Bật `RedisSaver` thay `MemorySaver` khi `REDIS_URL` set (graph checkpoint — tách khỏi chat DB) |
| 3.7 | `scripts/seed_chat_fixture.py` — golden messages spec §12 |

**Tiêu chí xong:** Restart API không mất lịch sử; `langgraph_thread_id` ổn định; reconnect SSE (P1b).

---

### Phase 4 — Cứng hóa production (2–4 ngày)

→ **[phase-4-production.md](./chat-sse/phase-4-production.md)**

| # | Việc |
|---|------|
| 4.1 | JWT validation thật (issuer/audience từ gateway admin) |
| 4.2 | 403 channel ACL; 404 channel; 400 validation Zod-equivalent (Pydantic) |
| 4.3 | Rate limit / channel (429 + `Retry-After`) |
| 4.4 | Timeout run (60s) → SSE `AGENT_TIMEOUT` |
| 4.5 | Structured logging + correlation `run_id` |
| 4.6 | *(Tuỳ chọn)* Sentry SDK Python |

---

### Phase 5 — P2 (backlog)

→ **[phase-5-backlog.md](./chat-sse/phase-5-backlog.md)**

- `POST .../attachments` multipart
- `content.delta` token-level từ `astream_events` LLM streams
- `GET /messages/{messageId}` recovery (spec §5.6)
- System messages (`sender: system`)

---

## 6. Hợp đồng API — quyết định cần chốt trước code

| # | Quyết định | Đề xuất mặc định |
|---|------------|------------------|
| D1 | `thread_id` vs `channelId` | `{userId}:{channelId}` khi có auth; else `channelId` |
| D2 | Một `action_prompt` / thread | BE xóa/đánh dấu resolved prompt cũ khi POST mới |
| D3 | `actionId: custom` | P0: không xử lý server; FE focus input; P1: `expectsTextInput` trong prompt |
| D4 | Structured agent UI | P0 text-only; P1 mở rộng `PlannerDecision` + SQL result → `table` |
| D5 | Stream token | Chỉ `content.paragraph` P0; `content.delta` P1 |
| D6 | Chạy song song Telegram + API | Shared `SupervisorGraph` singleton; checkpointer Redis bắt buộc nếu 2 process |

Cập nhật `chat-sse-be-spec.md` khi chốt D1–D6.

---

## 7. Cấu hình môi trường

```bash
# API server (mới)
API_HOST=0.0.0.0
API_PORT=8080
API_CORS_ORIGINS=http://localhost:5173
CHAT_REQUIRE_AUTH=false          # P0 dev
CHAT_JWT_SECRET=                  # P1

# Giữ nguyên từ CLAUDE.md
SUPERVISOR_PROVIDER=...
WORKER_PROVIDER=...
OPENSEARCH_...
REDIS_URL=redis://localhost:6379/0   # P1 LangGraph checkpoint (không lưu chat messages)

# Chat DB — §4.3.16
CHAT_DATABASE_URL=postgresql://admin:password123@localhost:5432/agentic_chat
CHAT_DB_POOL_MIN=2
CHAT_DB_POOL_MAX=10
CHAT_RUN_TIMEOUT_SEC=60
CHAT_RUN_EVENTS_RETENTION_DAYS=7
```

---

## 8. Kiểm thử

| Lớp | Phạm vi |
|-----|---------|
| Unit | SSE formatter; mapper `final_output` → `AgentMessageData`; validation POST body |
| API | TestClient REST; mock `RunService` / adapter |
| Integration | Một channel, một câu hỏi metadata đơn giản — skip nếu OpenSearch/LLM down |
| Contract | Golden file: ordered list SSE events từ fixture spec §12 |
| Manual | `curl -N -H "Authorization: Bearer ..." -H "Accept: text/event-stream" -d '{"type":"text","content":"..."}'` |

**Lệnh:**

```bash
pytest tests/test_chat_api_channels.py tests/test_chat_sse_integration.py -v
uvicorn api.app:app --reload --port 8080
```

---

## 9. Rủi ro & giảm thiểu

| Rủi ro | Tác động | Giảm thiểu |
|--------|----------|------------|
| `final_output` chỉ là SQL text | FE thiếu table/buttons đẹp | Mapper P0 paragraphs; P1 structured output |
| HITL không có `options[]` trong state | Không khớp `ActionPromptCard` | Mở rộng planner JSON hoặc wrap `message_to_user` thành 1 option |
| SSE proxy timeout (nginx) | Cắt stream | `X-Accel-Buffering: no`, heartbeat comment mỗi 15s |
| MemorySaver multi-instance | Mất session | Redis checkpointer trước production |
| LLM chậm | FE treo | `error` event + timeout; disable input khi 409 |

---

## 10. Checklist triển khai (tracking)

### P0 — MVP ghép FE

- [ ] FastAPI app + CORS + health
- [ ] Schemas `Message` / POST body (Pydantic)
- [ ] `GET /channels`
- [ ] `GET /channels/{id}/messages` (+ fixture seed)
- [ ] `POST /channels/{id}/messages` → SSE
- [ ] Events: `run.start`, `user.ack`, `message.start`, `trace.step`, `content.paragraph`, `message.end`
- [ ] HITL: `action.prompt` + resume `type: action`
- [ ] 409 run in progress
- [ ] Bearer trên stream (fetch-compatible)
- [ ] Tests API unit (mock graph)

### P1 — Production-ready

- [ ] Migration `chat.*` tables (§4.3.12)
- [ ] Postgres repositories + seed channels
- [ ] Thread / run / message status rules (§4.3.7–4.3.8)
- [ ] `seed_chat_fixture.py` golden history
- [ ] Redis LangGraph checkpointer (tách chat DB)
- [ ] `Last-Event-ID` reconnect
- [ ] Idempotency-Key
- [ ] JWT + channel ACL
- [ ] `table` / `action.buttons` từ kết quả SQL worker
- [ ] Rate limit + timeout events

### P2 — Spec phụ

- [ ] Attachments
- [ ] `content.delta` token stream
- [ ] `GET /messages/{messageId}`

---

## 11. Thứ tự ưu tiên công việc (sprint gợi ý)

| Tuần | Focus |
|------|--------|
| **S1** | Phase 0 + 1 — FE đọc channel/history từ API |
| **S2** | Phase 2.1–2.3 — POST SSE + trace steps + HITL prompt |
| **S3** | Phase 2.4 mapper + tests + manual curl; fix D3/D4 |
| **S4** | Phase 3 DB migration §4.3 + Redis checkpoint; Phase 4 auth/limits |

---

## 12. Liên kết tài liệu

| Tài liệu | Nội dung |
|----------|----------|
| [chat-sse/README.md](./chat-sse/README.md) | Index phase docs cho dev |
| [chat-sse-be-spec.md](./chat-sse-be-spec.md) | Hợp đồng FE ↔ BE (event names, payloads) |
| [CLAUDE.md](../CLAUDE.md) | Kiến trúc supervisor, metadata, SQL writer |
| [chat-sse/database-design.md](./chat-sse/database-design.md) | Thiết kế DB (tách từ §4.3) |
| §4.3 (file này) | Thiết kế DB đầy đủ + DDL |
| `scripts/migrations/chat/001_init.sql` | DDL (tạo khi implement Phase 3) |
| `src/main.py` | Reference implementation streaming + HITL |

---

*Khi BE chốt quyết định §6 (D1–D6), cập nhật đồng thời `chat-sse-be-spec.md` và checklist §10 trước khi FE merge `ChatApi` / `useChatStream`.*
