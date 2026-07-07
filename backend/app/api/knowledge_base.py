from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


class KnowledgeBaseCreate(BaseModel):
    title: str
    content: str
    category: str | None = None
    tags: str | None = None
    source_url: str | None = None
    client_workspace_id: int | None = None


@router.post("")
async def create_kb_item(
    req: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    service = KnowledgeBaseService(db)
    item = await service.create_item(
        agency_id=agency.id,
        client_workspace_id=req.client_workspace_id,
        title=req.title,
        content=req.content,
        category=req.category,
        tags=req.tags,
        source_url=req.source_url,
        created_by=current_user.id,
    )
    return {
        "id": item.id,
        "title": item.title,
        "category": item.category,
    }


@router.get("")
async def list_kb_items(
    client_workspace_id: int | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    service = KnowledgeBaseService(db)
    items = await service.list_items(agency.id, client_workspace_id, category)
    return [
        {
            "id": i.id,
            "title": i.title,
            "category": i.category,
            "tags": i.tags,
            "client_workspace_id": i.client_workspace_id,
            "created_by": i.created_by,
            "created_at": i.created_at.isoformat(),
        }
        for i in items
    ]


@router.get("/search")
async def search_kb(
    q: str = Query(...),
    client_workspace_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    service = KnowledgeBaseService(db)
    items = await service.search(agency.id, q, client_workspace_id)
    return [
        {
            "id": i.id,
            "title": i.title,
            "content": i.content[:500] + "...",
            "category": i.category,
            "relevance": "text_match",
        }
        for i in items
    ]


@router.get("/{item_id}")
async def get_kb_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agency=Depends(get_current_agency),
):
    service = KnowledgeBaseService(db)
    item = await service.get_item(item_id, agency.id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "category": item.category,
        "tags": item.tags,
        "source_url": item.source_url,
        "created_at": item.created_at.isoformat(),
    }


@router.delete("/{item_id}")
async def delete_kb_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
    agency=Depends(get_current_agency),
):
    service = KnowledgeBaseService(db)
    if not await service.delete_item(item_id, agency.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return {"message": "Item deleted"}
