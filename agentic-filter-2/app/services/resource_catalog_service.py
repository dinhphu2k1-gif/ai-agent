"""Catalog search and scope stats for Add Permission wizard (Phase 4)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin_contract import (
    ResourcePathSegment,
    ResourceScopeStatsOut,
    ResourceSearchData,
    ResourceSearchResultOut,
    ResourceTreeNodeOut,
)
from app.services.resource_tree_service import ResourceTreeService

_BREADCRUMB_SEP = " › "


class ResourceCatalogError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ResourceCatalogService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._rr = ResourceRepository(session)
        self._tree = ResourceTreeService(session)

    def search(self, q: str, *, limit: int = 50) -> ResourceSearchData:
        needle = (q or "").strip().lower()
        if not needle:
            return ResourceSearchData(results=[])

        cap = max(1, min(limit, 100))
        results: list[ResourceSearchResultOut] = []
        for db_node in self._tree.build_fe_tree():
            self._collect_search_matches(db_node, [], needle, results, cap)
            if len(results) >= cap:
                break
        return ResourceSearchData(results=results[:cap])

    def _collect_search_matches(
        self,
        node: ResourceTreeNodeOut,
        ancestors: list[ResourceTreeNodeOut],
        needle: str,
        results: list[ResourceSearchResultOut],
        cap: int,
    ) -> None:
        if len(results) >= cap:
            return
        chain = [*ancestors, node]
        if needle in node.name.lower():
            path = [
                ResourcePathSegment(id=n.id, name=n.name, type=n.type)
                for n in chain
            ]
            results.append(
                ResourceSearchResultOut(
                    node=ResourceTreeNodeOut(
                        id=node.id,
                        name=node.name,
                        type=node.type,
                        children=None,
                        is_primary_key=node.is_primary_key,
                        is_foreign_key=node.is_foreign_key,
                    ),
                    path=path,
                    breadcrumb=_BREADCRUMB_SEP.join(n.name for n in chain),
                )
            )
        for child in node.children or []:
            self._collect_search_matches(child, chain, needle, results, cap)
            if len(results) >= cap:
                return

    def scope_stats(self, resource_id: uuid.UUID) -> ResourceScopeStatsOut:
        res = self._rr.get_resource(resource_id)
        if res is None:
            raise ResourceCatalogError("NOT_FOUND", "Resource not found")

        rtype = res.resource_type
        if rtype == "DATABASE":
            return self._scope_stats_database(resource_id)
        if rtype == "SCHEMA":
            return self._scope_stats_schema(resource_id)
        raise ResourceCatalogError(
            "BAD_REQUEST",
            "scope-stats is only supported for DATABASE or SCHEMA resources",
        )

    def _scope_stats_database(self, database_id: uuid.UUID) -> ResourceScopeStatsOut:
        db = self._rr.get_database(database_id)
        if db is None:
            raise ResourceCatalogError("NOT_FOUND", "Database not found")

        schema_count = 0
        table_count = 0
        column_count = 0
        for sch in self._rr.list_schemas_for_database(database_id):
            schema_count += 1
            for tbl in self._rr.list_tables_for_schema(sch.resource_id):
                table_count += 1
                column_count += len(self._rr.list_columns_for_table(tbl.resource_id))

        name = db.name
        return ResourceScopeStatsOut(
            resource_id=str(database_id),
            resource_name=name,
            resource_type="database",
            schema_count=schema_count,
            table_count=table_count,
            column_count=column_count,
            message=(
                f"Permission will apply to {name} and propagate to all child resources."
            ),
        )

    def _scope_stats_schema(self, schema_id: uuid.UUID) -> ResourceScopeStatsOut:
        sch = self._rr.get_schema(schema_id)
        if sch is None:
            raise ResourceCatalogError("NOT_FOUND", "Schema not found")

        db = self._rr.get_database(sch.database_id)
        db_name = db.name if db else "database"

        table_count = 0
        column_count = 0
        for tbl in self._rr.list_tables_for_schema(schema_id):
            table_count += 1
            column_count += len(self._rr.list_columns_for_table(tbl.resource_id))

        name = sch.name
        return ResourceScopeStatsOut(
            resource_id=str(schema_id),
            resource_name=name,
            resource_type="schema",
            schema_count=1,
            table_count=table_count,
            column_count=column_count,
            message=(
                f"Permission will apply to {db_name}.{name} and propagate to all "
                "child resources."
            ),
        )
