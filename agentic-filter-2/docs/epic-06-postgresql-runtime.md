# Epic 6: PostgreSQL Runtime

## Tham chiếu

- [architecture_plan.md](architecture_plan.md) **§14 Epic 6**, **§3.5 Query Analyzer**, **§11.1 PostgreSQL**, **§8.1 Runtime API**, **§9** (`api/runtime.py`, `query/analyzer.py`, `query/postgres_rewriter.py`, `connectors/postgres.py`, `schemas/runtime.py`).

## Mục tiêu epic

Runtime endpoint thực thi **SELECT** MVP: parse/analyze query, kiểm tra column/table, inject row filter vào `WHERE`, từ chối query ngoài phạm vi; connector thực thi query đã rewrite — **fail closed** nếu rewrite/authorize lỗi.

## Phụ thuộc

- **Epic 5** (authorization decision + filters).
- **Epic 4** (user context / token).
- **Epic 1** (skeleton).

## Dev-agent — checklist triển khai

- [x] `runtime.py` (hoặc router runtime): nhận body query + context backend=postgres theo **§8.1**.
- [x] `query/analyzer.py`: subset SELECT MVP — projection, FROM schema.table, WHERE tùy chọn; từ chối DDL/DML/multi-statement (**§11.1**, **§15.3**).
- [x] `postgres_rewriter.py`: inject row filter `AND`; tạo `WHERE` nếu thiếu; parameter binding cho biến runtime (user_id, tenant, …).
- [x] Column allow/deny: strip hoặc 403 column không được phép.
- [x] `connectors/postgres.py`: pool, timeout, retry transient; **không** nhận SQL chưa qua PDP + rewriter (**§3.6**).
- [x] Lỗi: 403 forbidden, 422 unsupported query (**§12**).
- [x] Tests: allow path, deny, row filter correctness, unsupported SQL rejected.

## Acceptance criteria (§14)

- Query allowed được execute.
- Query denied trả `403`.
- Row filter được inject đúng.
- Unsupported query fail closed.

## QA-agent — phạm vi kiểm thử

- §15.2: token hợp lệ + allow + Postgres thành công; thiếu permission → 403.
- §15.2: row filter chỉ trả đúng phạm vi (integration).
- §15.3: multi-statement, DML/DDL chặn; column denied; IAM timeout (kết hợp Epic 4).

## Code review — trọng tâm

- **Không** nối chuỗi SQL từ input không tin cậy (**§3.5**); dùng parser/builder + parameter.
- Luôn đường đi: IAM → PDP → rewrite → execute; không shortcut.

## Open decisions (§17)

- Phạm vi SQL MVP cụ thể (subquery, join, …) — document rõ để 422 nhất quán.
