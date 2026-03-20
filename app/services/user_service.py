from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status

from app.database.document import prepare_update
from app.services.audit_service import audit_service
from app.schemas.user_schema import UserUpdate
from app.utils.password_hash import hash_password, verify_password


class UserService:
    async def list_users(self, db, role: str | None = None) -> list[dict]:
        users = await db.users.find_many({}, sort=[("created_at", -1)])
        if role:
            users = [user for user in users if user.get("role") == role]
        return users

    async def get_by_id(self, db, user_id: UUID) -> dict:
        user = await db.users.find_one({"id": str(user_id)})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    async def update_user(self, db, user_id: UUID, data: UserUpdate) -> dict:
        user = await self.get_by_id(db, user_id)
        changes = data.model_dump(exclude_unset=True)
        user.update(prepare_update(changes))
        await db.users.replace_one({"id": user["id"]}, user)
        await audit_service.log_event(
            db,
            action="update",
            resource="user",
            actor=user,
            details={"fields": sorted(changes.keys())},
        )
        return user

    async def delete_user(self, db, user_id: UUID) -> None:
        user = await self.get_by_id(db, user_id)
        await db.users.delete_one({"id": user["id"]})
        await audit_service.log_event(
            db,
            action="delete",
            resource="user",
            actor=user,
            details={"email": user["email"]},
        )

    async def system_stats(self, db) -> dict:
        total_users = await db.users.count_documents({})
        total_patients = await db.patients.count_documents({})
        active_alerts = await db.alerts.count_documents({"status": "active"})
        return {"total_users": total_users, "total_patients": total_patients, "active_alerts": active_alerts}

    async def update_profile(self, db, current_user: dict, data: dict) -> dict:
        user = await self.get_by_id(db, UUID(current_user["sub"]))
        for key in {"name", "phone", "ward"}:
            if key in data:
                user[key] = data[key]
        user.update(prepare_update({}))
        await db.users.replace_one({"id": user["id"]}, user)
        await audit_service.log_event(
            db,
            action="update",
            resource="profile",
            actor=user,
            details={"fields": sorted(key for key in data if key in {"name", "phone", "ward"})},
        )
        return user

    async def change_password(self, db, current_user: dict, current_password: str, new_password: str) -> None:
        user = await self.get_by_id(db, UUID(current_user["sub"]))
        if not verify_password(current_password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")
        user["password_hash"] = hash_password(new_password)
        user.update(prepare_update({}))
        await db.users.replace_one({"id": user["id"]}, user)
        await audit_service.log_event(
            db,
            action="update",
            resource="password",
            actor=user,
            details={},
        )


user_service = UserService()
