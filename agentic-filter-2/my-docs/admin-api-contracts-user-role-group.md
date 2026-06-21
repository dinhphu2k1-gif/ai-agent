# Hợp đồng API — User / Role / Group Management

> **Phiên bản:** 2026-05-19 (viết lại — ví dụ khớp mock/UI)  
> **Đối tượng:** Nhóm backend + FE (`agentic-fe`)  
> **Routes FE:** `/admin/users`, `/admin/roles`, `/admin/groups`  
> **Prefix đề xuất:** `/api/v1/admin`  
> **Envelope FE:** `ApiResponse<T>` — `src/api/index.ts`

Tài liệu mô tả endpoint và **JSON mẫu trích từ dữ liệu đang hiển thị trên UI** (mock hiện tại). Backend có thể đổi path; cần giữ **shape `data`** tương đương để FE ghép API.

---

## A. Quy ước tích hợp

### A.1 HTTP & auth

| Mục | Giá trị |
|-----|---------|
| Base URL | `VITE_APP_API_URL` |
| Prefix | `/api/v1/admin` |
| Auth | `Authorization: Bearer <accessToken>` |
| Content-Type | `application/json` |

### A.2 Envelope response

```json
{
  "success": true,
  "message": "OK",
  "data": {}
}
```

**Lỗi:**

```json
{
  "success": false,
  "message": "Role name already exists",
  "data": {
    "code": "ROLE_NAME_CONFLICT",
    "field": "name"
  }
}
```

| HTTP | FE xử lý |
|------|-----------|
| `403` | Redirect `VITE_LOGIN_URL` |
| `400` | Validation — hiển thị `message` |
| `404` | Không tìm thấy entity |
| `409` | Conflict (tên trùng, xóa entity đang dùng) |

### A.3 Phân trang

Query: `page`, `pageSize`, `sort`, `orderBy` (khớp `PageableRequest`).

`data` bọc `PageableResponse<T>`:

```json
{
  "data": [],
  "currentPage": 1,
  "totalItems": 3,
  "totalPages": 1
}
```

> **Cần thống nhất:** `page` 0-based hay 1-based.

### A.4 Thời gian & nhãn hiển thị

UI User Management hiện dùng chuỗi tương đối (`"2 mins ago"`, `"3 days ago"`). Đề xuất API:

| Trường | Kiểu | UI |
|--------|------|-----|
| `lastActiveAt` | ISO 8601 | FE format relative |
| `lastActiveLabel` | `string` (optional) | Hiển thị trực tiếp nếu backend muốn giữ copy sẵn |

Tương tự `createdAt` trên group: mock hiển thị `"Oct 12, 2023"` — API nên trả ISO; FE format locale.

### A.5 Ghi chú FE (frontend-api-integration-patterns)

- Hủy request khi đổi `selectedRoleId` / `selectedGroupId` (`AbortController`).
- Search catalog: debounce ~400ms.
- Chỉ retry 5xx; không retry 4xx.
- Mutations: loading / error / success từng thao tác; tránh global loading chung.

### A.6 Role: `name` vs `displayName`

Cùng `roleId` nhưng **tên khác nhau giữa hai màn**:

| `roleId` | Role Management (list) | Group Management (assigned role card) |
|----------|------------------------|-------------------------------------|
| `role-data-scientist-eu` | `Data_Scientist_EU` | `Data Pipeline Admin` |
| `role-marketing-analyst` | `Marketing_Analyst` | `Warehouse Read-Only` |
| `role-sysadmin-global` | `SysAdmin_Global` | `Platform Auditor` |

**Đề xuất model Role:**

```json
{
  "id": "role-data-scientist-eu",
  "name": "Data_Scientist_EU",
  "displayName": "Data Pipeline Admin",
  "description": "Full access to manage and execute ETL pipelines..."
}
```

FE Role list dùng `name`; Group panel dùng `displayName` (hoặc `label`).

---

## B. Ánh xạ UI → API

### B.1 User Management (`src/pages/user-management/`)

| UI | Hành vi | Endpoint | Nguồn mock |
|----|---------|----------|------------|
| `UserTable` | Danh sách + checkbox | `GET /users` | `mockUsers` trong `index.tsx` |
| `Toolbar` | Search / filter status | `GET /users?search=&status=` | (chưa wire) |
| `UserDetailDrawer` | Xem chi tiết row | `GET /users/{id}` | row đã chọn |
| `AddUserDrawer` | Tạo user | `POST /users` | `UserFormData` |
| `AddUserDrawer` | Dropdown groups/roles | `GET /groups/options`, `GET /roles/options` | `GROUPS` / `ROLES` constants |
| `AddGroupDrawer` (bulk) | Gán group | `POST /users/bulk/assign-groups` | `selectedIds` |
| `AddRoleDrawer` (bulk) | Gán role | `POST /users/bulk/assign-roles` | `selectedIds` |
| `ConfirmDeactivateModal` | Deactivate | `POST /users/bulk/deactivate` | `selectedIds` |

### B.2 Role Management (`src/pages/role-management/`)

| UI | Hành vi | Endpoint | Nguồn mock |
|----|---------|----------|------------|
| `RoleListPanel` | List + search | `GET /roles` | `initialRoles` |
| `RoleListPanel` | Duplicate / rename / delete | `POST .../duplicate`, `PATCH`, `DELETE` | handlers trong `index.tsx` |
| `AddRoleDrawer` | Tạo role | `POST /roles` | `RoleFormData` |
| `PermissionsPanel` | List permissions | `GET /roles/{roleId}/permissions` | `dataScientistPermissions` (8 dòng) |
| `AddPermissionDrawer` | Grant / edit | `POST` / `PUT` permissions | `PermissionGrantPayload` |
| `AddPermissionDrawer` | Cây resource | `GET /resources/tree` | `MOCK_RESOURCES` |
| `ActorsPanel` | Users + groups | `GET /roles/{roleId}/actors` | `initialActorsByRoleId` |
| Assign drawers | Catalog | `GET /users/catalog`, `GET /groups/catalog` | `AVAILABLE_*_CATALOG` |

**Mặc định khi mở màn:** `selectedRoleId = role-data-scientist-eu`.

### B.3 Group Management (`src/pages/group-management/`)

| UI | Hành vi | Endpoint | Nguồn mock |
|----|---------|----------|------------|
| `GroupListPanel` | List + search | `GET /groups` | `initialGroups` |
| `AddGroupDrawer` | Tạo group | `POST /groups` | `GroupFormData` |
| `GroupDetailPanel` | Members | `GET /groups/{id}/members` | `membersByGroupId` |
| `AddMemberToGroupDrawer` | Thêm member | `POST /groups/{id}/members` | `AVAILABLE_MEMBERS_CATALOG` |
| `GroupDetailPanel` | Assigned roles | `GET /groups/{id}/roles` | `rolesByGroupId` |
| `AssignRolesToGroupDrawer` | Gán role | `POST /groups/{id}/roles` | `AVAILABLE_ROLES_CATALOG` |
| `GroupPermissionsPanel` | Effective permissions | `GET /groups/{id}/effective-permissions` | merge direct + inherited |
| `AddPermissionDrawer` | Direct grant | `POST /groups/{id}/permissions` | `permissionsByGroupId` |
| Inherited row | Edit/delete | — | Chỉ qua Role API |
| Direct row | Edit/delete | `PUT` / `DELETE` group permissions | `ownership: group` |

**Mặc định khi mở màn:** `selectedGroupId = grp-de-core`.

---

## C. Model dùng chung

> Types: `src/pages/role-management/types.ts`, `src/pages/group-management/types.ts`, `src/components/add-permission/types.ts`

### C.1 Permission (hiển thị trên list)

```typescript
type PermissionEffect = 'ALLOW' | 'DENY'
type PermissionAction = 'USAGE' | 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE'
type ResourceType = 'DATABASE' | 'SCHEMA' | 'TABLE' | 'COLUMN'

interface Permission {
  id: string
  resourceType: ResourceType
  path: { label: string; resourceId?: string }[]
  effect: PermissionEffect
  action: PermissionAction
  modifier?: {
    type: 'ROW_FILTER' | 'COLUMN_MASK'
    label: string
    conditionExpression?: string
    maskType?: 'FULL' | 'PARTIAL' | 'HASH' | 'NULLIFY'
    maskPattern?: string
  }
  isHighlighted?: boolean  // UI: viền đỏ — DENY nổi bật
}
```

**Ví dụ đặc trưng UI** (dòng DENY highlight — `perm-table-2`):

```json
{
  "id": "perm-table-2",
  "resourceType": "TABLE",
  "path": [{ "label": "raw_events" }, { "label": "pii_dump_raw" }],
  "effect": "DENY",
  "action": "SELECT",
  "isHighlighted": true
}
```

*Nguồn: `src/pages/role-management/mock-data.ts` — `dataScientistPermissions`*

### C.2 EffectivePermission (Group Management)

```typescript
interface EffectivePermission extends Permission {
  ownership: 'group' | 'role'
  sourceRoleId: string | null
  sourceRoleName: string  // "Direct" | "Data Pipeline Admin" | ...
}
```

### C.3 PermissionGrantPayload (Add Permission wizard)

```json
{
  "resourcePath": [
    { "id": "db1", "name": "analytics_db", "type": "database" },
    { "id": "sch1", "name": "public", "type": "schema" },
    { "id": "tbl1", "name": "users", "type": "table" },
    { "id": "col2", "name": "email", "type": "column" }
  ],
  "resourceType": "column",
  "actions": ["SELECT"],
  "effect": "ALLOW",
  "columnMask": {
    "enabled": true,
    "maskType": "PARTIAL",
    "maskPattern": "***@***.com"
  }
}
```

Backend expand → 1 permission / action. FE mapper: `src/components/add-permission/utils/mapGrantPayloadToPermissions.ts`.

---

## D. User Management

**Route:** `/admin/users`  
**Nguồn:** `src/pages/user-management/index.tsx`

### D.1 GET `/users`

**Query:** `page`, `pageSize`, `search`, `status` (`Active` | `Inactive` | `All`)

**Response** — đủ **3 user** như bảng trên màn hình:

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "data": [
      {
        "id": "1",
        "name": "John Doe",
        "email": "john.doe@insight.io",
        "status": "Active",
        "groups": ["Data Science", "Alpha Team"],
        "roles": ["Admin"],
        "lastActive": "2 mins ago",
        "lastActiveAt": "2026-05-19T08:58:00Z",
        "initials": "JD"
      },
      {
        "id": "2",
        "name": "Alice Smith",
        "email": "a.smith@insight.io",
        "status": "Inactive",
        "groups": ["Marketing"],
        "roles": ["Viewer"],
        "lastActive": "3 days ago",
        "lastActiveAt": "2026-05-16T10:00:00Z",
        "initials": "AS"
      },
      {
        "id": "3",
        "name": "Bob Chen",
        "email": "b.chen@insight.io",
        "status": "Active",
        "groups": ["Engineering", "Backend", "DevOps"],
        "roles": ["Editor", "Deployer"],
        "lastActive": "1 hr ago",
        "lastActiveAt": "2026-05-19T07:30:00Z",
        "initials": "BC"
      }
    ],
    "currentPage": 1,
    "totalItems": 3,
    "totalPages": 1
  }
}
```

### D.2 GET `/users/{userId}`

Ví dụ `userId = "1"` (John Doe — mở drawer khi click row):

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "id": "1",
    "name": "John Doe",
    "email": "john.doe@insight.io",
    "username": "john.doe",
    "status": "Active",
    "groups": [
      { "id": "grp-catalog-ds", "name": "Data Science" },
      { "id": "grp-catalog-alpha", "name": "Alpha Team" }
    ],
    "roles": [{ "id": "role-catalog-admin", "name": "Admin" }],
    "lastActive": "2 mins ago",
    "lastActiveAt": "2026-05-19T08:58:00Z",
    "initials": "JD"
  }
}
```

> Phase 1 form Add User vẫn dùng **tên** group/role string; phase 2 nên chuyển sang `groupIds` / `roleIds`.

### D.3 POST `/users`

**Body** (khớp `AddUserDrawer` / Zod):

```json
{
  "fullName": "Jane Doe",
  "email": "jane.doe@insight.io",
  "username": "jane.doe",
  "groups": ["Data Science", "Alpha Team"],
  "roles": ["Editor"],
  "isActive": true
}
```

**Response `data`:** user mới (cùng shape list item, `id` do server sinh).

### D.4 GET `/groups/options` và GET `/roles/options`

Phục vụ dropdown Add User (`GROUPS` / `ROLES` trong `AddUserDrawer.tsx`):

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "groups": ["Engineering", "Marketing", "Data Science", "Alpha Team", "Backend", "DevOps"],
    "roles": ["Admin", "Editor", "Viewer", "Deployer"]
  }
}
```

Hoặc tách hai endpoint trả `{ "id", "name" }[]`.

### D.5 POST `/users/bulk/assign-groups`

Ví dụ: chọn John Doe + Bob Chen, gán groups:

```json
{
  "userIds": ["1", "3"],
  "groupIds": ["grp-de-core"]
}
```

> Nếu phase 1 giữ tên string: `{ "userIds": ["1","3"], "groupNames": ["Data Engineering Core"] }` — cần thống nhất.

**Response:**

```json
{
  "success": true,
  "message": "Groups assigned",
  "data": { "updatedCount": 2 }
}
```

### D.6 POST `/users/bulk/assign-roles`

```json
{
  "userIds": ["1", "3"],
  "roleIds": ["role-data-scientist-eu"]
}
```

### D.7 POST `/users/bulk/deactivate`

```json
{
  "userIds": ["2"]
}
```

**Response:**

```json
{
  "success": true,
  "message": "Users deactivated",
  "data": { "updatedCount": 1 }
}
```

---

## E. Role Management

**Route:** `/admin/roles`  
**Nguồn:** `src/pages/role-management/mock-data.ts`

### E.1 GET `/roles`

Đủ **3 role** như sidebar:

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "data": [
      {
        "id": "role-data-scientist-eu",
        "name": "Data_Scientist_EU",
        "displayName": "Data Pipeline Admin",
        "permissionCount": 8,
        "userCount": 5,
        "groupCount": 2,
        "icon": "shield"
      },
      {
        "id": "role-marketing-analyst",
        "name": "Marketing_Analyst",
        "displayName": "Warehouse Read-Only",
        "permissionCount": 3,
        "userCount": 12,
        "groupCount": 1,
        "icon": "shield"
      },
      {
        "id": "role-sysadmin-global",
        "name": "SysAdmin_Global",
        "displayName": "Platform Auditor",
        "permissionCount": 142,
        "userCount": 2,
        "groupCount": 0,
        "icon": "shield_lock"
      }
    ],
    "currentPage": 1,
    "totalItems": 3,
    "totalPages": 1
  }
}
```

### E.2 POST `/roles`

```json
{
  "name": "Data_Analyst_APAC"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Role created",
  "data": {
    "id": "role-20260519-001",
    "name": "Data_Analyst_APAC",
    "displayName": "Data_Analyst_APAC",
    "permissionCount": 0,
    "userCount": 0,
    "groupCount": 0,
    "icon": "shield"
  }
}
```

### E.3 PATCH `/roles/{roleId}` — Rename

```json
{
  "name": "Data_Scientist_EU_v2"
}
```

### E.4 POST `/roles/{roleId}/duplicate`

Ví dụ duplicate `role-data-scientist-eu`:

```json
{
  "success": true,
  "message": "Role duplicated",
  "data": {
    "id": "role-data-scientist-eu-copy-1716123456",
    "name": "Data_Scientist_EU_copy",
    "displayName": "Data Pipeline Admin (copy)",
    "permissionCount": 8,
    "userCount": 0,
    "groupCount": 0,
    "icon": "shield"
  }
}
```

### E.5 DELETE `/roles/{roleId}`

`204` hoặc envelope `success: true`. `409` nếu role cuối cùng hoặc đang được tham chiếu.

### E.6 GET `/roles/role-data-scientist-eu/permissions`

**Toàn bộ 8 permission** hiển thị khi chọn role mặc định:

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "permissions": [
      {
        "id": "perm-db-1",
        "resourceType": "DATABASE",
        "path": [{ "label": "prod_eu_central" }],
        "effect": "ALLOW",
        "action": "USAGE"
      },
      {
        "id": "perm-schema-1",
        "resourceType": "SCHEMA",
        "path": [{ "label": "prod_eu_central" }, { "label": "analytics" }],
        "effect": "ALLOW",
        "action": "USAGE"
      },
      {
        "id": "perm-schema-2",
        "resourceType": "SCHEMA",
        "path": [{ "label": "prod_eu_central" }, { "label": "raw_events" }],
        "effect": "ALLOW",
        "action": "USAGE"
      },
      {
        "id": "perm-table-1",
        "resourceType": "TABLE",
        "path": [{ "label": "analytics" }, { "label": "user_metrics_agg" }],
        "effect": "ALLOW",
        "action": "SELECT"
      },
      {
        "id": "perm-table-2",
        "resourceType": "TABLE",
        "path": [{ "label": "raw_events" }, { "label": "pii_dump_raw" }],
        "effect": "DENY",
        "action": "SELECT",
        "isHighlighted": true
      },
      {
        "id": "perm-table-3",
        "resourceType": "TABLE",
        "path": [{ "label": "analytics" }, { "label": "regional_sales" }],
        "effect": "ALLOW",
        "action": "SELECT",
        "modifier": { "type": "ROW_FILTER", "label": "Row Filter" }
      },
      {
        "id": "perm-table-4",
        "resourceType": "TABLE",
        "path": [{ "label": "analytics" }, { "label": "staging_users" }],
        "effect": "ALLOW",
        "action": "SELECT"
      },
      {
        "id": "perm-column-1",
        "resourceType": "COLUMN",
        "path": [{ "label": "users" }, { "label": "email" }],
        "effect": "ALLOW",
        "action": "SELECT",
        "modifier": { "type": "COLUMN_MASK", "label": "Masked" }
      }
    ],
    "summary": {
      "total": 8,
      "allowCount": 7,
      "denyCount": 1,
      "modifierCount": 2
    }
  }
}
```

### E.7 POST `/roles/{roleId}/permissions` — Grant

**Body** (wizard — path thực tế từ `mockResourceTree.ts`):

```json
{
  "resourcePath": [
    { "id": "db1", "name": "analytics_db", "type": "database" },
    { "id": "sch1", "name": "public", "type": "schema" },
    { "id": "tbl1", "name": "users", "type": "table" },
    { "id": "col2", "name": "email", "type": "column" }
  ],
  "resourceType": "column",
  "actions": ["SELECT"],
  "effect": "ALLOW",
  "columnMask": {
    "enabled": true,
    "maskType": "PARTIAL",
    "maskPattern": "***@***.com"
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "Permissions created",
  "data": {
    "created": [
      {
        "id": "perm-new-1716123456789-0",
        "resourceType": "COLUMN",
        "path": [{ "label": "analytics_db" }, { "label": "public" }, { "label": "users" }, { "label": "email" }],
        "effect": "ALLOW",
        "action": "SELECT",
        "modifier": { "type": "COLUMN_MASK", "label": "PARTIAL: ***@***.com" }
      }
    ]
  }
}
```

### E.8 PUT `/roles/{roleId}/permissions/{permissionId}`

Body: cùng shape grant (một action). Ví dụ sửa `perm-table-3`.

### E.9 DELETE `/roles/{roleId}/permissions/{permissionId}`

Ví dụ xóa `perm-table-2`.

### E.10 GET `/roles/role-data-scientist-eu/actors`

Khớp cột Actors khi mở role mặc định:

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "users": [
      {
        "id": "user-1",
        "name": "Sarah Jenkins",
        "email": "s.jenkins@corp.com",
        "avatarUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuAI-tpkCHTk_FM-WIPVZAnP6qp6duhNSclr0aza5t7IkIxk2Q6kv5XtmNQeDFzW1dLSFyQeUhsAZ95jH2TsaO_SfoVC_3a14mLktyFJpz3yhRYLRvGQxdDOXBm3ZDjfOi8UJAjScT49VmoJfRCpQ7Uvlk__4z1EtSA59I07_09JuJx56flUDophxeDuJKmPI3anLjDlNzAKxjU0jf_mquFo8E-Q4-sjXz_K29BQ90oUjySOq3U-ovtO4mwxJF7F5mfIcZtnxSPj0BOI",
        "isOnline": true
      },
      {
        "id": "user-2",
        "name": "David Chen",
        "email": "d.chen@corp.com",
        "avatarUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuCpjjPnNHbyc37vNHJpTaEAnviVGOaKPUbC-e5VkXrmFGf4x57pd5snxs2MMOenatDs8fh1oOabanVp_JJv_EQornovXsbz9AmxsQf2OOC4BIKFazE_TdxR77lfppuhkmR7CGtENiK7Zut5DO7IlBT7zwzAqlCN-3fUD8hIHQy6c2ubt2yO13HJjSdtfTyR8RyEAMpFQNlfLqzGjO0xqA8Wp-6FyopCxF5l1It0wrQZR9QKcuZIJQfYH3fM5h94NUUjLZBoKLCabDOT",
        "isOnline": true
      },
      {
        "id": "user-3",
        "name": "Elena Rodriguez",
        "email": "e.rodriguez@corp.com",
        "isOnline": false
      },
      {
        "id": "user-4",
        "name": "James Wilson",
        "email": "j.wilson@corp.com",
        "isOnline": true
      },
      {
        "id": "user-5",
        "name": "Priya Sharma",
        "email": "p.sharma@corp.com",
        "isOnline": false
      }
    ],
    "groups": [
      { "id": "group-1", "name": "EU_Data_Team", "memberCount": 8 },
      { "id": "group-2", "name": "Global_Analytics_Read", "memberCount": 4 }
    ],
    "totalAffectedUsers": 17
  }
}
```

| Thao tác | Method | Path | Body |
|----------|--------|------|------|
| Gán users | `POST` | `/roles/{roleId}/users` | `{ "userIds": ["catalog-u3"] }` |
| Gỡ user | `DELETE` | `/roles/{roleId}/users/{userId}` | — |
| Gán groups | `POST` | `/roles/{roleId}/groups` | `{ "groupIds": ["g2"] }` |
| Gỡ group | `DELETE` | `/roles/{roleId}/groups/{groupId}` | — |

### E.11 GET `/users/catalog`

Dùng trong Assign Users drawer — `AVAILABLE_USERS_CATALOG`:

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "data": [
      {
        "id": "catalog-u1",
        "name": "Eleanor Vance",
        "email": "e.vance@corp.com",
        "isOnline": true,
        "avatarUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuBd8gf5vXlKpv1cYWZU6mEi4Tiy2WyQi84QkiZA6lug3pgq4umeopqc5L19yaSiLSLSKkE3bsYQClLHRG9g-vI9VCoWIH_EUsfPcchKMbGOvch4Y2d0upivpJMefV5Fx1GqtmqjTwdjo-ARNQUoamwXsj732AWMDTpEKwsoS35pAFJ61Ja7LpnHW72EpdKNvJDRNDJidVLb8gXMciufYX8RcwP_fOhamtioEPZuEJLvMDR0QEv2txVaME7gafQs2n4ZzP5EgXKQLHkY"
      },
      {
        "id": "catalog-u2",
        "name": "Julian Montague",
        "email": "j.montague@corp.com",
        "isOnline": false,
        "avatarUrl": "https://lh3.googleusercontent.com/aida-public/AB6AXuD2zhXNNYCMxBS6ue-kegcv3lfpfsCKaiMnihnTDFD_bp9So9zMyKYUL9pJmFjcSBBV68uGvD6T4BbloYRsjixMmOwiwxN2FvgVqNZF3iDf20iJp7w8pDP_EXbuRQnhjT6UVpGKvB0k7c6GcYvun1XJ7npF1bqaiKDwK6mr38IFhQEXRDr6QMDIP8FKEXYrkSsYhVeNwByFbRGnTW145aCTYqMDaAHzT8awEKZKfkK8SjAL2qmqqgF8NDL2loSr1uc-UchdCIwbFxkL"
      },
      { "id": "catalog-u3", "name": "Alex Turner", "email": "a.turner@corp.com", "isOnline": true },
      { "id": "catalog-u4", "name": "Maria Garcia", "email": "m.garcia@corp.com", "isOnline": true },
      { "id": "catalog-u5", "name": "Sam Chen", "email": "s.chen@corp.com", "isOnline": false }
    ],
    "currentPage": 1,
    "totalItems": 5,
    "totalPages": 1
  }
}
```

### E.12 GET `/groups/catalog`

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "data": [
      {
        "id": "g1",
        "name": "Security Operations",
        "memberCount": 42,
        "description": "Global threat monitoring and incident response team."
      },
      {
        "id": "g2",
        "name": "Data Science",
        "memberCount": 18,
        "description": "Advanced analytics, predictive modeling, and machine learning infrastructure."
      },
      {
        "id": "g3",
        "name": "Marketing",
        "memberCount": 12,
        "description": "External communications and brand strategy execution."
      },
      {
        "id": "g4",
        "name": "Executive Board",
        "memberCount": 5,
        "description": "High-level strategic oversight and top-tier access credentials."
      },
      {
        "id": "g5",
        "name": "Alpha Team",
        "memberCount": 8,
        "description": "Special projects and rapid deployment unit."
      }
    ],
    "currentPage": 1,
    "totalItems": 5,
    "totalPages": 1
  }
}
```

---

## F. Group Management

**Route:** `/admin/groups`  
**Nguồn:** `src/pages/group-management/mock-data.ts`

### F.1 GET `/groups`

Ba group trên list panel:

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "data": [
      {
        "id": "grp-de-core",
        "name": "Data Engineering Core",
        "memberCount": 12,
        "roleCount": 3,
        "createdAt": "2023-10-12T00:00:00Z",
        "createdAtLabel": "Oct 12, 2023",
        "description": "Core data platform engineering and pipeline operations."
      },
      {
        "id": "grp-marketing",
        "name": "Marketing Analysts",
        "memberCount": 8,
        "roleCount": 2,
        "createdAt": "2024-01-04T00:00:00Z",
        "createdAtLabel": "Jan 4, 2024",
        "description": "Campaign analytics and marketing data consumers."
      },
      {
        "id": "grp-contractors",
        "name": "External Contractors",
        "memberCount": 24,
        "roleCount": 1,
        "createdAt": "2024-03-22T00:00:00Z",
        "createdAtLabel": "Mar 22, 2024",
        "description": "Limited-access external collaborators."
      }
    ],
    "currentPage": 1,
    "totalItems": 3,
    "totalPages": 1
  }
}
```

> `memberCount` trên list (12) là số marketing/summary; panel Members hiển thị **4** member trong mock — backend nên đồng bộ hoặc trả `memberCount` = số member thực tế trong `GET .../members`.

### F.2 POST `/groups`

```json
{
  "name": "Platform SRE",
  "description": "Site reliability and observability."
}
```

### F.3 DELETE `/groups/{groupId}`

Ví dụ xóa `grp-contractors`.

### F.4 GET `/groups/grp-de-core/members`

Bốn member như Members section:

```json
{
  "success": true,
  "message": "OK",
  "data": [
    {
      "id": "member-as",
      "name": "Alice Smith",
      "email": "alice.smith@datagate.co",
      "initials": "AS",
      "status": "Active"
    },
    {
      "id": "member-bj",
      "name": "Bob Jones",
      "email": "bob.jones@datagate.co",
      "initials": "BJ",
      "status": "Active"
    },
    {
      "id": "member-ec",
      "name": "Elena Rodriguez",
      "email": "e.rodriguez@datagate.co",
      "initials": "ER",
      "status": "Active"
    },
    {
      "id": "member-jw",
      "name": "James Wilson",
      "email": "j.wilson@datagate.co",
      "initials": "JW",
      "status": "Inactive"
    }
  ]
}
```

### F.5 POST `/groups/grp-de-core/members`

```json
{
  "memberIds": ["catalog-u1", "catalog-u4"]
}
```

### F.6 DELETE `/groups/grp-de-core/members/{memberId}`

Ví dụ: `member-jw` (James Wilson).

### F.7 GET `/groups/grp-de-core/roles`

Ba role card — **display name** (không phải `Data_Scientist_EU`):

```json
{
  "success": true,
  "message": "OK",
  "data": [
    {
      "id": "role-data-scientist-eu",
      "name": "Data Pipeline Admin",
      "description": "Full access to manage and execute ETL pipelines across all production environments.",
      "permissionCount": 8
    },
    {
      "id": "role-marketing-analyst",
      "name": "Warehouse Read-Only",
      "description": "Select access to core analytics schemas in the central data warehouse.",
      "permissionCount": 3
    },
    {
      "id": "role-sysadmin-global",
      "name": "Platform Auditor",
      "description": "Read-only oversight across administrative resources.",
      "permissionCount": 142
    }
  ]
}
```

### F.8 POST `/groups/grp-de-core/roles`

```json
{
  "roleIds": ["role-marketing-analyst"]
}
```

### F.9 DELETE `/groups/grp-de-core/roles/{roleId}`

Gỡ assignment; không xóa role global.

### F.10 GET `/members/catalog`

`AddMemberToGroupDrawer`:

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "data": [
      { "id": "catalog-u1", "name": "Eleanor Vance", "email": "e.vance@corp.com", "isOnline": true },
      { "id": "catalog-u2", "name": "Julian Montague", "email": "j.montague@corp.com", "isOnline": false },
      { "id": "catalog-u3", "name": "Alex Turner", "email": "a.turner@corp.com", "isOnline": true },
      { "id": "catalog-u4", "name": "Priya Sharma", "email": "p.sharma@corp.com", "isOnline": true },
      { "id": "catalog-u5", "name": "David Chen", "email": "d.chen@corp.com", "isOnline": false }
    ],
    "currentPage": 1,
    "totalItems": 5,
    "totalPages": 1
  }
}
```

### F.11 GET `/roles/catalog`

`AssignRolesToGroupDrawer`:

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "data": [
      {
        "id": "role-data-scientist-eu",
        "name": "Data Pipeline Admin",
        "description": "Full access to manage and execute ETL pipelines across all production environments.",
        "permissionCount": 8
      },
      {
        "id": "role-marketing-analyst",
        "name": "Warehouse Read-Only",
        "description": "Select access to core analytics schemas in the central data warehouse.",
        "permissionCount": 3
      },
      {
        "id": "role-sysadmin-global",
        "name": "Platform Auditor",
        "description": "Read-only oversight across administrative resources.",
        "permissionCount": 142
      }
    ],
    "currentPage": 1,
    "totalItems": 3,
    "totalPages": 1
  }
}
```

### F.12 GET `/groups/grp-de-core/permissions` — Direct only

Mock ban đầu rỗng; sau grant direct:

```json
{
  "success": true,
  "message": "OK",
  "data": []
}
```

### F.13 POST `/groups/grp-de-core/permissions` — Direct grant

Cùng body grant như §E.7. Response: permissions với `ownership` implied group.

### F.14 GET `/groups/grp-de-core/effective-permissions`

Merge direct + inherited từ 3 role đã assign. Ví dụ **trạng thái demo** (mock: chưa có direct; 12 inherited unique ids):

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "permissions": [
      {
        "id": "perm-db-1",
        "resourceType": "DATABASE",
        "path": [{ "label": "prod_eu_central" }],
        "effect": "ALLOW",
        "action": "USAGE",
        "ownership": "role",
        "sourceRoleId": "role-data-scientist-eu",
        "sourceRoleName": "Data Pipeline Admin"
      },
      {
        "id": "perm-table-2",
        "resourceType": "TABLE",
        "path": [{ "label": "raw_events" }, { "label": "pii_dump_raw" }],
        "effect": "DENY",
        "action": "SELECT",
        "isHighlighted": true,
        "ownership": "role",
        "sourceRoleId": "role-data-scientist-eu",
        "sourceRoleName": "Data Pipeline Admin"
      },
      {
        "id": "perm-mkt-1",
        "resourceType": "DATABASE",
        "path": [{ "label": "marketing_dw" }],
        "effect": "ALLOW",
        "action": "USAGE",
        "ownership": "role",
        "sourceRoleId": "role-marketing-analyst",
        "sourceRoleName": "Warehouse Read-Only"
      },
      {
        "id": "perm-admin-1",
        "resourceType": "DATABASE",
        "path": [{ "label": "*" }],
        "effect": "ALLOW",
        "action": "USAGE",
        "ownership": "role",
        "sourceRoleId": "role-sysadmin-global",
        "sourceRoleName": "Platform Auditor"
      }
    ],
    "summary": {
      "total": 12,
      "allowCount": 11,
      "denyCount": 1,
      "modifierCount": 2
    },
    "inheritedSummary": {
      "permissionCount": 12,
      "resourceTypeCount": 4,
      "roleCount": 3
    }
  }
}
```

> Response đầy đủ gồm 12 dòng (8 + 3 + 1, dedupe theo `id`). Ví dụ trên rút gọn 4 dòng đại diện.

**Sau khi user Add Permission (direct)** — thêm dòng:

```json
{
  "id": "perm-g-direct-001",
  "resourceType": "SCHEMA",
  "path": [{ "label": "analytics_db" }, { "label": "public" }],
  "effect": "ALLOW",
  "action": "USAGE",
  "ownership": "group",
  "sourceRoleId": null,
  "sourceRoleName": "Direct"
}
```

| `ownership` | Edit trên Group UI | API sửa/xóa |
|-------------|-------------------|-------------|
| `group` | Có | `PUT/DELETE /groups/{groupId}/permissions/{id}` |
| `role` | Không (read-only) | `PUT/DELETE /roles/{sourceRoleId}/permissions/{id}` |

---

## G. Shared — Resource tree

### G.1 GET `/resources/tree`

Khớp `src/components/add-permission/data/mockResourceTree.ts` — dùng bởi Add Permission trên Role và Group:

```json
{
  "success": true,
  "message": "OK",
  "data": [
    {
      "id": "db1",
      "name": "analytics_db",
      "type": "database",
      "children": [
        {
          "id": "sch1",
          "name": "public",
          "type": "schema",
          "children": [
            {
              "id": "tbl1",
              "name": "users",
              "type": "table",
              "children": [
                { "id": "col1", "name": "id", "type": "column", "isPrimaryKey": true },
                { "id": "col2", "name": "email", "type": "column" },
                { "id": "col3", "name": "created_at", "type": "column" }
              ]
            },
            {
              "id": "tbl2",
              "name": "events",
              "type": "table",
              "children": [
                { "id": "col4", "name": "event_id", "type": "column", "isPrimaryKey": true },
                { "id": "col5", "name": "event_type", "type": "column" },
                { "id": "col6", "name": "user_id", "type": "column", "isForeignKey": true }
              ]
            }
          ]
        },
        {
          "id": "sch2",
          "name": "internal",
          "type": "schema",
          "children": [
            { "id": "tbl3", "name": "audit_logs", "type": "table" }
          ]
        }
      ]
    },
    {
      "id": "db2",
      "name": "marketing_db",
      "type": "database",
      "children": [
        {
          "id": "sch3",
          "name": "campaigns",
          "type": "schema",
          "children": [
            { "id": "tbl4", "name": "ads_performance", "type": "table" }
          ]
        }
      ]
    }
  ]
}
```

---

## H. Bảng tổng hợp endpoint

Prefix: `/api/v1/admin`

| # | Method | Path | Màn hình |
|---|--------|------|----------|
| 1 | GET | `/users` | User list |
| 2 | GET | `/users/{id}` | User detail |
| 3 | POST | `/users` | Add user |
| 4 | GET | `/groups/options` | Add user — groups |
| 5 | GET | `/roles/options` | Add user — roles |
| 6 | POST | `/users/bulk/assign-groups` | Bulk |
| 7 | POST | `/users/bulk/assign-roles` | Bulk |
| 8 | POST | `/users/bulk/deactivate` | Bulk |
| 9 | GET | `/roles` | Role list |
| 10 | POST | `/roles` | Add role |
| 11 | PATCH | `/roles/{id}` | Rename |
| 12 | POST | `/roles/{id}/duplicate` | Duplicate |
| 13 | DELETE | `/roles/{id}` | Delete role |
| 14 | GET | `/roles/{id}/permissions` | Permissions |
| 15 | POST | `/roles/{id}/permissions` | Grant |
| 16 | PUT | `/roles/{id}/permissions/{permId}` | Edit |
| 17 | DELETE | `/roles/{id}/permissions/{permId}` | Delete |
| 18 | GET | `/roles/{id}/actors` | Actors |
| 19 | POST | `/roles/{id}/users` | Assign users |
| 20 | DELETE | `/roles/{id}/users/{userId}` | Unassign |
| 21 | POST | `/roles/{id}/groups` | Assign groups |
| 22 | DELETE | `/roles/{id}/groups/{groupId}` | Unassign |
| 23 | GET | `/users/catalog` | Role — assign users |
| 24 | GET | `/groups/catalog` | Role — assign groups |
| 25 | GET | `/groups` | Group list |
| 26 | POST | `/groups` | Add group |
| 27 | DELETE | `/groups/{id}` | Delete group |
| 28 | GET | `/groups/{id}/members` | Members |
| 29 | POST | `/groups/{id}/members` | Add members |
| 30 | DELETE | `/groups/{id}/members/{memberId}` | Remove |
| 31 | GET | `/members/catalog` | Add member drawer |
| 32 | GET | `/groups/{id}/roles` | Assigned roles |
| 33 | POST | `/groups/{id}/roles` | Assign roles |
| 34 | DELETE | `/groups/{id}/roles/{roleId}` | Unassign |
| 35 | GET | `/roles/catalog` | Assign roles drawer |
| 36 | GET | `/groups/{id}/permissions` | Direct perms |
| 37 | POST | `/groups/{id}/permissions` | Direct grant |
| 38 | PUT | `/groups/{id}/permissions/{permId}` | Edit direct |
| 39 | DELETE | `/groups/{id}/permissions/{permId}` | Delete direct |
| 40 | GET | `/groups/{id}/effective-permissions` | Effective panel |
| 41 | GET | `/resources/tree` | Permission wizard |

---

## I. Phụ lục — Demo dataset (trạng thái mở app)

Mô tả snapshot khi user mở app lần đầu (không thao tác thêm). Dùng seed DB hoặc contract test.

```json
{
  "defaults": {
    "roleManagement": { "selectedRoleId": "role-data-scientist-eu" },
    "groupManagement": { "selectedGroupId": "grp-de-core" }
  },
  "users": [
    { "id": "1", "name": "John Doe", "status": "Active" },
    { "id": "2", "name": "Alice Smith", "status": "Inactive" },
    { "id": "3", "name": "Bob Chen", "status": "Active" }
  ],
  "roles": [
    { "id": "role-data-scientist-eu", "name": "Data_Scientist_EU", "permissionCount": 8 },
    { "id": "role-marketing-analyst", "name": "Marketing_Analyst", "permissionCount": 3 },
    { "id": "role-sysadmin-global", "name": "SysAdmin_Global", "permissionCount": 142 }
  ],
  "groups": [
    { "id": "grp-de-core", "name": "Data Engineering Core", "roleCount": 3 },
    { "id": "grp-marketing", "name": "Marketing Analysts", "roleCount": 2 },
    { "id": "grp-contractors", "name": "External Contractors", "roleCount": 1 }
  ],
  "grp-de-core": {
    "members": ["member-as", "member-bj", "member-ec", "member-jw"],
    "assignedRoles": [
      { "id": "role-data-scientist-eu", "displayName": "Data Pipeline Admin" },
      { "id": "role-marketing-analyst", "displayName": "Warehouse Read-Only" },
      { "id": "role-sysadmin-global", "displayName": "Platform Auditor" }
    ],
    "directPermissions": [],
    "inheritedPermissionCount": 12
  },
  "role-data-scientist-eu": {
    "permissionIds": [
      "perm-db-1",
      "perm-schema-1",
      "perm-schema-2",
      "perm-table-1",
      "perm-table-2",
      "perm-table-3",
      "perm-table-4",
      "perm-column-1"
    ],
    "actorUserIds": ["user-1", "user-2", "user-3", "user-4", "user-5"],
    "actorGroupIds": ["group-1", "group-2"]
  }
}
```

---

## J. Câu hỏi mở cho backend

1. `page` phân trang: 0-based hay 1-based?
2. User list: `groups`/`roles` trả **tên** hay `{ id, name }[]`?
3. Bulk assign: **append** hay **replace** membership?
4. Role model: tách `name` (technical) và `displayName` (UI card)?
5. `memberCount` trên group list vs số member thực trong `GET /members` — cùng nguồn?
6. Effective permissions: merge **server-side** (khuyến nghị) hay FE gọi nhiều API?
7. Grant permission: một `POST` trả mảng `created[]` hay single aggregate?
8. Duplicate role: có copy actors không?
9. User id `"1"`/`"2"`/`"3"` vs UUID — migration path?
10. Xóa group/role: soft delete hay hard delete?
11. `isHighlighted` do backend set khi `effect=DENY` hay FE tự suy ra?
12. Catalog `catalog-u1` vs actor `user-1` — cùng bảng `users`?

---

## K. Gợi ý triển khai FE (không nằm scope backend)

| Service | File đề xuất |
|---------|----------------|
| Users | `src/api/UserAdminApi.ts` |
| Roles | `src/api/RoleAdminApi.ts` |
| Groups | `src/api/GroupAdminApi.ts` |
| Resources | `src/api/ResourceApi.ts` |

Mỗi method: `ApiService.get/post` → unwrap `response.data.data`, hỗ trợ `signal` cho `AbortController`.

---

## Changelog

| Ngày | Thay đổi |
|------|----------|
| 2026-05-19 | Viết lại toàn bộ: ví dụ JSON khớp mock/UI; bảng ánh xạ; demo dataset; `name` vs `displayName` |
