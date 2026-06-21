# Agent personas (Cursor Rules)

Repo **agentic-filter-2** mô tả **Filter Service** (lớp bảo vệ truy cập dữ liệu giữa agent layer và PostgreSQL/OpenSearch). Tài liệu nền: [my-docs/0_srs.md](my-docs/0_srs.md), [docs/architecture_plan.md](docs/architecture_plan.md).

Trong Cursor có hai cơ chế bổ sung cho nhau:

- **Rules** ([`.cursor/rules/`](.cursor/rules/)): file `.mdc` với `globs` / rule picker; ví dụ `@agent-backend_engineer.mdc`.
- **Subagents** ([`.cursor/agents/`](.cursor/agents/)): file `.md` với `name` + `description` trong frontmatter; prompt riêng khi bạn giao việc cho subagent (ví dụ: *Use the planner subagent to …*).

## Bảng agent (Rules)

| Agent | File rule | Khi dùng |
|-------|-----------|----------|
| backend_engineer | [`.cursor/rules/agent-backend_engineer.mdc`](.cursor/rules/agent-backend_engineer.mdc) | Triển khai API FastAPI, IAM, cache, policy, rewrite, connector, masking |
| business_analyst | [`.cursor/rules/agent-business_analyst.mdc`](.cursor/rules/agent-business_analyst.mdc) | User story, AC, làm rõ luồng admin/runtime theo SRS |
| code_reviewer | [`.cursor/rules/agent-code_reviewer.mdc`](.cursor/rules/agent-code_reviewer.mdc) | Review PR: bảo mật, correctness, style tối thiểu |
| devops_engineer | [`.cursor/rules/agent-devops_engineer.mdc`](.cursor/rules/agent-devops_engineer.mdc) | CI/CD, Docker, compose, infra-as-code |
| docs_researcher | [`.cursor/rules/agent-docs_researcher.mdc`](.cursor/rules/agent-docs_researcher.mdc) | Đối chiếu và tổng hợp tài liệu trong repo |
| delivery_planner | [`.cursor/rules/agent-delivery_planner.mdc`](.cursor/rules/agent-delivery_planner.mdc) | Milestone, phụ thuộc, MVP, ưu tiên backlog |
| frontend_engineer | [`.cursor/rules/agent-frontend_engineer.mdc`](.cursor/rules/agent-frontend_engineer.mdc) | UI khi có; architecture giai đoạn đầu có thể không có UI admin |
| qa_tester | [`.cursor/rules/agent-qa_tester.mdc`](.cursor/rules/agent-qa_tester.mdc) | Test case, biên, regression cho auth/policy/rewrite |
| solution_architect | [`.cursor/rules/agent-solution_architect.mdc`](.cursor/rules/agent-solution_architect.mdc) | Ranh giới hệ thống, trade-off, đồng bộ với architecture plan |
| uiux_designer | [`.cursor/rules/agent-uiux_designer.mdc`](.cursor/rules/agent-uiux_designer.mdc) | Layout, UX, a11y khi có màn hình hoặc demo |

## Cursor Subagents (`.cursor/agents/`)

| `name` | File | Vai trò |
|--------|------|---------|
| `planner` | [`.cursor/agents/planner.md`](.cursor/agents/planner.md) | Lên kế hoạch milestone, phụ thuộc, tiêu chí done; giao việc cho dev / review / qa |
| `dev-agent` | [`.cursor/agents/dev-agent.md`](.cursor/agents/dev-agent.md) | Triển khai code Filter Service (FastAPI, IAM, policy, rewrite, masking) |
| `review-agent` | [`.cursor/agents/review-agent.md`](.cursor/agents/review-agent.md) | Review bảo mật và chất lượng sau thay đổi code |
| `qa-agent` | [`.cursor/agents/qa-agent.md`](.cursor/agents/qa-agent.md) | Thiết kế case test / QA trước merge |

Gợi ý gọi (theo Cursor): *Use the planner subagent to …*, *Use the dev-agent subagent to …*, *Use the review-agent subagent to …*, *Use the qa-agent subagent to …*.

## Ghi chú

- Có thể `@` nhiều rule khi cần góc nhìn kết hợp (ví dụ `delivery_planner` + `backend_engineer`).
- Giai đoạn đầu có thể chỉ có tài liệu và chưa có thư mục `app/`; rule vẫn áp dụng khi file khớp `globs` xuất hiện.
