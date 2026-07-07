from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.services.audit_service import create_audit_log
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.EMPLOYEE


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


@router.post("")
async def create_user(
    req: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
    agency=Depends(get_current_agency),
):
    service = UserService(db)
    user = await service.create_user(
        agency_id=agency.id,
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        role=req.role,
    )
    await create_audit_log(db, agency.id, current_user.id, "user.create", "user", user.id)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
    }


@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    service = UserService(db)
    users = await service.list_users(agency.id)
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in users
    ]


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    service = UserService(db)
    user = await service.get_user(user_id, agency.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    req: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
    agency=Depends(get_current_agency),
):
    service = UserService(db)
    user = await service.update_user(
        user_id,
        agency.id,
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        role=req.role,
        is_active=req.is_active,
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await create_audit_log(db, agency.id, current_user.id, "user.update", "user", user_id)
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role.value}
