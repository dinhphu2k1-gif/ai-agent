# Phase 4 — Resource catalog APIs (P1)

## Goal

API hỗ trợ bước Resource/Modifier FE: tìm kiếm catalog, thống kê scope, danh sách action theo loại resource.

## Phụ thuộc

- [Phase 2](phase-2-presenter-tests.md) (grant ổn định). Có thể song song [Phase 3](phase-3-docs-verification.md).

## Tasks

- [x] **4.1** Tạo `app/services/resource_catalog_service.py`: `search(q, limit)` — duyệt cây/DB, trả `results[]` với `node`, `path`, `breadcrumb` → Verify: `GET /api/v1/admin/resources/search?q=email` trả ≥1 kết quả trên seed
- [x] **4.2** `scope_stats(resource_id)` — đếm schema/table/column dưới node DATABASE hoặc SCHEMA → Verify: `GET .../resources/{dbId}/scope-stats` counts khớp query SQL đếm con
- [x] **4.3** Pydantic: `ResourceSearchResultOut`, `ResourceScopeStatsOut` trong `admin_contract.py` → Verify: OpenAPI `/docs` hiển thị schema
- [x] **4.4** Router `app/api/admin_permission_wizard.py` (hoặc mở rộng `admin_shared.py`): register GET search + scope-stats trong `main.py` → Verify: curl 200 + envelope `ApiResponse`
- [x] **4.5** `GET /api/v1/admin/permissions/action-catalog?resourceType=TABLE` — đọc `app/core/permission_actions.py` + fallback `permission_types` DB → Verify: response chứa `SELECT`, `DESCRIBE` cho TABLE
- [x] **4.6** Tests: `tests/test_admin_resource_catalog_api.py` cho search + stats + action-catalog → Verify: pytest green (8 passed)

## Done when

- [x] FE có thể thay hardcode scope 12/48/210 bằng API stats (khi nối UI).
- [x] Search box có endpoint (khi FE gọi).
- [x] Action catalog khớp resource type.

## Files chính

```text
app/services/resource_catalog_service.py
app/core/permission_actions.py
app/api/admin_permission_wizard.py
app/schemas/admin_contract.py
tests/test_admin_resource_catalog_api.py
```

## Ghi chú

- Không cần migration mới (trừ index search P2).
- `resourceType` query param: chấp nhận `table` và `TABLE`.
