from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.patient_controller import patient_controller
from app.schemas.patient_schema import PatientCreate, PatientUpdate
from app.middlewares.auth_middleware import get_current_user

from app.database.db_connection import get_db

router = APIRouter(prefix="/patients", tags=["Patients"])
security = HTTPBearer()

async def auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_current_user(credentials)

@router.post("/", status_code=201, summary="Create a new patient (Doctor only)")
async def create_patient(data: PatientCreate, current_user: dict = Depends(auth), db = Depends(get_db)):
    if current_user["role"] not in ("doctor",):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=403, detail="Only doctors can add patients")
    return await patient_controller.create_patient(data, db=db)

@router.get("/", summary="List all patients with pagination")
async def get_patients(skip: int = Query(0), limit: int = Query(20), ward: Optional[str] = None,
                       current_user: dict = Depends(auth), db = Depends(get_db)):
    return await patient_controller.get_patients(skip, limit, ward, db=db)

@router.get("/search", summary="Search patients by name or MRN")
async def search_patients(q: str = Query(..., min_length=2), current_user: dict = Depends(auth), db = Depends(get_db)):
    return await patient_controller.search_patients(q, db=db)

@router.get("/stats/dashboard", summary="Dashboard patient statistics")
async def dashboard_stats(current_user: dict = Depends(auth), db = Depends(get_db)):
    return await patient_controller.dashboard_stats(db=db)

@router.get("/{patient_id}", summary="Get a single patient by ID")
async def get_patient(patient_id: UUID, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await patient_controller.get_patient(patient_id, db=db)

@router.put("/{patient_id}", summary="Update patient details")
async def update_patient(patient_id: UUID, data: PatientUpdate, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await patient_controller.update_patient(patient_id, data, db=db)

@router.delete("/{patient_id}", summary="Delete a patient (Admin only)")
async def delete_patient(patient_id: UUID, current_user: dict = Depends(auth), db = Depends(get_db)):
    if current_user["role"] != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin only")
    return await patient_controller.delete_patient(patient_id, db=db)
