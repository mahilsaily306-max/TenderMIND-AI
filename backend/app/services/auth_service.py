from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_qr_code_base64,
    generate_totp_secret,
    get_totp_uri,
    verify_password,
    verify_totp,
)
from app.models.user import User
from app.services.audit_service import create_audit_log


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, email: str, password: str, _ip_address: str | None = None) -> dict | None:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return {
            "user": user,
            "requires_2fa": user.totp_enabled,
        }

    async def verify_2fa(self, user: User, token: str) -> bool:
        if not user.totp_secret:
            return False
        return verify_totp(user.totp_secret, token)

    async def login(self, user: User, ip_address: str | None = None) -> dict:
        access_token = create_access_token({"sub": str(user.id), "role": user.role.value, "agency_id": user.agency_id})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        user.last_login_at = datetime.now(UTC)
        user.last_login_ip = ip_address
        await self.db.commit()

        await create_audit_log(
            db=self.db,
            agency_id=user.agency_id,
            user_id=user.id,
            action="user.login",
            entity_type="user",
            entity_id=user.id,
            ip_address=ip_address,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "agency_id": user.agency_id,
            },
        }

    async def setup_2fa(self, user: User) -> dict:
        secret = generate_totp_secret()
        user.totp_secret = secret
        await self.db.commit()

        uri = get_totp_uri(secret, user.email)
        qr_code = generate_qr_code_base64(uri)

        return {
            "secret": secret,
            "qr_code": qr_code,
            "uri": uri,
        }

    async def enable_2fa(self, user: User, token: str) -> bool:
        if not verify_totp(user.totp_secret, token):
            return False
        user.totp_enabled = True
        await self.db.commit()
        return True

    async def disable_2fa(self, user: User) -> None:
        user.totp_secret = None
        user.totp_enabled = False
        await self.db.commit()
