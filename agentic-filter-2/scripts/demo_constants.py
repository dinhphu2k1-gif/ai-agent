"""Constants for local demo seed + mock IAM (keep in sync with seed_demo_data.py)."""

from __future__ import annotations

import uuid

# IAM + Permission DB user must match this id.
DEMO_USER_ID: uuid.UUID = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

DATABASE_LOGICAL_NAME = "demo_db"
SCHEMA_NAME = "public"
TABLE_LOGICAL_NAME = "orders"

# OpenSearch: index name == logical table name (see ``resolve_opensearch_index_to_table_resource_id``).
OPENSEARCH_CUSTOMERS_TABLE = "customers"

MOCK_IAM_DEFAULT_PORT = 9999

# Stable UUIDs for admin UI demo seed (contract §I) — uuid5 in seed_demo_data.ADMIN_DEMO_NS
ADMIN_DEMO_NS = uuid.UUID("e9e9e9e9-e9e9-4e9e-8e9e-e9e9e9e9e9e9")
