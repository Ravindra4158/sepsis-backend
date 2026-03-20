import uuid
from sqlalchemy import Column, SmallInteger, Numeric, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    risk_score      = Column(SmallInteger, nullable=False)
    risk_level      = Column(String(10), nullable=False)
    lstm_probability = Column(Numeric(5, 4), nullable=True)
    xgb_probability  = Column(Numeric(5, 4), nullable=True)
    ensemble_probability = Column(Numeric(5, 4), nullable=True)
    sirs_score      = Column(SmallInteger, nullable=True)
    sofa_score      = Column(SmallInteger, nullable=True)
    feature_snapshot = Column(JSONB, nullable=True)
    top_features    = Column(JSONB, nullable=True)
    model_version   = Column(String(20), default="v1.0")
    patient         = relationship("Patient", back_populates="predictions")
