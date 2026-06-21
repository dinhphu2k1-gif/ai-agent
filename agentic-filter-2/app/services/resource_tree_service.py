"""Build resource hierarchy for Epic 3 (snake) and admin contract §G (camelCase children)."""

from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy.orm import Session

from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin import (
    ColumnTreeOut,
    DatabaseTreeOut,
    ResourceTreeOut,
    SchemaTreeOut,
    TableTreeOut,
)
from app.schemas.admin_contract import ResourceTreeNodeOut

ResourceType = Literal["database", "schema", "table", "column"]


def column_key_flags(name: str) -> tuple[bool | None, bool | None]:
    """Heuristic PK/FK flags for permission wizard (contract §G.1)."""
    lower = name.lower()
    if lower in ("id", "event_id"):
        return True, None
    if lower.endswith("_id"):
        return None, True
    return None, None


def column_key_flags_for_tree(col: Column) -> tuple[bool | None, bool | None]:
    """Prefer catalog metadata; fall back to name heuristic when unset."""
    from app.models.resource import Column as ColumnModel

    if not isinstance(col, ColumnModel):
        raise TypeError("expected Column model instance")
    if col.is_primary_key is not None or col.is_foreign_key is not None:
        return col.is_primary_key, col.is_foreign_key
    return column_key_flags(col.name)


class ResourceTreeError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class ResourceTreeService:
    def __init__(self, session: Session) -> None:
        self._rr = ResourceRepository(session)

    def build_children_for_parent(
        self, parent_id: uuid.UUID
    ) -> list[ResourceTreeNodeOut]:
        """One hierarchy level under parent (Phase 6 lazy tree)."""
        res = self._rr.get_resource(parent_id)
        if res is None:
            raise ResourceTreeError("NOT_FOUND", "Resource not found")

        rtype = res.resource_type.upper()
        if rtype == "DATABASE":
            return [
                ResourceTreeNodeOut(
                    id=str(sch.resource_id),
                    name=sch.name,
                    type="schema",
                    children=None,
                )
                for sch in self._rr.list_schemas_for_database(parent_id)
            ]
        if rtype == "SCHEMA":
            return [
                ResourceTreeNodeOut(
                    id=str(tbl.resource_id),
                    name=tbl.name,
                    type="table",
                    children=None,
                )
                for tbl in self._rr.list_tables_for_schema(parent_id)
            ]
        if rtype == "TABLE":
            nodes: list[ResourceTreeNodeOut] = []
            for col in self._rr.list_columns_for_table(parent_id):
                is_pk, is_fk = column_key_flags_for_tree(col)
                nodes.append(
                    ResourceTreeNodeOut(
                        id=str(col.resource_id),
                        name=col.name,
                        type="column",
                        is_primary_key=is_pk,
                        is_foreign_key=is_fk,
                        children=None,
                    )
                )
            return nodes
        if rtype == "COLUMN":
            return []
        raise ResourceTreeError("BAD_REQUEST", f"Unsupported parent type: {rtype}")

    def build_fe_tree(self) -> list[ResourceTreeNodeOut]:
        nodes: list[ResourceTreeNodeOut] = []
        for db_row in self._rr.list_databases():
            schema_nodes: list[ResourceTreeNodeOut] = []
            for sch in self._rr.list_schemas_for_database(db_row.resource_id):
                table_nodes: list[ResourceTreeNodeOut] = []
                for tbl in self._rr.list_tables_for_schema(sch.resource_id):
                    col_nodes: list[ResourceTreeNodeOut] = []
                    for col in self._rr.list_columns_for_table(tbl.resource_id):
                        is_pk, is_fk = column_key_flags_for_tree(col)
                        col_nodes.append(
                            ResourceTreeNodeOut(
                                id=str(col.resource_id),
                                name=col.name,
                                type="column",
                                is_primary_key=is_pk,
                                is_foreign_key=is_fk,
                            )
                        )
                    table_nodes.append(
                        ResourceTreeNodeOut(
                            id=str(tbl.resource_id),
                            name=tbl.name,
                            type="table",
                            children=col_nodes or None,
                        )
                    )
                schema_nodes.append(
                    ResourceTreeNodeOut(
                        id=str(sch.resource_id),
                        name=sch.name,
                        type="schema",
                        children=table_nodes or None,
                    )
                )
            nodes.append(
                ResourceTreeNodeOut(
                    id=str(db_row.resource_id),
                    name=db_row.name,
                    type="database",
                    children=schema_nodes or None,
                )
            )
        return nodes

    def build_epic3_tree(self) -> ResourceTreeOut:
        databases_out: list[DatabaseTreeOut] = []
        for db_row in self._rr.list_databases():
            schemas_out: list[SchemaTreeOut] = []
            for sch in self._rr.list_schemas_for_database(db_row.resource_id):
                tables_out: list[TableTreeOut] = []
                for tbl in self._rr.list_tables_for_schema(sch.resource_id):
                    cols = [
                        ColumnTreeOut(
                            resource_id=c.resource_id,
                            name=c.name,
                            data_type=c.data_type,
                        )
                        for c in self._rr.list_columns_for_table(tbl.resource_id)
                    ]
                    tables_out.append(
                        TableTreeOut(
                            resource_id=tbl.resource_id,
                            name=tbl.name,
                            columns=cols,
                        )
                    )
                schemas_out.append(
                    SchemaTreeOut(
                        resource_id=sch.resource_id,
                        name=sch.name,
                        tables=tables_out,
                    )
                )
            databases_out.append(
                DatabaseTreeOut(
                    resource_id=db_row.resource_id,
                    name=db_row.name,
                    schemas=schemas_out,
                )
            )
        return ResourceTreeOut(databases=databases_out)
