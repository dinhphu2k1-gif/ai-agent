# Nginx reverse proxy for Chat SSE

Use these settings when terminating TLS or proxying to the Chat API (`uvicorn` on port 8080).

## Required directives

```nginx
location /api/v1/chat/ {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Connection "";

    # SSE: disable buffering so events flush immediately
    proxy_buffering off;
    proxy_cache off;

    # Must exceed CHAT_RUN_TIMEOUT_SEC (default 60s); add margin for TLS/handshake
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
}
```

## Staging checklist

- `CHAT_REQUIRE_AUTH=true` and `CHAT_JWT_SECRET` set (never log `Authorization` headers).
- `CHAT_RUN_TIMEOUT_SEC` aligned with `proxy_read_timeout`.
- `X-Accel-Buffering: no` is also set by the API response; nginx `proxy_buffering off` is still required.
- Redis (`REDIS_URL`) for LangGraph checkpointing when running multiple API workers.
