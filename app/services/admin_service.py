from __future__ import annotations

from typing import Any

from app.config.settings import settings
from app.database.document import ensure_document, normalize_payload, prepare_update
from app.ml.model_loader import get_model
from app.services.audit_service import audit_service


DEFAULT_SYSTEM_SETTINGS = {
    "id": "default",
    "notifications": {
        "emailAlerts": True,
        "smsAlerts": False,
        "pagerAlerts": True,
        "autoEscalateMin": 10,
    },
    "model": {
        "criticalThreshold": settings.MODEL_THRESHOLD_CRITICAL,
        "highThreshold": settings.MODEL_THRESHOLD_HIGH,
        "moderateThreshold": settings.MODEL_THRESHOLD_MODERATE,
        "pollingInterval": 5,
    },
    "operations": {
        "dataRetentionDays": 365,
        "maintenanceMode": False,
    },
}


class AdminService:
    async def get_stats(self, db) -> dict[str, Any]:
        users = await db.users.find_many({})
        total_users = len(users)
        role_counts = {
            "total_doctors": sum(1 for user in users if user.get("role") == "doctor"),
            "total_nurses": sum(1 for user in users if user.get("role") == "nurse"),
            "total_admins": sum(1 for user in users if user.get("role") == "admin"),
            "inactive_users": sum(1 for user in users if not user.get("is_active", True)),
        }
        total_patients = await db.patients.count_documents({})
        total_alerts = await db.alerts.count_documents({})
        active_alerts = await db.alerts.count_documents({"status": "active"})
        critical_alerts = await db.alerts.count_documents({"status": "active", "severity": "critical"})
        return {
            "total_users": total_users,
            "total_patients": total_patients,
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
            "api_latency_ms": 24,
            "model_latency_ms": 82,
            "database_mode": "mongo" if db.__class__.__name__ == "MotorDatabaseAdapter" else "in_memory",
            **role_counts,
        }

    async def get_audit_log(self, db, limit: int = 20) -> dict[str, Any]:
        items = await audit_service.list_events(db, limit=limit)
        return {"items": items, "count": len(items)}

    async def get_settings(self, db) -> dict[str, Any]:
        settings_doc = await db.system_settings.find_one({"id": "default"})
        if settings_doc:
            return settings_doc

        settings_doc = ensure_document(normalize_payload(DEFAULT_SYSTEM_SETTINGS), doc_id="default")
        settings_doc["id"] = "default"
        await db.system_settings.insert_one(settings_doc)
        return settings_doc

    async def update_settings(self, db, payload: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any]:
        current = await self.get_settings(db)
        current.update(prepare_update(normalize_payload(payload)))
        await db.system_settings.replace_one({"id": "default"}, current)
        await audit_service.log_event(
            db,
            action="update",
            resource="system_settings",
            actor=actor,
            details={"fields": sorted(payload.keys())},
        )
        return current

    async def get_health(self, db) -> dict[str, Any]:
        model = get_model()
        model_health = model.health() if model else {"status": "fallback", "provider": "rules", "model_version": "rule-based"}
        return {
            "api": {"status": "online", "latency_ms": 24},
            "database": {
                "status": "online",
                "mode": "mongo" if db.__class__.__name__ == "MotorDatabaseAdapter" else "in_memory",
                "name": settings.MONGODB_DB_NAME,
            },
            "model": model_health,
            "alerts": {"status": "online", "active_alerts": await db.alerts.count_documents({"status": "active"})},
        }


admin_service = AdminService()
