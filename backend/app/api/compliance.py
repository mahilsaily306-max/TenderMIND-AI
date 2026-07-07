
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.compliance_item import ComplianceItem, ComplianceStatus
from app.models.tender import Tender
from app.models.user import User
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/compliance", tags=["compliance"])


class ComplianceUpdate(BaseModel):
    status: ComplianceStatus
    note: str | None = None


class ComplianceCreate(BaseModel):
    requirement: str
    category: str | None = None
    status: ComplianceStatus = ComplianceStatus.PENDING
    note: str | None = None


@router.get("/tender/{tender_id}")
async def list_compliance_items(
    tender_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    # Verify tender scope
    result = await db.execute(
        select(Tender).where(Tender.id == tender_id, Tender.agency_id == agency.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    items = await db.execute(
        select(ComplianceItem).where(ComplianceItem.tender_id == tender_id).order_by(ComplianceItem.id)
    )
    return [
        {
            "id": item.id,
            "requirement": item.requirement,
            "category": item.category,
            "status": item.status.value,
            "is_ai_generated": item.is_ai_generated,
            "is_editable": item.is_editable,
            "source_page": item.source_page,
            "source_clause": item.source_clause,
            "note": item.note,
        }
        for item in items.scalars().all()
    ]


@router.patch("/{item_id}")
async def update_compliance_item(
    item_id: int,
    req: ComplianceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    result = await db.execute(select(ComplianceItem).where(ComplianceItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance item not found")

    # Verify tender scope
    t_result = await db.execute(
        select(Tender).where(Tender.id == item.tender_id, Tender.agency_id == agency.id)
    )
    if not t_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance item not found")

    item.status = req.status
    if req.note is not None:
        item.note = req.note
    item.updated_by = current_user.id
    await db.commit()
    await db.refresh(item)
    await create_audit_log(db, agency.id, current_user.id, "compliance.update", "compliance_item", item.id)
    return {
        "id": item.id,
        "status": item.status.value,
        "note": item.note,
    }


@router.post("/tender/{tender_id}")
async def create_compliance_item(
    tender_id: int,
    req: ComplianceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    # Verify tender scope
    result = await db.execute(
        select(Tender).where(Tender.id == tender_id, Tender.agency_id == agency.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    item = ComplianceItem(
        tender_id=tender_id,
        requirement=req.requirement,
        category=req.category,
        status=req.status,
        note=req.note,
        is_ai_generated=False,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {
        "id": item.id,
        "requirement": item.requirement,
        "status": item.status.value,
    }
