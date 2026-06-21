# M4 — Group Management (E12)

| | |
|---|---|
| **Mục tiêu** | CRUD group, members, roles on group, direct permissions, **effective-permissions** |
| **Thời lượng** | 7–8 ngày |
| **Phụ thuộc** | [M1](m1-admin-foundation.md), [M3](m3-admin-roles.md) (`PermissionPresenter` + role perms) |
| **Chặn** | M5 |
| **Tiếp theo** | [m5-admin-polish.md](m5-admin-polish.md) |

**Endpoint contract §H:** #25–40

---

## Dev — checklist

### EffectivePermissionService — `app/services/effective_permission_service.py`

- [x] **M4.1.1** Load `GROUP_PERMISSION` → `ownership=group` → Verify: unit direct-only case
- [x] **M4.1.2** Load `GROUP_ROLE` → `ROLE_PERMISSION` → `ownership=role`, `sourceRoleName` → Verify: inherited only case
- [x] **M4.1.3** Dedupe + DENY wins (resource + action) → Verify: unit conflict case
- [x] **M4.1.4** `summary`, `inheritedSummary` counts → Verify: khớp contract §F.14

### AdminGroupService — `app/services/admin_group_service.py`

| Task | Endpoint # |
|------|------------|
| **M4.2.1** list, create, delete group | #25–27 |
| **M4.2.2** members list/add/remove + `members/catalog` | #28–31 |
| **M4.2.3** group roles assign/unassign + `roles/catalog` | #32–35 |
| **M4.2.4** direct permissions CRUD | #36–39 |
| **M4.2.5** `get_effective_permissions` | #40 |
| **M4.2.6** invalidate cache users khi đổi members | — |

### Routes — `app/api/admin_groups.py`

- [x] **M4.3.1** Router mới + `main.py` include, tag `admin-groups`
- [x] **M4.3.2** PUT/DELETE direct perm: từ chối nếu không phải `GROUP_PERMISSION` → Verify: 403 trên inherited row

### Seed

- [x] **M4.4.1** `grp-de-core`: 3 roles assigned + direct perms nếu cần demo → Verify: seed script
- [x] **M4.4.2** `GET .../effective-permissions` ~12 inherited (sau seed đủ) → Verify: manual hoặc snapshot

### Tests

- [x] **M4.T1** `tests/test_effective_permission_service.py`
- [x] **M4.T2** `tests/test_admin_groups_api.py`

---

## Verification (gate merge)

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/admin/groups/grp-de-core/effective-permissions" \
  | jq '.data.inheritedSummary, (.data.permissions | length)'
```

**Done khi:**

- [x] 16 endpoint group (#25–40).
- [x] Effective panel: inherited có `sourceRoleName`; direct có `ownership=group`.
- [x] Thêm/xóa member → cache user context invalidated.

---

## QA (trước merge)

- [ ] Không sửa inherited permission qua group PUT/DELETE (403/404).
- [ ] `memberCount` trên list nhất quán với GET members (hoặc documented).
- [ ] Grant permission trên role → xuất hiện trong group effective với đúng `sourceRoleName`.

---

## Giao việc gợi ý

| Dev | Phạm vi |
|-----|--------|
| Dev A | M4.1 + M4.2.5 + M4.T1 |
| Dev B | M4.2.1–M4.2.4 + M4.3 + M4.T2 |

**PR đề xuất:** PR-5 (sau PR-3).
