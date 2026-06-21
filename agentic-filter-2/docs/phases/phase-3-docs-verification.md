# Phase 3 — Tài liệu & xác nhận Phase 0–2

## Goal

Cập nhật tài liệu vận hành/API cho wizard; xác nhận initiative P0 đủ điều kiện bàn giao FE.

## Phụ thuộc

- [Phase 2](phase-2-presenter-tests.md) done.

## Tasks

- [x] **3.1** `docs/api-fe-integration.md`: thêm mục Add Permission — grant body, multi-action, DB/schema không modifier, CORS/`CORS_ALLOWED_ORIGINS` → Verify: FE đọc được flow 4 bước
- [x] **3.2** `docs/huong-dan-chay-va-curl.md`: ví dụ grant table + row filter + column mask; dùng id từ `/resources/tree` → Verify: copy-paste curl chạy được trên DB đã seed
- [x] **3.3** `docs/api-reference.md`: ghi rõ semantics `created[]` (N permissions), validation errors 400 → Verify: khớp implementation thực tế
- [x] **3.4** Chạy regression: `pytest tests/test_admin_permission_grant.py tests/test_admin_roles_api.py tests/test_admin_groups_api.py tests/test_resource_tree_service.py -q` → Verify: all green
- [x] **3.5** Checklist bàn giao FE (manual): create permission role; edit permission; create trên group; preflight OPTIONS không 405 → Verify: tick checklist [plan §9 manual](../implementation_plan_add_permission_wizard.md#9-kiểm-thử) — file [fe-handoff-p0-checklist.md](fe-handoff-p0-checklist.md)

## Done when

- [x] Docs đồng bộ code Phase 0–2.
- [ ] QA/FE sign-off checklist P0 (hoặc ticket với evidence curl/pytest).

## Verification (phase cuối P0)

Đây là phase xác nhận — **không** thêm feature mới.
