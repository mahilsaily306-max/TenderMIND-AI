
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.tender import Tender
from app.models.user import User
from app.services.audit_service import create_audit_log
from app.services.comment_service import CommentService

router = APIRouter(prefix="/comments", tags=["comments"])


class CommentCreate(BaseModel):
    tender_id: int
    content: str
    parent_id: int | None = None


@router.post("")
async def create_comment(
    req: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    # Verify tender scope
    result = await db.execute(
        select(Tender).where(Tender.id == req.tender_id, Tender.agency_id == agency.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    service = CommentService(db)
    comment = await service.create_comment(
        tender_id=req.tender_id,
        author_id=current_user.id,
        content=req.content,
        parent_id=req.parent_id,
    )
    await create_audit_log(db, agency.id, current_user.id, "comment.create", "comment", comment.id)
    return {
        "id": comment.id,
        "tender_id": comment.tender_id,
        "content": comment.content,
        "author_id": comment.author_id,
        "mentions": comment.mentions,
        "created_at": comment.created_at.isoformat(),
    }


@router.get("")
async def list_comments(
    tender_id: int = Query(...),
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

    service = CommentService(db)
    comments = await service.list_comments(tender_id)
    return [
        {
            "id": c.id,
            "parent_id": c.parent_id,
            "author_id": c.author_id,
            "content": c.content,
            "mentions": c.mentions,
            "created_at": c.created_at.isoformat(),
        }
        for c in comments
    ]
