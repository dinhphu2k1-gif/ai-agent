"""
OpenSearch Search Client cho Metadata Agent — OOP.
"""

from typing import Optional
from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer

from ..config import OPENSEARCH_CONFIG, INDEX_NAME, EMBEDDING_MODEL_NAME


class OpenSearchClient:
    """Client tra cứu Data Dictionary trên OpenSearch."""

    def __init__(self, config: dict = None, index_name: str = None, embedding_model_name: str = None):
        self._config = config or OPENSEARCH_CONFIG
        self._index_name = index_name or INDEX_NAME
        self._embedding_model_name = embedding_model_name or EMBEDDING_MODEL_NAME
        self._client: Optional[OpenSearch] = None
        self._embed_model: Optional[SentenceTransformer] = None

    # ── Connection ─────────────────────────────────────────

    @property
    def client(self) -> OpenSearch:
        """Lazy-init OpenSearch client."""
        if self._client is None:
            self._client = OpenSearch(**self._config)
            try:
                info = self._client.info()
                print(
                    f"✅ [Metadata Agent] Kết nối OpenSearch: v{info['version']['number']} "
                    f"| Cluster: {info['cluster_name']}"
                )
            except Exception as e:
                print(f"⚠️ [Metadata Agent] Kết nối OpenSearch thất bại: {e}")
        return self._client

    @property
    def embed_model(self) -> SentenceTransformer:
        """Lazy-init embedding model."""
        if self._embed_model is None:
            print(f"🧠 [Metadata Agent] Đang tải mô hình embedding {self._embedding_model_name}...")
            self._embed_model = SentenceTransformer(self._embedding_model_name)
            print(f"✅ [Metadata Agent] Embedding model sẵn sàng.")
        return self._embed_model

    # ── Search Methods ─────────────────────────────────────

    def search_by_keyword(
        self,
        query: str,
        record_type: Optional[str] = None,
        table_name: Optional[str] = None,
        size: int = 10,
    ) -> list[dict]:
        """BM25 keyword search trên business_name, description, business_rules."""
        must_clauses = [
            {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "business_name^3",
                        "description^2",
                        "business_rules",
                        "table_purpose",
                        "relationship_name^2",
                    ],
                }
            }
        ]

        if record_type:
            must_clauses.append({"term": {"record_type": record_type}})
        if table_name:
            must_clauses.append({"term": {"table_name": table_name}})

        body = {
            "query": {"bool": {"must": must_clauses}},
            "_source": {"excludes": ["description_vector"]},
            "size": size,
        }

        result = self.client.search(index=self._index_name, body=body)
        return result["hits"]["hits"]

    def search_by_semantic(self, query_text: str, size: int = 10) -> list[dict]:
        """k-NN semantic search trên description_vector."""
        q_vec = self.embed_model.encode([query_text], normalize_embeddings=True)[0].tolist()

        body = {
            "size": size,
            "_source": {"excludes": ["description_vector"]},
            "query": {
                "knn": {
                    "description_vector": {
                        "vector": q_vec,
                        "k": size,
                    }
                }
            },
        }

        result = self.client.search(index=self._index_name, body=body)
        return result["hits"]["hits"]

    def hybrid_search(
        self,
        query_text: str,
        record_type: Optional[str] = None,
        size: int = 10,
    ) -> list[dict]:
        """Hybrid search: BM25 keyword + k-NN semantic."""
        q_vec = self.embed_model.encode([query_text], normalize_embeddings=True)[0].tolist()

        should_clauses = [
            {
                "knn": {
                    "description_vector": {
                        "vector": q_vec,
                        "k": size,
                    }
                }
            },
            {
                "multi_match": {
                    "query": query_text,
                    "fields": [
                        "business_name^3",
                        "description^2",
                        "business_rules",
                        "table_purpose",
                        "relationship_name^2",
                    ],
                    "boost": 0.3,
                }
            },
        ]

        filter_clauses = []
        if record_type:
            filter_clauses.append({"term": {"record_type": record_type}})

        bool_query = {"should": should_clauses}
        if filter_clauses:
            bool_query["filter"] = filter_clauses

        body = {
            "size": size,
            "_source": {"excludes": ["description_vector"]},
            "query": {"bool": bool_query},
        }

        result = self.client.search(index=self._index_name, body=body)
        return result["hits"]["hits"]

    def get_table_schema(self, table_name: str) -> list[dict]:
        """Lấy toàn bộ COLUMN records của một bảng."""
        body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"record_type": "COLUMN"}},
                        {"term": {"table_name": table_name}},
                    ]
                }
            },
            "_source": {"excludes": ["description_vector"]},
            "sort": [{"column_name": {"order": "asc"}}],
            "size": 100,
        }

        result = self.client.search(index=self._index_name, body=body)
        return result["hits"]["hits"]

    def get_table_metadata(self, table_name: str) -> list[dict]:
        """Lấy TABLE-level metadata (record_type=TABLE) của một bảng."""
        body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"record_type": "TABLE"}},
                        {"term": {"table_name": table_name}},
                    ]
                }
            },
            "_source": {"excludes": ["description_vector"]},
            "size": 1,
        }

        result = self.client.search(index=self._index_name, body=body)
        return result["hits"]["hits"]

    def get_relationships(self, table_names: list[str]) -> list[dict]:
        """Lấy RELATIONSHIP records chứa bất kỳ bảng nào trong danh sách."""
        body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"record_type": "RELATIONSHIP"}},
                    ],
                    "should": [
                        {"terms": {"related_tables": table_names}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "_source": {"excludes": ["description_vector"]},
            "size": 10,
        }

        result = self.client.search(index=self._index_name, body=body)
        return result["hits"]["hits"]

    # ── Format Helpers ─────────────────────────────────────

    @staticmethod
    def format_search_results(hits: list[dict]) -> str:
        """Format kết quả search thành text có cấu trúc cho LLM đọc."""
        if not hits:
            return "Không tìm thấy kết quả nào trong Data Dictionary."

        sections = []
        for hit in hits:
            src = hit["_source"]
            rt = src.get("record_type", "COLUMN")

            if rt == "TABLE":
                section = (
                    f"[TABLE] {src.get('table_name', '')} — {src.get('business_name', '')}\n"
                    f"  Mô tả: {src.get('description', '')}\n"
                    f"  Mục đích: {src.get('table_purpose', '')}\n"
                    f"  Primary Key: {src.get('primary_key_columns', '')}\n"
                    f"  Natural Key: {src.get('natural_key', '')}\n"
                    f"  Bảng liên quan: {', '.join(src.get('related_tables', []))}\n"
                    f"  Ước tính rows: {src.get('estimated_row_count', '')}\n"
                    f"  Quy tắc: {src.get('business_rules', '') or 'N/A'}"
                )
            elif rt == "RELATIONSHIP":
                section = (
                    f"[RELATIONSHIP] {src.get('relationship_name', '')}\n"
                    f"  Mô tả: {src.get('description', '')}\n"
                    f"  Join Path: {src.get('join_path', '')}\n"
                    f"  Sample SQL: {src.get('sample_sql', '')}\n"
                    f"  Bảng liên quan: {', '.join(src.get('related_tables', []))}"
                )
            else:  # COLUMN
                fk_info = ""
                if src.get("is_foreign_key"):
                    fk_info = f" → FK({src.get('references_table', '')}.{src.get('references_column', '')})"
                pk_info = " [PK]" if src.get("is_primary_key") else ""

                section = (
                    f"[COLUMN] {src.get('table_name', '')}.{src.get('column_name', '')}"
                    f"{pk_info}{fk_info}\n"
                    f"  Kiểu: {src.get('data_type', '')}\n"
                    f"  Tên nghiệp vụ: {src.get('business_name', '')}\n"
                    f"  Mô tả: {src.get('description', '')}\n"
                    f"  Allowed values: {src.get('allowed_values', '') or 'N/A'}\n"
                    f"  Quy tắc: {src.get('business_rules', '') or 'N/A'}"
                )

            sections.append(section)

        return "\n\n".join(sections)
