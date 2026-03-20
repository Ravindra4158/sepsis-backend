from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.prediction_controller import prediction_controller
from app.database.db_connection import get_db
from app.middlewares.auth_middleware import get_current_user

router = APIRouter(prefix="/patients/{patient_id}/predictions", tags=["Predictions"])
security = HTTPBearer()

async def auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_current_user(credentials)

@router.post("/", status_code=201, summary="Run AI sepsis risk prediction for a patient")
async def predict(patient_id: UUID, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await prediction_controller.predict(patient_id, db=db)

@router.get("/", summary="Get prediction history for a patient")
async def get_history(patient_id: UUID, limit: int = 24, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await prediction_controller.get_history(patient_id, limit, db=db)
