# Epic 3: Admin API

## Tham chiếu

- [architecture_plan.md](architecture_plan.md) **§14 Epic 3**, **§6 Admin flow**, **§8.2 Admin API**, **§9** (`api/admin_*.py`, `schemas/admin.py`, `services/audit_service.py`, `cache/invalidation.py`).

## Mục tiêu epic

Cho phép admin quản lý resource tree, permission ALLOW/DENY, assignment user/group/role, row filter và column mask; ghi `PERMISSION_CHANGE_LOG` và **invalidate cache** sau thay đổi (**§10**).

## Phụ thuộc

- **Epic 2** (schema + repository).

## Dev-agent — checklist triển khai

- [x] Pydantic schemas admin; router `admin_resources`, `admin_permissions`, `admin_assignments` theo **§8.2** (contract tối thiểu MVP).
- [x] CRUD resource: database → schema → table → column.
- [x] Tạo permission gắn `resource_id`, `permission_type_id`, effect ALLOW/DENY.
- [x] Assignment: user/group/role ↔ permission; role/group nesting theo ERD.
- [x] API row filter + column mask gắn permission.
- [x] Ghi `PERMISSION_CHANGE_LOG` mọi thay đổi permission/assignment/filter/mask ảnh hưởng policy.
- [x] Gọi invalidation cache: affected users hoặc bump `permission_version` (**§10 MVP**).
- [x] Chuẩn hóa lỗi `400` payload sai; không lộ stack ra client.

## Acceptance criteria (§14)

- Admin có thể tạo database/schema/table/column.
- Admin có thể gán permission cho user/group/role.
- Permission change log được ghi đúng.

## QA-agent — phạm vi kiểm thử

- §15.2: *Permission admin update làm cache snapshot bị invalidate* (sau khi có cache Epic 4 — có thể viết test integration sau Epic 4 hoặc mock Redis).
- Happy path admin API + negative: resource không tồn tại, FK violation trả lỗi rõ.

## Code review — trọng tâm

- Phân quyền **admin** (ai gọi được API này) — nếu MVP chưa có IAM admin role, ghi rõ guard tạm hoặc network policy.
- Không log payload nhạy cảm đầy đủ.

## Open decisions (§17)

- Đồng bộ user/group/role từ IAM vs quản lý bản sao trong Permission DB — ảnh hưởng assignment API và validation.
