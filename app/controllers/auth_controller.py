from app.database.db_connection import get_db
from app.services.auth_service import auth_service
from app.schemas.user_schema import UserCreate, UserLogin, UserResponse, TokenResponse, ForgotPassword, ResetPassword, TokenRefresh

class AuthController:
    async def register(self, data: UserCreate, db):
        user = await auth_service.register(db, data)
        return {"message": "User registered successfully", "user": UserResponse.model_validate(user)}

    async def login(self, data: UserLogin, db):
        result = await auth_service.login(db, data)
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            user=UserResponse.model_validate(result["user"]),
        )

    async def get_me(self, current_user: dict, db):
        from uuid import UUID
        user = await auth_service.get_me(db, UUID(current_user["sub"]))
        if not user:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.model_validate(user)

    async def logout(self) -> dict:
        return await auth_service.logout("")

    async def refresh_token(self, data, db):
        return await auth_service.refresh_token(data)

    async def forgot_password(self, data: ForgotPassword, db):
        return await auth_service.forgot_password(data, db)

    async def reset_password(self, data: ResetPassword, db):
        return await auth_service.reset_password(data, db)

auth_controller = AuthController()
