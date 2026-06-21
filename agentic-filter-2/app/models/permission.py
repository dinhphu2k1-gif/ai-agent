from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PermissionType(Base):
    __tablename__ = "permission_types"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (
        Index("ix_permissions_resource_id", "resource_id"),
        Index("ix_permissions_permission_type_id", "permission_type_id"),
        CheckConstraint(
            "effect IN ('ALLOW', 'DENY')",
            name="ck_permissions_effect",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False
    )
    permission_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permission_types.id", ondelete="RESTRICT"), nullable=False
    )
    effect: Mapped[str] = mapped_column(String(16), nullable=False)

    permission_type: Mapped[PermissionType] = relationship()


class RowFilter(Base):
    __tablename__ = "row_filters"
    __table_args__ = (
        UniqueConstraint("permission_id", name="uq_row_filters_permission_id"),
        Index("ix_row_filters_permission_id", "permission_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False
    )
    condition_expr: Mapped[str] = mapped_column(Text, nullable=False)


class ColumnMask(Base):
    """Column mask policy per permission (one row per permission)."""

    __tablename__ = "column_masks"
    __table_args__ = (
        UniqueConstraint("permission_id", name="uq_column_masks_permission_id"),
        CheckConstraint(
            "mask_type IN ('FULL','PARTIAL','HASH','NULLIFY','CUSTOM')",
            name="ck_column_masks_mask_type",
        ),
        Index("ix_column_masks_permission_id", "permission_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    mask_type: Mapped[str] = mapped_column(String(20), nullable=False)
    mask_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
