from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.middlewares.auth_middleware import get_current_user
from app.database.db_connection import get_db
from fastapi import HTTPException
from app.services.admin_service import admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])
security = HTTPBearer()

async def admin_only(credentials: HTTPAuthorizationCredentials = Depends(security)):
    current_user = await get_current_user(credentials)
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.get("/stats", summary="Get system-wide statistics (Admin only)")
async def admin_stats(current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await admin_service.get_stats(db)

@router.get("/audit-log", summary="Get system audit logs (Admin only)")
async def audit_log(limit: int = 20, current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await admin_service.get_audit_log(db, limit=limit)

@router.get("/settings", summary="Get system settings (Admin only)")
async def get_settings(current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await admin_service.get_settings(db)

@router.put("/settings", summary="Update system settings (Admin only)")
async def update_settings(data: dict, current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await admin_service.update_settings(db, data, current_user)

@router.get("/health", summary="Get service health snapshot (Admin only)")
async def health_snapshot(current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await admin_service.get_health(db)
