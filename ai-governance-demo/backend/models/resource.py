"""Resource Catalog — 4-level hierarchy: DATABASE → SCHEMA → TABLE → COLUMN."""
import uuid
from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type = Column(String(32), nullable=False)  # DATABASE | SCHEMA | TABLE | COLUMN


class Database(Base):
    __tablename__ = "databases"

    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)


class Schema(Base):
    __tablename__ = "schemas"

    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True)
    database_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)


class Table(Base):
    __tablename__ = "tables"

    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True)
    schema_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)


class ColumnResource(Base):
    __tablename__ = "columns"

    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True)
    table_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    data_type = Column(String(128), nullable=False, default="text")
    is_primary_key = Column(Boolean, default=False)
