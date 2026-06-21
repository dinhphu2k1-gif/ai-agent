# M3 — Role Management (E11)

| | |
|---|---|
| **Mục tiêu** | CRUD role, nested permissions (`PermissionPresenter`), actors đầy đủ, catalog |
| **Thời lượng** | 7–8 ngày |
| **Phụ thuộc** | [M1](m1-admin-foundation.md); khuyến nghị [M2](m2-admin-users.md) (USER_ROLE) |
| **Chặn** | M4, M5 (tree wizard) |
| **Tiếp theo** | [m4-admin-groups.md](m4-admin-groups.md) |

**Endpoint contract §H:** #9–24 (#19–20 có thể đã xong ở M2)

---

## Dev — checklist (theo thứ tự gợi ý)

### 1. PermissionPresenter — `app/services/permission_presenter.py`

- [x] **M3.1.1** Walk resource → `path: string[]` (DATABASE→…→COLUMN) → Verify: unit test 4 cấp
- [x] **M3.1.2** Map `action`, `modifier` (row_filter / column_mask) → Verify: khớp contract §C
- [x] **M3.1.3** `to_fe_permission`, `list_for_role(role_id)` → Verify: object đủ field FE

### 2. AdminRoleService — `app/services/admin_role_service.py`

- [x] **M3.2.1** `list_roles` + `permissionCount`, `userCount`, `groupCount` → Verify: list §E
- [x] **M3.2.2** `create_role`, `rename_role` (PATCH), `delete_role` → 409 if in use → Verify: DELETE role đang gán group → 409
- [x] **M3.2.3** `duplicate_role` — clone permissions, không clone actors → Verify: bản copy có perm, không có USER_ROLE
- [x] **M3.2.4** `list_permissions`, `grant_permissions`, `update_permission`, `delete_permission` → Verify: #14–17
- [x] **M3.2.5** `get_actors`, assign/unassign users & groups on role → Verify: #18–22 (bổ sung M2.4)
- [x] **M3.2.6** `users/catalog`, `groups/catalog` → Verify: #23–24

### 3. Routes — `app/api/admin_roles.py`

**Nhóm A — CRUD (#9–13)**

- [x] **M3.3.A** GET/POST `/roles`, PATCH `/roles/{id}`, POST duplicate, DELETE

**Nhóm B — Permissions (#14–17)**

- [x] **M3.3.B** GET/POST/PUT/DELETE `/roles/{id}/permissions[...]`

**Nhóm C — Actors (#18–22)**

- [x] **M3.3.C** GET actors full; POST/DELETE groups on role

**Nhóm D — Catalog (#23–24)**

- [x] **M3.3.D** GET `/users/catalog`, `/groups/catalog`

- [x] **M3.3.1** Thay stub M1 — router đầy đủ trong `main.py`
- [x] **M3.3.2** Map `IntegrityError` → 409 `ROLE_NAME_CONFLICT` / `ENTITY_IN_USE`

### 4. Seed

- [x] **M3.4.1** 8 permissions cho `role-data-scientist-eu` (ALLOW/DENY) → Verify: seed idempotent
- [x] **M3.4.2** GET permissions trả 8 items → Verify: curl count = 8

### Tests

- [x] **M3.T1** `tests/test_permission_presenter.py`
- [x] **M3.T2** `tests/test_admin_roles_api.py` — CRUD, perm, duplicate, delete 409

---

## Verification (gate merge)

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/admin/roles/role-data-scientist-eu/permissions" \
  | jq '.success, (.data | length)'
```

**Done khi:**

- [x] 16 endpoint role (#9–24) hoạt động.
- [x] DENY permission có `effect: DENY` trong JSON.
- [x] Sửa/xóa permission → audit + cache invalidation.

---

## QA (trước merge)

- [ ] Mở role demo → 8 permissions như contract §E.6.
- [ ] Duplicate role → permissions copied, actors không copy.
- [ ] Delete role referenced by group → 409 envelope.

---

## Giao việc gợi ý

| Sprint nội bộ | Nội dung |
|---------------|----------|
| Tuần 1 | M3.1 + M3.3.A + M3.T1 |
| Tuần 2 | M3.2 + M3.3.B–D + M3.4 + M3.T2 |

**PR đề xuất:** PR-3 (CRUD + permissions), PR-4 (actors + catalog) — sau PR-1; PR-4 sau PR-2 nếu dùng chung USER_ROLE tests.
