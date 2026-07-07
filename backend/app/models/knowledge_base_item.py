from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class KnowledgeBaseItem(Base):
    __tablename__ = "knowledge_base_items"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False, index=True)
    client_workspace_id = Column(Integer, ForeignKey("client_workspaces.id"), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)
    source_url = Column(String(1000), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
