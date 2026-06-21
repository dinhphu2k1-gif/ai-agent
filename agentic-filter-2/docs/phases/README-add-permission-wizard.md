# Add Permission Wizard — Lộ trình phase (dev)

> **Tổng quan:** [implementation_plan_add_permission_wizard.md](../implementation_plan_add_permission_wizard.md)  
> **Schema:** [schema_review_add_permission_wizard_fe.md](../schema_review_add_permission_wizard_fe.md)  
> **Spec FE:** [my-docs/add-permission-resource-modifier-be-spec.md](../../my-docs/add-permission-resource-modifier-be-spec.md)

## Thứ tự thực hiện

```text
Phase 0 (schema) → Phase 1 (grant core) → Phase 2 (presenter + test)
    → Phase 3 (docs)     → Phase 4–5 (P1 APIs, song song được sau Phase 2)
    → Phase 6 (backlog P2)
```

| Phase | File | PR gợi ý | Ước lượng | Chặn FE production |
|-------|------|----------|-----------|-------------------|
| **0** | [phase-0-schema-migration.md](phase-0-schema-migration.md) ✅ | PR-S | 0.5–1 ngày | Có |
| **1** | [phase-1-grant-service.md](phase-1-grant-service.md) ✅ | PR-A (phần 1) | 1.5–2 ngày | Có |
| **2** | [phase-2-presenter-tests.md](phase-2-presenter-tests.md) ✅ | PR-A (phần 2) | 1–1.5 ngày | Có |
| **3** | [phase-3-docs-verification.md](phase-3-docs-verification.md) ✅ | PR-B | 0.5 ngày | Khuyến nghị |
| **4** | [phase-4-catalog-apis.md](phase-4-catalog-apis.md) ✅ | PR-C | 2 ngày | Không (P1) |
| **5** | [phase-5-wizard-dx-apis.md](phase-5-wizard-dx-apis.md) ✅ | PR-D | 1.5–2 ngày | Không (P1) |
| **6** | [phase-6-scale-backlog.md](phase-6-scale-backlog.md) ✅ | TBD | Backlog | Không |

**Đã xong (không giao lại):** CORS (`main.py`), `GET /api/v1/admin/resources/tree` (+ lazy `parentId`), Phase 0 schema, Phase 1 `PermissionGrantService`, Phase 2 presenter + grant E2E tests, Phase 4–5 wizard APIs, Phase 6 mask engine + inherited PUT guard (6.5 MV tùy chọn chưa làm).

## Done khi (initiative)

- [x] Phase 0–3 xong + pytest grant green + docs wizard.
- [ ] FE xác nhận wizard create/edit role & group không dùng mock tree.
- [x] Phase 4 catalog APIs (search, scope-stats, action-catalog).
- [x] Phase 5 validate/preview row-filter & column-mask.
