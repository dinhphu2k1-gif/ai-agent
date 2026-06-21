"""Re-export OpenSearch customers index helpers (shared with ``scripts/seed_demo_data.py``)."""

from __future__ import annotations

from scripts.opensearch_customers_seed import (
    CUSTOMERS_INDEX,
    delete_customers_index,
    seed_customers_index_two_documents,
)

__all__ = [
    "CUSTOMERS_INDEX",
    "delete_customers_index",
    "seed_customers_index_two_documents",
]
