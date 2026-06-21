# Epic 4: IAM And User Context

## Tham chiếu

- [architecture_plan.md](architecture_plan.md) **§14 Epic 4**, **§3.2 IAM Client**, **§3.3 User Context Và Cache**, **§9** (`iam/`, `services/user_context_service.py`, `cache/`).

## Mục tiêu epic

Xác thực token qua IAM Service, xây dựng user context (profile + membership), cache Redis theo key đề xuất, xử lý user inactive — nền tảng cho mọi runtime request.

## Phụ thuộc

- **Epic 1** (HTTP client, config, logging).
- **Epic 2–3** hữu ích cho membership trong DB nếu không lấy hết từ IAM; nếu IAM trả đủ group/role, vẫn cần Permission DB cho assignment chi tiết (thường sau Epic 3).

## Dev-agent — checklist triển khai

- [x] `iam/client.py`: validate token HTTPX, timeout ngắn, retry có giới hạn; circuit breaker tùy chọn.
- [x] `iam/schemas.py`: mapping response IAM → internal user DTO.
- [x] `user_context_service.py`: hợp nhất IAM + đọc membership/role từ DB nếu kiến trúc yêu cầu.
- [x] `cache/redis_client.py`, `cache/keys.py`: `user_context:{user_id}`, TTL §3.3.
- [x] Inactive user → từ chối request (403 hoặc 401 theo contract đã chốt).
- [x] Token invalid → **401** (**§12**).
- [x] Không cache token raw; không log token (**§3.2**, **§12**).
- [x] Tests: token valid/invalid, inactive, cache hit/miss (Redis testcontainer hoặc mock).

## Acceptance criteria (§14)

- Token hợp lệ tạo được user context.
- Token invalid trả `401`.
- Inactive user bị chặn.
- Cache hit/miss được test.

## QA-agent — phạm vi kiểm thử

- §15.2: *Runtime request với token invalid trả 401* (khi có route runtime; có thể test unit/integration IAM middleware trước Epic 6).
- §15.3: *IAM timeout không cho request đi tiếp* (fail closed).
- §15.1 (một phần): cache key generation (sau khi có permission snapshot Epic 5 mở rộng).

## Code review — trọng tâm

- Timeout/retry không gây stampede; không leak PII trong log lỗi IAM.
- Fail-closed khi IAM không phản hồi (502/503 theo §12).

## Open decisions (§17)

- Cơ chế đồng bộ user/group/role từ IAM hay bản sao DB — quyết định ảnh hưởng shape `user_context`.
