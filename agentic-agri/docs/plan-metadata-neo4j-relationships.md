# Metadata Agent: Neo4j thay OpenSearch cho Relationships

## Goal

Trong `opensearch_retriever_node`, bỏ `client.get_relationships()` (OpenSearch/filter-service) và dùng Neo4j để mở rộng tập bảng + đường JOIN. Mọi bảng mới từ Neo4j phải được bổ sung TABLE/COLUMN metadata (qua filter-service hoặc OpenSearch) trước khi synthesizer/SQL Writer dùng.

## Hiện trạng (cần thay)

| Thành phần | Hành vi hiện tại | Vấn đề |
|------------|------------------|--------|
| `nodes.py` L185–197 | `client.get_relationships(tables[:5])` | Giới hạn 5 bảng seed, tối đa 10 RELATIONSHIP doc OpenSearch |
| `nodes.py` L201–227 | Chỉ `target_tables` mới gọi `get_table_metadata` + `get_table_schema` | Bảng phát hiện qua hybrid search / Neo4j không được lấy đủ schema |
| `sql_writer_agent/neo4j_client.py` | `build_context()`, `find_join_paths()`, `get_direct_relationships()` | Chỉ dùng ở SQL Writer, chưa dùng trong metadata retriever |
| `MetadataState` | `list_tables`, `raw_results` | Chưa có field riêng cho join context từ Neo4j |

## Kiến trúc đích

```
query_analyzer
    → opensearch_retriever
        1. hybrid/keyword → seed tables + hits (TABLE/COLUMN)
        2. Neo4j expand(seed tables) → related tables + join paths (text)
        3. expanded_tables = seed ∪ neo4j_tables \ already_fetched
        4. Với mỗi table trong expanded_tables: get_table_metadata + get_table_schema
        5. Gộp hits + format [RELATIONSHIP] từ Neo4j
    → result_synthesizer → synthesized_schema (đủ bảng + JOIN cho SQL Writer)
```

---

## Tasks

- [x] **Task 1: Mở rộng Neo4j client — trả về cấu trúc, không chỉ text**  
  File: `src/universal_agent/sql_writer_agent/neo4j_client.py` (hoặc tách `metadata_agent/neo4j_relationship_client.py` import shared).  
  Thêm:
  - `collect_related_tables(seed_tables, max_hops=2) -> list[str]` — từ `REFERENCES` edges + nodes trong `shortestPath`
  - `format_relationships_for_metadata(table_names) -> str` — format `[RELATIONSHIP]` / `[FK]` / `[PATH]` tương thích synthesizer (cùng style `OpenSearchClient.format_search_results`)  
  → Verify: unit test với mock driver hoặc Neo4j local (`pytest tests/test_neo4j_metadata_expansion.py -v`) trả đủ tên bảng khi seed `GL_JOURNAL_LINES`.

- [x] **Task 2: Cập nhật `MetadataState` + graph docstring**  
  File: `state.py`, `graph.py`.  
  Thêm optional: `neo4j_join_context: str`, `expanded_tables: list[str]` (debug/telemetry).  
  → Verify: type-check / import subgraph không lỗi.

- [x] **Task 3: Refactor `opensearch_retriever_node` — Neo4j thay OpenSearch relationships**  
  File: `nodes.py`.  
  - Xóa block `client.get_relationships(...)` (L185–197).  
  - Sau khi có `tables_to_find_rels`: gọi Neo4j → `related_tables`, `join_text`.  
  - `all_tables_for_schema = unique(seed từ hits + target_tables + related_tables)`.  
  - Loop **tất c** `all_tables_for_schema` (không chỉ `target_tables`): nếu chưa có COLUMN hits cho bảng đó → `get_table_metadata` + `get_table_schema`.  
  - Append `join_text` vào `raw_results` (hoặc state `neo4j_join_context` rồi merge trước format).  
  - Neo4j lỗi: log warning, tiếp tục với OpenSearch hits (không fail cả retriever).  
  → Verify: log `[Retriever] Neo4j expanded: N tables, M paths` và không còn gọi `/relationships` filter-service.

- [x] **Task 4: Cập nhật prompts**  
  File: `prompts.py`.  
  - Query analyzer: ghi chú RELATIONSHIP lấy từ Neo4j graph, `record_types` có thể bỏ `"RELATIONSHIP"` khỏi OpenSearch (giữ TABLE/COLUMN).  
  - Synthesizer: section **ĐƯỜNG DẪN JOIN** ưu tiên block Neo4j nếu có.  
  → Verify: một lần chạy subgraph in-memory với mock Neo4j + mock client schema.

- [x] **Task 5: Env & dependency**  
  File: `env.example`, `config.py` (nếu cần).  
  Document: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`; optional `METADATA_NEO4J_MAX_HOPS=2`, `METADATA_NEO4J_ENABLED=true`.  
  → Verify: `python scripts/seed_neo4j_relationships.py` + health Neo4j trước khi test E2E.

- [x] **Task 6: Tests**  
  - `tests/test_metadata_agent.py`: mock Neo4j expansion → assert `get_table_schema` được gọi cho bảng mới (vd. `GL_ACCOUNTS` khi seed chỉ có `GL_JOURNAL_LINES`).  
  - Giữ `test_get_relationships_*` trong OpenSearch integration tests (client vẫn tồn tại, chỉ retriever không dùng).  
  → Verify: `pytest tests/test_metadata_agent.py tests/test_neo4j_metadata_expansion.py -v`.

- [ ] **Task 7: Verification E2E (manual)**  
  1. Seed: OpenSearch dictionary + Neo4j graph.  
  2. Bật filter-service + `METADATA_USE_FILTER_SERVICE=true`.  
  3. Câu hỏi cross-domain (vd. *"số dư tài khoản khách hàng theo bút toán GL"*).  
  4. Kiểm tra log: bảng CIF + GL đều có COLUMN; synthesized_schema có JOIN path; SQL Writer không thiếu bảng.  
  → Verify: supervisor monitor hoặc chat API, `metadata_context` chứa ≥2 domain tables + join.

---

## Done When

- [x] Retriever **không** gọi `get_relationships` OpenSearch/filter-service.
- [x] Bảng chỉ xuất hiện qua Neo4j expansion vẫn có TABLE + COLUMN trong `raw_results` / `synthesized_schema`.
- [ ] SQL Writer nhận đủ metadata để JOIN (verify E2E manual).
- [x] Unit tests pass; E2E manual 1 câu cross-domain (Task 7 — chạy thủ công khi Neo4j + filter-service sẵn sàng).

## Ghi chú

- **Không xóa** `FilterServiceClient.get_relationships` / `OpenSearchClient.get_relationships` — có thể dùng ở tool khác hoặc fallback sau này.
- **Trùng Neo4j ở SQL Writer**: metadata agent là nguồn schema chính; SQL Writer `neo4j_context` giữ làm enrichment phụ (tránh duplicate prompt dài — có thể tắt writer Neo4j khi metadata đã gộp JOIN).
- **Giới hạn token**: cap số bảng expand (vd. max 8 bảng, max 15 relationship lines) — config `METADATA_NEO4J_MAX_TABLES`.
- **Permission**: schema bảng mở rộng vẫn qua filter-service `userId`; Neo4j chỉ gợi ý tên bảng, filter-service từ chối bảng không được phép.

## Phụ thuộc

- Neo4j đã seed: `python scripts/seed_neo4j_relationships.py`
- Filter-service hoặc OpenSearch direct cho TABLE/COLUMN
- Package `neo4j` đã có trong project (SQL Writer)
