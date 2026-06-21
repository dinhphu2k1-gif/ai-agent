"""Create / refresh OpenSearch index ``customers`` (two docs: Alice tenant 1, Bob tenant 2)."""

from __future__ import annotations

import json
from typing import Any

import httpx

CUSTOMERS_INDEX = "customers"


def delete_customers_index(client: httpx.Client) -> None:
    r = client.delete(f"/{CUSTOMERS_INDEX}")
    if r.status_code not in (200, 404):
        r.raise_for_status()


def seed_customers_index_two_documents(client: httpx.Client) -> None:
    """Index ``customers`` with two docs (tenant_id 1 and 2). Idempotent: replaces index."""
    delete_customers_index(client)
    mapping: dict[str, Any] = {
        "mappings": {
            "properties": {
                "name": {"type": "text"},
                "tenant_id": {"type": "integer"},
            }
        }
    }
    r = client.put(f"/{CUSTOMERS_INDEX}", json=mapping)
    r.raise_for_status()

    lines = [
        json.dumps({"index": {"_index": CUSTOMERS_INDEX, "_id": "1"}}),
        json.dumps({"name": "Alice", "tenant_id": 1}),
        json.dumps({"index": {"_index": CUSTOMERS_INDEX, "_id": "2"}}),
        json.dumps({"name": "Bob", "tenant_id": 2}),
    ]
    ndjson = "\n".join(lines) + "\n"
    r = client.post(
        "/_bulk",
        content=ndjson.encode("utf-8"),
        headers={"Content-Type": "application/x-ndjson"},
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get("errors"):
        raise RuntimeError(f"Bulk indexing errors: {payload}")

    r = client.post(f"/{CUSTOMERS_INDEX}/_refresh")
    r.raise_for_status()
