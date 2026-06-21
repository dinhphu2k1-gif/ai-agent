# M1 — Admin Contract Foundation (E9)

| | |
|---|---|
| **Mục tiêu** | Envelope `ApiResponse`, pagination, migration identity, repo list, router shell, seed tối thiểu |
| **Thời lượng** | 4–5 ngày |
| **Phụ thuộc** | Epic 2–3 |
| **Chặn** | M2, M3 |
| **Tiếp theo** | [m2-admin-users.md](m2-admin-users.md), [m3-admin-roles.md](m3-admin-roles.md) |

---

## Dev — checklist

### Schema & migration

- [x] **M1.1.1** `users.full_name`, `users.last_active_at` → `app/models/identity.py` + migration → Verify: `alembic upgrade head` OK
- [x] **M1.1.2** `roles.display_name` (default = `name` khi tạo) → Verify: insert role có `display_name`
- [x] **M1.1.3** `groups.description` nullable → Verify: cột tồn tại trong DB
- [x] **M1.1.4** (Tùy chọn) Seed `permission_type` USAGE, INSERT, UPDATE, DELETE → Verify: bảng type có đủ tên cho wizard sau

### Contract schemas

- [x] **M1.2.1** `ApiResponse[T]`, `ApiErrorData` trong `app/schemas/admin_contract.py` → Verify: import từ router không lỗi
- [x] **M1.2.2** `PageableResponse[T]`, query parser `page`/`pageSize`/`sort`/`search` (1-based) → Verify: unit test page=1 trả trang đầu
- [x] **M1.2.3** Helper `ok()` / `fail()` trong `app/api/deps.py` (hoặc `core/admin_response.py`) → Verify: JSON có `success`, `message`, `data`

### Repository

- [x] **M1.3.1** `identity_repo.list_users(...)` + count → Verify: `(rows, total)` với DB seed
- [x] **M1.3.2** `list_roles`, `list_groups` tương tự → Verify: pagination hoạt động
- [x] **M1.3.3** `get_user_by_id` eager load groups + direct roles → Verify: 1 query plan hợp lý (không N+1 từng user)
- [x] **M1.3.4** `add_user_role` idempotent → Verify: gán 2 lần không raise
- [x] **M1.3.5** `remove_user_role`, `list_users_for_role` → Verify: unit test add/remove

### Router & main

- [x] **M1.4.1** Tạo `app/api/admin_users.py`, prefix `/api/v1/admin`, tag `admin-users`, `verify_admin_mvp` → Verify: OpenAPI có path
- [x] **M1.4.2** Stub `app/api/admin_roles.py` — `GET /roles` trả list rỗng bọc envelope → Verify: curl 200
- [x] **M1.4.3** `main.py` include 2 router → Verify: `uvicorn` start không lỗi

### Seed

- [x] **M1.5.1** `scripts/seed_demo_data.py`: 3 users, 3 roles, 3 groups (contract §I) → Verify: chạy 2 lần không duplicate lỗi
- [x] **M1.5.2** Seed `USER_GROUP`, `USER_ROLE`, `GROUP_ROLE` cho `grp-de-core` → Verify: junction rows tồn tại

### Tests

- [x] **M1.T1** `tests/test_admin_contract_foundation.py` — envelope + pagination edge → Verify: `pytest` pass

---

## Verification (gate merge)

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/admin/roles?page=1&pageSize=10" | jq '.success, .message, .data'
```

**Done khi:**

- [x] Response envelope đúng shape FE.
- [x] Test Epic 2–3 vẫn pass (không break migration).
- [ ] PR review: không log token; migration reversible.

---

## QA (trước merge)

- [x] Pagination: `page` vượt range → list rỗng, `totalItems` đúng.
- [x] `pageSize=0` hoặc thiếu → 400 envelope hoặc default hợp lý (document).

---

## Giao việc gợi ý

| Dev | Phạm vi |
|-----|--------|
| Dev A | M1.1 + M1.3 |
| Dev B | M1.2 + M1.4 + M1.T1 |
| Dev A/B | M1.5 (sau migration) |

**PR đề xuất:** PR-1 (toàn bộ M1).
