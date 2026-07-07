from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User, UserRole


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(
        self,
        agency_id: int,
        email: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.EMPLOYEE,
    ) -> User:
        user = User(
            agency_id=agency_id,
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role=role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user(self, user_id: int, agency_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id, User.agency_id == agency_id))
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, agency_id: int, **kwargs) -> User | None:
        user = await self.get_user(user_id, agency_id)
        if not user:
            return None
        if "password" in kwargs and kwargs["password"]:
            kwargs["password_hash"] = get_password_hash(kwargs.pop("password"))
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def list_users(self, agency_id: int) -> list[User]:
        result = await self.db.execute(select(User).where(User.agency_id == agency_id).order_by(User.full_name))
        return list(result.scalars().all())

    async def deactivate_user(self, user_id: int, agency_id: int) -> bool:
        user = await self.get_user(user_id, agency_id)
        if not user:
            return False
        user.is_active = False
        await self.db.commit()
        return True
