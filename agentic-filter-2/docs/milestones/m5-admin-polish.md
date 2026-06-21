# M5 — Shared, Docs & Parity (E13)

| | |
|---|---|
| **Mục tiêu** | Resource tree FE, seed §I hoàn chỉnh, curl doc, regression Epic 3, initiative DoD |
| **Thời lượng** | 3–4 ngày |
| **Phụ thuộc** | [M3](m3-admin-roles.md) (wizard tree); khuyến nghị M2–M4 xong |
| **Chặn** | Release FE integration |
| **Tiếp theo** | — (initiative complete) |

**Endpoint contract §H:** #41 + tài liệu vận hành

---

## Dev — checklist

### Resource tree

- [x] **M5.1.1** `GET /api/v1/admin/resources/tree` — wrap `admin_resources` logic, shape §G (`type`, `children`, PK/FK) → Verify: curl JSON khớp mock wizard
- [x] **M5.1.2** Document field naming (snake vs camel) trong OpenAPI / curl doc

### Prefix (chốt với team)

- [x] **M5.2** Chọn **A** (một prefix `/api/v1/admin` cho tất cả admin) hoặc **B** (giữ `/v1/admin` Epic 3 tạm)
- [ ] **M5.2.A** Nếu A: sửa router Epic 3 + `tests/test_epic3_admin_api.py` → Verify: pytest Epic 3 pass
- [x] **M5.2.B** Nếu B: bảng mapping prefix trong curl doc → Verify: FE chỉ gọi `/api/v1/admin`

### Documentation & seed

- [x] **M5.3.1** Curl examples 41 endpoint trong [huong-dan-chay-va-curl.md](../huong-dan-chay-va-curl.md) → Verify: copy-paste chạy được
- [x] **M5.3.2** `scripts/seed_demo_data.py` — full §I snapshot → Verify: chạy trên DB trống ra đúng counts
- [x] **M5.3.3** `tests/fixtures/admin_contract_snapshot.json` + test so subset fields → Verify: CI pass

### Regression

- [x] **M5.4.1** `pytest` full suite → Verify: green
- [ ] **M5.4.2** (Tùy chọn) `ADMIN_CONTRACT_API_ENABLED` gate trong `main.py`

---

## Verification (gate merge)

**Done khi (initiative):**

- [x] [implementation_plan §12](../implementation_plan_user_role_group_admin.md#12-definition-of-done-toàn-bộ-initiative) — tất cả checkbox đạt.
- [x] FE trỏ một base URL `/api/v1/admin`.
- [x] Demo mở app: users/roles/groups + `grp-de-core` effective ~ contract §I.

```bash
pytest tests/test_admin_contract_foundation.py tests/test_admin_users_api.py \
  tests/test_admin_roles_api.py tests/test_admin_groups_api.py tests/test_epic3_admin_api.py -q
```

---

## QA (trước merge)

- [ ] Full §I demo dataset walkthrough (manual hoặc automated).
- [ ] Epic 3 regression không đổi hành vi ngoài prefix (nếu đổi prefix).
- [ ] Security smoke: no token → 401/403.

---

## Giao việc gợi ý

| Dev | Phạm vi |
|-----|--------|
| Dev A | M5.1 + M5.3.1 |
| Dev B | M5.3.2–M5.3.3 + M5.4 |
| QA | M5.4.1 full regression |

**PR đề xuất:** PR-6 (sau PR-2–5).
