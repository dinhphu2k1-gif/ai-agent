# Phase 2 — POST + SSE core (critical path)

> **Ước lượng:** 3–5 ngày  
> **Phụ thuộc:** [phase-1-rest-readonly.md](./phase-1-rest-readonly.md)  
> **Tiếp theo:** [phase-3-persistence.md](./phase-3-persistence.md)

## Goal

`POST /api/v1/chat/channels/{channelId}/messages` trả **SSE stream** (`text/event-stream`), chạy supervisor LangGraph, map event cho FE — gồm HITL `action.prompt`.

## Phạm vi

| Trong scope | Ngoài scope |
|-------------|-------------|
| Events P0: `run.start`, `user.ack`, `message.start`, `trace.step`, `content.paragraph`, `message.end`, `action.prompt`, `error`, `run.failed` | Postgres (Phase 3) |
| `type: text` và `type: action` body | `content.delta` token stream |
| 409 run in progress (in-memory lock) | Attachments |
| Bearer trên stream (fetch) | JWT production |

## Reference implementation

Copy pattern từ `src/main.py`:

- `app.get_state(config)` — HITL check `clarification_node` in `snapshot.next`
- `app.update_state` + `astream_events(None)` — resume
- `astream_events(current_input, config, version="v2")` — `on_chain_start` → trace
- `node_status_map` (L80–87 `main.py`)

## Tasks

### A. Infrastructure SSE

- [x] **2.1** `src/api/streaming/sse.py`  
  - `format_sse(event: str, data: dict, event_id: str | None = None) -> str`  
  - Format: `id:\nevent:\ndata: {json}\n\n` (một dòng JSON)  
  - Optional: comment heartbeat `: ping\n\n` mỗi 15s trong generator  
  → Verify: unit test parse output có đúng 2 newlines sau data

- [x] **2.2** `src/api/schemas/chat.py` — thêm `PostMessageRequest` (`type: text|action`, `content`, `actionId`, `label`, `replyToMessageId`)

### B. Domain services

- [x] **2.3** `src/chat/services/run_service.py`  
  - `langgraph_thread_id = f"{user_id}:{channel_id}"` (D1)  
  - In-memory `active_runs: dict[channel_id, run_id]`  
  - `start_run()` → 409 nếu active  
  - Persist user message (in-memory repo) → yield `user.ack`  
  → Verify: double POST nhanh → 409

- [x] **2.4** `src/chat/adapters/supervisor_stream.py` — `SupervisorStreamAdapter`  
  - Inject compiled graph `app` từ `universal_agent.supervisor.graph`  
  - Async generator `stream(channel_id, user_id, body) -> AsyncIterator[ChatSseEvent]`  
  - Map table (spec §5.3):

| SSE event | Khi emit |
|-----------|----------|
| `run.start` | Đầu stream |
| `user.ack` | Sau insert user msg |
| `message.start` | Trước agent output |
| `trace.step` | `on_chain_start` + known `node_status_map` |
| `content.paragraph` | `final_output` hoặc chunk text |
| `action.prompt` | Sau stream nếu `clarification_node` pending |
| `message.end` | Kết thúc agent message |
| `error` / `run.failed` | Exception |

- [x] **2.5** Graph input — text mới:

```python
current_input = {
    "user_input": content,
    "investigation_log": [f"Nhận yêu cầu: {content}"],
}
config = {"configurable": {"thread_id": langgraph_thread_id}}
```

- [x] **2.6** Graph input — HITL resume (`type: action`):

```python
if snapshot.next and "clarification_node" in snapshot.next:
    app.update_state(config, {
        "investigation_log": [f"Người dùng trả lời (HITL): {label}"],
    })
    current_input = None
```

- [x] **2.7** Resolve pending `action_prompt` in-memory khi POST mới (D2) — xóa/đánh dấu resolved trước insert user msg

### C. Mapper

- [x] **2.8** `src/chat/mappers/agent_message_mapper.py`  
  - `final_output` → `paragraphs: [text]`  
  - SQL fenced code → giữ trong paragraph + optional trace step `sql_writer_worker_node`  
  - `message_to_user` → `ActionPromptData` với 1 option free-text nếu chưa có `ui_options` từ planner  
  → Verify: unit test với sample SQL markdown string

### D. HTTP route

- [x] **2.9** Extend `messages.py` — `POST /channels/{channel_id}/messages`  
  - Require header `Accept: text/event-stream` (hoặc default stream)  
  - `StreamingResponse` async generator  
  - Headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`  
  - **Không** bọc SSE trong `ApiResponse`  
  - Auth: đọc Bearer từ request (middleware đặt `request.state.user_id`)

- [x] **2.10** Sau stream: lưu agent message vào `InMemoryMessageRepository` (paragraphs + trace nếu có)

### E. Tests

- [x] **2.11** `tests/test_chat_sse_unit.py` — sse formatter, mapper (no LLM)

- [x] **2.12** `tests/test_chat_sse_integration.py` — TestClient POST + đọc stream lines  
  - Mock graph **hoặc** `@pytest.mark.skipif` khi không có vLLM/OpenSearch  
  - Assert thứ tự event tối thiểu: `run.start` → … → `message.end`  
  → Verify: `pytest tests/test_chat_sse_integration.py -v`

### F. Manual verification

- [x] **2.13** curl:

```bash
curl -N -X POST "http://localhost:8080/api/v1/chat/channels/market-trends/messages" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "Authorization: Bearer dev" \
  -d "{\"type\":\"text\",\"content\":\"Cho tôi schema bảng GL_ACCOUNTS\"}"
```

→ Verify: thấy `event: trace.step` và `event: content.paragraph` hoặc `message.end`

## `node_status_map` (copy từ main.py)

```python
NODE_STATUS_MAP = {
    "planner": ("Supervisor", "Đang phân tích kế hoạch", "psychology"),
    "metadata_worker_node": ("Metadata", "Kích hoạt tra cứu metadata", "dataset"),
    "query_analyzer": ("Query Analyzer", "Phân tích truy vấn", "search"),
    "opensearch_retriever": ("OpenSearch", "Truy vấn vector DB", "travel_explore"),
    "result_synthesizer": ("Synthesizer", "Tổng hợp schema", "description"),
    "sql_writer_worker_node": ("SQL Writer", "Sinh SQL", "code"),
}
```

Emit `trace.step` với `title`, `description`, `icon` (Material name).

## `action.prompt` payload (spec §5.4)

```json
{
  "messageId": "uuid",
  "promptData": {
    "title": "Awaiting your direction",
    "description": "<message_to_user>",
    "options": [{ "label": "...", "actionId": "..." }],
    "customOptionLabel": "Option D: Custom Input"
  }
}
```

P0: nếu planner chỉ có `message_to_user` string — tạo một option `{ "label": message_to_user, "actionId": "free_text" }`.

## Done when

- [x] POST text → SSE stream với trace steps + paragraph chứa output (SQL hoặc text)
- [x] Khi graph dừng HITL → `action.prompt` xuất hiện; POST `type: action` → resume và tiếp tục stream
- [x] 409 khi POST trong lúc run active
- [x] GET history sau POST phản ánh user + agent messages (in-memory)
- [x] Unit tests pass; integration skip hoặc pass khi có LLM

## Rủi ro (phase 2)

| Rủi ro | Xử lý |
|--------|--------|
| LLM/OpenSearch down | Test skip; manual cần `.env` |
| Stream không kết thúc | `finally` emit `message.end` hoặc `run.failed` |
| Proxy buffer SSE | Header `X-Accel-Buffering: no` nếu deploy nginx |

## Tham chiếu

- [chat-sse-be-spec.md](../chat-sse-be-spec.md) §4.3, §5, §6
- `src/main.py` L45–148
- [chat-sse-implementation-plan.md](../chat-sse-implementation-plan.md) §5 Phase 2
