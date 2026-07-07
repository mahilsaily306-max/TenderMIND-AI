import json
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment

MENTION_RE = re.compile(r"@(\w+)")


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_comment(
        self,
        tender_id: int,
        author_id: int,
        content: str,
        parent_id: int | None = None,
    ) -> Comment:
        mentions = MENTION_RE.findall(content)
        comment = Comment(
            tender_id=tender_id,
            author_id=author_id,
            content=content,
            parent_id=parent_id,
            mentions=json.dumps(mentions) if mentions else None,
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def list_comments(self, tender_id: int) -> list[Comment]:
        result = await self.db.execute(
            select(Comment).where(Comment.tender_id == tender_id).order_by(Comment.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete_comment(self, comment_id: int, user_id: int) -> bool:
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id, Comment.author_id == user_id))
        comment = result.scalar_one_or_none()
        if not comment:
            return False
        await self.db.delete(comment)
        await self.db.commit()
        return True
