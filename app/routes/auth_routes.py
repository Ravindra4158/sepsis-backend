from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.controllers.auth_controller import auth_controller
from app.schemas.user_schema import UserCreate, UserLogin, ForgotPassword, ResetPassword, TokenRefresh
from app.middlewares.auth_middleware import get_current_user

from app.database.db_connection import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

@router.post("/register", status_code=201, summary="Register a new user")
async def register(data: UserCreate, db = Depends(get_db)):
    return await auth_controller.register(data, db=db)

@router.post("/login", summary="Login and receive JWT tokens")
async def login(data: UserLogin, db = Depends(get_db)):
    return await auth_controller.login(data, db=db)

@router.get("/me", summary="Get current authenticated user")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security), db = Depends(get_db)):
    current_user = await get_current_user(credentials)
    return await auth_controller.get_me(current_user, db=db)

@router.post("/logout", summary="Logout and invalidate session")
async def logout():
    return await auth_controller.logout()

@router.post("/refresh", summary="Refresh access token using refresh token")
async def refresh_token(data: TokenRefresh, db = Depends(get_db)):
    return await auth_controller.refresh_token(data, db=db)

@router.post("/forgot-password", summary="Request password reset email")
async def forgot_password(data: ForgotPassword, db = Depends(get_db)):
    return await auth_controller.forgot_password(data, db=db)

@router.post("/reset-password", summary="Reset password with token")
async def reset_password(data: ResetPassword, db = Depends(get_db)):
    return await auth_controller.reset_password(data, db=db)
