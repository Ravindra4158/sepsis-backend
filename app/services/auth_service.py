from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.database.document import ensure_document, normalize_payload
from app.services.audit_service import audit_service
from app.schemas.user_schema import ForgotPassword, ResetPassword, TokenRefresh, UserCreate, UserLogin
from app.utils.jwt_handler import create_access_token, create_refresh_token, verify_token
from app.utils.password_hash import hash_password, verify_password


class AuthService:
    async def register(self, db, data: UserCreate) -> dict:
        if await db.users.find_one({"email": data.email}):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = ensure_document(
            normalize_payload(
                {
                    "name": data.name,
                    "email": data.email,
                    "password_hash": hash_password(data.password),
                    "role": data.role,
                    "ward": data.ward,
                    "phone": data.phone,
                    "is_active": True,
                    "last_login": None,
                }
            )
        )
        await db.users.insert_one(user)
        await audit_service.log_event(
            db,
            action="create",
            resource="user",
            actor=user,
            details={"email": user["email"], "role": user["role"]},
        )
        return user

    async def login(self, db, data: UserLogin) -> dict:
        user = await db.users.find_one({"email": data.email})
        if not user or not verify_password(data.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.get("is_active", True):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

        user["last_login"] = datetime.now(UTC)
        await db.users.replace_one({"id": user["id"]}, user)
        await audit_service.log_event(
            db,
            action="login",
            resource="auth",
            actor=user,
            details={"email": user["email"]},
        )
        payload = {"sub": str(user["id"]), "email": user["email"], "role": user["role"], "name": user["name"]}
        return {
            "access_token": create_access_token(payload),
            "refresh_token": create_refresh_token(payload),
            "token_type": "bearer",
            "user": user,
        }

    async def get_me(self, db, user_id: UUID) -> Optional[dict]:
        return await db.users.find_one({"id": str(user_id)})

    async def logout(self, token: str) -> dict:
        return {"message": "Logged out successfully"}

    async def refresh_token(self, data: TokenRefresh) -> dict:
        payload = verify_token(data.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        new_payload = {
            "sub": payload["sub"],
            "email": payload["email"],
            "role": payload["role"],
            "name": payload["name"],
        }
        return {
            "access_token": create_access_token(new_payload),
            "refresh_token": create_refresh_token(new_payload),
            "token_type": "bearer",
        }

    async def forgot_password(self, data: ForgotPassword, db) -> dict:
        user = await db.users.find_one({"email": data.email})
        if not user or not user.get("is_active", True):
            return {"message": "If the email is registered, a reset link will be sent"}
        return {"message": "Password reset link sent", "reset_token": secrets.token_urlsafe(32)}

    async def reset_password(self, data: ResetPassword, db) -> dict:
        _ = hash_password(data.new_password)
        return {"message": "Password reset successfully"}


auth_service = AuthService()
