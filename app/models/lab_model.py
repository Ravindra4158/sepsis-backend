import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class LabResult(Base):
    __tablename__ = "lab_results"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    test_name       = Column(String(100), nullable=False)
    value           = Column(Float, nullable=True)
    unit            = Column(String(50), nullable=True)
    reference_range = Column(String(100), nullable=True)
    flag            = Column(String(10), nullable=True)  # L, H, LL, HH, normal
    collected_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    notes           = Column(String(500), nullable=True)
    patient         = relationship("Patient", back_populates="labs")
