import enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql import func

from app.core.database import Base


class ComplianceStatus(str, enum.Enum):
    PENDING = "pending"
    MET = "met"
    NOT_MET = "not_met"
    EXEMPTED = "exempted"


class ComplianceItem(Base):
    __tablename__ = "compliance_items"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    requirement = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    status = Column(SAEnum(ComplianceStatus), nullable=False, default=ComplianceStatus.PENDING)
    is_ai_generated = Column(Boolean, default=False, nullable=False)
    is_editable = Column(Boolean, default=True, nullable=False)
    source_page = Column(Integer, nullable=True)
    source_clause = Column(String(100), nullable=True)
    source_chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=True)
    note = Column(Text, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
