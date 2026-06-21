# Epic 5: Authorization Engine

## Tham chiếu

- [architecture_plan.md](architecture_plan.md) **§14 Epic 5**, **§3.4 Permission Engine**, **§7 Authorization Rules**, **§9** (`services/permission_resolver.py`, `authorization_service.py`, `row_filter_service.py`, `cache/` cho permission snapshot).

## Mục tiêu epic

Policy Decision Point: gom quyền từ user/group/role, match resource path, conflict resolution (DENY ưu tiên), default deny, trả decision kèm row filters và column masks; cache permission snapshot (**§3.3**, **§10**).

## Phụ thuộc

- **Epic 2–3** (dữ liệu permission + assignment + filter/mask).
- **Epic 4** (user context để biết user đang resolve cho ai).

## Dev-agent — checklist triển khai

- [x] `permission_resolver.py`: aggregate permission từ user, group, role kế thừa (**§3.4**, **§7**).
- [x] Resource path matching (database/schema/table/column) và action (SELECT, …).
- [x] Conflict: DENY thắng ALLOW cùng scope; quyền cụ thể không override DENY cụ thể.
- [x] Default deny nếu không có quyền phù hợp.
- [x] Output: ALLOW, DENY, ALLOW_WITH_FILTER, ALLOW_WITH_MASK, ALLOW_WITH_FILTER_AND_MASK + payload filter/mask cho rewriter/masking.
- [x] `permission_snapshot:{user_id}` cache + version/timestamp invalidation khi admin đổi policy (**§10**).
- [x] Unit tests đầy đủ các case trong acceptance.

## Acceptance criteria (§14)

- Test cover user direct permission.
- Test cover group permission.
- Test cover role permission.
- Test cover group inherited role.
- Test cover conflict `ALLOW` và `DENY`.

## QA-agent — phạm vi kiểm thử

- §15.1: resolver, DENY override ALLOW, default deny, resource inheritance, row filter AND combination (ở mức unit/integration resolver).
- §15.4 regression matrix (toàn bộ dòng liên quan PDP).
- §15.3: *Permission DB hoặc cache lỗi fail closed* khi không resolve được policy.

## Code review — trọng tâm

- Không có “shortcut” bypass PDP cho runtime.
- Độ phức tạp thuật toán có test rõ; tránh N+1 query không kiểm soát.

## Open decisions (§17)

- Cách xử lý aggregate/expression với column mask (**§7.4**) — PDP có thể trả flag “unsupported” dẫn tới 422.
