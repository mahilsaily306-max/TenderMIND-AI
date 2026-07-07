import os
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document, DocumentStatus


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_document(
        self,
        tender_id: int,
        uploaded_by: int,
        filename: str,
        file_content: bytes,
        mime_type: str | None = None,
    ) -> Document:
        storage_path = Path(settings.storage_path) / str(tender_id)
        storage_path.mkdir(parents=True, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = storage_path / unique_name

        with open(file_path, "wb") as f:
            f.write(file_content)

        doc = Document(
            tender_id=tender_id,
            uploaded_by=uploaded_by,
            filename=unique_name,
            original_filename=filename,
            file_path=str(file_path),
            file_size_bytes=len(file_content),
            mime_type=mime_type,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def get_document(self, document_id: int) -> Document | None:
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def list_documents(self, tender_id: int) -> list[Document]:
        result = await self.db.execute(
            select(Document).where(Document.tender_id == tender_id).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_document(self, document_id: int) -> bool:
        doc = await self.get_document(document_id)
        if not doc:
            return False
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        await self.db.delete(doc)
        await self.db.commit()
        return True

    async def update_status(
        self, document_id: int, status: DocumentStatus, error_message: str | None = None
    ) -> Document | None:
        doc = await self.get_document(document_id)
        if not doc:
            return None
        doc.status = status
        if error_message:
            doc.error_message = error_message
        await self.db.commit()
        await self.db.refresh(doc)
        return doc
