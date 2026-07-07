from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base_item import KnowledgeBaseItem


class KnowledgeBaseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_item(
        self,
        agency_id: int,
        client_workspace_id: int | None,
        title: str,
        content: str,
        created_by: int,
        category: str | None = None,
        tags: str | None = None,
        source_url: str | None = None,
    ) -> KnowledgeBaseItem:
        item = KnowledgeBaseItem(
            agency_id=agency_id,
            client_workspace_id=client_workspace_id,
            title=title,
            content=content,
            category=category,
            tags=tags,
            source_url=source_url,
            created_by=created_by,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def list_items(
        self, agency_id: int, client_workspace_id: int | None = None, category: str | None = None
    ) -> list[KnowledgeBaseItem]:
        query = select(KnowledgeBaseItem).where(KnowledgeBaseItem.agency_id == agency_id)
        if client_workspace_id:
            query = query.where(KnowledgeBaseItem.client_workspace_id == client_workspace_id)
        if category:
            query = query.where(KnowledgeBaseItem.category == category)
        query = query.order_by(KnowledgeBaseItem.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_item(self, item_id: int, agency_id: int) -> KnowledgeBaseItem | None:
        result = await self.db.execute(
            select(KnowledgeBaseItem).where(KnowledgeBaseItem.id == item_id, KnowledgeBaseItem.agency_id == agency_id)
        )
        return result.scalar_one_or_none()

    async def delete_item(self, item_id: int, agency_id: int) -> bool:
        item = await self.get_item(item_id, agency_id)
        if not item:
            return False
        await self.db.delete(item)
        await self.db.commit()
        return True

    async def search(
        self, agency_id: int, query: str, client_workspace_id: int | None = None
    ) -> list[KnowledgeBaseItem]:
        from sqlalchemy import or_

        search_filter = or_(
            KnowledgeBaseItem.title.ilike(f"%{query}%"),
            KnowledgeBaseItem.content.ilike(f"%{query}%"),
            KnowledgeBaseItem.tags.ilike(f"%{query}%"),
        )
        db_query = select(KnowledgeBaseItem).where(
            KnowledgeBaseItem.agency_id == agency_id,
            search_filter,
        )
        if client_workspace_id:
            db_query = db_query.where(KnowledgeBaseItem.client_workspace_id == client_workspace_id)
        db_query = db_query.limit(20)
        result = await self.db.execute(db_query)
        return list(result.scalars().all())
