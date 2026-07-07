import enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql import func

from app.core.database import Base


class ProposalSectionStatus(enum.StrEnum):
    DRAFT = "draft"
    AI_GENERATED = "ai_generated"
    REVIEWED = "reviewed"
    FINAL = "final"


class ProposalSection(Base):
    __tablename__ = "proposal_sections"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    section_title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    status = Column(SAEnum(ProposalSectionStatus), nullable=False, default=ProposalSectionStatus.DRAFT)
    is_ai_generated = Column(Boolean, default=False, nullable=False)
    word_count = Column(Integer, nullable=True)
    parent_section_id = Column(Integer, ForeignKey("proposal_sections.id"), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
