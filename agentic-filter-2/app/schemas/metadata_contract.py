from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

MetadataRecordType = Literal["TABLE", "COLUMN", "RELATIONSHIP"]


class MetadataUserContext(BaseModel):
    user_id: str = Field(..., min_length=1, alias="userId")
    thread_id: str | None = Field(default=None, alias="threadId")

    model_config = {"populate_by_name": True}


class MetadataHybridSearchRequest(MetadataUserContext):
    query: str = Field(..., min_length=1)
    size: int = Field(default=10, ge=1, le=100)
    record_type: MetadataRecordType | None = Field(default=None, alias="recordType")
    table_name: str | None = Field(default=None, alias="tableName", min_length=1)

    model_config = {"populate_by_name": True}

    @field_validator("record_type", mode="before")
    @classmethod
    def _normalize_record_type(cls, value: str | None) -> str | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return str(value).strip().upper()


class MetadataKeywordSearchRequest(MetadataUserContext):
    query: str = Field(..., min_length=1)
    size: int = Field(default=10, ge=1, le=100)
    record_type: MetadataRecordType | None = Field(default=None, alias="recordType")
    table_name: str | None = Field(default=None, alias="tableName", min_length=1)

    model_config = {"populate_by_name": True}

    @field_validator("record_type", mode="before")
    @classmethod
    def _normalize_record_type(cls, value: str | None) -> str | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return str(value).strip().upper()


class MetadataRelationshipsRequest(MetadataUserContext):
    table_names: list[str] = Field(..., min_length=1, alias="tableNames")
    size: int = Field(default=20, ge=1, le=100)

    model_config = {"populate_by_name": True}


class MetadataFormatResultsRequest(BaseModel):
    hits: list[dict[str, Any]] = Field(default_factory=list)


class MetadataHitOut(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    score: float | None = Field(default=None, alias="_score")
    source: dict[str, Any] = Field(default_factory=dict, alias="_source")

    model_config = {"populate_by_name": True}


class MetadataFilteredOut(BaseModel):
    removed_tables: list[str] = Field(default_factory=list, alias="removedTables")
    removed_columns: list[str] = Field(default_factory=list, alias="removedColumns")
    removed_relationships: list[str] = Field(
        default_factory=list, alias="removedRelationships"
    )

    model_config = {"populate_by_name": True}


class MetadataWarningOut(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class MetadataDebugOut(BaseModel):
    took_ms: int = Field(alias="tookMs")
    query_mode: str = Field(alias="queryMode")
    index: str
    hybrid_leg: str | None = Field(
        default=None,
        alias="hybridLeg",
        description="knn_bm25 | keyword_fallback",
    )

    model_config = {"populate_by_name": True}


class MetadataSearchDataOut(BaseModel):
    hits: list[dict[str, Any]] = Field(default_factory=list)
    filtered: MetadataFilteredOut = Field(default_factory=MetadataFilteredOut)
    warnings: list[MetadataWarningOut] = Field(default_factory=list)
    debug: MetadataDebugOut | None = None


class MetadataFormatDataOut(BaseModel):
    raw_results: str = Field(alias="rawResults")

    model_config = {"populate_by_name": True}


class MetadataApiResponse(BaseModel):
    success: bool = True
    data: MetadataSearchDataOut | MetadataFormatDataOut | None = None
    error: dict[str, Any] | None = None


MetadataErrorCode = Literal[
    "VALIDATION_ERROR",
    "FORBIDDEN",
    "UPSTREAM_ERROR",
    "TIMEOUT",
    "USER_NOT_FOUND",
    "EMBEDDING_UNAVAILABLE",
]
