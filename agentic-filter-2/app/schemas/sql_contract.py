from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


SqlDialect = Literal["postgresql"]


class SqlUserContext(BaseModel):
    user_id: str = Field(..., min_length=1, alias="userId")
    thread_id: str | None = Field(default=None, alias="threadId")

    model_config = {"populate_by_name": True}


class SqlQueryScopeTable(BaseModel):
    name: str = Field(..., min_length=1)
    schema_name: str | None = Field(default="public", alias="schema")
    columns: list[str] | None = None
    alias: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _norm_name(cls, v: str) -> str:
        return str(v or "").strip().upper()

    @field_validator("schema_name", mode="before")
    @classmethod
    def _norm_schema(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class SqlQueryScope(BaseModel):
    source: Literal["metadata_agent", "sql_parser", "manual"] = "metadata_agent"
    tables: list[SqlQueryScopeTable] = Field(..., min_length=1)


class SqlExecuteOptions(BaseModel):
    apply_row_filter: bool = Field(default=True, alias="applyRowFilter")
    apply_column_masking: bool = Field(default=True, alias="applyColumnMasking")
    allow_rewrite: bool = Field(default=True, alias="allowRewrite")
    strict_scope_match: bool = Field(default=True, alias="strictScopeMatch")

    model_config = {"populate_by_name": True}


class SqlExecuteRequest(SqlUserContext):
    sql: str = Field(..., min_length=1)
    dialect: SqlDialect = "postgresql"
    limit: int = Field(default=100, ge=1, le=1000)
    query_scope: SqlQueryScope = Field(..., alias="queryScope")
    options: SqlExecuteOptions = Field(default_factory=SqlExecuteOptions)

    model_config = {"populate_by_name": True}


class SqlWarningOut(BaseModel):
    code: str
    message: str
    resource: str | None = None


class SqlScopeMatchOut(BaseModel):
    declared_tables: list[str] = Field(default_factory=list, alias="declaredTables")
    parsed_tables: list[str] = Field(default_factory=list, alias="parsedTables")
    undeclared_tables: list[str] = Field(default_factory=list, alias="undeclaredTables")
    strict_scope_match: bool = Field(default=True, alias="strictScopeMatch")

    model_config = {"populate_by_name": True}


class SqlFilteredOut(BaseModel):
    checked_tables: list[str] = Field(default_factory=list, alias="checkedTables")
    checked_columns: list[str] = Field(default_factory=list, alias="checkedColumns")
    denied_tables: list[str] = Field(default_factory=list, alias="deniedTables")
    denied_columns: list[str] = Field(default_factory=list, alias="deniedColumns")
    masked_columns: list[str] = Field(default_factory=list, alias="maskedColumns")
    applied_row_filters: list[str] = Field(default_factory=list, alias="appliedRowFilters")
    scope_match: SqlScopeMatchOut | None = Field(default=None, alias="scopeMatch")

    model_config = {"populate_by_name": True}


class SqlExecuteDataOut(BaseModel):
    executed_sql: str = Field(alias="executedSql")
    columns: list[str]
    rows: list[list[Any]]
    row_count: int = Field(alias="rowCount")
    truncated: bool = False
    filtered: SqlFilteredOut = Field(default_factory=SqlFilteredOut)
    warnings: list[SqlWarningOut] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class SqlErrorOut(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    sql_state: str | None = Field(default=None, alias="sqlState")
    dialect: str | None = None

    model_config = {"populate_by_name": True}


class SqlExecuteResponse(BaseModel):
    success: bool = True
    data: SqlExecuteDataOut | None = None
    error: SqlErrorOut | None = None

