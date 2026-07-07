import enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql import func

from app.core.database import Base


class NotificationType(enum.StrEnum):
    TENDER_ASSIGNED = "tender_assigned"
    TASK_ASSIGNED = "task_assigned"
    STATUS_CHANGE = "status_change"
    COMMENT_MENTION = "comment_mention"
    DEADLINE_APPROACHING = "deadline_approaching"
    AI_READY = "ai_ready"
    SUBMISSION_REMINDER = "submission_reminder"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(SAEnum(NotificationType), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
