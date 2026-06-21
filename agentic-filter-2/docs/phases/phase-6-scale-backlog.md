# Phase 6 — Scale & chất lượng catalog (backlog P2)

## Goal

Cải thiện catalog và policy ở quy mô lớn / metadata đầy đủ — sau khi P0–P1 ổn định với FE.

## Phụ thuộc

- Phase 0–5 hoàn tất hoặc được product ưu tiên lùi.

## Tasks

- [x] **6.1** Lazy tree: `GET /api/v1/admin/resources/tree?parentId={uuid}` trả children một cấp → Verify: expand node không tải full tree
- [x] **6.2** Migration: `columns.is_primary_key`, `columns.is_foreign_key`; seed/metadata; tree ưu tiên DB rồi fallback heuristic → Verify: `g2a3b4c5d602` + pytest `test_resource_tree_service`
- [x] **6.3** Runtime mask: align engine PARTIAL/HASH với `PermissionValidationService.preview` → Verify: runtime output = preview cho cùng input
- [x] **6.4** Effective permissions: `PUT` inherited row → `403` / `PERMISSION_NOT_DIRECT` khi `ownership != group` → Verify: test effective-permissions + group PUT deny
- [ ] **6.5** (Tùy chọn) Index/search MV cho catalog lớn — theo [schema review S6](../schema_review_add_permission_wizard_fe.md#5-khoảng-trống-schema--migration-đề-xuất) — chưa triển khai (P2+)

## Done when

- [x] Ticket P2 core (6.1–6.4) triển khai + pytest; 6.5 estimate riêng khi catalog lớn.

## Ghi chú

Phase này **không chặn** release wizard MVP nếu Phase 0–3 đã xong.

**Triển khai:** `ResourceTreeService.build_children_for_parent`, `app/services/column_mask_engine.py`, tests `test_phase6_scale_backlog.py`.
