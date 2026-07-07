from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, decode_token
from app.models.user import User
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TwoFactorRequest(BaseModel):
    email: EmailStr
    token: str
    temp_token: str


class Setup2FAResponse(BaseModel):
    secret: str
    qr_code: str
    uri: str


class Enable2FARequest(BaseModel):
    token: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    ip = request.client.host if request.client else None
    result = await service.authenticate(req.email, req.password, ip)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = result["user"]

    if result["requires_2fa"]:
        temp_token = create_access_token({"sub": str(user.id), "purpose": "2fa"}, expires_delta=timedelta(minutes=5))
        return {"requires_2fa": True, "temp_token": temp_token}

    login_result = await service.login(user, ip)
    return login_result


@router.post("/login/2fa")
async def verify_2fa(req: TwoFactorRequest, request: Request, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.temp_token)
    if not payload or payload.get("purpose") != "2fa":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired temp token")

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = AuthService(db)
    if not await service.verify_2fa(user, req.token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA token")

    ip = request.client.host if request.client else None
    login_result = await service.login(user, ip)
    return login_result


@router.post("/2fa/setup")
async def setup_2fa(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.setup_2fa(current_user)


@router.post("/2fa/enable")
async def enable_2fa(req: Enable2FARequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    if not await service.enable_2fa(current_user, req.token):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA token")
    return {"message": "2FA enabled"}


@router.post("/2fa/disable")
async def disable_2fa(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    await service.disable_2fa(current_user)
    return {"message": "2FA disabled"}


@router.post("/refresh")
async def refresh_token(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = create_access_token({"sub": payload["sub"], "role": payload.get("role"), "agency_id": payload.get("agency_id")})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "agency_id": current_user.agency_id,
        "totp_enabled": current_user.totp_enabled,
        "is_active": current_user.is_active,
    }
