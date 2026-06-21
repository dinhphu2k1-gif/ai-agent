import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel

from database import get_db
from models import User, Role, UserRole, Permission, RowFilter, ColumnMask
from models.resource import Schema, Table, ColumnResource

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Schemas
class UserCreate(BaseModel):
    username: str
    full_name: str
    branch_code: Optional[str] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str
    branch_code: Optional[str]

class PermissionRow(BaseModel):
    resource_id: uuid.UUID
    resource_name: str
    resource_type: str  # 'SCHEMA', 'TABLE', 'COLUMN'
    effect: str
    row_filter: Optional[str] = None
    mask_type: Optional[str] = None

class PermissionUpdate(BaseModel):
    resource_id: uuid.UUID
    effect: str
    row_filter: Optional[str] = None
    mask_type: Optional[str] = None

@router.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.execute(select(User)).scalars().all()
    return users

@router.post("/users", response_model=UserResponse)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.username == user_in.username)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=user_in.username,
        full_name=user_in.full_name,
        branch_code=user_in.branch_code
    )
    db.add(new_user)
    db.flush()

    role_name = f"custom_{user_in.username}"
    custom_role = Role(name=role_name, display_name=f"Quyền tùy chỉnh - {user_in.username}")
    db.add(custom_role)
    db.flush()

    db.add(UserRole(user_id=new_user.id, role_id=custom_role.id))
    db.commit()

    return new_user

@router.get("/users/{user_id}/permissions", response_model=List[PermissionRow])
def get_user_permissions(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    user_role = db.execute(select(UserRole).where(UserRole.user_id == user_id)).scalars().first()
    if not user_role:
        return []
    
    role_id = user_role.role_id

    # Fetch all permissions for this role
    perms = db.execute(select(Permission).where(Permission.role_id == role_id)).scalars().all()
    perm_map = {p.resource_id: p for p in perms}
    
    # Preload row filters and column masks
    perm_ids = [p.id for p in perms]
    row_filters = db.execute(select(RowFilter).where(RowFilter.permission_id.in_(perm_ids))).scalars().all() if perm_ids else []
    col_masks = db.execute(select(ColumnMask).where(ColumnMask.permission_id.in_(perm_ids))).scalars().all() if perm_ids else []
    
    rf_map = {rf.permission_id: rf.condition_expr for rf in row_filters}
    cm_map = {cm.permission_id: cm.mask_type for cm in col_masks}

    # Fetch resources
    schemas = db.execute(select(Schema)).scalars().all()
    tables = db.execute(select(Table)).scalars().all()
    columns = db.execute(select(ColumnResource)).scalars().all()

    schema_dict = {s.resource_id: s for s in schemas}
    table_dict = {t.resource_id: t for t in tables}

    rows = []
    
    # Schemas
    for s in schemas:
        p = perm_map.get(s.resource_id)
        rows.append(PermissionRow(
            resource_id=s.resource_id,
            resource_name=s.name,
            resource_type="SCHEMA",
            effect=p.effect if p else "ALLOW",
            row_filter=rf_map.get(p.id) if p else None,
            mask_type=None
        ))
        
    # Tables
    for t in tables:
        s_name = schema_dict[t.schema_id].name if t.schema_id in schema_dict else "unknown"
        p = perm_map.get(t.resource_id)
        rows.append(PermissionRow(
            resource_id=t.resource_id,
            resource_name=f"{s_name}.{t.name}",
            resource_type="TABLE",
            effect=p.effect if p else "ALLOW",
            row_filter=rf_map.get(p.id) if p else None,
            mask_type=None
        ))
        
    # Columns
    for c in columns:
        t = table_dict.get(c.table_id)
        s_name = "unknown"
        t_name = "unknown"
        if t:
            t_name = t.name
            s_name = schema_dict[t.schema_id].name if t.schema_id in schema_dict else "unknown"
        
        p = perm_map.get(c.resource_id)
        # For columns, if mask_type is "DENY", it's currently stored as effect=DENY in DB (as we did in step 1).
        # We need to map it back to mask_type="DENY" or leave it as effect="DENY".
        # Let's use the explicit `effect` and `mask_type` directly from DB.
        effect = p.effect if p else "ALLOW"
        mask_type = cm_map.get(p.id) if p else "NONE"
        if effect == "DENY":
            mask_type = "DENY" # For UI convenience
            
        rows.append(PermissionRow(
            resource_id=c.resource_id,
            resource_name=f"{s_name}.{t_name}.{c.name}",
            resource_type="COLUMN",
            effect=effect,
            row_filter=None,
            mask_type=mask_type
        ))

    return rows

@router.put("/users/{user_id}/permissions")
def update_user_permissions(user_id: uuid.UUID, updates: List[PermissionUpdate], db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    user_role = db.execute(select(UserRole).where(UserRole.user_id == user_id)).scalars().first()
    if not user_role:
        raise HTTPException(404, "User has no role")
    
    role_id = user_role.role_id

    for update in updates:
        resource_id = update.resource_id
        
        # Determine actual effect and mask
        effect = "DENY" if update.effect == "DENY" or update.mask_type == "DENY" else "ALLOW"
        
        perm = db.execute(select(Permission).where(Permission.role_id == role_id, Permission.resource_id == resource_id)).scalar_one_or_none()
        if not perm:
            perm = Permission(role_id=role_id, resource_id=resource_id, action="SELECT", effect=effect)
            db.add(perm)
            db.flush()
        else:
            perm.effect = effect
            
        # Row Filter
        if update.row_filter:
            rf = db.execute(select(RowFilter).where(RowFilter.permission_id == perm.id)).scalar_one_or_none()
            if not rf:
                db.add(RowFilter(permission_id=perm.id, condition_expr=update.row_filter))
            else:
                rf.condition_expr = update.row_filter
        else:
            db.execute(RowFilter.__table__.delete().where(RowFilter.permission_id == perm.id))
            
        # Column Mask
        if update.mask_type and update.mask_type not in ["NONE", "DENY"]:
            cm = db.execute(select(ColumnMask).where(ColumnMask.permission_id == perm.id)).scalar_one_or_none()
            if not cm:
                db.add(ColumnMask(permission_id=perm.id, mask_type=update.mask_type, mask_pattern="***"))
            else:
                cm.mask_type = update.mask_type
        else:
            db.execute(ColumnMask.__table__.delete().where(ColumnMask.permission_id == perm.id))

    db.commit()
    return {"message": "Permissions updated"}
