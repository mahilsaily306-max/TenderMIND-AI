from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.bid_readiness_score import BidReadinessScore
from app.models.task import Task
from app.models.tender import Tender
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    # Tender stats
    tenders_result = await db.execute(
        select(Tender.status, func.count(Tender.id)).where(Tender.agency_id == agency.id).group_by(Tender.status)
    )
    tender_stats = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in tenders_result.fetchall()}

    total_tenders = sum(tender_stats.values())
    won = tender_stats.get("won", 0)
    lost = tender_stats.get("lost", 0)

    # Task stats
    tasks_result = await db.execute(
        select(Task.status, func.count(Task.id))
        .join(Tender, Task.tender_id == Tender.id)
        .where(Tender.agency_id == agency.id)
        .group_by(Task.status)
    )
    task_stats = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in tasks_result.fetchall()}

    # Latest scores (scoped to agency)
    scores_result = await db.execute(
        select(BidReadinessScore)
        .join(Tender, BidReadinessScore.tender_id == Tender.id)
        .where(Tender.agency_id == agency.id)
        .order_by(BidReadinessScore.calculated_at.desc())
        .limit(5)
    )
    recent_scores = [
        {"tender_id": s.tender_id, "overall_score": s.overall_score, "calculated_at": s.calculated_at.isoformat()}
        for s in scores_result.scalars().all()
    ]

    return {
        "tenders": {
            "total": total_tenders,
            "by_status": tender_stats,
            "win_rate": won / (won + lost) if (won + lost) > 0 else 0,
        },
        "tasks": {
            "total": sum(task_stats.values()),
            "by_status": task_stats,
        },
        "recent_scores": recent_scores,
    }


@router.get("/pipeline")
async def get_pipeline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    """Get tender pipeline by deadline."""
    result = await db.execute(
        select(Tender).where(
            Tender.agency_id == agency.id,
            Tender.status.in_(["identified", "qualification", "in_progress", "internal_review"]),
        ).order_by(Tender.bid_deadline.asc())
    )
    tenders = result.scalars().all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status.value,
            "bid_deadline": t.bid_deadline.isoformat() if t.bid_deadline else None,
            "estimated_value": t.estimated_value,
            "ai_readiness_score": t.ai_readiness_score,
        }
        for t in tenders
    ]
