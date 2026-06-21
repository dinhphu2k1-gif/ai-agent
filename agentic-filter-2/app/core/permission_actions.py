"""Action catalog per resource type for Add Permission wizard (P1)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import PermissionType

# Preferred actions per leaf scope; intersected with DB permission_types when present.
ACTIONS_BY_RESOURCE_TYPE: dict[str, list[str]] = {
    "DATABASE": ["USAGE"],
    "SCHEMA": ["USAGE"],
    "TABLE": ["SELECT", "INSERT", "UPDATE", "DELETE", "DESCRIBE"],
    "COLUMN": ["SELECT"],
}


def normalize_resource_type(resource_type: str) -> str:
    return resource_type.strip().upper()


def catalog_actions_for_resource_type(
    session: Session, resource_type: str
) -> list[str]:
    """Return allowed action names for wizard step 2, filtered to seeded types."""
    key = normalize_resource_type(resource_type)
    preferred = ACTIONS_BY_RESOURCE_TYPE.get(key)
    if preferred is None:
        return []

    db_names = set(
        session.scalars(select(PermissionType.name).order_by(PermissionType.name)).all()
    )
    if not db_names:
        return list(preferred)
    return [a for a in preferred if a in db_names]
