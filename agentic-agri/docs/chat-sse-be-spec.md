# Chat API — Hợp đồng Backend (legacy pointer)

> **Đã thay thế bởi tài liệu tích hợp FE (2026-05-21).**

## Tài liệu chính thức cho Frontend

👉 **[chat-fe-integration.md](./chat-fe-integration.md)** — REST + SSE + TypeScript types + ví dụ `fetch`, mã lỗi, checklist.

Nội dung gồm:

- Base URL, auth JWT, rate limit, CORS  
- Toàn bộ endpoint (`channels`, `messages`, `attachments`, `runs/{id}/stream`)  
- Hợp đồng SSE (event types + payload **khớp code**, gồm `content.delta.text`)  
- Mode POST+SSE và mode `?async=true` + GET stream  
- Idempotency, reconnect `lastEventId`, recovery `GET /messages/{id}`  

## Tài liệu nội bộ BE (theo phase)

- [chat-sse/README.md](./chat-sse/README.md) — lộ trình Phase 0–5  
- [chat-sse-implementation-plan.md](./chat-sse-implementation-plan.md) — kế hoạch tổng  
- [deploy/nginx-chat-sse.md](./deploy/nginx-chat-sse.md) — proxy SSE  

File spec gốc (draft dài) được giữ làm pointer để link cũ không gãy; **không** dùng làm nguồn tích hợp mới.
