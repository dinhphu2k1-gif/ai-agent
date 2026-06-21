# Phase 5 — Wizard DX APIs (validate & preview)

## Goal

API hỗ trợ bước Modifier FE: validate row filter, preview column mask; làm rõ hành vi `PUT` khi edit permission.

## Phụ thuộc

- [Phase 4](phase-4-catalog-apis.md) (cùng router `admin_permission_wizard`).

## Tasks

- [x] **5.1** `app/services/permission_validation_service.py`: `validate_row_filter(resource_path, expression)` — normalize hoặc trả `errors[]` (parser tối thiểu: non-empty, cấm `;` hoặc rule project) → Verify: POST validate valid/invalid body
- [x] **5.2** `preview_column_mask(mask_type, pattern, sample_value)` — logic PARTIAL `X`/`x`, FULL/HASH/NULLIFY theo spec FE §4.2 → Verify: POST preview `091-XXX-XXXX` + sample `0912345678` → masked string
- [x] **5.3** Pydantic: `RowFilterValidateBody/Result`, `ColumnMaskPreviewBody/Result` + routes POST trong `admin_permission_wizard.py` → Verify: OpenAPI + curl
- [x] **5.4** Quyết định + doc `PUT .../permissions/{id}`: giữ **single action** (chỉ `actions[0]`) hoặc thiết kế replace — ghi trong `api-fe-integration.md` → Verify: product/FE ack trên ticket
- [x] **5.5** Tests `tests/test_permission_validation_service.py` (unit preview/validate) + 1 integration test route → Verify: pytest green

## Done when

- [x] FE có thể gọi preview/validate thay client-only demo (khi tích hợp).
- [x] Hành vi edit permission được document rõ.

## Ghi chú

- Preview **không** lưu DB; `testValue` không có trong grant payload.
- HASH salt: dùng hằng dev trong config, không commit secret.
