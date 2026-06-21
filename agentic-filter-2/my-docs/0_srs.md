# Tài liệu mô tả cho filter service

# 1. Phạm vi
* Filter service là 1 layer bảo vệ tránh truy cập vượt quyền trong hệ thống agentic AI System nhiệm vụ nhận request từ meta agent hoặc sql writer agent, xác thực token thông qua IAM service (api url), lấy thông tin user, kiểm tra quyền truy cập theo các mức: database, schema, table, column, row. Viết lại query khi gọi xuống Opensearch, PostgreSql. Thực hiện truy vấn dữ liệu, hậu xử lý (masking dữ liệu) cho layer agent trên.

# 2. Yêu cầu chức năng
## 2.1 Danh sách chức năng
- Nhận request, xác thực token bằng cách gọi sang iam service, build user context, cache user
- Quản lý việc phân quyền, phân quyền truy cập theo các mức: database, schema, table, column, row. 
- Engine phân quyền theo mức database, schema, table, column kết hợp: 
    - row-level security: cùng bảng, user khác nhau thấy tập dữ liệu khác nhau
    - Column masking: cùng cột, user khác nhau thấy mức độ che giấu khác nhau
- Cơ chế viết lại query khi gọi xuống opensearch và postgresql
## 2.2 Mô tả quy trình nghiệp vụ
### 2.2.1: Đối với admin
- Admin có quyền tạo permission: cho phép, từ chối truy cập vào resource nào đó. Gán permision cho role, group, user. Có thể gán role cho group. Có thể gán user vào group. Có thể gán role cho user. Admin có thể tạo row filter, column mask gán cho user, group, role.
### 2.2.2: Đối với hệ thống
- Hệ thống nhận request từ agent layer, xác thực token thông qua iam service (url check), lấy ra thông tin user, lấy ra quyền, cache tại redis. Hệ thống phân giải yêu cầu, check quyền truy cập vào các resource, sửa lại query, thực hiện query, hậu xử lý nếu cần.

# 3. Yêu cầu phi chức năng
- Ngôn ngữ sử dụng python, fast api
