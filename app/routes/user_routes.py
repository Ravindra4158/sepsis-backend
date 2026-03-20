from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.user_controller import user_controller
from app.schemas.user_schema import UserCreate, UserUpdate
from app.middlewares.auth_middleware import get_current_user
from fastapi import HTTPException

router = APIRouter(prefix="/users", tags=["Users"])
from app.database.db_connection import get_db

security = HTTPBearer()

async def auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_current_user(credentials)

async def admin_only(current_user: dict = Depends(auth)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user

@router.get("/", summary="List all users (Admin only)")
async def get_users(role: Optional[str] = None, current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await user_controller.get_users(role, db=db)

@router.get("/system-stats", summary="Get system-wide statistics (Admin only)")
async def system_stats(current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await user_controller.system_stats(db=db)

@router.post("/", status_code=201, summary="Create a user (Admin only)")
async def create_user(data: UserCreate, current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await user_controller.create_user(data, db=db)

@router.get("/{user_id}", summary="Get a single user (Admin only)")
async def get_user(user_id: UUID, current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await user_controller.get_user(user_id, db=db)

@router.put("/me/profile", summary="Update my profile (All users)")
async def update_my_profile(data: dict, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await user_controller.update_profile(current_user, data, db=db)

from app.schemas.user_schema import PasswordChange
@router.put("/me/password", summary="Change my password (All users)")
async def change_my_password(data: PasswordChange, current_user: dict = Depends(auth), db = Depends(get_db)):
    return await user_controller.change_password(current_user, data.current_password, data.new_password, db=db)

@router.put("/{user_id}", summary="Update a user (Admin only)")
async def update_user(user_id: UUID, data: UserUpdate, current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await user_controller.update_user(user_id, data, db=db)

@router.delete("/{user_id}", summary="Delete a user (Admin only)")
async def delete_user(user_id: UUID, current_user: dict = Depends(admin_only), db = Depends(get_db)):
    return await user_controller.delete_user(user_id, db=db)
