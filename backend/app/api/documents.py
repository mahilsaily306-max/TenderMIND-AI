from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_agency
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.tender import Tender
from app.models.user import User
from app.services.audit_service import create_audit_log
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    tender_id: int = Form(...),
    file: UploadFile = File(...),
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

    content = await file.read()
    service = DocumentService(db)
    doc = await service.upload_document(
        tender_id=tender_id,
        uploaded_by=current_user.id,
        filename=file.filename or "unnamed",
        file_content=content,
        mime_type=file.content_type,
    )
    await create_audit_log(db, agency.id, current_user.id, "document.upload", "document", doc.id)
    return {
        "id": doc.id,
        "filename": doc.original_filename,
        "file_size_bytes": doc.file_size_bytes,
        "mime_type": doc.mime_type,
        "status": doc.status.value,
    }


@router.get("")
async def list_documents(
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

    service = DocumentService(db)
    docs = await service.list_documents(tender_id)
    return [
        {
            "id": d.id,
            "original_filename": d.original_filename,
            "file_size_bytes": d.file_size_bytes,
            "mime_type": d.mime_type,
            "status": d.status.value,
            "uploaded_by": d.uploaded_by,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner", "manager")),
    agency=Depends(get_current_agency),
):
    service = DocumentService(db)
    doc = await service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    # Verify tender scope
    result = await db.execute(
        select(Tender).where(Tender.id == doc.tender_id, Tender.agency_id == agency.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await service.delete_document(document_id)
    await create_audit_log(db, agency.id, current_user.id, "document.delete", "document", document_id)
    return {"message": "Document deleted"}
