#Tài liệu cập nhật mô tả chỉnh sửa cho filter service

# 1. Phạm vi
* Tài liệu viết về những chỉnh sửa bao gồm chỉ rõ cơ chế gán permission, role, group. Tài liệu đính kèm api contract cho màn quản lý user, quản lý group, quản lý role để quy chuẩn lại API có thể ghép với FE

# 2. Mô tả chi tiết
## 2.1 Mô tả chi tiết nghiệp vụ
### Quy trình gán permission, role, group
- Role là một tập hợp chứa nhiều permission
- Role có thể gán vào Group
- Permission có thể gán trực tiếp vào Group
- Group chứa nhiều user
- Role được gán vào user

## 2.2 Hợp đồng API cho các màn user
- Tài liệu chi tiết trong [tài liệu hợp đồng API](admin-api-contracts-user-role-group.md)