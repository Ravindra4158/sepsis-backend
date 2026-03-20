from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

class PatientCreate(BaseModel):
    mrn: str = Field(..., min_length=3, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    date_of_birth: date
    gender: str = Field(..., pattern="^(M|F|O)$")
    ward: str
    bed_number: int = Field(..., ge=1)
    primary_diagnosis: Optional[str] = None
    comorbidities: Optional[List[str]] = []
    admitted_at: Optional[datetime] = None
    physician_name: Optional[str] = None

class PatientUpdate(BaseModel):
    ward: Optional[str] = None
    bed_number: Optional[int] = None
    primary_diagnosis: Optional[str] = None
    comorbidities: Optional[List[str]] = None
    discharged_at: Optional[datetime] = None
    physician_name: Optional[str] = None

class PatientResponse(BaseModel):
    id: UUID
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    ward: str
    bed_number: int
    primary_diagnosis: Optional[str]
    comorbidities: Optional[List[str]]
    admitted_at: Optional[datetime]
    discharged_at: Optional[datetime]
    physician_name: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}
