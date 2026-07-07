from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    field_name = Column(String(255), nullable=False)
    field_value = Column(Text, nullable=True)
    is_ai_generated = Column(Boolean, default=True, nullable=False)
    confidence = Column(Integer, nullable=True)
    is_resolved = Column(Boolean, default=True, nullable=False)
    source_page = Column(Integer, nullable=True)
    source_clause = Column(String(100), nullable=True)
    source_chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
