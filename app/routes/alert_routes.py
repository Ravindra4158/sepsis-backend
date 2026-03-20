from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.alert_controller import alert_controller
from app.schemas.alert_schema import AlertAcknowledge, AlertResolve
from app.database.db_connection import get_db
from app.middlewares.auth_middleware import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])
security = HTTPBearer()

async def auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_current_user(credentials)

@router.get("/", summary="List all alerts with optional filters")
async def get_alerts(status: Optional[str] = None, severity: Optional[str] = None,
                     limit: int = 50, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await alert_controller.get_alerts(status, severity, limit, db=db)

@router.get("/stats", summary="Get alert statistics (counts by severity)")
async def get_stats(current_user: dict = Depends(auth), db = Depends(get_db)):
    return await alert_controller.get_stats(db=db)

@router.get("/patient/{patient_id}", summary="Get all alerts for a specific patient")
async def get_patient_alerts(patient_id: UUID, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await alert_controller.get_patient_alerts(patient_id, db=db)

@router.patch("/{alert_id}/acknowledge", summary="Acknowledge an active alert")
async def acknowledge(alert_id: UUID, data: AlertAcknowledge, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await alert_controller.acknowledge_alert(alert_id, data, current_user, db=db)

@router.patch("/{alert_id}/resolve", summary="Resolve an alert")
async def resolve(alert_id: UUID, data: AlertResolve, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await alert_controller.resolve_alert(alert_id, data, db=db)

@router.patch("/{alert_id}/escalate", summary="Escalate an alert to higher priority")
async def escalate(alert_id: UUID, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await alert_controller.escalate_alert(alert_id, current_user, db=db)
