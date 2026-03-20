from __future__ import annotations

from typing import Any

from app.database.document import ensure_document, normalize_payload


class AuditService:
    async def log_event(
        self,
        db,
        *,
        action: str,
        resource: str,
        actor: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entry = ensure_document(
            normalize_payload(
                {
                    "action": action,
                    "resource": resource,
                    "actor_id": actor.get("id") if actor else None,
                    "actor_name": actor.get("name") if actor else "System",
                    "actor_role": actor.get("role") if actor else "system",
                    "timestamp": actor.get("timestamp") if actor else None,
                    "details": details or {},
                }
            )
        )
        entry["timestamp"] = entry["updated_at"]
        await db.audit_logs.insert_one(entry)
        return entry

    async def list_events(self, db, limit: int = 20) -> list[dict[str, Any]]:
        return await db.audit_logs.find_many({}, sort=[("timestamp", -1)], limit=limit)


audit_service = AuditService()
