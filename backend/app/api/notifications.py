from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    notifications = await service.list_notifications(current_user.id, unread_only, limit)
    return [
        {
            "id": n.id,
            "type": n.type.value,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "reference_type": n.reference_type,
            "reference_id": n.reference_id,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    count = await service.count_unread(current_user.id)
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    await service.mark_read(notification_id, current_user.id)
    return {"message": "Marked as read"}


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    await service.mark_all_read(current_user.id)
    return {"message": "All marked as read"}
