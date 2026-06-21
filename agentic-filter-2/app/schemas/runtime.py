"""Runtime API schemas."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class UserContextResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    username: str
    email: str
    is_active: bool
    group_ids: list[uuid.UUID] = Field(default_factory=list)
    direct_role_ids: list[uuid.UUID] = Field(default_factory=list)
    inherited_role_ids: list[uuid.UUID] = Field(default_factory=list)


class AuthorizeRequest(BaseModel):
    resource_id: uuid.UUID
    action: str = Field(default="SELECT", min_length=1, max_length=64)


class ColumnMaskPolicyOut(BaseModel):
    permission_id: uuid.UUID
    mask_type: str
    mask_pattern: str | None


class PolicyDecisionOut(BaseModel):
    decision: str
    row_filter_exprs: list[str] = Field(default_factory=list)
    column_masks: list[ColumnMaskPolicyOut] = Field(default_factory=list)
    combined_row_filter: str | None = None
    deny_reason: str | None = None


class FilterQueryRequest(BaseModel):
    backend: Literal["postgres"] = "postgres"
    database: str = Field(..., min_length=1, max_length=255)
    query: str = Field(..., min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = Field(default=None, max_length=128)


class QueryPolicyOut(BaseModel):
    decision: str
    masked_columns: list[str] = Field(default_factory=list)
    row_filters_applied: int = 0


class FilterQueryResponse(BaseModel):
    request_id: str | None = None
    backend: str
    columns: list[str]
    rows: list[dict[str, Any]]
    policy: QueryPolicyOut


class FilterSearchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    backend: Literal["opensearch"] = "opensearch"
    index: str = Field(..., min_length=1, max_length=255)
    query: dict[str, Any]
    request_id: str | None = Field(default=None, max_length=128)
    source: Any | None = Field(
        default=None,
        validation_alias=AliasChoices("_source", "source"),
    )
    size: int | None = Field(default=None, ge=1, le=10_000)
    from_: int | None = Field(default=None, validation_alias="from", ge=0)
    sort: list[Any] | dict[str, Any] | None = None
    post_filter: dict[str, Any] | None = None


class FilterSearchResponse(BaseModel):
    request_id: str | None = None
    backend: Literal["opensearch"] = "opensearch"
    hits: dict[str, Any]
    policy: QueryPolicyOut
