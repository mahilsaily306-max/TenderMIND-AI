from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func

from app.core.database import Base


class UserClientAccess(Base):
    __tablename__ = "user_client_access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    client_workspace_id = Column(Integer, ForeignKey("client_workspaces.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
