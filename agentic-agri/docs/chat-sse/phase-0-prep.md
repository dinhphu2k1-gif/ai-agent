# Phase 0 — Chuẩn bị HTTP API

> **Ước lượng:** 0.5–1 ngày  
> **Phụ thuộc:** Không  
> **Tiếp theo:** [phase-1-rest-readonly.md](./phase-1-rest-readonly.md)

## Goal

Có FastAPI server chạy độc lập Telegram: health check, CORS, cấu hình env — **không** thay đổi LangGraph supervisor.

## Phạm vi

| Trong scope | Ngoài scope |
|-------------|-------------|
| `pyproject.toml` dependencies | Chat routes |
| `src/api/app.py` skeleton | Postgres |
| `GET /health` | SSE |
| CORS + env | Auth JWT thật |

## Tasks

- [x] **0.1** Thêm vào `pyproject.toml`: `fastapi`, `uvicorn[standard]` (dev: thêm vào `[project.optional-dependencies] api` hoặc dependencies chính)  
  → Verify: `pip install -e ".[dev]"` (hoặc tương đương) không lỗi

- [x] **0.2** Tạo `src/api/__init__.py`, `src/api/app.py`  
  - Factory `create_app()`  
  - Mount prefix tạm (optional) hoặc root  
  - Lifespan: load `dotenv`  
  → Verify: `python -c "from api.app import app"` (PYTHONPATH=`src`)

- [x] **0.3** `GET /health` → `{"status":"ok"}`  
  → Verify: `curl http://localhost:8080/health` → 200

- [x] **0.4** CORS middleware — đọc `API_CORS_ORIGINS` (comma-separated), mặc định `http://localhost:5173`  
  → Verify: Response có header `access-control-allow-origin` khi gọi từ origin FE

- [x] **0.5** Mở rộng config (file mới `src/api/settings.py` hoặc mở rộng `universal_agent/config.py` tách phần API):  
  `API_HOST`, `API_PORT`, `API_CORS_ORIGINS`, `CHAT_REQUIRE_AUTH` (default `false`)  
  → Verify: Document trong `env.example` (không commit secrets; `.env.example` bị gitignore pattern)

- [x] **0.6** Script chạy: document trong README hoặc comment  
  `uvicorn api.app:app --host 0.0.0.0 --port 8080 --app-dir src`  
  → Verify: Server start, Telegram `python src/main.py` vẫn chạy song song

## Files tạo mới (tối thiểu)

```
src/api/
  __init__.py
  app.py
  settings.py          # optional
```

## Cấu hình env (Phase 0)

```bash
API_HOST=0.0.0.0
API_PORT=8080
API_CORS_ORIGINS=http://localhost:5173
CHAT_REQUIRE_AUTH=false
```

## Done when

- [x] Health endpoint 200
- [x] CORS hoạt động với origin FE dev
- [x] Không sửa `supervisor/graph.py`, `main.py` behavior
- [x] `pytest` suite hiện có vẫn pass (`tests/test_api_health.py` thêm cho Phase 0)

## Tham chiếu

- [chat-sse-implementation-plan.md](../chat-sse-implementation-plan.md) §5 Phase 0
- [CLAUDE.md](../../CLAUDE.md) — install commands
