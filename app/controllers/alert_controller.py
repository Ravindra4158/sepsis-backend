from typing import Optional
from uuid import UUID
from app.services.alert_service import alert_service
from app.schemas.alert_schema import AlertResponse, AlertAcknowledge, AlertResolve
from app.websocket.alert_socket import broadcast_event

class AlertController:
    async def get_alerts(self, status: Optional[str], severity: Optional[str],
                         limit: int, db):
        alerts = await alert_service.get_all(db, status, severity, limit)
        return [AlertResponse.model_validate(a) for a in alerts]

    async def get_patient_alerts(self, patient_id: UUID, db):
        alerts = await alert_service.get_by_patient(db, patient_id)
        return [AlertResponse.model_validate(a) for a in alerts]

    async def acknowledge_alert(self, alert_id: UUID, data: AlertAcknowledge,
                                current_user: dict, db):
        alert = await alert_service.acknowledge(db, alert_id, UUID(current_user["sub"]))
        await broadcast_event({"type": "alert_updated", "alert": alert})
        return {"message": "Alert acknowledged", "alert": AlertResponse.model_validate(alert)}

    async def resolve_alert(self, alert_id: UUID, data: AlertResolve, db):
        alert = await alert_service.resolve(db, alert_id)
        await broadcast_event({"type": "alert_updated", "alert": alert})
        return {"message": "Alert resolved", "alert": AlertResponse.model_validate(alert)}

    async def escalate_alert(self, alert_id: UUID, current_user: dict, db):
        alert = await alert_service.escalate(db, alert_id)
        await broadcast_event({"type": "alert_updated", "alert": alert})
        return {"message": "Alert escalated", "alert": AlertResponse.model_validate(alert)}

    async def get_stats(self, db):
        return await alert_service.get_stats(db)

alert_controller = AlertController()
