from __future__ import annotations

import uuid

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class IamUserClaims(BaseModel):
    """Normalized claims after IAM token validation (internal DTO)."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    user_id: uuid.UUID = Field(validation_alias=AliasChoices("user_id", "sub", "id"))
    username: str = Field(validation_alias=AliasChoices("username", "preferred_username"))
    email: str = Field(validation_alias=AliasChoices("email", "mail"))
    is_active: bool = Field(
        default=True,
        validation_alias=AliasChoices("is_active", "active", "enabled"),
    )
