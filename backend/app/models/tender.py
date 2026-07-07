import enum

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql import func

from app.core.database import Base


class TenderStatus(enum.StrEnum):
    IDENTIFIED = "identified"
    QUALIFICATION = "qualification"
    IN_PROGRESS = "in_progress"
    INTERNAL_REVIEW = "internal_review"
    SUBMITTED = "submitted"
    WON = "won"
    LOST = "lost"
    WITHDRAWN = "withdrawn"


VALID_TRANSITIONS = {
    TenderStatus.IDENTIFIED: [TenderStatus.QUALIFICATION, TenderStatus.WITHDRAWN],
    TenderStatus.QUALIFICATION: [TenderStatus.IN_PROGRESS, TenderStatus.WITHDRAWN],
    TenderStatus.IN_PROGRESS: [TenderStatus.INTERNAL_REVIEW, TenderStatus.WITHDRAWN],
    TenderStatus.INTERNAL_REVIEW: [TenderStatus.SUBMITTED, TenderStatus.IN_PROGRESS, TenderStatus.WITHDRAWN],
    TenderStatus.SUBMITTED: [TenderStatus.WON, TenderStatus.LOST, TenderStatus.WITHDRAWN],
    TenderStatus.WON: [],
    TenderStatus.LOST: [],
    TenderStatus.WITHDRAWN: [],
}


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False, index=True)
    client_workspace_id = Column(Integer, ForeignKey("client_workspaces.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    reference_number = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(TenderStatus), nullable=False, default=TenderStatus.IDENTIFIED)
    bid_deadline = Column(Date, nullable=True)
    estimated_value = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    ai_readiness_score = Column(Float, nullable=True)
    ai_go_nogo_recommendation = Column(String(20), nullable=True)
    ai_go_nogo_explanation = Column(Text, nullable=True)
    tender_metadata = Column("metadata", Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
