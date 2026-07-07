from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def create_audit_log(
    db: AsyncSession,
    agency_id: int,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    changes: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    log = AuditLog(
        agency_id=agency_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    await db.commit()
    return log
