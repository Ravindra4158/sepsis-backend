import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role       = Column(SAEnum("doctor","nurse","admin", name="user_role"), nullable=False)
    ward       = Column(String(20), nullable=True)
    phone      = Column(String(20), nullable=True)
    is_active  = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
