"""REST envelope types aligned with admin API (success, message, data)."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    message: str = ""
    data: T


class PageableResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    message: str = ""
    data: list[T]
    current_page: int = Field(1, alias="currentPage")
    total_items: int = Field(0, alias="totalItems")
    total_pages: int = Field(0, alias="totalPages")
