"""Resolve OpenSearch index name to catalog table resource (Epic 7 MVP)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.repositories.resource_repo import ResourceRepository


class UnknownOpenSearchIndexError(ValueError):
    def __init__(self, index: str) -> None:
        super().__init__(f"Unknown index '{index}' in resource catalog")
        self.index = index


class AmbiguousOpenSearchIndexError(ValueError):
    def __init__(self, index: str) -> None:
        super().__init__(
            f"Index '{index}' matches multiple tables; disambiguate mapping (§17)"
        )
        self.index = index


def resolve_opensearch_index_to_table_resource_id(
    session: Session, index: str
) -> uuid.UUID:
    """
    MVP convention: OpenSearch index name equals logical table name (unique in catalog).
    """
    rr = ResourceRepository(session)
    ids = rr.find_table_resource_ids_by_table_name(index.strip())
    if not ids:
        raise UnknownOpenSearchIndexError(index)
    if len(ids) > 1:
        raise AmbiguousOpenSearchIndexError(index)
    return ids[0]
