import uuid
from sqlalchemy import Column, SmallInteger, Numeric, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base

class VitalReading(Base):
    __tablename__ = "vital_readings"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    heart_rate      = Column(SmallInteger, nullable=True)
    systolic_bp     = Column(SmallInteger, nullable=True)
    diastolic_bp    = Column(SmallInteger, nullable=True)
    temperature     = Column(Numeric(4, 1), nullable=True)
    respiratory_rate = Column(SmallInteger, nullable=True)
    spo2            = Column(SmallInteger, nullable=True)
    wbc             = Column(Numeric(5, 2), nullable=True)
    lactate         = Column(Numeric(4, 2), nullable=True)
    creatinine      = Column(Numeric(4, 2), nullable=True)
    source          = Column(String(50), default="manual")
    notes           = Column(String(500), nullable=True)
    patient         = relationship("Patient", back_populates="vitals")
