from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_admin_mvp
from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin import (
    ColumnCreate,
    ColumnOut,
    DatabaseCreate,
    DatabaseOut,
    ResourceTreeOut,
    SchemaCreate,
    SchemaOut,
    TableCreate,
    TableOut,
)
from app.services.resource_tree_service import ResourceTreeService

router = APIRouter(
    prefix="/api/v1/admin/resources",
    tags=["admin-resources"],
    dependencies=[Depends(verify_admin_mvp)],
)


@router.post("/databases", response_model=DatabaseOut, status_code=status.HTTP_201_CREATED)
def create_database(
    body: DatabaseCreate,
    db: Session = Depends(get_db),
) -> DatabaseOut:
    rr = ResourceRepository(db)
    res = rr.create_resource("DATABASE")
    db_row = rr.create_database(res.id, body.name, body.description)
    return DatabaseOut(
        resource_id=db_row.resource_id, name=db_row.name, description=db_row.description
    )


@router.post("/schemas", response_model=SchemaOut, status_code=status.HTTP_201_CREATED)
def create_schema(body: SchemaCreate, db: Session = Depends(get_db)) -> SchemaOut:
    rr = ResourceRepository(db)
    if rr.get_database(body.database_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database resource not found",
        )
    res = rr.create_resource("SCHEMA")
    sch = rr.create_schema(res.id, body.database_id, body.name)
    return SchemaOut(
        resource_id=sch.resource_id, database_id=sch.database_id, name=sch.name
    )


@router.post("/tables", response_model=TableOut, status_code=status.HTTP_201_CREATED)
def create_table(body: TableCreate, db: Session = Depends(get_db)) -> TableOut:
    rr = ResourceRepository(db)
    if rr.get_schema(body.schema_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema resource not found",
        )
    res = rr.create_resource("TABLE")
    tbl = rr.create_table(res.id, body.schema_id, body.name)
    return TableOut(
        resource_id=tbl.resource_id, schema_id=tbl.schema_id, name=tbl.name
    )


@router.post("/columns", response_model=ColumnOut, status_code=status.HTTP_201_CREATED)
def create_column(body: ColumnCreate, db: Session = Depends(get_db)) -> ColumnOut:
    rr = ResourceRepository(db)
    if rr.get_table(body.table_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table resource not found",
        )
    res = rr.create_resource("COLUMN")
    col = rr.create_column(
        res.id,
        body.table_id,
        body.name,
        body.data_type,
        is_primary_key=body.is_primary_key,
        is_foreign_key=body.is_foreign_key,
    )
    return ColumnOut.model_validate(col)


@router.get("/mvp-tree", response_model=ResourceTreeOut)
def get_resource_tree(db: Session = Depends(get_db)) -> ResourceTreeOut:
    """Epic 3 resource tree shape (`databases` root). FE wizard uses ``GET /api/v1/admin/resources/tree``."""
    return ResourceTreeService(db).build_epic3_tree()
