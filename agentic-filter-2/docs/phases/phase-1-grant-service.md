# Phase 1 — Permission grant service (core)

## Goal

Tách logic grant wizard vào service dùng chung: resolve `resourcePath` theo **UUID**, validate payload FE, bỏ auto-tạo catalog khi grant.

## Phụ thuộc

- [Phase 0](phase-0-schema-migration.md) merged (S1 + seed types).

## Tasks

- [x] **1.1** Tạo `app/services/permission_grant_service.py` với `resolve_resource_id(body: PermissionGrantBody) -> UUID` — walk `resourcePath[]`, verify từng `id` tồn tại và đúng chuỗi database→schema→table→column → Verify: unit test path hợp lệ / sai thứ tự / id lạ → exception rõ
- [x] **1.2** Implement `validate_grant(body)` theo ma trận [plan §5](../implementation_plan_add_permission_wizard.md#5-ma-trận-validation-p0--bắt-buộc): path, resourceType, actions, effect, modifier theo TABLE/COLUMN, không dual modifier → Verify: pytest parametrized 400/404
- [x] **1.3** `apply_grant(role_id, body)` / `apply_grant_group(group_id, body)`: tạo N `permissions` cho N actions; upsert `row_filters` / `column_masks`; `role_permissions` / `group_permissions`; audit + cache invalidate — **không** gọi `create_database` trong grant → Verify: count `resources` không đổi sau grant lỗi path
- [x] **1.4** Refactor `admin_role_service.py` và `admin_group_service.py`: delegate grant/update/delete permission tới `PermissionGrantService`; xóa `_resolve_resource_from_path` cũ → Verify: `tests/test_admin_roles_api.py` grant vẫn pass với id từ seed tree
- [x] **1.5** Router: map `GrantValidationError` / `ValueError` → `400` + `ApiResponse` (`invalid_action`, `invalid_modifier`, …) → Verify: POST grant thiếu `conditionExpression` → 400 JSON có `success: false`

## Done when

- [x] Grant role/group chỉ chấp nhận `resourcePath[].id` có trong DB.
- [x] Action không tồn tại → 400, không skip im lặng.
- [x] TABLE + row filter / COLUMN + mask lưu đúng bảng.

## Files chính

```text
app/services/permission_grant_service.py   (mới)
app/services/admin_role_service.py         (refactor)
app/services/admin_group_service.py        (refactor)
app/repositories/resource_repo.py          (lookup by id nếu thiếu)
tests/test_permission_grant_validation.py  (mới, tối thiểu)
```

## Ghi chú

- Semantics: **một permission / một action** (giữ như hiện tại).
- `PUT` multi-action vẫn single action — xử lý Phase 5 nếu product yêu cầu.
