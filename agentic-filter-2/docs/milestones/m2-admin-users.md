# M2 — User Management (E10)

| | |
|---|---|
| **Mục tiêu** | API màn User Management + gán role trực tiếp (`USER_ROLE`) + assign user từ màn Role |
| **Thời lượng** | 4–5 ngày |
| **Phụ thuộc** | [M1](m1-admin-foundation.md) merged |
| **Chặn** | M4 (một phần), Actors đầy đủ trong M3 |
| **Tiếp theo** | [m3-admin-roles.md](m3-admin-roles.md) |

**Endpoint contract §H:** #1–8, #19–20

---

## Dev — checklist

### Service — `app/services/admin_user_service.py`

- [x] **M2.1.1** `list_users` → `UserListItem` (name, email, status, `groups[]`, `roles[]` string, initials, lastActive*) → Verify: khớp JSON §D.1
- [x] **M2.1.2** `get_user` → `UserDetail`, `roles` **chỉ direct** `USER_ROLE` → Verify: §D.2
- [x] **M2.1.3** `create_user` — `USER_GROUP` + `USER_ROLE` trong 1 transaction → Verify: `POST /users` + `GET` detail
- [x] **M2.1.4** `bulk_assign_groups`, `bulk_assign_roles`, `bulk_deactivate` (append) → Verify: `updatedCount` đúng
- [x] **M2.1.5** Mọi mutation: `record_policy_change` + `invalidate_cache_for_users` → Verify: mock Redis key cleared / version bump

### DTOs — `app/schemas/admin_contract.py`

- [x] **M2.2.1** `UserListItem`, `UserDetail`, `UserCreateBody`, bulk request bodies
- [x] **M2.2.2** `GroupOptionsOut`, `RoleOptionsOut`

### Routes — `app/api/admin_users.py`

| # | Method | Path | Task |
|---|--------|------|------|
| 1 | GET | `/users` | M2.3.1 |
| 2 | GET | `/users/{id}` | M2.3.2 |
| 3 | POST | `/users` | M2.3.3 |
| 4 | GET | `/groups/options` | M2.3.4 |
| 5 | GET | `/roles/options` | M2.3.5 |
| 6 | POST | `/users/bulk/assign-groups` | M2.3.6 |
| 7 | POST | `/users/bulk/assign-roles` | M2.3.7 |
| 8 | POST | `/users/bulk/deactivate` | M2.3.8 |

- [x] **M2.3.9** Filter `status`, `search` trên list → Verify: Inactive chỉ còn user inactive
- [x] **M2.3.10** 404 → `success: false`, code `NOT_FOUND`

### Actors (trong `app/api/admin_roles.py`)

| # | Method | Path | Task |
|---|--------|------|------|
| 19 | POST | `/roles/{id}/users` | M2.4.1 |
| 20 | DELETE | `/roles/{id}/users/{userId}` | M2.4.2 |

- [ ] **M2.4.3** (Tùy chọn) `GET /roles/{id}/actors` stub users direct — M3 hoàn thiện groups

### Tests

- [x] **M2.T1** `tests/test_admin_users_api.py` — list, create, bulk, 404 → Verify: `pytest` pass
- [x] **M2.T2** Bulk assign role 2 lần cùng cặp → Verify: không 500

---

## Verification (gate merge)

| Scenario | Cách kiểm tra |
|----------|----------------|
| List seed | `GET /users` → 3 user; John có `roles` chứa Admin |
| Create + role | `POST /users` body có `roles` → detail có role |
| Bulk role | `POST /users/bulk/assign-roles` → list cập nhật |
| Actors | `POST /roles/{id}/users` → `GET /users/{id}` thấy role |
| Unassign direct | `DELETE /roles/.../users/{id}` → `roles[]` mất; inherited qua group vẫn còn ở runtime |

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/admin/users?page=1&pageSize=10" | jq '.data.data[0].roles'
```

**Done khi:**

- [x] 8 endpoint user + POST/DELETE assign user trên role hoạt động.
- [x] FE có thể thay mock `mockUsers`.
- [x] Cache invalidate sau assign role (test hoặc manual Redis).

---

## QA (trước merge)

- [x] §D flows: list, detail, add user, bulk groups/roles, deactivate.
- [x] User có role direct + cùng role qua group: list `roles[]` chỉ direct; runtime vẫn merge (Epic 4–5).
- [ ] Không lộ stack trace; 401 không token.

---

## Giao việc gợi ý

| Dev | Phạm vi |
|-----|--------|
| Dev A | M2.1 + M2.3 (users router) |
| Dev B | M2.2 + M2.T* + M2.4 (actors) |

**PR đề xuất:** PR-2 (sau PR-1).
