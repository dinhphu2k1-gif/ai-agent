from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any


@dataclass(frozen=True)
class ColumnMeta:
    schema_name: str
    table_name: str
    column_name: str
    data_type: str
    is_primary_key: bool
    is_foreign_key: bool
    references_table: str | None
    references_column: str | None
    business_name: str | None
    description: str | None
    allowed_values: tuple[str, ...]
    business_rules: str | None
    domain_name: str | None
    ordinal_position: int

    @property
    def pg_table_name(self) -> str:
        return self.table_name.lower()

    @property
    def pg_name(self) -> str:
        return self.column_name.lower()


@dataclass(frozen=True)
class TableMeta:
    schema_name: str
    table_name: str
    business_name: str | None
    description: str | None
    table_purpose: str | None
    primary_key_columns: tuple[str, ...]
    natural_key_columns: tuple[str, ...]
    related_tables: tuple[str, ...]
    estimated_row_count: Any
    business_rules: str | None
    domain_name: str | None
    columns: tuple[ColumnMeta, ...]

    @property
    def pg_name(self) -> str:
        return self.table_name.lower()


@dataclass(frozen=True)
class ForeignKeyMeta:
    child_table: str
    child_column: str
    parent_table: str
    parent_column: str
    business_name: str | None
    description: str | None

    @property
    def child_pg_table(self) -> str:
        return self.child_table.lower()

    @property
    def child_pg_column(self) -> str:
        return self.child_column.lower()

    @property
    def parent_pg_table(self) -> str:
        return self.parent_table.lower()

    @property
    def parent_pg_column(self) -> str:
        return self.parent_column.lower()


@dataclass(frozen=True)
class RelationshipMeta:
    name: str
    description: str | None
    join_path: str | None
    sample_sql: str | None
    tables: tuple[str, ...]
    domain_name: str | None


@dataclass(frozen=True)
class MetadataBundle:
    tables: tuple[TableMeta, ...]
    columns: tuple[ColumnMeta, ...]
    foreign_keys: tuple[ForeignKeyMeta, ...]
    relationships: tuple[RelationshipMeta, ...]


@lru_cache(maxsize=1)
def load_all_records() -> tuple[dict[str, Any], ...]:
    from seed_data_dictionary import ALL_RECORDS

    return tuple(ALL_RECORDS)


def _normalize_sequence(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value).strip()
    if not text:
        return ()
    return tuple(part.strip() for part in text.split(",") if part.strip())


def parse_allowed_values(values: Any) -> tuple[str, ...]:
    normalized = []
    for item in _normalize_sequence(values):
        normalized.append(item.split(":", 1)[0].strip())
    return tuple(value for value in normalized if value)


@lru_cache(maxsize=1)
def extract_column_records() -> tuple[ColumnMeta, ...]:
    columns: list[ColumnMeta] = []

    for ordinal_position, record in enumerate(load_all_records(), start=1):
        if record.get("record_type") != "COLUMN":
            continue
        columns.append(
            ColumnMeta(
                schema_name=record.get("schema_name", ""),
                table_name=record.get("table_name", ""),
                column_name=record.get("column_name", ""),
                data_type=record.get("data_type", "TEXT"),
                is_primary_key=bool(record.get("is_primary_key")),
                is_foreign_key=bool(record.get("is_foreign_key")),
                references_table=record.get("references_table"),
                references_column=record.get("references_column"),
                business_name=record.get("business_name"),
                description=record.get("description"),
                allowed_values=parse_allowed_values(record.get("allowed_values")),
                business_rules=record.get("business_rules"),
                domain_name=record.get("domain_name"),
                ordinal_position=ordinal_position,
            )
        )

    return tuple(columns)


@lru_cache(maxsize=1)
def extract_foreign_keys() -> tuple[ForeignKeyMeta, ...]:
    foreign_keys = []

    for column in extract_column_records():
        if not column.is_foreign_key or not column.references_table or not column.references_column:
            continue
        foreign_keys.append(
            ForeignKeyMeta(
                child_table=column.table_name,
                child_column=column.column_name,
                parent_table=column.references_table,
                parent_column=column.references_column,
                business_name=column.business_name,
                description=column.description,
            )
        )

    return tuple(foreign_keys)


@lru_cache(maxsize=1)
def extract_relationship_records() -> tuple[RelationshipMeta, ...]:
    relationships = []

    for record in load_all_records():
        if record.get("record_type") != "RELATIONSHIP":
            continue
        relationships.append(
            RelationshipMeta(
                name=record.get("relationship_name", ""),
                description=record.get("description"),
                join_path=record.get("join_path"),
                sample_sql=record.get("sample_sql"),
                tables=_normalize_sequence(record.get("related_tables")),
                domain_name=record.get("domain_name"),
            )
        )

    return tuple(relationships)


@lru_cache(maxsize=1)
def extract_table_records() -> tuple[TableMeta, ...]:
    columns_by_table: dict[str, list[ColumnMeta]] = {}
    first_seen: dict[str, int] = {}

    for column in extract_column_records():
        columns_by_table.setdefault(column.table_name, []).append(column)
        first_seen.setdefault(column.table_name, column.ordinal_position)

    table_records: list[TableMeta] = []
    seen_tables: set[str] = set()

    for record in load_all_records():
        if record.get("record_type") != "TABLE":
            continue
        table_name = record.get("table_name", "")
        table_columns = tuple(columns_by_table.get(table_name, []))
        pk_columns = tuple(column.column_name for column in table_columns if column.is_primary_key)
        if not pk_columns:
            pk_columns = _normalize_sequence(record.get("primary_key_columns"))
        table_records.append(
            TableMeta(
                schema_name=record.get("schema_name", ""),
                table_name=table_name,
                business_name=record.get("business_name"),
                description=record.get("description"),
                table_purpose=record.get("table_purpose"),
                primary_key_columns=pk_columns,
                natural_key_columns=_normalize_sequence(record.get("natural_key")),
                related_tables=_normalize_sequence(record.get("related_tables")),
                estimated_row_count=record.get("estimated_row_count"),
                business_rules=record.get("business_rules"),
                domain_name=record.get("domain_name"),
                columns=table_columns,
            )
        )
        seen_tables.add(table_name)

    for table_name, table_columns in columns_by_table.items():
        if table_name in seen_tables:
            continue
        table_records.append(
            TableMeta(
                schema_name=table_columns[0].schema_name,
                table_name=table_name,
                business_name=None,
                description=None,
                table_purpose=None,
                primary_key_columns=tuple(
                    column.column_name for column in table_columns if column.is_primary_key
                ),
                natural_key_columns=(),
                related_tables=(),
                estimated_row_count=None,
                business_rules=None,
                domain_name=table_columns[0].domain_name,
                columns=tuple(table_columns),
            )
        )

    table_records.sort(key=lambda table: first_seen.get(table.table_name, 10**9))
    return tuple(table_records)


@lru_cache(maxsize=1)
def load_metadata_bundle() -> MetadataBundle:
    return MetadataBundle(
        tables=extract_table_records(),
        columns=extract_column_records(),
        foreign_keys=extract_foreign_keys(),
        relationships=extract_relationship_records(),
    )


def topological_table_order(
    tables: tuple[TableMeta, ...] | list[TableMeta],
    foreign_keys: tuple[ForeignKeyMeta, ...] | list[ForeignKeyMeta],
) -> list[str]:
    dependency_map = {table.table_name: set() for table in tables}

    for foreign_key in foreign_keys:
        if foreign_key.child_table == foreign_key.parent_table:
            continue
        if foreign_key.child_table not in dependency_map:
            dependency_map[foreign_key.child_table] = set()
        dependency_map[foreign_key.child_table].add(foreign_key.parent_table)
        dependency_map.setdefault(foreign_key.parent_table, set())

    ready = sorted(table_name for table_name, deps in dependency_map.items() if not deps)
    ordered: list[str] = []

    while ready:
        current = ready.pop(0)
        ordered.append(current)
        for table_name, deps in dependency_map.items():
            if current in deps:
                deps.remove(current)
                if not deps and table_name not in ordered and table_name not in ready:
                    ready.append(table_name)
                    ready.sort()

    remaining = sorted(table_name for table_name in dependency_map if table_name not in ordered)
    return ordered + remaining


def infer_table_category(table: TableMeta) -> str:
    table_name = table.table_name.upper()
    if table_name.endswith("_LINES"):
        return "transaction_detail"
    if table_name.endswith("_HEADERS"):
        return "transaction"
    if "BALANCE" in table_name:
        return "aggregate"
    if table_name.endswith("_PERIODS") or table_name.endswith("_COST_CENTERS"):
        return "dimension"
    if table_name.endswith("_CUSTOMERS") or table_name.endswith("_ACCOUNTS"):
        return "master"
    if table_name.endswith("_IDENTIFICATIONS") or table_name.endswith("_ADDRESSES"):
        return "detail"
    return "reference"
