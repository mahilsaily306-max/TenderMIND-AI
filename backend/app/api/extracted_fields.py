from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.extracted_field import ExtractedField
from app.models.tender import Tender
from app.models.user import User

router = APIRouter(prefix="/extracted-fields", tags=["extracted-fields"])


class FieldUpdate(BaseModel):
    field_value: str | None = None
    is_verified: bool = False
    is_resolved: bool | None = None


@router.get("/tender/{tender_id}")
async def list_extracted_fields(
    tender_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    # Verify tender scope
    result = await db.execute(select(Tender).where(Tender.id == tender_id, Tender.agency_id == agency.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    fields = await db.execute(
        select(ExtractedField).where(ExtractedField.tender_id == tender_id).order_by(ExtractedField.field_name)
    )
    return [
        {
            "id": f.id,
            "field_name": f.field_name,
            "field_value": f.field_value,
            "is_ai_generated": f.is_ai_generated,
            "confidence": f.confidence,
            "is_resolved": f.is_resolved,
            "source_page": f.source_page,
            "source_clause": f.source_clause,
            "is_verified": f.is_verified,
        }
        for f in fields.scalars().all()
    ]


@router.patch("/{field_id}")
async def update_extracted_field(
    field_id: int,
    req: FieldUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    result = await db.execute(select(ExtractedField).where(ExtractedField.id == field_id))
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    # Verify tender scope
    t_result = await db.execute(select(Tender).where(Tender.id == field.tender_id, Tender.agency_id == agency.id))
    if not t_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    if req.field_value is not None:
        field.field_value = req.field_value
    field.is_verified = req.is_verified
    if req.is_resolved is not None:
        field.is_resolved = req.is_resolved
    if req.is_verified:
        field.verified_by = current_user.id
    await db.commit()
    await db.refresh(field)
    return {
        "id": field.id,
        "field_name": field.field_name,
        "field_value": field.field_value,
        "is_verified": field.is_verified,
        "is_resolved": field.is_resolved,
    }
