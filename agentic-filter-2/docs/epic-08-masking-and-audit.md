# Epic 8: Masking And Audit

## Tham chiếu

- [architecture_plan.md](architecture_plan.md) **§14 Epic 8**, **§3.7 Masking Engine**, **§3.8 Audit Logger**, **§12** (log security), **§13 Observability**, **§9** (`services/masking_service.py`, `services/audit_service.py`, `api/audit.py`).

## Mục tiêu epic

Sau connector: áp dụng column mask (FULL, PARTIAL, HASH, NULLIFY) trên response đã chuẩn hóa; ghi **ACCESS_LOG** cho allow/deny/error; baseline metrics/logging — không ghi token hay dữ liệu raw nhạy cảm.

## Phụ thuộc

- **Epic 6** tối thiểu (pipeline runtime Postgres end-to-end); phần OpenSearch đầy đủ khi **Epic 7** xong.
- **Epic 5** (column mask policy trên decision).
- **Epic 3** đã có `PERMISSION_CHANGE_LOG`; Epic 8 nhấn **ACCESS_LOG** runtime (**§3.8**).

## Dev-agent — checklist triển khai

- [x] `masking_service.py`: áp dụng mask theo tên column đã resolve, map projection key (alias) qua `logical_column_to_result_keys` / `apply_column_masks_to_row` (**§3.7**).
- [x] Các kiểu FULL, PARTIAL, HASH (salt `MASKING_HASH_SALT` config), NULLIFY, CUSTOM (giữ từ MVP).
- [x] Wire sau connector: Postgres + OpenSearch `_source` trong `filter_query_service` / `filter_search_service`; deny vẫn ghi audit trong `except` service (**§12**).
- [x] `audit_service.py` + persistence `ACCESS_LOG`: thêm `decision`, `request_id` (migration); `record_runtime_access` + log structured không token/row (**§12**).
- [x] Metrics §13: `app/observability/metrics.py` — request/deny/masking latency; hook từ `filter.py` + masking.
- [x] Structured logging: `app.runtime_audit` logger chỉ metadata an toàn.

## Acceptance criteria (§14)

- Masking áp dụng đúng trên response.
- Audit log không chứa token hoặc dữ liệu raw nhạy cảm.
- Access log có user, resource, action, result (+ decision, request_id khi có).

## QA-agent — phạm vi kiểm thử

- §15.1: masking engine từng kiểu (unit).
- §15.2: *Runtime request có column mask trả dữ liệu đã mask*; *Access log được ghi cho allow và deny*.
- §15.3: *Alias không bypass được masking*; kết hợp aggregate edge nếu đã chốt rule (**§7.4** / §17).
- §18 Definition of Done (cross-check toàn pipeline).

## Code review — trọng tâm

- Mọi đường response nhạy cảm đi qua masking khi policy yêu cầu.
- Log/metrics không chứa PII/query body đầy đủ.

## Open decisions (§17)

- Aggregate/expression chứa column bị mask — MVP chặn hay rule riêng; thống nhất với PDP/rewriter.
