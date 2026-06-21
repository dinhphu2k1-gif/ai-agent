# Phase 2 — Presenter FE parity & integration tests

## Goal

Response permission đủ field để FE **edit** wizard (full `path`, modifier labels); test end-to-end grant có row filter và column mask.

## Phụ thuộc

- [Phase 1](phase-1-grant-service.md) merged.

## Tasks

- [x] **2.1** Sửa `build_path_labels` trong `permission_presenter.py`: COLUMN → db→schema→table→column; TABLE → 3 cấp; SCHEMA → 2 cấp — dùng `ResourceRepository` walk parent → Verify: unit test path length 4 cho column permission
- [x] **2.2** `ROW_FILTER`: `label` = `conditionExpression` (không `"Row Filter"`); `COLUMN_MASK`: giữ `PARTIAL: {pattern}` hoặc type-only → Verify: `to_fe_permission` snapshot khớp spec §5.5
- [x] **2.3** Tạo `tests/test_admin_permission_grant.py`: seed tree → POST grant TABLE + `rowFilter` → GET permissions có `modifier.conditionExpression`; POST COLUMN + `columnMask` PARTIAL → `maskType`/`maskPattern` → Verify: `pytest tests/test_admin_permission_grant.py -q` green
- [x] **2.4** Cập nhật `test_admin_roles_api.py`: thay id giả `d1/s1/t1` bằng UUID từ `ResourceTreeService.build_fe_tree()` hoặc fixture seed → Verify: không phụ thuộc tên auto-create
- [x] **2.5** (Tùy chọn) Mở rộng `tests/test_admin_contract_snapshot.py` cho một permission có modifier → Verify: CI contract subset pass

## Done when

- [x] FE có thể hydrate edit từ `path[].resourceId` + `modifier.*` không parse `label`.
- [x] pytest grant integration green cùng role API smoke.

## Curl smoke (sau Phase 2)

```bash
# Tree → lấy col id → grant mask → list
curl -sS -H "X-Admin-Token: $ADMIN_TOKEN" \
  "http://127.0.0.1:8000/api/v1/admin/resources/tree"
# POST .../roles/{id}/permissions với resourcePath id thật + columnMask
```

## Ghi chú

- `resourceType` trong response: UPPERCASE (`COLUMN`, …).
- CORS đã bật — không thuộc phase này.
