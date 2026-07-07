import enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql import func

from app.core.database import Base


class UserRole(str, enum.Enum):
    OWNER = "owner"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    is_active = Column(Boolean, default=True, nullable=False)
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
