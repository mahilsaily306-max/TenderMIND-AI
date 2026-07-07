from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.client_workspace import ClientWorkspace
from app.models.tender import VALID_TRANSITIONS, Tender, TenderStatus
from app.models.user import User, UserRole
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/tenders", tags=["tenders"])


class TenderCreate(BaseModel):
    client_workspace_id: int
    title: str
    reference_number: str | None = None
    description: str | None = None
    bid_deadline: date | None = None
    estimated_value: float | None = None
    currency: str = "USD"


class TenderUpdate(BaseModel):
    title: str | None = None
    reference_number: str | None = None
    description: str | None = None
    status: TenderStatus | None = None
    bid_deadline: date | None = None
    estimated_value: float | None = None
    currency: str | None = None
    assigned_to: int | None = None


@router.post("")
async def create_tender(
    req: TenderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    # Verify workspace belongs to same agency
    ws_result = await db.execute(
        select(ClientWorkspace).where(
            ClientWorkspace.id == req.client_workspace_id,
            ClientWorkspace.agency_id == agency.id,
        )
    )
    workspace = ws_result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    tender = Tender(
        agency_id=agency.id,
        client_workspace_id=req.client_workspace_id,
        title=req.title,
        reference_number=req.reference_number,
        description=req.description,
        bid_deadline=req.bid_deadline,
        estimated_value=req.estimated_value,
        currency=req.currency,
        created_by=current_user.id,
    )
    db.add(tender)
    await db.commit()
    await db.refresh(tender)
    await create_audit_log(db, agency.id, current_user.id, "tender.create", "tender", tender.id)
    return {"id": tender.id, "title": tender.title, "status": tender.status.value}


@router.get("")
async def list_tenders(
    workspace_id: int | None = None,
    status_filter: TenderStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    query = select(Tender).where(Tender.agency_id == agency.id)

    if workspace_id:
        query = query.where(Tender.client_workspace_id == workspace_id)

    if current_user.role == UserRole.EMPLOYEE:
        query = query.where(Tender.assigned_to == current_user.id)

    if status_filter:
        query = query.where(Tender.status == status_filter)

    query = query.order_by(Tender.created_at.desc())
    result = await db.execute(query)
    tenders = result.scalars().all()

    return [
        {
            "id": t.id,
            "title": t.title,
            "reference_number": t.reference_number,
            "status": t.status.value,
            "client_workspace_id": t.client_workspace_id,
            "bid_deadline": t.bid_deadline.isoformat() if t.bid_deadline else None,
            "estimated_value": t.estimated_value,
            "assigned_to": t.assigned_to,
            "ai_readiness_score": t.ai_readiness_score,
            "created_at": t.created_at.isoformat(),
        }
        for t in tenders
    ]


@router.get("/{tender_id}")
async def get_tender(
    tender_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    result = await db.execute(select(Tender).where(Tender.id == tender_id, Tender.agency_id == agency.id))
    tender = result.scalar_one_or_none()
    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    return {
        "id": tender.id,
        "client_workspace_id": tender.client_workspace_id,
        "title": tender.title,
        "reference_number": tender.reference_number,
        "description": tender.description,
        "status": tender.status.value,
        "bid_deadline": tender.bid_deadline.isoformat() if tender.bid_deadline else None,
        "estimated_value": tender.estimated_value,
        "currency": tender.currency,
        "assigned_to": tender.assigned_to,
        "created_by": tender.created_by,
        "ai_readiness_score": tender.ai_readiness_score,
        "ai_go_nogo_recommendation": tender.ai_go_nogo_recommendation,
        "ai_go_nogo_explanation": tender.ai_go_nogo_explanation,
        "created_at": tender.created_at.isoformat(),
        "updated_at": tender.updated_at.isoformat(),
    }


@router.patch("/{tender_id}")
async def update_tender(
    tender_id: int,
    req: TenderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    result = await db.execute(select(Tender).where(Tender.id == tender_id, Tender.agency_id == agency.id))
    tender = result.scalar_one_or_none()
    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    if req.status and req.status != tender.status:
        allowed = VALID_TRANSITIONS.get(tender.status, [])
        if req.status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot transition from {tender.status.value} to {req.status.value}. "
                    f"Allowed: {[s.value for s in allowed]}"
                ),
            )
        tender.status = req.status

    if req.title is not None:
        tender.title = req.title
    if req.reference_number is not None:
        tender.reference_number = req.reference_number
    if req.description is not None:
        tender.description = req.description
    if req.bid_deadline is not None:
        tender.bid_deadline = req.bid_deadline
    if req.estimated_value is not None:
        tender.estimated_value = req.estimated_value
    if req.currency is not None:
        tender.currency = req.currency
    if req.assigned_to is not None:
        # Verify user belongs to same agency
        user_result = await db.execute(select(User).where(User.id == req.assigned_to, User.agency_id == agency.id))
        if not user_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user not found in agency")
        tender.assigned_to = req.assigned_to

    await db.commit()
    await db.refresh(tender)
    await create_audit_log(db, agency.id, current_user.id, "tender.update", "tender", tender_id)
    return {"id": tender.id, "title": tender.title, "status": tender.status.value}


@router.delete("/{tender_id}")
async def delete_tender(
    tender_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
    agency=Depends(get_current_agency),
):
    result = await db.execute(select(Tender).where(Tender.id == tender_id, Tender.agency_id == agency.id))
    tender = result.scalar_one_or_none()
    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")
    await db.delete(tender)
    await db.commit()
    await create_audit_log(db, agency.id, current_user.id, "tender.delete", "tender", tender_id)
    return {"message": "Tender deleted"}
