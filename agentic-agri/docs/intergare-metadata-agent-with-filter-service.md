# Tích hợp với filter service
## 1. Mục tiêu
Khi truy cập đến cơ sở dữ liệu sẽ không gọi trực tiếp mà phải gọi thông qua filter-service để tránh vượt quyền dữ liệu:
- Đối với metadata_agent: không lấy trực tiếp gọi qua OpenSearchClient mà gọi api cho filter-service, filter-service sẽ check quyền của user, cảnh báo các resource truy cập trái phép, tự động loại bỏ các resource nếu chưa được phân quyền trả về dữ liệu.