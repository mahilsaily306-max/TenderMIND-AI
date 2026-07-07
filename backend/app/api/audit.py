"""Audit log / timeline endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.audit_log import AuditLog
from app.models.tender import Tender
from app.models.user import User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/tender/{tender_id}")
async def get_tender_timeline(
    tender_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    # Verify tender scope
    result = await db.execute(select(Tender).where(Tender.id == tender_id, Tender.agency_id == agency.id))
    if not result.scalar_one_or_none():
        return []

    logs = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.agency_id == agency.id,
            AuditLog.entity_type == "tender",
            AuditLog.entity_id == tender_id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    )
    return [
        {
            "id": log.id,
            "action": log.action,
            "user_id": log.user_id,
            "changes": log.changes,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs.scalars().all()
    ]


@router.get("")
async def get_audit_logs(
    entity_type: str | None = Query(None),
    entity_id: int | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    query = select(AuditLog).where(AuditLog.agency_id == agency.id)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    query = query.order_by(AuditLog.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "changes": log.changes,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in result.scalars().all()
    ]
