from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class LabCreate(BaseModel):
    test_name: str = Field(..., min_length=2, max_length=100)
    value: Optional[float] = Field(None, ge=-1000, le=10000)
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = Field(None, pattern="^(normal|L|H|LL|HH|ABNORMAL)$")
    collected_at: Optional[datetime] = None
    notes: Optional[str] = None

class LabResponse(BaseModel):
    id: UUID
    patient_id: UUID
    test_name: str
    value: Optional[float]
    unit: Optional[str]
    reference_range: Optional[str]
    flag: Optional[str]
    collected_at: datetime
    notes: Optional[str]
    model_config = {"from_attributes": True}
