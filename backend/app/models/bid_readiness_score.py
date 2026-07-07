from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.sql import func

from app.core.database import Base


class BidReadinessScore(Base):
    __tablename__ = "bid_readiness_scores"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    overall_score = Column(Float, nullable=False)
    compliance_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    capacity_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    past_performance_score = Column(Float, nullable=True)
    weights_used = Column(Text, nullable=False)
    breakdown = Column(Text, nullable=True)
    calculated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
