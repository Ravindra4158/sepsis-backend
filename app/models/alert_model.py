import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database.base import Base

class SepsisAlert(Base):
    __tablename__ = "sepsis_alerts"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_id   = Column(UUID(as_uuid=True), ForeignKey("risk_predictions.id"), nullable=True)
    severity        = Column(String(10), nullable=False)
    risk_score      = Column(String(5), nullable=True)
    message         = Column(Text, nullable=True)
    flags           = Column(ARRAY(String), default=list)
    status          = Column(String(20), default="active", index=True)
    triggered_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at     = Column(DateTime(timezone=True), nullable=True)
    escalated       = Column(Boolean, default=False)
    patient         = relationship("Patient", back_populates="alerts")
    acknowledged_by_user = relationship("User", foreign_keys=[acknowledged_by])
