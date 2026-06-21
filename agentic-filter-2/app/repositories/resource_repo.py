from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.resource import Column, Database, Resource, Schema, Table


class ResourceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_resource(self, resource_type: str) -> Resource:
        row = Resource(resource_type=resource_type)
        self._session.add(row)
        self._session.flush()
        return row

    def get_resource(self, resource_id: uuid.UUID) -> Resource | None:
        return self._session.get(Resource, resource_id)

    def create_database(
        self, resource_id: uuid.UUID, name: str, description: str | None
    ) -> Database:
        row = Database(resource_id=resource_id, name=name, description=description)
        self._session.add(row)
        self._session.flush()
        return row

    def create_schema(
        self, resource_id: uuid.UUID, database_id: uuid.UUID, name: str
    ) -> Schema:
        row = Schema(resource_id=resource_id, database_id=database_id, name=name)
        self._session.add(row)
        self._session.flush()
        return row

    def create_table(
        self, resource_id: uuid.UUID, schema_id: uuid.UUID, name: str
    ) -> Table:
        row = Table(resource_id=resource_id, schema_id=schema_id, name=name)
        self._session.add(row)
        self._session.flush()
        return row

    def create_column(
        self,
        resource_id: uuid.UUID,
        table_id: uuid.UUID,
        name: str,
        data_type: str,
        *,
        is_primary_key: bool | None = None,
        is_foreign_key: bool | None = None,
    ) -> Column:
        if is_primary_key is None and is_foreign_key is None:
            from app.services.resource_tree_service import column_key_flags

            is_primary_key, is_foreign_key = column_key_flags(name)
        row = Column(
            resource_id=resource_id,
            table_id=table_id,
            name=name,
            data_type=data_type,
            is_primary_key=is_primary_key,
            is_foreign_key=is_foreign_key,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get_database(self, resource_id: uuid.UUID) -> Database | None:
        return self._session.get(Database, resource_id)

    def list_schemas_for_database(self, database_id: uuid.UUID) -> list[Schema]:
        return list(
            self._session.scalars(
                select(Schema).where(Schema.database_id == database_id)
            ).all()
        )

    def list_databases(self) -> list[Database]:
        return list(self._session.scalars(select(Database)).all())

    def get_schema(self, resource_id: uuid.UUID) -> Schema | None:
        return self._session.get(Schema, resource_id)

    def get_table(self, resource_id: uuid.UUID) -> Table | None:
        return self._session.get(Table, resource_id)

    def get_column(self, resource_id: uuid.UUID) -> Column | None:
        return self._session.get(Column, resource_id)

    def list_tables_for_schema(self, schema_id: uuid.UUID) -> list[Table]:
        return list(
            self._session.scalars(select(Table).where(Table.schema_id == schema_id)).all()
        )

    def list_columns_for_table(self, table_id: uuid.UUID) -> list[Column]:
        return list(
            self._session.scalars(select(Column).where(Column.table_id == table_id)).all()
        )

    def find_database_resource_id_by_name(self, name: str) -> uuid.UUID | None:
        row = self._session.scalars(select(Database).where(Database.name == name)).first()
        return row.resource_id if row else None

    def find_schema_resource_id(self, database_resource_id: uuid.UUID, name: str) -> uuid.UUID | None:
        row = self._session.scalars(
            select(Schema).where(
                Schema.database_id == database_resource_id,
                Schema.name == name,
            )
        ).first()
        return row.resource_id if row else None

    def find_table_resource_id(self, schema_resource_id: uuid.UUID, name: str) -> uuid.UUID | None:
        row = self._session.scalars(
            select(Table).where(
                Table.schema_id == schema_resource_id,
                Table.name == name,
            )
        ).first()
        return row.resource_id if row else None

    def find_column_resource_id(self, table_resource_id: uuid.UUID, name: str) -> uuid.UUID | None:
        row = self._session.scalars(
            select(Column).where(
                Column.table_id == table_resource_id,
                Column.name == name,
            )
        ).first()
        if row is not None:
            return row.resource_id
        # Catalog may store lowercase names while SQL/parser use uppercase identifiers.
        return self._session.scalars(
            select(Column.resource_id).where(
                Column.table_id == table_resource_id,
                Column.name.ilike(name),
            )
        ).first()

    def find_table_resource_ids_by_table_name(self, name: str) -> list[uuid.UUID]:
        """All table resources whose logical table name matches (OpenSearch index → table MVP)."""
        rows = self._session.scalars(select(Table).where(Table.name == name)).all()
        return [r.resource_id for r in rows]

    def get_ancestor_resource_ids(self, resource_id: uuid.UUID) -> list[uuid.UUID]:
        """Ancestors from target up to database: [self, parent, ..., db] (§7.1)."""
        res = self.get_resource(resource_id)
        if res is None:
            return []
        out: list[uuid.UUID] = []
        if res.resource_type == "COLUMN":
            col = self.get_column(resource_id)
            if col is None:
                return []
            out.append(resource_id)
            tbl = self.get_table(col.table_id)
            if tbl is None:
                return out
            out.append(tbl.resource_id)
            sch = self.get_schema(tbl.schema_id)
            if sch is None:
                return out
            out.append(sch.resource_id)
            out.append(sch.database_id)
            return out
        if res.resource_type == "TABLE":
            tbl = self.get_table(resource_id)
            if tbl is None:
                return []
            out.append(resource_id)
            sch = self.get_schema(tbl.schema_id)
            if sch is None:
                return out
            out.append(sch.resource_id)
            out.append(sch.database_id)
            return out
        if res.resource_type == "SCHEMA":
            sch = self.get_schema(resource_id)
            if sch is None:
                return []
            out.append(resource_id)
            out.append(sch.database_id)
            return out
        if res.resource_type == "DATABASE":
            out.append(resource_id)
            return out
        return [resource_id]
