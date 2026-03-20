from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class AlertResponse(BaseModel):
    id: UUID
    patient_id: UUID
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    ward: Optional[str] = None
    bed: Optional[str] = None
    severity: str
    risk_score: Optional[str]
    message: Optional[str]
    flags: Optional[List[str]]
    status: str
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[UUID]
    resolved_at: Optional[datetime]
    escalated: bool
    model_config = {"from_attributes": True}

class AlertAcknowledge(BaseModel):
    note: Optional[str] = None

class AlertResolve(BaseModel):
    note: Optional[str] = None
