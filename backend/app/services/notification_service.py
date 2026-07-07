from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: int,
        type: NotificationType,
        title: str,
        message: str | None = None,
        reference_type: str | None = None,
        reference_id: int | None = None,
    ) -> Notification:
        n = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self.db.add(n)
        await self.db.commit()
        await self.db.refresh(n)
        return n

    async def list_notifications(self, user_id: int, unread_only: bool = False, limit: int = 50) -> list[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        query = query.order_by(Notification.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_read(self, notification_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        )
        n = result.scalar_one_or_none()
        if not n:
            return False
        n.is_read = True
        await self.db.commit()
        return True

    async def mark_all_read(self, user_id: int) -> None:
        await self.db.execute(update(Notification).where(Notification.user_id == user_id).values(is_read=True))
        await self.db.commit()

    async def count_unread(self, user_id: int) -> int:
        result = await self.db.execute(
            select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        return len(result.scalars().all())
