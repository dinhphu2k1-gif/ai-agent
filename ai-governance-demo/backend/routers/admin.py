import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel

from database import get_db
from models import User, Role, UserRole, Permission, RowFilter, ColumnMask
from models.resource import Table, ColumnResource

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

class PermissionConfig(BaseModel):
    table_access: Optional[str] = "ALLOW"
    row_filter: Optional[str] = None
    phone_mask: Optional[str] = None  # 'PARTIAL', 'HASH', 'REDACT', 'NONE'
    id_mask: Optional[str] = None

@router.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.execute(select(User)).scalars().all()
    return users

@router.post("/users", response_model=UserResponse)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
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

    # Create Custom Role
    role_name = f"custom_{user_in.username}"
    custom_role = Role(name=role_name, display_name=f"Quyền tùy chỉnh - {user_in.username}")
    db.add(custom_role)
    db.flush()

    # Link User to Role
    db.add(UserRole(user_id=new_user.id, role_id=custom_role.id))
    db.commit()

    return new_user

@router.get("/users/{user_id}/permissions")
def get_user_permissions(user_id: uuid.UUID, db: Session = Depends(get_db)):
    # Find user
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    # Get user role
    user_role = db.execute(select(UserRole).where(UserRole.user_id == user_id)).scalars().first()
    if not user_role:
        return {}
    
    role_id = user_role.role_id

    # Get row filter for table 'customers'
    tbl = db.execute(select(Table).where(Table.name == "customers")).scalar_one_or_none()
    
    row_filter = None
    table_access = "ALLOW"
    if tbl:
        perm = db.execute(select(Permission).where(Permission.role_id == role_id, Permission.resource_id == tbl.resource_id)).scalar_one_or_none()
        if perm:
            table_access = perm.effect
            rf = db.execute(select(RowFilter).where(RowFilter.permission_id == perm.id)).scalar_one_or_none()
            if rf:
                row_filter = rf.condition_expr

    # Get masks for phone_number and id_number
    col_phone = db.execute(select(ColumnResource).where(ColumnResource.name == "phone_number")).scalar_one_or_none()
    col_idnum = db.execute(select(ColumnResource).where(ColumnResource.name == "id_number")).scalar_one_or_none()

    phone_mask = "NONE"
    id_mask = "NONE"

    if col_phone:
        perm = db.execute(select(Permission).where(Permission.role_id == role_id, Permission.resource_id == col_phone.resource_id)).scalar_one_or_none()
        if perm:
            if perm.effect == "DENY":
                phone_mask = "DENY"
            else:
                cm = db.execute(select(ColumnMask).where(ColumnMask.permission_id == perm.id)).scalar_one_or_none()
                if cm:
                    phone_mask = cm.mask_type
    
    if col_idnum:
        perm = db.execute(select(Permission).where(Permission.role_id == role_id, Permission.resource_id == col_idnum.resource_id)).scalar_one_or_none()
        if perm:
            if perm.effect == "DENY":
                id_mask = "DENY"
            else:
                cm = db.execute(select(ColumnMask).where(ColumnMask.permission_id == perm.id)).scalar_one_or_none()
                if cm:
                    id_mask = cm.mask_type

    return {
        "table_access": table_access,
        "row_filter": row_filter,
        "phone_mask": phone_mask,
        "id_mask": id_mask
    }

@router.put("/users/{user_id}/permissions")
def update_user_permissions(user_id: uuid.UUID, config: PermissionConfig, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    user_role = db.execute(select(UserRole).where(UserRole.user_id == user_id)).scalars().first()
    if not user_role:
        raise HTTPException(404, "User has no role")
    
    role_id = user_role.role_id

    # Resources
    tbl_customers = db.execute(select(Table).where(Table.name == "customers")).scalar_one_or_none()
    tbl_txns = db.execute(select(Table).where(Table.name == "transactions")).scalar_one_or_none()
    col_phone = db.execute(select(ColumnResource).where(ColumnResource.name == "phone_number")).scalar_one_or_none()
    col_idnum = db.execute(select(ColumnResource).where(ColumnResource.name == "id_number")).scalar_one_or_none()

    def _set_perm(resource_id, row_filter_expr=None, mask_type=None, mask_pattern="***", access_effect="ALLOW"):
        if not resource_id: return
        
        effect = "DENY" if mask_type == "DENY" else access_effect

        # Find existing permission
        perm = db.execute(select(Permission).where(Permission.role_id == role_id, Permission.resource_id == resource_id)).scalar_one_or_none()
        if not perm:
            perm = Permission(role_id=role_id, resource_id=resource_id, action="SELECT", effect=effect)
            db.add(perm)
            db.flush()
        else:
            perm.effect = effect
        
        # Row Filter
        if row_filter_expr:
            rf = db.execute(select(RowFilter).where(RowFilter.permission_id == perm.id)).scalar_one_or_none()
            if not rf:
                db.add(RowFilter(permission_id=perm.id, condition_expr=row_filter_expr))
            else:
                rf.condition_expr = row_filter_expr
        else:
            db.execute(RowFilter.__table__.delete().where(RowFilter.permission_id == perm.id))
        
        # Column Mask
        if mask_type and mask_type not in ["NONE", "DENY"]:
            cm = db.execute(select(ColumnMask).where(ColumnMask.permission_id == perm.id)).scalar_one_or_none()
            if not cm:
                db.add(ColumnMask(permission_id=perm.id, mask_type=mask_type, mask_pattern=mask_pattern))
            else:
                cm.mask_type = mask_type
        else:
            db.execute(ColumnMask.__table__.delete().where(ColumnMask.permission_id == perm.id))

    if tbl_customers:
        _set_perm(tbl_customers.resource_id, row_filter_expr=config.row_filter, access_effect=config.table_access)
    if tbl_txns:
        _set_perm(tbl_txns.resource_id, row_filter_expr=config.row_filter, access_effect=config.table_access)
    
    if col_phone:
        _set_perm(col_phone.resource_id, mask_type=config.phone_mask)
    if col_idnum:
        _set_perm(col_idnum.resource_id, mask_type=config.id_mask)
    
    db.commit()
    return {"message": "Permissions updated"}
