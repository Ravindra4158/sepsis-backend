from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.vitals_controller import vitals_controller
from app.schemas.vital_schema import VitalCreate
from app.database.db_connection import get_db
from app.middlewares.auth_middleware import get_current_user

router = APIRouter(prefix="/patients/{patient_id}/vitals", tags=["Vitals"])
security = HTTPBearer()

async def auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_current_user(credentials)

@router.post("/", status_code=201, summary="Record new vital signs (Nurse only)")
async def add_vital(patient_id: UUID, data: VitalCreate, current_user: dict = Depends(auth), db = Depends(get_db)):
    if current_user["role"] not in ("nurse", "doctor"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Nurses and Doctors only")
    return await vitals_controller.add_vital(patient_id, data, db=db)

@router.post("/mock", status_code=201, summary="Generate mock vital signs for a patient")
async def add_mock_vital(patient_id: UUID, critical: bool | None = None, current_user: dict = Depends(auth), db = Depends(get_db)):
    if current_user["role"] not in ("nurse", "doctor", "admin"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Authorized clinical staff only")
    return await vitals_controller.add_mock_vital(patient_id, db=db, critical=critical)

@router.get("/latest", summary="Get the most recent vitals for a patient")
async def get_latest(patient_id: UUID, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await vitals_controller.get_latest(patient_id, db=db)

@router.get("/history", summary="Get vitals history for a patient")
async def get_history(patient_id: UUID, limit: int = 50, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await vitals_controller.get_history(patient_id, limit, db=db)
