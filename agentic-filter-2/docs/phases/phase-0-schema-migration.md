# Phase 0 — Schema & seed (wizard FE)

## Goal

Chốt schema PostgreSQL cho resource / permission / row_filter / column_mask khớp FE, merge migration **S1** và bổ sung `permission_types` cần cho wizard.

## Phụ thuộc

- Không (bắt đầu initiative).
- Đọc trước: [schema_review_add_permission_wizard_fe.md](../schema_review_add_permission_wizard_fe.md) §3–§6.

## Tasks

- [x] **0.1** Rà soát checklist R1–R9 trong schema review; ghi nhận kết quả vào PR description → Verify: mọi mục có trạng thái Đúng / Cần S1 / Code P0
- [x] **0.2** Tạo Alembic migration: `UNIQUE (permission_id)` trên `row_filters` (`uq_row_filters_permission_id`); model `RowFilter` thêm `UniqueConstraint` → Verify: `alembic upgrade head` OK; `\d row_filters` có unique trên `permission_id`
- [x] **0.3** Bổ sung seed `permission_types`: ít nhất `DESCRIBE` (và giữ USAGE/INSERT/UPDATE/DELETE nếu chưa có) trong `scripts/seed_demo_data.py` hoặc migration data → Verify: `SELECT name FROM permission_types` có `SELECT`, `DESCRIBE`
- [x] **0.4** Seed demo: ít nhất 1 permission TABLE + `row_filters`, 1 COLUMN + `column_masks` (role seed hoặc script riêng) → Verify: query join thấy `condition_expr` và `mask_pattern` không null
- [x] **0.5** Chạy `python scripts/seed_demo_data.py` trên DB dev; `GET /api/v1/admin/resources/tree` trả `analytics_db` 4 tầng, `id` là UUID → Verify: curl tree, `.data[0].children` không rỗng
- [x] **0.6** (Tùy chọn) `CHECK (effect IN ('ALLOW','DENY'))` trên `permissions` nếu team đồng ý → Verify: insert effect `FOO` fail ở DB

## Done when

- [x] Migration S1 merged; không còn nhiều `row_filters` cho một `permission_id`.
- [x] Checklist seed §6 schema review: 3 ô tick.
- [x] Dev Phase 1 có thể resolve grant bằng UUID từ tree (không dùng id giả `d1`/`t1`).

## Kết quả rà soát R1–R9 (0.1)

| # | Trạng thái | Ghi chú |
|---|------------|---------|
| R1 | Đúng | Giữ semantics N permissions / N actions |
| R2 | Đúng | `uq_column_masks_permission_id` |
| R3 | **Đã S1** | Migration `f1a2b3c4d501` |
| R4 | Đúng | CASCADE catalog |
| R5 | **Đã seed** | DESCRIBE + USAGE/INSERT/UPDATE/DELETE |
| R6 | **Đã S2** | `ck_permissions_effect` |
| R7 | Code P0.2 | Service validation (Phase 1) |
| R8 | Code P0.1 | Resolve UUID (Phase 1) |
| R9 | Đúng | Chấp nhận modifier với DENY |

## Thay đổi code (PR-S)

| Thành phần | Path |
|------------|------|
| Migration S1+S2+DESCRIBE | `alembic/versions/f1a2b3c4d501_row_filters_unique_and_types.py` |
| Models | `app/models/permission.py` |
| Seed types + wizard modifiers | `scripts/seed_demo_data.py` → `seed_permission_wizard_modifier_demo` |
| Tests | `tests/test_phase0_schema.py` |
| Verify script | `scripts/verify_phase0_schema.py` |

## Verify nhanh

```powershell
$env:DATABASE_URL="postgresql+psycopg://filter:filter@127.0.0.1:5433/filter_db"
.\env-filter\Scripts\python.exe -m alembic upgrade head
.\env-filter\Scripts\python.exe scripts/seed_demo_data.py
.\env-filter\Scripts\python.exe scripts/verify_phase0_schema.py
.\env-filter\Scripts\python.exe -m pytest tests/test_phase0_schema.py -q
```

## Ghi chú

- **Không** thêm bảng mới cho MVP.
- `column_masks` đã có `uq_column_masks_permission_id` — không đổi.
- PK/FK cột (`columns.is_primary_key`) thuộc Phase 6.

## Tham chiếu code

| Thành phần | Path |
|------------|------|
| Models | `app/models/resource.py`, `app/models/permission.py` |
| Migration gốc | `alembic/versions/cfeb49a5c688_uuid_schema_all_tables.py` |
| Seed tree | `scripts/seed_demo_data.py` → `seed_permission_wizard_resource_tree` |
