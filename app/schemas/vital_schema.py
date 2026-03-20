from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class VitalCreate(BaseModel):
    heart_rate: Optional[int] = Field(None, ge=0, le=300)
    systolic_bp: Optional[int] = Field(None, ge=0, le=300)
    diastolic_bp: Optional[int] = Field(None, ge=0, le=200)
    temperature: Optional[float] = Field(None, ge=25.0, le=45.0)
    respiratory_rate: Optional[int] = Field(None, ge=0, le=80)
    spo2: Optional[int] = Field(None, ge=0, le=100)
    wbc: Optional[float] = Field(None, ge=0, le=200)
    lactate: Optional[float] = Field(None, ge=0, le=30)
    creatinine: Optional[float] = Field(None, ge=0, le=30)
    source: Optional[str] = "manual"
    notes: Optional[str] = None

class VitalResponse(BaseModel):
    id: UUID
    patient_id: UUID
    recorded_at: datetime
    heart_rate: Optional[int]
    systolic_bp: Optional[int]
    diastolic_bp: Optional[int]
    temperature: Optional[float]
    respiratory_rate: Optional[int]
    spo2: Optional[int]
    wbc: Optional[float]
    lactate: Optional[float]
    creatinine: Optional[float]
    source: Optional[str]
    notes: Optional[str]
    model_config = {"from_attributes": True}
