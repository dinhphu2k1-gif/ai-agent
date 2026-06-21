# FE handoff checklist — Add Permission wizard (P0)

> Backend Phase 0–2 + docs Phase 3. Manual QA trên UI hoặc curl — tick khi đã xác nhận.

**Chuẩn bị**

- [ ] Postgres + seed: `python scripts/seed_demo_data.py`
- [ ] API: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- [ ] FE `.env`: `CORS_ALLOWED_ORIGINS` gồm origin dev (ví dụ `http://localhost:5173`)
- [ ] `ADMIN_API_TOKEN` trống (dev) hoặc FE gửi `X-Admin-Token`

**Catalog (bước Resource)**

- [ ] `GET /api/v1/admin/resources/tree` trả `analytics_db`, `marketing_db` (không dùng mock tree)
- [ ] Chọn node TABLE/COLUMN gửi đúng `resourcePath[].id` (UUID từ API)

**Create permission — Role**

- [ ] Mở Add Permission trên role → chọn cột → PARTIAL mask → submit → list **1 dòng** với `modifier.type = COLUMN_MASK`, `maskPattern` trong response
- [ ] Grant TABLE + row filter → list có `conditionExpression` (không chỉ label chung chung)
- [ ] Multi-action (`SELECT` + `DESCRIBE`) → list thêm **2 dòng** (hoặc `created.length === 2` trên POST response)

**Edit permission — Role**

- [ ] Edit permission → form hydrate `maskPattern` / `conditionExpression` từ API (không parse `modifier.label`)

**Create permission — Group**

- [ ] Grant trực tiếp trên group (`POST /groups/{groupId}/permissions`) thành công; `GET .../permissions` thấy dòng mới
- [ ] Quyền kế thừa từ role: `PUT/DELETE` group permission trả `403 PERMISSION_NOT_DIRECT` (nếu UI gọi nhầm)

**CORS**

- [ ] Preflight `OPTIONS` tới `/api/v1/admin/...` từ origin FE **không** 405
- [ ] POST grant từ browser với credentials (nếu dùng) thành công

**Regression backend (evidence)**

- [ ] `pytest tests/test_admin_permission_grant.py tests/test_admin_roles_api.py tests/test_admin_groups_api.py tests/test_resource_tree_service.py -q` — all green

**Chưa P0 (ghi nhận, không chặn sign-off)**

- [ ] `GET /resources/search`, `scope-stats`, `action-catalog` (Phase 4 — backend sẵn; FE nối UI)
- [ ] `validate/row-filter`, `preview/column-mask` (Phase 5)
- [ ] Scope stats trên bước Modifier khi chọn database (P1.2)

Tham chiếu: [implementation_plan §9](../implementation_plan_add_permission_wizard.md#9-kiểm-thử), [api-fe-integration §9.1](../api-fe-integration.md).
