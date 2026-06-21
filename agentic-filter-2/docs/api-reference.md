# Filter Service — Danh mục API (đầy đủ)

Tài liệu tham chiếu cho **toàn bộ** endpoint hiện có. Chi tiết luồng runtime/filter cho agent: [api-fe-integration.md](./api-fe-integration.md).

**Base URL (local):** `http://127.0.0.1:8000` · **OpenAPI:** `GET /docs`

---

## 1. Xác thực (hai lớp)

| Lớp API | Prefix ví dụ | Header |
|---------|----------------|--------|
| **Runtime / Filter** | `/api/v1/runtime`, `/api/v1/filter` | `Authorization: Bearer <token>` (IAM hoặc bypass dev) |
| **Admin** | `/api/v1/admin/...` | `X-Admin-Token: <token>` nếu `ADMIN_API_TOKEN` được set |

Header admin tùy chọn:

| Header | Mô tả |
|--------|--------|
| `X-Changed-By` | Ghi audit policy (mặc định `admin-api`) |
| `X-Request-ID` | Correlation ID (runtime/filter) |

**Dev runtime:** `AUTH_BYPASS_ENABLED=true` — xem [api-fe-integration.md](./api-fe-integration.md) §2.1.

---

## 2. Định dạng response

### 2.1 Runtime / Filter (lỗi)

```json
{ "code": "unauthorized", "message": "...", "detail": null }
```

### 2.2 Admin contract (`/api/v1/admin/...` — Users, Groups, Roles)

Thành công:

```json
{
  "success": true,
  "message": "OK",
  "data": { }
}
```

Lỗi (ví dụ 404/409/403):

```json
{
  "success": false,
  "message": "Group not found",
  "data": { "code": "NOT_FOUND", "field": null }
}
```

Danh sách phân trang (`data`):

```json
{
  "data": [ ],
  "currentPage": 1,
  "totalItems": 42,
  "totalPages": 5
}
```

**Query phân trang (chung):** `page` (≥1), `pageSize` (1–500), `sort`, `orderBy`, `search`.

### 2.3 Admin MVP (permissions, assignments, resources CRUD, audit)

- Nhiều endpoint trả model trực tiếp (JSON object/array) hoặc `{"status":"ok"}`.
- Lỗi FastAPI: `{"detail": "..."}` hoặc body `code` như runtime.
- Gán permission đã có (theo `permission_id`): prefix **`/api/v1/admin/assignments`** — tách khỏi wizard grant trên `/api/v1/admin/groups|roles/.../permissions`.

---

## 3. Bảng tổng hợp endpoint

| # | Method | Path | Auth | Mô tả ngắn |
|---|--------|------|------|------------|
| **Health** |
| 1 | GET | `/health` | — | Health check |
| **Runtime** |
| 2 | GET | `/api/v1/runtime/user-context` | Bearer | User + groups + roles |
| 3 | POST | `/api/v1/runtime/authorize` | Bearer | Policy decision theo resource |
| **Filter** |
| 4 | POST | `/api/v1/filter/query` | Bearer | SELECT Postgres có policy |
| 5 | POST | `/api/v1/filter/search` | Bearer | OpenSearch có policy |
| **Admin — Resource tree (FE wizard)** |
| 6 | GET | `/api/v1/admin/resources/tree` | Admin | Cây DB/schema/table/column (camelCase, wizard) |
| **Admin — Users** |
| 7 | GET | `/api/v1/admin/users/catalog` | Admin | Catalog user (picker) |
| 8 | GET | `/api/v1/admin/users` | Admin | Danh sách user (page, `status`) |
| 9 | GET | `/api/v1/admin/users/{user_id}` | Admin | Chi tiết user |
| 10 | POST | `/api/v1/admin/users` | Admin | Tạo user |
| 11 | GET | `/api/v1/admin/groups/options` | Admin | Tên nhóm (dropdown) |
| 12 | GET | `/api/v1/admin/roles/options` | Admin | Tên role (dropdown) |
| 13 | POST | `/api/v1/admin/users/bulk/assign-groups` | Admin | Gán nhóm hàng loạt |
| 14 | POST | `/api/v1/admin/users/bulk/assign-roles` | Admin | Gán role hàng loạt |
| 15 | POST | `/api/v1/admin/users/bulk/deactivate` | Admin | Vô hiệu hóa hàng loạt |
| **Admin — Groups** |
| 16 | GET | `/api/v1/admin/groups` | Admin | Danh sách nhóm |
| 17 | POST | `/api/v1/admin/groups` | Admin | Tạo nhóm |
| 18 | DELETE | `/api/v1/admin/groups/{group_id}` | Admin | Xóa nhóm |
| 19 | GET | `/api/v1/admin/members/catalog` | Admin | Catalog user (thêm member) |
| 20 | GET | `/api/v1/admin/roles/catalog` | Admin | Catalog role (gán vào group) |
| 21 | GET | `/api/v1/admin/groups/{group_id}/members` | Admin | Thành viên nhóm |
| 22 | POST | `/api/v1/admin/groups/{group_id}/members` | Admin | Thêm member |
| 23 | DELETE | `/api/v1/admin/groups/{group_id}/members/{member_id}` | Admin | Xóa member |
| 24 | GET | `/api/v1/admin/groups/{group_id}/roles` | Admin | Role gán cho nhóm |
| 25 | POST | `/api/v1/admin/groups/{group_id}/roles` | Admin | Gán role cho nhóm |
| 26 | DELETE | `/api/v1/admin/groups/{group_id}/roles/{role_id}` | Admin | Gỡ role khỏi nhóm |
| 27 | GET | `/api/v1/admin/groups/{group_id}/permissions` | Admin | Quyền **trực tiếp** trên nhóm |
| 28 | POST | `/api/v1/admin/groups/{group_id}/permissions` | Admin | Cấp quyền (grant wizard) |
| 29 | PUT | `/api/v1/admin/groups/{group_id}/permissions/{permission_id}` | Admin | Sửa quyền trực tiếp |
| 30 | DELETE | `/api/v1/admin/groups/{group_id}/permissions/{permission_id}` | Admin | Xóa quyền trực tiếp |
| 31 | GET | `/api/v1/admin/groups/{group_id}/effective-permissions` | Admin | Quyền hiệu lực (direct + kế thừa role) |
| **Admin — Roles** |
| 32 | GET | `/api/v1/admin/roles` | Admin | Danh sách role |
| 33 | POST | `/api/v1/admin/roles` | Admin | Tạo role |
| 34 | PATCH | `/api/v1/admin/roles/{role_id}` | Admin | Đổi tên role |
| 35 | POST | `/api/v1/admin/roles/{role_id}/duplicate` | Admin | Nhân bản role |
| 36 | DELETE | `/api/v1/admin/roles/{role_id}` | Admin | Xóa role |
| 37 | GET | `/api/v1/admin/roles/{role_id}/permissions` | Admin | Danh sách quyền của role |
| 38 | POST | `/api/v1/admin/roles/{role_id}/permissions` | Admin | Cấp quyền cho role |
| 39 | PUT | `/api/v1/admin/roles/{role_id}/permissions/{permission_id}` | Admin | Sửa quyền role |
| 40 | DELETE | `/api/v1/admin/roles/{role_id}/permissions/{permission_id}` | Admin | Xóa quyền role |
| 41 | GET | `/api/v1/admin/roles/{role_id}/actors` | Admin | User/group chịu ảnh hưởng bởi role |
| 42 | POST | `/api/v1/admin/roles/{role_id}/users` | Admin | Gán user vào role |
| 43 | DELETE | `/api/v1/admin/roles/{role_id}/users/{user_id}` | Admin | Gỡ user khỏi role |
| 44 | POST | `/api/v1/admin/roles/{role_id}/groups` | Admin | Gán nhóm vào role |
| 45 | DELETE | `/api/v1/admin/roles/{role_id}/groups/{group_id}` | Admin | Gỡ nhóm khỏi role |
| 46 | GET | `/api/v1/admin/groups/catalog` | Admin | Catalog nhóm (picker) |
| **Admin — Permissions (low-level)** |
| 47 | POST | `/api/v1/admin/permissions` | Admin | Tạo permission record |
| 48 | GET | `/api/v1/admin/permissions` | Admin | Liệt kê (`limit`, `offset`) |
| 49 | PATCH | `/api/v1/admin/permissions/{permission_id}` | Admin | Đổi `effect` |
| 50 | DELETE | `/api/v1/admin/permissions/{permission_id}` | Admin | Xóa permission |
| 51 | POST | `/api/v1/admin/permissions/{permission_id}/row-filters` | Admin | Thêm row filter |
| 52 | POST | `/api/v1/admin/permissions/{permission_id}/column-masks` | Admin | Thêm/sửa column mask |
| **Admin — Assignments (gán permission/role đã có)** |
| 53 | POST | `/api/v1/admin/assignments/users/{user_id}/permissions` | Admin | Gán permission → user |
| 54 | POST | `/api/v1/admin/assignments/groups/{group_id}/permissions` | Admin | Gán permission → group |
| 55 | POST | `/api/v1/admin/assignments/roles/{role_id}/permissions` | Admin | Gán permission → role |
| 56 | POST | `/api/v1/admin/assignments/users/{user_id}/groups` | Admin | User vào group |
| 57 | POST | `/api/v1/admin/assignments/users/{user_id}/roles` | Admin | User nhận role |
| 58 | POST | `/api/v1/admin/assignments/groups/{group_id}/roles` | Admin | Group nhận role |
| **Admin — Resource catalog (CRUD)** |
| 59 | POST | `/api/v1/admin/resources/databases` | Admin | Tạo database logic |
| 60 | POST | `/api/v1/admin/resources/schemas` | Admin | Tạo schema |
| 61 | POST | `/api/v1/admin/resources/tables` | Admin | Tạo table |
| 62 | POST | `/api/v1/admin/resources/columns` | Admin | Tạo column |
| 63 | GET | `/api/v1/admin/resources/mvp-tree` | Admin | Cây resource (Epic 3) |
| **Admin — Audit** |
| 64 | GET | `/api/v1/admin/audit/access-logs` | Admin | Log truy cập runtime |
| 65 | GET | `/api/v1/admin/audit/permission-change-logs` | Admin | Log thay đổi policy |

---

## 4. Health

### `GET /health`

Response: `{ "status": "ok" }`

---

## 5. Runtime & Filter

Xem chi tiết request/response, lỗi, SQL subset: **[api-fe-integration.md](./api-fe-integration.md)** (§4–§7).

| Method | Path |
|--------|------|
| GET | `/api/v1/runtime/user-context` |
| POST | `/api/v1/runtime/authorize` |
| POST | `/api/v1/filter/query` |
| POST | `/api/v1/filter/search` |

---

## 6. Admin — Users

Prefix: `/api/v1/admin`

### `GET /users/catalog`

Phân trang. `data[]`: `{ id, name, email, isOnline, avatarUrl }`.

### `GET /users`

Query: `page`, `pageSize`, `sort`, `orderBy`, `search`, `status` (mặc định `All`).

`data[]`: `{ id, name, email, status, groups[], roles[], initials, lastActive, lastActiveAt }`.

### `GET /users/{user_id}`

`data`: `{ id, name, email, username, status, groups[{id,name}], roles[{id,name}], ... }`.

### `POST /users` → 201

Body (camelCase):

```json
{
  "fullName": "Nguyen Van A",
  "email": "a@example.com",
  "username": "user_a",
  "groups": ["uuid-or-empty"],
  "roles": [],
  "isActive": true
}
```

### `GET /groups/options` / `GET /roles/options`

`data`: `{ "groups": ["Tên nhóm", ...] }` hoặc `{ "roles": ["Tên role", ...] }`.

### `POST /users/bulk/assign-groups`

```json
{
  "userIds": ["uuid", "uuid"],
  "groupIds": [],
  "groupNames": ["Tên nhóm"]
}
```

### `POST /users/bulk/assign-roles`

```json
{
  "userIds": ["uuid"],
  "roleIds": [],
  "roleNames": ["Tên role"]
}
```

### `POST /users/bulk/deactivate`

```json
{ "userIds": ["uuid"] }
```

Response `data`: `{ "updatedCount": 3 }`.

---

## 7. Admin — Groups

Prefix: `/api/v1/admin`

### `GET /groups`

`data`: pageable `GroupListItem` — `{ id, name, memberCount, roleCount, description, createdAt, createdAtLabel }`.

### `POST /groups` → 201

```json
{ "name": "sales-team", "description": "optional" }
```

Conflict `409`: `GROUP_NAME_CONFLICT`.

### `DELETE /groups/{group_id}`

### `GET /members/catalog` / `GET /roles/catalog`

Picker phân trang cho UI gán member/role.

### Members

| Method | Path | Body |
|--------|------|------|
| GET | `/groups/{group_id}/members` | — |
| POST | `/groups/{group_id}/members` | `{ "memberIds": ["user-uuid"] }` |
| DELETE | `/groups/{group_id}/members/{member_id}` | — |

### Roles on group

| Method | Path | Body |
|--------|------|------|
| GET | `/groups/{group_id}/roles` | — |
| POST | `/groups/{group_id}/roles` | `{ "roleIds": ["role-uuid"] }` |
| DELETE | `/groups/{group_id}/roles/{role_id}` | — |

### Permissions on group (grant wizard)

| Method | Path | Body |
|--------|------|------|
| GET | `/groups/{group_id}/permissions` | `data`: `{ permissions[], summary }` |
| POST | `/groups/{group_id}/permissions` | `PermissionGrantBody` → 201 |
| PUT | `/groups/{group_id}/permissions/{permission_id}` | `PermissionGrantBody` |
| DELETE | `/groups/{group_id}/permissions/{permission_id}` | — |

`403` `PERMISSION_NOT_DIRECT`: quyền kế thừa từ role — không sửa/xóa qua API group.

### `GET /groups/{group_id}/effective-permissions`

Quyền **trực tiếp + kế thừa từ role** gán cho nhóm. `data`: `{ permissions[], summary, inheritedSummary }`.

---

## 8. Admin — Roles

Prefix: `/api/v1/admin`

### `GET /roles`

`data[]`: `{ id, name, displayName, permissionCount, userCount, groupCount, icon }`.

### `POST /roles` → 201

```json
{ "name": "analyst" }
```

### `PATCH /roles/{role_id}`

```json
{ "name": "analyst-renamed" }
```

### `POST /roles/{role_id}/duplicate` → 201

### `DELETE /roles/{role_id}`

`409` `ENTITY_IN_USE` nếu role còn gán user/group.

### Permissions on role

| Method | Path | Body |
|--------|------|------|
| GET | `/roles/{role_id}/permissions` | — |
| POST | `/roles/{role_id}/permissions` | `PermissionGrantBody` |
| PUT | `/roles/{role_id}/permissions/{permission_id}` | `PermissionGrantBody` |
| DELETE | `/roles/{role_id}/permissions/{permission_id}` | — |

### `GET /roles/{role_id}/actors`

`data`: `{ users[], groups[], totalAffectedUsers }`.

### Gán actor

| Method | Path | Body |
|--------|------|------|
| POST | `/roles/{role_id}/users` | `{ "userIds": ["uuid"] }` |
| DELETE | `/roles/{role_id}/users/{user_id}` | — |
| POST | `/roles/{role_id}/groups` | `{ "groupIds": ["uuid"] }` |
| DELETE | `/roles/{role_id}/groups/{group_id}` | — |

### `GET /groups/catalog`

Picker nhóm (phân trang).

---

## 9. Permission — schema dùng chung (FE wizard)

`PermissionGrantBody` (POST/PUT trên **role** hoặc **group**):

```json
{
  "resourcePath": [
    { "id": "db-resource-uuid", "name": "demo_db", "type": "database" },
    { "id": "schema-uuid", "name": "public", "type": "schema" },
    { "id": "table-uuid", "name": "orders", "type": "table" }
  ],
  "resourceType": "table",
  "actions": ["SELECT"],
  "effect": "ALLOW",
  "rowFilter": {
    "enabled": true,
    "conditionExpression": "tenant_id = 1"
  },
  "columnMask": {
    "enabled": false,
    "maskType": null,
    "maskPattern": null
  }
}
```

Response permission (trong list):

```json
{
  "id": "permission-uuid",
  "resourceType": "table",
  "path": [{ "label": "demo_db", "resourceId": "..." }],
  "effect": "ALLOW",
  "action": "SELECT",
  "modifier": {
    "type": "ROW_FILTER",
    "label": "Row filter",
    "conditionExpression": "tenant_id = 1",
    "maskType": null,
    "maskPattern": null
  },
  "isHighlighted": false
}
```

`modifier.type`: `ROW_FILTER` | `COLUMN_MASK`.

`summary` (kèm list): `{ total, allowCount, denyCount, modifierCount }`.

### 9.1 Grant create — `data.created[]` và lỗi validation

**POST** `/api/v1/admin/roles/{roleId}/permissions` và **POST** `/api/v1/admin/groups/{groupId}/permissions` trả **201** với:

```json
{
  "success": true,
  "message": "Permissions created",
  "data": {
    "created": [
      {
        "id": "permission-uuid-1",
        "resourceType": "TABLE",
        "path": [
          { "label": "analytics_db", "resourceId": "..." },
          { "label": "public", "resourceId": "..." },
          { "label": "users", "resourceId": "..." }
        ],
        "effect": "ALLOW",
        "action": "SELECT",
        "modifier": {
          "type": "ROW_FILTER",
          "label": "tenant_id = 1",
          "conditionExpression": "tenant_id = 1",
          "maskType": null,
          "maskPattern": null
        }
      }
    ]
  }
}
```

| Semantics | Mô tả |
|-----------|--------|
| **Một permission mỗi action** | `actions: ["SELECT", "DESCRIBE"]` → `created.length === 2`; mỗi item một `action` khác nhau, cùng `resourcePath` / modifier (nếu có). |
| **Không modifier** | `rowFilter` / `columnMask` absent hoặc `enabled: false` → không tạo `row_filters` / `column_masks`; `modifier` có thể `null` trong list. |
| **DATABASE / SCHEMA** | Grant hợp lệ không có row filter / column mask; `INVALID_MODIFIER` nếu bật modifier sai cấp. |

**PUT** `/roles/{roleId}/permissions/{permissionId}` (và tương tự group) trả **200** với **một** `FePermissionOut` trong `data` (không có `created[]`). Cập nhật một permission; `actions[0]` quyết định action sau PUT.

**Lỗi** — envelope `success: false`, `data: { "code": "<CODE>", "field": null }`:

| HTTP | `data.code` | Khi nào |
|------|-------------|---------|
| 400 | `BAD_REQUEST` | `actions` rỗng; `effect` không ALLOW/DENY; thiếu `conditionExpression` / `maskPattern`; cả row filter và column mask enabled; segment path không hợp lệ |
| 400 | `INVALID_ACTION` | Action không có trong `permission_types` |
| 400 | `INVALID_MODIFIER` | Row filter không phải TABLE; column mask không phải COLUMN |
| 404 | `RESOURCE_NOT_FOUND` | `resourcePath[].id` không tồn tại hoặc không khớp hierarchy (không auto-tạo catalog khi grant) |

Implementation: [`PermissionGrantService`](../app/services/permission_grant_service.py), handler map `GrantValidationError` → [`grant_validation_error`](../app/core/admin_response.py).

### 9.2 Catalog wizard (Phase 4)

| Method | Path | `data` |
|--------|------|--------|
| GET | `/api/v1/admin/resources/search?q=&limit=50` | `{ results: [{ node, path[], breadcrumb }] }` |
| GET | `/api/v1/admin/resources/{resourceId}/scope-stats` | `ResourceScopeStatsOut` (DATABASE hoặc SCHEMA) |
| GET | `/api/v1/admin/permissions/action-catalog?resourceType=TABLE` | `{ actions: ["SELECT", "DESCRIBE", ...] }` |

`scope-stats` trên TABLE/COLUMN → 400 `BAD_REQUEST`. `action-catalog` với `resourceType` không hỗ trợ → 400.

### 9.3 Wizard DX — validate & preview (Phase 5)

| Method | Path | Body | `data` |
|--------|------|------|--------|
| POST | `/api/v1/admin/permissions/validate/row-filter` | `{ resourcePath?, conditionExpression }` | `{ valid, normalizedExpression, errors[] }` |
| POST | `/api/v1/admin/permissions/preview/column-mask` | `{ maskType, maskPattern?, sampleValue }` | `{ maskedValue, algorithm }` |

Preview **không** ghi DB. `HASH` dùng salt dev [`masking_hash_salt`](../app/core/config.py). PUT edit: xem §9.1 — chỉ `actions[0]`.

---

## 10. Admin — Permissions (low-level CRUD)

Prefix: `/api/v1/admin/permissions`

Dùng khi đã có `permission_type_id` trong DB (seed/types). UI wizard thường dùng §9 thay vì API này.

### `POST /api/v1/admin/permissions` → 201

```json
{
  "resource_id": "uuid",
  "permission_type_id": "uuid",
  "effect": "ALLOW"
}
```

Response: `{ id, resource_id, permission_type_id, effect }`.

### `GET /api/v1/admin/permissions`

Query: `limit` (max 500), `offset`.

### `PATCH /api/v1/admin/permissions/{permission_id}`

```json
{ "effect": "DENY" }
```

### `DELETE /api/v1/admin/permissions/{permission_id}` → 204

### `POST /api/v1/admin/permissions/{permission_id}/row-filters` → 201

```json
{ "condition_expr": "tenant_id = 1" }
```

### `POST /api/v1/admin/permissions/{permission_id}/column-masks` → 201

```json
{
  "mask_type": "FULL",
  "mask_pattern": null
}
```

`mask_type`: `FULL` | `PARTIAL` | `HASH` | `NULLIFY` | `CUSTOM` (cần `mask_pattern`).

---

## 11. Admin — Assignments (gán liên kết)

Prefix: `/api/v1/admin/assignments`

Gán **permission đã tồn tại** (tạo bởi §10) tới subject — khác wizard grant ở §9:

| Method | Path | Body |
|--------|------|------|
| POST | `/api/v1/admin/assignments/users/{user_id}/permissions` | `{ "permission_id": "uuid", "granted_by": "optional" }` |
| POST | `/api/v1/admin/assignments/groups/{group_id}/permissions` | `{ "permission_id": "uuid" }` |
| POST | `/api/v1/admin/assignments/roles/{role_id}/permissions` | `{ "permission_id": "uuid" }` |
| POST | `/api/v1/admin/assignments/users/{user_id}/groups` | `{ "group_id": "uuid" }` |
| POST | `/api/v1/admin/assignments/users/{user_id}/roles` | `{ "role_id": "uuid" }` |
| POST | `/api/v1/admin/assignments/groups/{group_id}/roles` | `{ "role_id": "uuid" }` |

Response thành công: `{ "status": "ok" }`.

`POST .../users/.../groups` trùng membership → `400` `{ "code": "bad_request", ... }`.

---

## 12. Admin — Resource catalog

### `GET /api/v1/admin/resources/tree`

Cây cho permission wizard (camelCase, `isPrimaryKey`, `isForeignKey`).

- Không có query: cây lồng đầy đủ (`children` nested).
- `parentId` (UUID, Phase 6): chỉ **một cấp** con trực tiếp; mỗi node `children: null` (lazy expand).

### `GET /api/v1/admin/resources/mvp-tree`

Cây dạng Epic 3: `{ databases: [{ resource_id, name, schemas: [...] }] }`.

### CRUD

| Method | Path | Body chính |
|--------|------|------------|
| POST | `/api/v1/admin/resources/databases` | `{ name, description? }` |
| POST | `/api/v1/admin/resources/schemas` | `{ database_id, name }` |
| POST | `/api/v1/admin/resources/tables` | `{ schema_id, name }` |
| POST | `/api/v1/admin/resources/columns` | `{ table_id, name, data_type }` |

---

## 13. Admin — Audit

Prefix: `/api/v1/admin/audit`

### `GET /access-logs`

Query: `limit`, `offset`. Trả mảng: `user_id`, `resource_id`, `action`, `result`, `decision`, `request_id`, `accessed_at`.

### `GET /permission-change-logs`

Trả mảng: `permission_id`, `changed_by`, `change_type`, `changed_at`, `detail`.

---

## 14. Quan hệ User ↔ Group ↔ Role ↔ Permission

```text
User ──member──► Group ──has role──► Role
  │                │                    │
  │                └── direct perm       └── permissions (grant wizard)
  ├── direct role assignment
  └── direct permission (assignments API)

Effective quyền user (runtime):
  - Role trực tiếp + role kế thừa qua group
  - Permission gán user / group / role
  - DENY thắng ALLOW (PDP)
```

**Hai cách cấp quyền cho FE admin:**

1. **Wizard (khuyến nghị):** `POST /api/v1/admin/roles|groups/{id}/permissions` với `PermissionGrantBody`.
2. **Low-level:** tạo permission §10, rồi gán §11.

---

## 15. Mã lỗi admin thường gặp

| HTTP | `data.code` (khi có) | Tình huống |
|------|----------------------|------------|
| 404 | `NOT_FOUND` | User/group/role/permission không tồn tại |
| 409 | `GROUP_NAME_CONFLICT`, `ROLE_NAME_CONFLICT` | Trùng tên |
| 409 | `ENTITY_IN_USE` | Xóa role đang được dùng |
| 409 | `BAD_REQUEST` | Resource path không resolve |
| 403 | `PERMISSION_NOT_DIRECT` | Sửa/xóa quyền kế thừa qua group API |

---

## 16. Liên kết

| Tài liệu | Nội dung |
|----------|----------|
| [api-fe-integration.md](./api-fe-integration.md) | Runtime/filter, Bearer, ví dụ fetch |
| [huong-dan-chay-va-curl.md](./huong-dan-chay-va-curl.md) | Chạy local, seed, curl |
| `/docs` | Swagger UI đầy đủ schema |
