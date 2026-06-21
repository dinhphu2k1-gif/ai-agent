# Phase 5 — Backlog (P2)

> **Ước lượng:** theo priority product  
> **Phụ thuộc:** [phase-4-production.md](./phase-4-production.md)

## Goal

Các hạng mục spec chưa làm trong MVP — lên kế hoạch riêng khi Phase 0–4 ổn định.

## Items

### 5.1 Attachments

- [x] `POST /api/v1/chat/channels/{channelId}/attachments` — `multipart/form-data`
- [x] Bảng `chat_attachments`, `chat_message_attachments` — [database-design.md](./database-design.md)
- [x] `POST .../messages` nhận `attachmentIds: string[]`
- [x] Storage: local path P0 / S3 P1
- → Verify: upload file → gửi message kèm id → history hiển thị metadata (FE scope)

### 5.2 Token-level SSE (`content.delta`)

- [x] Subscribe `on_chat_model_stream` trong `astream_events`
- [x] Emit `content.delta` + flush `content.paragraph` (D5)
- [x] FE incremental render
- → Verify: stream có nhiều delta trước một paragraph

### 5.3 Message recovery API

- [x] `GET /api/v1/chat/messages/{messageId}` — full `AgentMessageData` khi FE miss `message.end` (spec §5.6)
- → Verify: GET trả đủ JSON sau run completed

### 5.4 System messages

- [x] `sender: system` — channel init / policy notice
- [x] FE render (ngoài scope BE nhưng contract ổn định)
- → Verify: seed system message trong channel history

### 5.5 Tách POST và stream (spec §4.4)

- [x] `POST` → `202 { runId, userMessageId }`
- [x] `GET /runs/{runId}/stream` — alternative cho clients không giữ connection POST
- → Verify: FE có thể dùng pattern 2-step

### 5.6 Retention job

- [x] Cron xóa `chat_run_events` older than `CHAT_RUN_EVENTS_RETENTION_DAYS`
- → Verify: count giảm sau job

### 5.7 Planner `ui_options` structured

- [x] `PlannerDecision.ui_options: list[{label, actionId}]` — khớp mock FE 3 options
- [x] Bỏ workaround single free-text option

## Done when (per item)

Mỗi item có issue riêng + PR riêng; không gộp vào MVP closure.

## Tham chiếu

- [chat-sse-be-spec.md](../chat-sse-be-spec.md) §4.4, §4.5, §10 checklist P2
- [chat-sse-implementation-plan.md](../chat-sse-implementation-plan.md) §5 Phase 5
