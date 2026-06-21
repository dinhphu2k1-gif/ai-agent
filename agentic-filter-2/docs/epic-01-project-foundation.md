# Epic 1: Project Foundation

## Tham chiếu

- [architecture_plan.md](architecture_plan.md) **§14 Epic 1**, **§9 Module Structure**, **§12** (error model), **§13** (baseline observability có thể chỉ stub).
- SRS: [0_srs.md](../my-docs/0_srs.md) (Python, FastAPI).

## Mục tiêu epic

Thiết lập khung dự án Filter Service: cấu trúc `app/`, cấu hình, logging, lỗi chuẩn, health check, kết nối DB/Redis/IAM URL, framework test và migration — để các epic sau chỉ bổ sung domain.

## Phụ thuộc

- Không có epic tiền nhiệm.

## Dev-agent — checklist triển khai

- [x] Tạo cây thư mục theo **§9**: `app/main.py`, `app/core/` (`config.py`, `errors.py`, `logging.py`, `security.py` stub nếu cần).
- [x] FastAPI app: lifespan, router gốc, middleware correlation/request id (nếu architecture yêu cầu §12/§13).
- [x] Pydantic Settings: DB URL, Redis URL, IAM base URL, log level.
- [x] Error model thống nhất (mapping tới mã §12 khi có).
- [x] `GET /health` (và readiness tùy chọn) trả OK khi process up; kiểm tra DB/Redis có thể làm từng bước sau.
- [x] Alembic (hoặc migration tool đã chốt) scaffold; chưa cần đầy đủ bảng domain (Epic 2).
- [x] pytest + fixture tối thiểu; `tests/` hoặc `app/tests/` theo convention đã chọn.
- [x] `pyproject.toml` / requirements: FastAPI, Uvicorn, SQLAlchemy/SQLModel, Alembic, Redis client, HTTPX.

## Acceptance criteria (§14)

- [x] Service chạy được local.
- [x] `/health` trả OK.
- [x] Có test smoke cho app startup.

## QA-agent — phạm vi kiểm thử

- [x] Smoke: khởi động app, gọi `/health`, một test tự động pass CI (`python -m pytest -q`; thêm xác nhận tay/CI nếu qa-agent cần).
- (Chưa yêu cầu đầy đủ §15.2 runtime — chưa có endpoint query.)

## Code review — trọng tâm

- Không commit secret; dùng env/example `.env.example` nếu có.
- Logging không in token hoặc connection string đầy đủ.
- Cấu trúc module rõ, không nhét logic domain vào `main.py` quá dày.

## Open decisions (§17)

- Chưa chặt schema row filter / mapping OpenSearch — không block Epic 1; ghi TODO trong `docs/` hoặc issue nếu cần.

## Điều phối (planner → dev-agent / review-agent / qa-agent)

Thứ tự gợi ý: **dev-agent** triển khai checklist → **review-agent** xem PR/nhánh → **qa-agent** xác nhận AC §14.

### Bước 1 — dev-agent

Mục tiêu: hoàn thành mọi mục trong **Dev-agent — checklist triển khai** ở trên; PR nhỏ nếu được (dependencies + skeleton trước, rồi health + test).

Gợi ý prompt (Cursor / subagent):

```text
Use the dev-agent subagent to implement Epic 1 per docs/epic-01-project-foundation.md:
pyproject + app/ §9 (main, core), Pydantic settings, error/logging stubs, GET /health,
Alembic scaffold, pytest smoke for startup. No permission/runtime features.
```

### Bước 2 — review-agent

Điều kiện vào: có diff (PR hoặc nhánh) sau bước 1.

Gợi ý prompt:

```text
Use the review-agent subagent to review the Epic 1 changes against
docs/epic-01-project-foundation.md section "Code review — trọng tâm":
secrets, logging, main.py size, dependency choices.
```

### Bước 3 — qa-agent

Gợi ý prompt:

```text
Use the qa-agent subagent to verify Epic 1 acceptance criteria in
docs/epic-01-project-foundation.md: local /health, automated smoke test,
document any manual steps for CI if needed.
```

### Đóng Epic 1

Chỉ đánh dấu epic xong khi cả ba điều **Acceptance criteria (§14)** đúng: service local, `/health` OK, smoke test pass.

Có thể `@.cursor/agents/dev-agent.md` / `review-agent.md` / `qa-agent.md` thay cho câu "Use the … subagent" nếu môi trường không delegate tự động.
