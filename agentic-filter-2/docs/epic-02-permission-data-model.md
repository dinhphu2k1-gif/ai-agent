# Epic 2: Permission Data Model

## Tham chiếu

- [architecture_plan.md](architecture_plan.md) **§14 Epic 2**, **§4 Data Model**, **§9** (`models/`, `repositories/`).

## Mục tiêu epic

Bảo đảm Permission DB phản ánh ERD: resource tree, permission, identity, assignment, audit schema — có migration và repository CRUD cơ bản để Epic 3 (Admin API) và Epic 5 (resolver) có dữ liệu.

## Phụ thuộc

- **Epic 1** (project skeleton, migration framework, DB connection).

## Dev-agent — checklist triển khai

- [x] Models: `RESOURCE` + subtype DATABASE/SCHEMA/TABLE/COLUMN; `PERMISSION`, `PERMISSION_TYPE`, `ROW_FILTER`, `COLUMN_MASK`; identity/assignment (`USER`, `GROUP`, `ROLE`, liên kết) theo **§4**.
- [x] Migration Alembic: đủ bảng + FK chính; index cho lookup theo `user_id`, `resource_id`, `permission_id`.
- [x] Repositories: `resource_repo`, `permission_repo`, `identity_repo`, `audit_repo` (CRUD tối thiểu).
- [x] Seed `PERMISSION_TYPE` (ví dụ `SELECT`) trong migration hoặc seed script.
- [x] Unit test repository: create/read/update/delete cơ bản trên vài entity đại diện.

## Acceptance criteria (§14)

- [x] Migration tạo đủ bảng và FK chính.
- [x] Repository tests pass cho create/read/update/delete cơ bản.

## QA-agent — phạm vi kiểm thử

- [x] §15.1 (một phần): resource inheritance có thể test ở mức model/repo nếu có helper; đầy đủ resolver chờ Epic 5.
- [x] Migration lên/xuống (upgrade/downgrade) trong môi trường test (`tests/test_epic2_migrations.py`).

## Code review — trọng tâm

- FK và cascade rõ ràng; không xóa mù quáng gây mất audit trail.
- Không hardcode môi trường trong model.

## Open decisions (§17)

- Cú pháp `ROW_FILTER.condition_expr` — có thể lưu string + validate phía service ở Epic 3/6; chốt sớm để tránh đổi schema.
