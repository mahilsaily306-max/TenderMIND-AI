
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.proposal_section import ProposalSection
from app.models.tender import Tender
from app.models.user import User
from app.services.copilot_service import CopilotService

router = APIRouter(prefix="/copilot", tags=["copilot"])


class CopilotRequest(BaseModel):
    text: str
    context: str | None = None


class ToneRequest(BaseModel):
    text: str
    tone: str


@router.post("/rewrite")
async def rewrite(req: CopilotRequest, current_user: User = Depends(get_current_user)):
    service = CopilotService()
    result = await service.rewrite(req.text, req.context)
    return {"original": req.text, "result": result, "type": "rewrite", "is_ai_generated": True}


@router.post("/expand")
async def expand(req: CopilotRequest, current_user: User = Depends(get_current_user)):
    service = CopilotService()
    result = await service.expand(req.text, req.context)
    return {"original": req.text, "result": result, "type": "expand", "is_ai_generated": True}


@router.post("/improve")
async def improve(req: CopilotRequest, current_user: User = Depends(get_current_user)):
    service = CopilotService()
    result = await service.improve(req.text)
    return {"original": req.text, "result": result, "type": "improve", "is_ai_generated": True}


@router.post("/change-tone")
async def change_tone(req: ToneRequest, current_user: User = Depends(get_current_user)):
    service = CopilotService()
    result = await service.change_tone(req.text, req.tone)
    return {"original": req.text, "result": result, "type": "tone_change", "tone": req.tone, "is_ai_generated": True}


@router.post("/sections")
async def create_proposal_section(
    tender_id: int = Query(...),
    section_title: str = Query(...),
    content: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    result = await db.execute(
        select(Tender).where(Tender.id == tender_id, Tender.agency_id == agency.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    section = ProposalSection(
        tender_id=tender_id,
        section_title=section_title,
        content=content,
        created_by=current_user.id,
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return {
        "id": section.id,
        "section_title": section.section_title,
        "content": section.content,
        "status": section.status.value,
    }


@router.get("/sections/{tender_id}")
async def list_sections(
    tender_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    result = await db.execute(
        select(Tender).where(Tender.id == tender_id, Tender.agency_id == agency.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    sections = await db.execute(
        select(ProposalSection).where(ProposalSection.tender_id == tender_id).order_by(ProposalSection.sort_order)
    )
    return [
        {
            "id": s.id,
            "section_title": s.section_title,
            "content": s.content,
            "status": s.status.value,
            "is_ai_generated": s.is_ai_generated,
            "word_count": s.word_count,
        }
        for s in sections.scalars().all()
    ]
