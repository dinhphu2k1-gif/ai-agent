# Universal Supervisor - Multi-Agentic AI Architecture

Universal Supervisor là một hệ thống Multi-Agent được thiết kế theo kiến trúc **Supervisor - Worker pattern** (dựa trên khuôn khổ LangGraph). Nhiệm vụ của hệ thống này là phân tích chuyên sâu các yêu cầu truy xuất dữ liệu phức tạp của người dùng đối với một Data Warehouse, xác định lược đồ cơ sở dữ liệu (metadata/schema) và sau đó tự động trả về một câu lệnh SQL PostgreSQL chính xác.

Dự án áp dụng phương pháp lập trình **Hướng Đối Tượng (OOP)** với tính đóng gói cao, mỗi bộ phần mềm agent được tách độc lập thành thư mục riêng với state, prompts, nodes, và graph logic riêng biệt.

---

## 🏛️ Tổng Quan Kiến Trúc

Hệ thống hoạt động qua 3 Agents (1 Supervisor + 2 Workers):

1. **Supervisor Agent (Planner & Router):**
   Đóng vai trò là tổng bộ chỉ huy. Mọi thông tin người dùng đều đi qua node này đầu tiên để suy luận (ReAct - Reasoning and Acting). Dựa vào mục tiêu, bối cảnh và lịch sử log làm việc, Agent này đưa ra quyết định (định tuyến):
   - Chuyển việc cho `metadata_agent`.
   - Chuyển kết quả sang cho `sql_writer_agent`.
   - Dừng lại hỏi người dùng bằng cách đặt trạng thái chờ (Human-In-The-Loop - HITL) qua node `clarification`.

2. **Metadata Agent Sub-graph (OpenSearch Worker):**
   Agent chuyên trách tra cứu lược đồ Database (Data Dictionary). Đây không phải là một node đơn thuần mà là một **Sub-Graph** bao gồm:
   - *Query Analyzer:* Phân tích chuyên sâu đầu vào để lên chiến lược tra cứu semantic hay keyword.
   - *OpenSearch Retriever:* Connect tới DB Vector OpenSearch, dùng Hybrid Search (BM25 + k-NN BGE-M3 algorithm) đi quét dữ liệu TABLE, COLUMN, RELATIONSHIP.
   - *Result Synthesizer:* Tổng hợp các mảng dữ liệu rời rạc, làm gọn thành một JSON/Text Schema Report sạch đẹp.

3. **SQL Writer Agent (Code Generator):**
   Từ thông tin kết luận truy xuất Schema mà Metadata Agent tổng hợp, SQL Writer đóng vai trò kỹ sư dữ liệu tự động lập trình lệnh SQL PostgreSQL chuẩn xác tuân thủ nghiêm ngặt schema hiện hành.

4. **Global Graph**
```mermaid
graph TD
    subgraph "Supervisor Graph"
        START --> context_retriever
        context_retriever --> planner
        planner -->|consult_agent| metadata_worker_node
        planner -->|consult_agent| sql_writer_worker_node
        planner -->|ask_user| clarification_node
        planner -->|finalize_plan| END_MAIN["END"]
        metadata_worker_node --> planner
        sql_writer_worker_node --> planner
        clarification_node --> planner
    end

    subgraph "Metadata Sub-Graph"
        direction TB
        S_START["START"] --> query_analyzer["query_analyzer_node\nLLM phân tích yêu cầu\n→ sinh search strategy"]
        query_analyzer --> opensearch_retriever["opensearch_retriever_node\nHybrid Search\nBM25 + k-NN"]
        opensearch_retriever --> result_synthesizer["result_synthesizer_node\nLLM tổng hợp\n→ schema có cấu trúc"]
        result_synthesizer --> S_END["END"]
    end
```
---

## 📂 Cấu Trúc Thư Mục

```text
universal_supervisor/
├── langgraph.json                    # Cấu hình biên dịch LangGraph gốc
├── .env                              # Thông số kết nối API Key và DB (Secret - Bị chặn đẩy Git)
├── docker-compose.yml                # Postgres, Redis Stack, OpenSearch, Neo4j, Ollama
├── env.example                       # Mẫu biến môi trường (.env)
├── scripts/
│   ├── seed_data_dictionary.py       # OpenSearch — metadata data dictionary
│   ├── seed_postgres_data.py         # PostgreSQL — bảng GL/CIF + sample rows
│   ├── seed_neo4j_relationships.py   # Neo4j — quan hệ bảng cho SQL writer
│   ├── seed_chat_fixture.py          # Postgres chat — tin nhắn mẫu market-trends
│   └── migrations/chat/              # Schema chat (001–003)
├── tests/                            # Automation Test (pytest) theo các Levels (Logic -> Intergartion)
│
└── src/universal_agent/              # Toàn bộ mã nguồn cốt lõi Universal Agent AI
    ├── config.py                     # Quản lý constant kết nối môi trường gốc  
    ├── models.py                     # Quản lý khởi tạo Model thông minh qua OOP (LLMFactory)
    ├── utils.py                      # Parser text string và markdown chung
    │
    ├── supervisor/                   # AGENT 1: SUPERVISOR
    │   ├── state.py                  # Defines UniversalState & PlannerDecision schema
    │   ├── prompts.py                # PLANNER_SYSTEM_PROMPT
    │   ├── nodes.py                  # Retrieve Context, Planner, Clarification logic
    │   └── graph.py                  # Module ghép nối StateGraph -> SupervisorGraph Object
    │
    ├── metadata_agent/               # AGENT 2: METADATA SUB-GRAPH
    │   ├── state.py                  # Schema điều phối nội vi Metadata Agent
    │   ├── prompts.py                # Prompts phân tích và tổng hợp truy vấn AI
    │   ├── nodes.py                  # Analyze, Retrieve, Synthesize logics
    │   ├── opensearch_client.py      # OpenSearchClient OOP class chuyên truy suất hybrid search
    │   └── graph.py                  # Nối StateGraph nội bộ tạo ngắt mạch Sub-Graph
    │
    └── sql_writer_agent/             # AGENT 3: SQL WRITER
        ├── prompts.py                # Prompts ra lệnh viết SQL thuần kỹ thuật cứng
        └── nodes.py                  # Node logic điều phối code generator
```

---

## 🛠️ Luồng Khởi Chạy Và Execution

1. **Start ➔ Context Retriever:** 
   Giả lập truy vấn dữ liệu ngữ cảnh Long-term memory của Session người dùng.
   
2. **investigative_planner_node:**
   Dựa theo Request của người dùng, Supervisor LLM quyết định `intent`: `consult_agent`, `ask_user`, hay `finalize_plan`.

3. **dynamic_router (Routing Logic):**
   - Rẽ nhánh gọi Sub-Graph qua `metadata_worker_node` nếu cần tra cứu cấu trúc Data Warehouse.
   - Hoặc rẽ nhánh sang `sql_writer_worker_node` nếu hệ thống có đủ Metadata Context để lập trình.
   - Ngắt luồng gọi luồng Human In The Loop tại `clarification_node` để hỏi ngược User (ví dụ: User viết truy vấn chưa rõ ý).

4. Sau khi các `worker_node` làm xong tác vụ cục bộ của mình, Edge sẽ dội ngược trạng thái (kèm update log) **trở lại** `planner_node` để Supervisor nhận định lần nữa đã đủ điều kiện finalize hay cần rẽ tiếp.

## 🚀 Hướng Dẫn Chạy Local

### 1. Cài đặt Python

Python 3.10+ và virtualenv (khuyến nghị).

```bash
pip install -e .
pip install -e ".[dev]"
pip install -e ".[api]"

# Thêm khi chạy script seed (OpenSearch / Postgres / Neo4j)
pip install psycopg2-binary neo4j
```

Sao chép biến môi trường và điền API key LLM:

```bash
copy env.example .env   # Windows
# cp env.example .env   # Linux/macOS
```

Các biến bắt buộc cho agent: `SUPERVISOR_PROVIDER`, `WORKER_PROVIDER` và API key tương ứng (Google hoặc vLLM) — xem `env.example` và `src/universal_agent/models.py`.

---

### 2. Docker Compose — dịch vụ nào cần chạy?

File: [`docker-compose.yml`](docker-compose.yml)

| Service | Container | Port | Dùng cho |
|---------|-----------|------|----------|
| **postgres** | `postgres_db` | 5432 | Chat API (`agentic_chat`), dữ liệu GL/CIF (`core_banking`), SQL execution |
| **redis** | `redis_db` | 6379 | LangGraph checkpoint (`REDIS_URL`) — **bắt buộc Redis Stack**, không dùng `redis:alpine` |
| **opensearch** | `opensearch_db` | 9200 (HTTPS) | Metadata agent — data dictionary (hybrid search) |
| **neo4j** | `neo4j_db` | 7474 (UI), 7687 (Bolt) | SQL writer — gợi ý JOIN / quan hệ bảng |
| **ollama** | `ollama_container` | 11434 | Tùy chọn — LLM local (cần GPU NVIDIA trong compose) |

**Gói tối thiểu — chỉ Chat HTTP API + checkpoint:**

```bash
docker compose up -d postgres redis
```

**Gói đầy đủ — Chat + Metadata + SQL writer (khuyến nghị khi test agent):**

```bash
docker compose up -d postgres redis opensearch neo4j
```

**Tất cả (kể cả Ollama):**

```bash
docker compose up -d
```

Kiểm tra health:

```bash
docker compose ps
docker exec opensearch_db curl -sk -u "admin:MetadaaAgent@2026!" https://127.0.0.1:9200/_cluster/health?pretty
docker exec redis_db redis-cli ping
```

Thông tin đăng nhập mặc định trong compose:

- **PostgreSQL:** `admin` / `password123`, database mặc định container: `my_database`
- **OpenSearch:** `admin` / `MetadaaAgent@2026!` (khớp `OPENSEARCH_PASSWORD` trong `.env`)
- **Neo4j:** `neo4j` / `password123` (Browser: http://localhost:7474)
- **Redis:** không password (localhost:6379)

---

### 3. Cấu hình `.env` (khớp Docker)

Ví dụ tối thiểu cho **Chat API + agent** trên máy local:

```bash
# Chat
CHAT_DATABASE_URL=postgresql://admin:password123@localhost:5432/agentic_chat
CHAT_USE_MEMORY=false
REDIS_URL=redis://localhost:6379/0
CHAT_EMIT_CONTENT_DELTA=false

# OpenSearch (metadata)
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=MetadaaAgent@2026!
OPENSEARCH_INDEX=data_dictionary

# Postgres GL/CIF (SQL execution) — khi chạy seed_postgres_data.py
PG_HOST=localhost
PG_PORT=5432
PG_USER=admin
PG_PASSWORD=password123
PG_DATABASE=core_banking

# Neo4j (SQL writer relationships)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
```

---

### 4. Seed dữ liệu (thứ tự chạy)

Chạy **sau khi** container tương ứng đã healthy.

#### 4.1 PostgreSQL — database Chat (`agentic_chat`)

Tạo database (một lần):

```bash
docker exec postgres_db psql -U admin -d my_database -c "CREATE DATABASE agentic_chat;"
```

Áp migration schema chat (theo thứ tự):

```bash
# Windows PowerShell — pipe SQL vào container
Get-Content scripts/migrations/chat/001_init.sql | docker exec -i postgres_db psql -U admin -d agentic_chat
Get-Content scripts/migrations/chat/002_channel_members.sql | docker exec -i postgres_db psql -U admin -d agentic_chat
Get-Content scripts/migrations/chat/003_attachments.sql | docker exec -i postgres_db psql -U admin -d agentic_chat
```

```bash
# Linux/macOS
docker exec -i postgres_db psql -U admin -d agentic_chat < scripts/migrations/chat/001_init.sql
docker exec -i postgres_db psql -U admin -d agentic_chat < scripts/migrations/chat/002_channel_members.sql
docker exec -i postgres_db psql -U admin -d agentic_chat < scripts/migrations/chat/003_attachments.sql
```

Migration `001_init.sql` đã seed 4 channel mẫu (`threat-intel`, `network-anomaly`, `insider-risk`, `market-trends`). `002` gán `dev-user` quyền participant.

**Tin nhắn mẫu cho channel `market-trends` (tùy chọn):**

```bash
python scripts/seed_chat_fixture.py
```

#### 4.2 OpenSearch — data dictionary (metadata agent)

Cần `opensearch` đang chạy. Lần đầu tải embedding model `BAAI/bge-m3` có thể mất vài phút.

```bash
python scripts/seed_data_dictionary.py
```

#### 4.3 PostgreSQL — bảng GL/CIF + dữ liệu mẫu (SQL execution)

Tạo database `core_banking` (một lần), rồi seed:

```bash
docker exec postgres_db psql -U admin -d my_database -c "CREATE DATABASE core_banking;"
python scripts/seed_postgres_data.py
```

Script tạo bảng GL/CIF và ~100 dòng/bảng — dùng khi SQL writer thực thi query trên Postgres.

#### 4.4 Neo4j — quan hệ bảng (SQL writer)

Cần `neo4j` đang chạy:

```bash
python scripts/seed_neo4j_relationships.py
```

---

### 5. Chạy ứng dụng

**Chat HTTP API** (FastAPI — tích hợp FE, SSE, Postgres, Redis checkpoint):

```bash
uvicorn api.app:app --host 0.0.0.0 --port 9001 --app-dir src
```

```bash
# Health
curl http://localhost:9001/health

# Danh sách channel
curl http://localhost:9001/api/v1/chat/channels

# Tạo channel
curl -X POST http://localhost:9001/api/v1/chat/channels \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Q4 revenue analysis\"}"

# Lịch sử tin nhắn
curl "http://localhost:9001/api/v1/chat/channels/market-trends/messages?page=1&pageSize=50"

# Gửi tin + SSE (cần LLM + OpenSearch đã seed)
curl -N -X POST "http://localhost:9001/api/v1/chat/channels/market-trends/messages" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d "{\"type\":\"text\",\"content\":\"Mô tả bảng CIF_CUSTOMERS\"}"
```

Chi tiết contract FE: [`docs/chat-fe-integration_updated.md`](docs/chat-fe-integration_updated.md).

**Telegram bot** (giao diện cũ, tách với Chat API):

```bash
# TELEGRAM_BOT_TOKEN trong .env
python src/main.py
```

**LangGraph dev server** (tùy chọn):

```bash
langgraph dev
```

---

### 6. Kiểm thử (pytest)

Hệ thống AI Supervisor Agent hỗ trợ chẩn đoán và debug độc lập theo từng cấp bậc (Mock → Integration → E2E) bằng `pytest`:
```bash
# Unit logic checks (0% API Calls)
pytest tests/test_metadata_agent.py -v

# Logic call trực tiếp OpenSearch Database Integration
pytest tests/test_opensearch_integration.py -v

# Toàn luồng SubGraph Metadata + Full API call
pytest tests/test_metadata_subgraph.py -v
```
Khởi động tương tác test tay Supervisor tổng:
```bash
python -m tests.test_supervisor
```
