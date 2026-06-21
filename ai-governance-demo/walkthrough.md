# Demo AI Governance (Local Version)

Mình đã hoàn tất việc xây dựng một project AI Governance mới hoàn toàn từ đầu, không phụ thuộc vào 3 repo cũ và chạy **100% offline/local**.

## 🛠 Kiến trúc Hệ thống

Dự án nằm tại thư mục: `/home/dinhphu/Documents/ai-agent/ai-governance-demo/`

- **Database:** PostgreSQL (chạy qua Docker trên port 5433).
- **LLM Engine:** Ollama (chạy qua Docker trên port 11435, sử dụng GPU).
- **Model:** `qwen2.5:7b` (đã pull xong và sẵn sàng).
- **Backend:** FastAPI (Python), port 8000. Đảm nhiệm phân quyền, SQL rewrite, column masking và gọi LLM để dịch ngôn ngữ tự nhiên sang SQL.
- **Frontend:** React + Vite, port 5173. Giao diện có sẵn tính năng đổi người dùng để test phân quyền.

## 🚀 Trạng thái hiện tại

Mọi thứ **đang chạy ngầm** và sẵn sàng để bạn test ngay bây giờ!

1. **Frontend:** Mở trình duyệt và truy cập `http://localhost:5173`
2. **Backend API:** `http://localhost:8000/docs` (nếu bạn muốn xem Swagger UI)

> [!TIP]
> Tất cả các services (Docker, Backend, Frontend) đã được mình khởi chạy tự động. Bạn chỉ cần mở trình duyệt lên là có thể thao tác ngay!

## 🧪 Kịch bản Test End-to-End

Hãy mở trang web `http://localhost:5173` và làm theo các bước sau:

### 1. Test với Giao dịch viên (teller_hn)
- Ở góc trên cùng, chọn user **Nguyễn Thị Hoa (GDV)**.
- Trong ô chat, gõ: `"Cho tôi xem danh sách khách hàng"`
- **Kết quả mong muốn:** Bạn sẽ chỉ thấy 2 khách hàng thuộc chi nhánh `HN`. Các cột `phone_number` và `id_number` sẽ bị làm mờ (masked) thành chuỗi `***`.

### 2. Test với Giám đốc chi nhánh (manager_hcm)
- Chuyển user sang **Trần Quốc Bảo (GĐ)**.
- Gõ lại câu hỏi: `"Cho tôi xem danh sách khách hàng"`
- **Kết quả mong muốn:** Sẽ chỉ hiển thị 2 khách hàng thuộc chi nhánh `HCM`. Cột số điện thoại hiển thị bình thường, nhưng cột `id_number` sẽ bị mã hoá Hash một chiều (e.g. `e3b0c44298fc`).

### 3. Test với Kiểm toán viên (auditor)
- Chuyển user sang **Lê Minh Tuấn (KTV)**.
- Gõ câu hỏi: `"Lấy cho tôi toàn bộ giao dịch"` hoặc `"Cho tôi xem danh sách khách hàng"`
- **Kết quả mong muốn:** Hiển thị toàn bộ dữ liệu của tất cả chi nhánh, không có dòng nào bị ẩn và không có cột nào bị mask.

## 📦 Cách quản lý project (Dành cho những lần chạy sau)

Nếu bạn khởi động lại máy, đây là cách để chạy lại toàn bộ hệ thống:

```bash
cd /home/dinhphu/Documents/ai-agent/ai-governance-demo

# 1. Bật Database & Ollama
docker compose up -d

# 2. Bật Backend (Mở 1 terminal mới)
cd backend
source .venv/bin/activate
python main.py

# 3. Bật Frontend (Mở 1 terminal mới)
cd frontend
npm run dev
```

> [!NOTE]
> Database đã được mình cấu hình tự động seed sẵn dữ liệu mẫu. Cấu trúc DB cũng đã được mapping thành catalog tài nguyên đa cấp (Database -> Schema -> Table -> Column) như mô tả trong lý thuyết SeABank.
