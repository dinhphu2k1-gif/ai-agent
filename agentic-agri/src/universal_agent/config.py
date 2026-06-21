# src/universal_agent/config.py
"""
Cấu hình chung cho OpenSearch và Embedding Model.
Tái sử dụng bởi cả main.py (nạp dữ liệu) và agent (tra cứu).
"""

import os
from dotenv import load_dotenv
from opensearchpy import RequestsHttpConnection

load_dotenv()

# ════════════════════════════════════════════════════════════
# OPENSEARCH CONNECTION
# ════════════════════════════════════════════════════════════

OPENSEARCH_CONFIG = {
    "host": os.environ.get("OPENSEARCH_HOST", "192.168.2.161"),
    "port": int(os.environ.get("OPENSEARCH_PORT", 9200)),
    "use_ssl": True,
    "verify_certs": False,
    "http_auth": (
        os.environ.get("OPENSEARCH_USER", "admin"),
        os.environ.get("OPENSEARCH_PASSWORD", "MetadaaAgent@2026!"),
    ),
    "connection_class": RequestsHttpConnection,
    "timeout": 30,
    "ssl_assert_hostname": False,
    "ssl_show_warn": False,
    "retry_on_timeout": True,
    "max_retries": 3,
}

# ════════════════════════════════════════════════════════════
# INDEX
# ════════════════════════════════════════════════════════════

INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "data_dictionary")

# ════════════════════════════════════════════════════════════
# EMBEDDING MODEL
# ════════════════════════════════════════════════════════════

EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", 1024))

# ════════════════════════════════════════════════════════════
# FILTER SERVICE (metadata agent — permission-filtered retrieval)
# ════════════════════════════════════════════════════════════

def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


FILTER_SERVICE_BASE_URL = os.environ.get("FILTER_SERVICE_BASE_URL", "").strip() or None
FILTER_SERVICE_TIMEOUT_SEC = float(os.environ.get("FILTER_SERVICE_TIMEOUT_SEC", "10"))
METADATA_USE_FILTER_SERVICE = _parse_bool(
    os.environ.get("METADATA_USE_FILTER_SERVICE"), default=False
)
METADATA_TEST_USER_ID = os.environ.get("METADATA_TEST_USER_ID", "").strip() or None

# ════════════════════════════════════════════════════════════
# NEO4J (metadata agent — relationship expansion)
# ════════════════════════════════════════════════════════════

METADATA_NEO4J_ENABLED = _parse_bool(
    os.environ.get("METADATA_NEO4J_ENABLED"), default=True
)
METADATA_NEO4J_MAX_HOPS = int(os.environ.get("METADATA_NEO4J_MAX_HOPS", "2"))
METADATA_NEO4J_MAX_TABLES = int(os.environ.get("METADATA_NEO4J_MAX_TABLES", "8"))

# ════════════════════════════════════════════════════════════
# SQL EXECUTION (writer agent — filter-service or direct Postgres)
# ════════════════════════════════════════════════════════════

SQL_USE_FILTER_SERVICE = _parse_bool(
    os.environ.get("SQL_USE_FILTER_SERVICE"), default=False
)
SQL_EXECUTOR_DIALECT = os.environ.get("SQL_EXECUTOR_DIALECT", "postgresql").lower().strip()
MAX_SQL_REPAIR_ATTEMPTS = int(os.environ.get("MAX_SQL_REPAIR_ATTEMPTS", "2"))
SQL_EXECUTION_TIMEOUT_SEC = float(os.environ.get("SQL_EXECUTION_TIMEOUT_SEC", "60"))
