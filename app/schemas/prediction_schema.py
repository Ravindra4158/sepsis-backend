from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class PredictionResponse(BaseModel):
    id: UUID
    patient_id: UUID
    predicted_at: datetime
    risk_score: int
    risk_level: str
    lstm_probability: Optional[float]
    xgb_probability: Optional[float]
    ensemble_probability: Optional[float]
    sirs_score: Optional[int]
    sofa_score: Optional[int]
    top_features: Optional[List[Dict[str, Any]]]
    model_version: Optional[str]
    model_config = {"from_attributes": True}
