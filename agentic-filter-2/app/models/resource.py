from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (Index("ix_resources_resource_type", "resource_type"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)


class Database(Base):
    __tablename__ = "databases"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    resource: Mapped[Resource] = relationship()


class Schema(Base):
    __tablename__ = "schemas"
    __table_args__ = (Index("ix_schemas_database_id", "database_id"),)

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True
    )
    database_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    resource: Mapped[Resource] = relationship(foreign_keys=[resource_id])


class Table(Base):
    __tablename__ = "tables"
    __table_args__ = (Index("ix_tables_schema_id", "schema_id"),)

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True
    )
    schema_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    resource: Mapped[Resource] = relationship(foreign_keys=[resource_id])


class Column(Base):
    __tablename__ = "columns"
    __table_args__ = (Index("ix_columns_table_id", "table_id"),)

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True
    )
    table_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(128), nullable=False)
    is_primary_key: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_foreign_key: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    resource: Mapped[Resource] = relationship(foreign_keys=[resource_id])
