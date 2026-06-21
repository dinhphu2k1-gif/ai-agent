# Epic 7: OpenSearch Runtime

## Tham chiếu

- [architecture_plan.md](architecture_plan.md) **§14 Epic 7**, **§3.5** (OpenSearch JSON), **§11.2 OpenSearch**, **§8.1 Runtime API**, **§9** (`query/opensearch_rewriter.py`, `query/resource_resolver.py`, `connectors/opensearch.py`).

## Mục tiêu epic

Runtime search JSON: resolve index/field → resource, áp dụng PDP, inject row filter vào `bool.filter` (hoặc tương đương), connector thực thi; field denied bị chặn/loại bỏ theo rule đã chốt.

## Phụ thuộc

- **Epic 5** (decision + filters).
- **Epic 4**, **Epic 1**.
- Khuyến nghị làm **sau Epic 6** cho MVP tuần tự; có thể song song nhánh nếu PDP đã ổn định.

## Dev-agent — checklist triển khai

- [x] Runtime endpoint search (body JSON DSL) — contract **§8.1** / **§11.2** MVP.
- [x] `resource_resolver.py`: mapping index → table resource (MVP: tên index = tên bảng, duy nhất trong catalog; nhiều bảng trùng tên → 422 §17).
- [x] `opensearch_rewriter.py`: merge filter an toàn; không cho client ghi đè policy filter (append vào `bool.filter`; `post_filter` cũng được merge).
- [x] `_source` / field allowlist theo column permission; deny field trong `_source.includes` → 403; không truyền `_source` → `includes` = toàn bộ cột được phép.
- [x] `connectors/opensearch.py`: timeout, error mapping 502 khi backend lỗi.
- [x] Tests với mock executor (integration container optional sau).

## Acceptance criteria (§14)

- Search allowed được execute.
- Field denied bị chặn hoặc loại bỏ theo rule đã chốt.
- Row filter được thêm vào `bool.filter`.

## QA-agent — phạm vi kiểm thử

- §15.3: *OpenSearch request không bypass được `_source` field restriction*.
- §15.2: allow/deny/row filter trên search path (tương tự Postgres nhưng DSL).
- Regression khi đổi mapping index/field (**§17**).

## Code review — trọng tâm

- DSL merge tránh injection / override filter độc hại.
- Không leak full query JSON nhạy cảm vào log.

## Open decisions (§17)

- **Mapping giữa OpenSearch index/field và resource** — MVP đã chốt: index = tên bảng (unique); có thể bổ sung bảng mapping / convention khác sau.
