import enum

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql import func

from app.core.database import Base


class SubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    submission_date = Column(Date, nullable=False)
    status = Column(SAEnum(SubmissionStatus), nullable=False, default=SubmissionStatus.DRAFT)
    submission_method = Column(String(100), nullable=True)
    confirmation_number = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    documents_included = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
