# Chat SSE Backend — Tài liệu triển khai theo phase

> Giao việc cho dev. Kế hoạch tổng: [chat-sse-implementation-plan.md](../chat-sse-implementation-plan.md)  
> **Tích hợp FE (API + SSE):** [chat-fe-integration.md](../chat-fe-integration.md)  
> Legacy pointer: [chat-sse-be-spec.md](../chat-sse-be-spec.md)

## Thứ tự thực hiện

| Phase | File | Ước lượng | Phụ thuộc |
|-------|------|-----------|-----------|
| 0 | [phase-0-prep.md](./phase-0-prep.md) | 0.5–1 ngày | — |
| 1 | [phase-1-rest-readonly.md](./phase-1-rest-readonly.md) | 1–2 ngày | Phase 0 |
| 2 | [phase-2-sse-core.md](./phase-2-sse-core.md) | 3–5 ngày | Phase 1 |
| 3 | [phase-3-persistence.md](./phase-3-persistence.md) | 2–3 ngày | Phase 2 |
| 4 | [phase-4-production.md](./phase-4-production.md) | 2–4 ngày | Phase 3 |
| 5 | [phase-5-backlog.md](./phase-5-backlog.md) | backlog | Phase 4 |

## Tài liệu bổ sung

| File | Khi nào đọc |
|------|-------------|
| [database-design.md](./database-design.md) | Phase 3 (bắt buộc trước khi viết migration) |

## Quyết định chung (D1–D6)

| ID | Mặc định |
|----|----------|
| D1 | `langgraph_thread_id` = `{userId}:{channelId}` |
| D2 | Một `action_prompt` pending / thread; resolve khi POST mới |
| D3 | `actionId: custom` — P0 no-op server-side |
| D4 | Agent UI structured — P0 chỉ `paragraphs` |
| D5 | `content.delta` + `content.paragraph` (tắt delta: `CHAT_EMIT_CONTENT_DELTA=false`) |
| D6 | Telegram + API song song → Redis checkpointer (Phase 3) |

## Repo anchor

- Graph: `src/universal_agent/supervisor/graph.py`
- Telegram reference: `src/main.py`
- Chưa có: `src/api/`, `src/chat/` (tạo từ Phase 0–1)
