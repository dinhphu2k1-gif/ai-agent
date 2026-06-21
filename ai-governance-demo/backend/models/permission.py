"""Permission models: Permission, RowFilter, ColumnMask."""
import uuid
from sqlalchemy import Column, String, Text, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (
        CheckConstraint("effect IN ('ALLOW', 'DENY')", name="ck_effect"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(32), nullable=False, default="SELECT")
    effect = Column(String(16), nullable=False)  # ALLOW or DENY


class RowFilter(Base):
    __tablename__ = "row_filters"
    __table_args__ = (
        UniqueConstraint("permission_id", name="uq_row_filter_perm"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    condition_expr = Column(Text, nullable=False)  # e.g. "branch_code = '{user.branch_code}'"


class ColumnMask(Base):
    __tablename__ = "column_masks"
    __table_args__ = (
        CheckConstraint("mask_type IN ('PARTIAL', 'HASH', 'REDACT')", name="ck_mask_type"),
        UniqueConstraint("permission_id", name="uq_col_mask_perm"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    mask_type = Column(String(20), nullable=False)  # PARTIAL, HASH, REDACT
    mask_pattern = Column(Text, nullable=True)  # e.g. "091***5678" for PARTIAL
