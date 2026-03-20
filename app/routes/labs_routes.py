from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.lab_controller import lab_controller
from app.schemas.lab_schema import LabCreate
from app.database.db_connection import get_db
from app.middlewares.auth_middleware import get_current_user

router = APIRouter(prefix="/patients/{patient_id}/labs", tags=["Labs"])
security = HTTPBearer()

async def auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_current_user(credentials)

@router.get("/", summary="Get lab results for a patient")
async def get_labs(patient_id: UUID, limit: int = 50, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await lab_controller.get_by_patient(patient_id, db=db)

@router.post("/", status_code=201, summary="Add new lab result (Nurse/Doctor only)")
async def create_lab(patient_id: UUID, data: LabCreate, current_user: dict = Depends(auth), db = Depends(get_db)):
    if current_user["role"] not in ("nurse", "doctor"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Nurses and Doctors only")
    return await lab_controller.create(patient_id, data, db=db)
