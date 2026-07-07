import logging
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.compliance_item import ComplianceItem
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.extracted_field import ExtractedField
from app.services.ai_service import extract_tender_requirements
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)


class RAGService:
    """Handles document parsing, chunking, embedding, and AI extraction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def parse_document(self, document_id: int) -> Document:
        """Parse a document into text chunks with page/clause refs."""
        doc_service = DocumentService(self.db)
        doc = await doc_service.get_document(document_id)
        if not doc:
            raise ValueError("Document not found")

        # Get client_workspace_id from the tender
        from app.models.tender import Tender

        tender_result = await self.db.execute(select(Tender).where(Tender.id == doc.tender_id))
        tender = tender_result.scalar_one_or_none()
        client_workspace_id = tender.client_workspace_id if tender else 0

        await doc_service.update_status(document_id, DocumentStatus.PROCESSING)

        try:
            file_path = Path(doc.file_path)
            raw_text = ""
            page_count = 0
            chunks = []

            if doc.mime_type == "application/pdf" or file_path.suffix.lower() == ".pdf":
                import pypdf

                reader = pypdf.PdfReader(str(file_path))
                page_count = len(reader.pages)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    raw_text += f"\n\n--- PAGE {i + 1} ---\n{text}"
                    # Chunk by page
                    chunks.append(
                        {
                            "content": text,
                            "page_number": i + 1,
                            "clause_reference": None,
                            "chunk_index": i,
                        }
                    )

            elif doc.mime_type in (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
            ) or file_path.suffix.lower() in (".docx", ".doc"):
                import docx

                d = docx.Document(str(file_path))
                full_text = "\n".join(p.text for p in d.paragraphs)
                raw_text = full_text
                page_count = 1
                # Split into ~1000-char chunks
                chunk_size = 1000
                for i in range(0, len(full_text), chunk_size):
                    chunks.append(
                        {
                            "content": full_text[i : i + chunk_size],
                            "page_number": None,
                            "clause_reference": None,
                            "chunk_index": len(chunks),
                        }
                    )
            else:
                # Try OCR with tesseract
                try:
                    import pytesseract
                    from PIL import Image

                    img = Image.open(file_path)
                    raw_text = pytesseract.image_to_string(img)
                    page_count = 1
                    chunks.append(
                        {
                            "content": raw_text,
                            "page_number": 1,
                            "clause_reference": None,
                            "chunk_index": 0,
                        }
                    )
                except Exception as exc:
                    raise ValueError(f"Unsupported file type: {doc.mime_type}") from exc

            # Delete existing chunks
            await self.db.execute(
                text("DELETE FROM document_chunks WHERE document_id = :did"),
                {"did": document_id},
            )

            # Save chunks
            for c in chunks:
                chunk = DocumentChunk(
                    document_id=document_id,
                    client_workspace_id=client_workspace_id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    page_number=c["page_number"],
                    clause_reference=c["clause_reference"],
                )
                self.db.add(chunk)

            doc.page_count = page_count
            await doc_service.update_status(document_id, DocumentStatus.PARSED)
            return doc

        except Exception as e:
            logger.error("Document parsing failed: %s", e)
            await doc_service.update_status(document_id, DocumentStatus.FAILED, str(e))
            raise

    async def generate_embeddings(self, document_id: int) -> None:
        """Generate embeddings for all chunks of a document."""
        result = await self.db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id))
        chunks = result.scalars().all()

        if not chunks:
            return

        import openai

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

        for chunk in chunks:
            try:
                resp = await client.embeddings.create(
                    input=chunk.content[:8000],
                    model=settings.embedding_model,
                )
                chunk.embedding = resp.data[0].embedding
            except Exception as e:
                logger.error("Embedding failed for chunk %d: %s", chunk.id, e)

        await self.db.commit()

    async def extract_requirements(self, document_id: int, tender_id: int) -> dict:
        """Run AI extraction on parsed document, save fields and compliance items."""
        result = await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
        )
        chunks = result.scalars().all()

        # Prepare chunk data for AI
        chunk_data = [
            {
                "content": c.content,
                "page_number": c.page_number,
                "clause_reference": c.clause_reference,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        full_text = "\n\n".join(c.content for c in chunks)
        extraction = await extract_tender_requirements(full_text, chunk_data)

        # Save extracted fields
        fields = extraction.get("fields", {})
        for field_name, field_info in fields.items():
            if isinstance(field_info, dict):
                value = field_info.get("value")
                source_page = field_info.get("source_page")
                source_clause = field_info.get("source_clause")
                is_resolved = field_info.get("is_resolved", True)
            else:
                value = str(field_info)
                source_page = None
                source_clause = None
                is_resolved = True

            existing = await self.db.execute(
                select(ExtractedField).where(
                    ExtractedField.tender_id == tender_id,
                    ExtractedField.field_name == field_name,
                )
            )
            ef = existing.scalar_one_or_none()
            if ef:
                ef.field_value = str(value) if value is not None else None
                ef.source_page = source_page
                ef.source_clause = source_clause
                ef.is_resolved = is_resolved
            else:
                ef = ExtractedField(
                    tender_id=tender_id,
                    field_name=field_name,
                    field_value=str(value) if value is not None else None,
                    is_ai_generated=True,
                    is_resolved=is_resolved,
                    source_page=source_page,
                    source_clause=source_clause,
                )
                self.db.add(ef)

        # Save compliance items
        compliance_items = extraction.get("compliance_items", [])
        for item in compliance_items:
            if isinstance(item, dict):
                ci = ComplianceItem(
                    tender_id=tender_id,
                    requirement=item.get("requirement", str(item)),
                    category=item.get("category"),
                    is_ai_generated=True,
                    source_page=item.get("source_page"),
                    source_clause=item.get("source_clause"),
                )
                self.db.add(ci)

        await self.db.commit()
        return extraction

    async def vector_search(self, query: str, client_workspace_id: int, top_k: int = 5) -> list[dict]:
        """Search document chunks by vector similarity."""
        import openai

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.embeddings.create(input=query, model=settings.embedding_model)
        query_embedding = resp.data[0].embedding

        # Use pgvector cosine similarity
        sql = text("""
            SELECT dc.id, dc.content, dc.page_number, dc.clause_reference,
                   dc.document_id, 1 - (dc.embedding <=> :query_emb) AS similarity
            FROM document_chunks dc
            WHERE dc.client_workspace_id = :workspace_id
              AND dc.embedding IS NOT NULL
            ORDER BY similarity DESC
            LIMIT :top_k
        """)

        result = await self.db.execute(
            sql,
            {"query_emb": str(query_embedding), "workspace_id": client_workspace_id, "top_k": top_k},
        )
        rows = result.fetchall()
        return [
            {
                "id": r[0],
                "content": r[1],
                "page_number": r[2],
                "clause_reference": r[3],
                "document_id": r[4],
                "similarity": float(r[5]),
            }
            for r in rows
        ]
