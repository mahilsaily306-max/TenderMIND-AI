from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.bid_readiness_score import BidReadinessScore
from app.models.tender import Tender
from app.models.user import User
from app.services.bid_readiness_service import BidReadinessService

router = APIRouter(prefix="/bid-readiness", tags=["bid-readiness"])


@router.post("/calculate/{tender_id}")
async def calculate_bid_readiness(
    tender_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    # Verify tender scope
    result = await db.execute(select(Tender).where(Tender.id == tender_id, Tender.agency_id == agency.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    service = BidReadinessService(db)
    score = await service.calculate(tender_id, calculated_by=current_user.id)
    return {
        "id": score.id,
        "overall_score": score.overall_score,
        "compliance_score": score.compliance_score,
        "experience_score": score.experience_score,
        "capacity_score": score.capacity_score,
        "risk_score": score.risk_score,
        "past_performance_score": score.past_performance_score,
        "weights_used": score.weights_used,
        "breakdown": score.breakdown,
        "calculated_at": score.calculated_at.isoformat(),
    }


@router.get("/{tender_id}")
async def get_latest_score(
    tender_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    result = await db.execute(
        select(BidReadinessScore)
        .where(BidReadinessScore.tender_id == tender_id)
        .order_by(BidReadinessScore.calculated_at.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No score calculated yet")

    return {
        "id": score.id,
        "overall_score": score.overall_score,
        "compliance_score": score.compliance_score,
        "experience_score": score.experience_score,
        "capacity_score": score.capacity_score,
        "risk_score": score.risk_score,
        "past_performance_score": score.past_performance_score,
        "weights_used": score.weights_used,
        "breakdown": score.breakdown,
        "calculated_at": score.calculated_at.isoformat(),
    }
