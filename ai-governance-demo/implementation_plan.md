# Demo AI Governance — Dự án mới, chạy hoàn toàn Local

## Mục tiêu

Xây dựng một project mới từ đầu, demo AI Governance cho thấy: **cùng 1 câu hỏi bằng ngôn ngữ tự nhiên, 3 người khác nhau nhận kết quả khác nhau** — nhờ Row Filter, Column Masking, và DENY.

Chạy hoàn toàn local, không cần internet, không phụ thuộc 3 repo cũ.

---

## Kiến trúc tối giản

```
┌─────────────────────────────────────────────────────────┐
│                    Web UI (Vite + React)                 │
│              Dropdown chọn user + Chat box               │
│                     port 5173                            │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP (SSE streaming)
┌───────────────────────▼─────────────────────────────────┐
│                  Backend (FastAPI)                        │
│                     port 8000                            │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Chat API     │  │ AI Agent     │  │ Filter Engine │  │
│  │ (SSE stream) │→ │ (Text→SQL)   │→ │ (Phân quyền)  │  │
│  └──────────────┘  └──────┬───────┘  └───────┬───────┘  │
│                           │                   │          │
│                    ┌──────▼───────┐    ┌──────▼───────┐  │
│                    │   Ollama     │    │  PostgreSQL   │  │
│                    │ qwen2.5:7b   │    │  (data +      │  │
│                    │  port 11434  │    │   catalog)    │  │
│                    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

> [!TIP]
> **Chỉ cần 2 service ngoài:** PostgreSQL + Ollama. Không cần OpenSearch, Neo4j, Redis. RAM ước tính ~3GB + ~5GB VRAM → dư sức chạy trên máy bạn.

---

## Cấu trúc thư mục

```
/home/dinhphu/Documents/ai-agent/ai-governance-demo/
├── docker-compose.yml          # PostgreSQL + Ollama
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── requirements.txt
│   ├── models/
│   │   ├── resource.py         # Resource Catalog (4 cấp)
│   │   ├── identity.py         # User, Role, Group
│   │   └── permission.py       # Permission, RowFilter, ColumnMask
│   ├── services/
│   │   ├── auth_service.py     # Xác định user từ request
│   │   ├── filter_engine.py    # Kiểm tra quyền + SQL rewrite + masking
│   │   └── ai_agent.py         # Gọi Ollama: text → SQL
│   ├── seed_data.py            # Tạo dữ liệu demo (users, roles, permissions, banking data)
│   └── alembic/                # DB migrations
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx             # Layout chính
│   │   ├── components/
│   │   │   ├── UserSwitcher.tsx    # Dropdown chọn user
│   │   │   ├── ChatBox.tsx         # Gửi câu hỏi + hiển thị kết quả
│   │   │   └── ResultTable.tsx     # Bảng dữ liệu (highlight mask/filter)
│   │   └── main.tsx
│   └── vite.config.ts
└── README.md
```

---

## Chi tiết từng Component

### 1. Docker Compose (PostgreSQL + Ollama)

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: demo
      POSTGRES_PASSWORD: demo123
      POSTGRES_DB: governance_demo
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  pg_data:
  ollama_data:
```

---

### 2. Backend — Database Models

**Resource Catalog (4 cấp):**
- Bảng `resources` (id, type) + 4 bảng con: `databases`, `schemas`, `tables`, `columns`
- Mỗi cấp con có `parent_id` trỏ về cấp cha (giống repo cũ nhưng đơn giản hơn)

**Identity:**
- `users` (id, username, branch_code)
- `roles` (id, name)
- `user_roles` (user_id, role_id)

**Permission:**
- `permissions` (id, role_id, resource_id, effect ALLOW/DENY)
- `row_filters` (permission_id, condition_expr) — VD: `branch_code = '{user.branch}'`
- `column_masks` (permission_id, mask_type, mask_pattern)

---

### 3. Backend — Filter Engine (Core logic)

Luồng xử lý khi AI sinh SQL xong:

```python
def filter_and_execute(sql: str, user: User, db: Session) -> FilteredResult:
    # 1. Parse SQL → lấy table + columns
    parsed = parse_sql(sql)
    
    # 2. Tra Resource Catalog → lấy resource_id
    table_rid = find_table(parsed.schema, parsed.table)
    
    # 3. Resolve quyền (đi từ COLUMN → TABLE → SCHEMA → DATABASE)
    for col in parsed.columns:
        decision = resolve_access(user, col_rid)
        if decision == DENY:
            raise PermissionDenied(f"Không có quyền đọc cột {col}")
    
    # 4. Thu thập Row Filters → inject vào WHERE
    filters = collect_row_filters(user, table_rid)
    # Thay {user.branch} bằng giá trị thật
    filters = substitute_variables(filters, user)
    sql = inject_where(sql, filters)
    
    # 5. Thực thi SQL
    rows = db.execute(sql)
    
    # 6. Áp dụng Column Masking
    masks = collect_column_masks(user, parsed.columns)
    rows = apply_masks(rows, masks)
    
    return FilteredResult(rows=rows, policy=...)
```

---

### 4. Backend — AI Agent (Text → SQL)

Đơn giản hóa: **1 agent duy nhất** (không cần multi-agent cho demo). Gọi Ollama trực tiếp:

```python
async def text_to_sql(question: str) -> str:
    prompt = f"""Bạn là chuyên gia SQL. Database PostgreSQL có schema core_banking gồm:
    
    Bảng customers: customer_id, full_name, phone_number, id_number, branch_code, balance
    Bảng transactions: txn_id, customer_id, amount, txn_type, txn_date, branch_code
    
    Viết câu SQL cho câu hỏi sau. CHỈ trả về SQL, không giải thích.
    
    Câu hỏi: {question}"""
    
    response = await call_ollama(model="qwen2.5:7b", prompt=prompt)
    return extract_sql(response)
```

> [!NOTE]
> Khác với hệ thống cũ dùng LangGraph Multi-Agent phức tạp, demo này dùng **1 lần gọi LLM duy nhất** để chuyển text → SQL. Đủ minh họa cho phần AI Governance mà không cần kiến trúc agent phức tạp.

---

### 5. Backend — Chat API (SSE Streaming)

```
POST /api/chat
Body: { "question": "...", "user_id": "teller_hn" }
Response: SSE stream
  → event: thinking   data: "Đang phân tích câu hỏi..."
  → event: sql        data: "SELECT ... FROM core_banking.customers"
  → event: policy     data: {"decision": "ALLOW_WITH_FILTER_AND_MASK", "row_filter": "branch_code='HN'", "masked_columns": ["phone_number"]}
  → event: result     data: [{"customer_id": 1, "full_name": "Nguyễn Văn An", "phone_number": "091***5678", ...}]
```

---

### 6. Frontend — Giao diện

Giao diện gồm 3 phần chính:

1. **Header:** Dropdown chọn user (Giao dịch viên HN / Giám đốc HCM / Kiểm toán viên) — đổi user sẽ thay avatar + badge hiển thị role
2. **Chat area:** Gõ câu hỏi bằng tiếng Việt, kết quả stream lên real-time
3. **Result panel:** Bảng dữ liệu với:
   - Các ô bị **mask** highlight màu vàng (VD: `091***5678`)
   - Badge hiển thị policy: `ALLOW_WITH_FILTER`, `ALLOW_WITH_MASK`, `DENIED`
   - Dòng thông báo filter: _"Đã lọc: chỉ hiển thị dữ liệu branch_code = 'HN'"_

---

### 7. Seed Data

Script `seed_data.py` tạo toàn bộ trong 1 lần chạy:

**Banking data:**
- 5 khách hàng (HN: 2, HCM: 2, DN: 1)
- 6 giao dịch

**Resource Catalog:**
- 1 DATABASE → 1 SCHEMA → 2 TABLE → 12 COLUMN

**Identity & Permission:** (như bảng matrix trong plan trước)

| User | Role | Branch | Đặc điểm |
|------|------|--------|-----------|
| `teller_hn` | `teller` | HN | Row filter HN, mask SĐT+CMND |
| `manager_hcm` | `branch_manager` | HCM | Row filter HCM, mask CMND (hash) |
| `auditor` | `compliance_auditor` | — | Xem toàn bộ, không hạn chế |

---

## Thứ tự triển khai

| # | Việc | Ước tính |
|---|------|----------|
| 1 | Tạo project + docker-compose + models + migrations | 30 phút |
| 2 | Viết filter_engine.py (core logic) | 30 phút |
| 3 | Viết ai_agent.py (text→SQL qua Ollama) | 20 phút |
| 4 | Viết Chat API (SSE streaming) | 20 phút |
| 5 | Viết seed_data.py | 20 phút |
| 6 | Dựng Frontend (React + Vite) | 40 phút |
| 7 | Test end-to-end 3 scenario | 20 phút |

**Tổng: ~3 giờ**

---

## Verification Plan

### Automated Tests
```bash
# Chạy seed
python backend/seed_data.py

# Test Filter Engine trực tiếp
pytest backend/tests/test_filter_engine.py

# Test 3 scenario bằng curl
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Cho tôi xem danh sách khách hàng", "user_id": "teller_hn"}'
```

### Manual Verification
1. Mở `http://localhost:5173`
2. Chọn user **Giao dịch viên HN** → hỏi "Cho tôi xem danh sách khách hàng" → thấy 2 KH HN, SĐT bị che
3. Đổi sang **Giám đốc HCM** → hỏi lại → thấy 2 KH HCM, SĐT đầy đủ
4. Đổi sang **Kiểm toán viên** → hỏi lại → thấy 5 KH, toàn bộ dữ liệu

---

## Open Questions

> [!IMPORTANT]
> 1. **Model Ollama:** Bạn đã pull `qwen2.5:7b` chưa? Hay muốn dùng model khác (VD: `llama3.1:8b`, `mistral:7b`)?
> 2. **Ngôn ngữ giao diện:** Frontend hiển thị tiếng Việt hay tiếng Anh?
> 3. **Vị trí project:** Tạo tại `/home/dinhphu/Documents/ai-agent/ai-governance-demo/` được không?
