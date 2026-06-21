# Kế hoạch theo Epic (Filter Service)

Tài liệu này chỉ mục **8 file epic** trong thư mục `docs/`, bám [architecture_plan.md](architecture_plan.md) mục **§14 Dev Agent Work Breakdown** và **§16 MVP Delivery Milestones**.

## Thứ tự phụ thuộc

```text
Epic1 → Epic2 → Epic3 → Epic4 → Epic5 → Epic6
                              └──────────────→ Epic7 (song song Epic6 sau Epic5)
Epic6 ─┐
Epic7 ─┼→ Epic8 (masking + access log + observability gắn runtime)
```

- **Epic 7** có thể bắt đầu sau **Epic 5** (cùng cần PDP) và **Epic 1** (skeleton/connector/config); không bắt buộc chờ Epic 6 nếu team chia nhánh, nhưng MVP thường làm **Epic 6 trước Epic 7**.
- **Epic 8** cần pipeline runtime có connector (tối thiểu **Epic 6** cho luồng Postgres); phần masking/audit cho OpenSearch bổ sung khi **Epic 7** xong.

## Bảng Epic và Milestone §16

| Epic | File | Milestone §16 (gợi ý) |
|------|------|-------------------------|
| 1 Project Foundation | [epic-01-project-foundation.md](epic-01-project-foundation.md) | Milestone 1 |
| 2 Permission Data Model | [epic-02-permission-data-model.md](epic-02-permission-data-model.md) | Milestone 1 |
| 3 Admin API | [epic-03-admin-api.md](epic-03-admin-api.md) | Milestone 1 |
| 4 IAM And User Context | [epic-04-iam-user-context.md](epic-04-iam-user-context.md) | Milestone 2 |
| 5 Authorization Engine | [epic-05-authorization-engine.md](epic-05-authorization-engine.md) | Milestone 2 |
| 6 PostgreSQL Runtime | [epic-06-postgresql-runtime.md](epic-06-postgresql-runtime.md) | Milestone 3 |
| 7 OpenSearch Runtime | [epic-07-opensearch-runtime.md](epic-07-opensearch-runtime.md) | Milestone 4 |
| 8 Masking And Audit | [epic-08-masking-and-audit.md](epic-08-masking-and-audit.md) | Milestone 4 |

## Agent

- **Dev-agent**: triển khai theo checklist trong từng file `epic-0N-*.md`.
- **QA-agent**: chạy phạm vi §15 tương ứng sau khi epic merge.
- **Review-agent**: dùng mục “Code review” trong từng file trước merge.

Tham chiếu tổng: [my-docs/0_srs.md](../my-docs/0_srs.md).
