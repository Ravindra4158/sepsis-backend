from __future__ import annotations

from typing import Optional
from uuid import UUID

from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.services.auth_service import auth_service
from app.services.user_service import user_service


class UserController:
    async def get_users(self, role: Optional[str], db):
        users = await user_service.list_users(db, role)
        return [UserResponse.model_validate(user) for user in users]

    async def get_user(self, user_id: UUID, db):
        user = await user_service.get_by_id(db, user_id)
        return UserResponse.model_validate(user)

    async def create_user(self, data: UserCreate, db):
        user = await auth_service.register(db, data)
        return {"message": "User created", "user": UserResponse.model_validate(user)}

    async def update_user(self, user_id: UUID, data: UserUpdate, db):
        user = await user_service.update_user(db, user_id, data)
        return {"message": "User updated", "user": UserResponse.model_validate(user)}

    async def delete_user(self, user_id: UUID, db):
        await user_service.delete_user(db, user_id)
        return {"message": "User deleted"}

    async def system_stats(self, db):
        return await user_service.system_stats(db)

    async def update_profile(self, current_user: dict, data: dict, db):
        user = await user_service.update_profile(db, current_user, data)
        return {"message": "Profile updated", "user": UserResponse.model_validate(user)}

    async def change_password(self, current_user: dict, current_password: str, new_password: str, db):
        await user_service.change_password(db, current_user, current_password, new_password)
        return {"message": "Password updated successfully"}


user_controller = UserController()
