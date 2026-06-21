# AI Governance Demo — SeABank

Đây là dự án demo (Proof of Concept) chạy hoàn toàn trên môi trường Local, minh họa khả năng **AI Governance (Phân quyền dữ liệu cho AI)**.

Dự án thể hiện việc: **Cùng 1 câu hỏi bằng ngôn ngữ tự nhiên, 3 user với vai trò khác nhau sẽ nhận được kết quả dữ liệu khác nhau** (thông qua Row-Level Security và Column Masking).

## 🚀 Hướng dẫn khởi chạy

### Yêu cầu hệ thống
- **Docker & Docker Compose** (để chạy PostgreSQL và Ollama)
- **Python 3.10+** (cho Backend FastAPI)
- **Node.js 18+** (cho Frontend React/Vite)

---

### Bước 1: Khởi động Database & AI Model (Ollama)

Dự án sử dụng `docker-compose` để chạy PostgreSQL và Ollama (với model `qwen2.5:7b`).

```bash
# Di chuyển vào thư mục gốc của dự án
cd /home/dinhphu/Documents/ai-agent/ai-governance-demo

# Khởi động các container (chạy ngầm)
docker compose up -d
```
*Lưu ý: Lần chạy đầu tiên Ollama có thể mất thời gian để tải model `qwen2.5:7b`.*

---

### Bước 2: Khởi chạy Backend (FastAPI)

Backend chứa logic phân quyền (Filter Engine), gọi AI, và API kết nối với Frontend.

```bash
# 1. Di chuyển vào thư mục backend
cd backend

# 2. Cài đặt các thư viện Python cần thiết
pip3 install -r requirements.txt --user

# 3. Tạo cơ sở dữ liệu mẫu (Chỉ cần chạy 1 lần đầu tiên)
# Script này tạo table, users, roles, permissions và dummy banking data
python3 seed_data.py

# 4. Khởi chạy server
python3 main.py
```
Backend sẽ chạy tại: **http://localhost:8000**

---

### Bước 3: Khởi chạy Frontend (React + Vite)

Giao diện để chat và thay đổi User mô phỏng các vai trò khác nhau.

```bash
# 1. Mở một terminal mới, di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt các package Node.js
npm install

# 3. Khởi chạy server giao diện
npm run dev
```
Frontend sẽ chạy tại: **http://localhost:5173**

---

## 💡 Cách sử dụng Demo

1. Mở trình duyệt và truy cập: **http://localhost:5173**
2. Tại phần Header, bạn sẽ thấy 3 nút để chuyển đổi User:
   - 👤 **Giao dịch viên (HN)**: Chỉ thấy khách hàng/giao dịch thuộc chi nhánh HN, bị che số điện thoại và CMND (***).
   - 👔 **Giám đốc chi nhánh (HCM)**: Chỉ thấy dữ liệu chi nhánh HCM, CMND bị băm (Hash).
   - 🔍 **Kiểm toán viên**: Xem được toàn bộ dữ liệu của tất cả chi nhánh, không bị che giấu.
3. Thử gõ câu hỏi: *"Cho tôi xem danh sách khách hàng"* hoặc *"Liệt kê các giao dịch"*.
4. Bấm **Gửi** và quan sát:
   - Các bước suy luận của AI (Thinking -> SQL Generation).
   - Chính sách (Policy) được hệ thống tự động áp dụng (Allow, Filter, Mask, Deny).
   - Kết quả dữ liệu trả về khác nhau tuỳ thuộc vào User bạn đang chọn.

---

## 📂 Kiến trúc thư mục chính

- `docker-compose.yml`: Cấu hình chạy DB và Ollama.
- `backend/models/`: Cấu trúc Resource Catalog 4 cấp, Identity, và Permission.
- `backend/services/filter_engine.py`: Core logic xử lý phân quyền (Rewrite SQL + Masking).
- `backend/services/ai_agent.py`: Gọi Ollama Text-to-SQL.
- `frontend/src/App.tsx`: Giao diện React tích hợp SSE streaming để hiển thị kết quả real-time.
