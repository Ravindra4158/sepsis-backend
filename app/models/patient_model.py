import uuid
from sqlalchemy import Column, String, Date, Integer, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin

class Patient(Base, TimestampMixin):
    __tablename__ = "patients"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mrn             = Column(String(20), unique=True, nullable=False, index=True)
    first_name      = Column(String(80), nullable=False)
    last_name       = Column(String(80), nullable=False)
    date_of_birth   = Column(Date, nullable=False)
    gender          = Column(String(1), nullable=False)
    ward            = Column(String(20), nullable=False)
    bed_number      = Column(Integer, nullable=False)
    primary_diagnosis = Column(Text, nullable=True)
    comorbidities   = Column(JSONB, default=list)
    admitted_at     = Column(DateTime(timezone=True), nullable=True)
    discharged_at   = Column(DateTime(timezone=True), nullable=True)
    physician_name  = Column(String(100), nullable=True)
    vitals          = relationship("VitalReading", back_populates="patient", cascade="all, delete-orphan")
    labs            = relationship("LabResult", back_populates="patient", cascade="all, delete-orphan")
    predictions     = relationship("RiskPrediction", back_populates="patient", cascade="all, delete-orphan")
    alerts          = relationship("SepsisAlert", back_populates="patient", cascade="all, delete-orphan")
