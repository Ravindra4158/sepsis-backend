from uuid import UUID
from app.services.prediction_service import prediction_service
from app.services.alert_service import alert_service
from app.services.notification_service import notification_service
from app.schemas.prediction_schema import PredictionResponse
from app.websocket.alert_socket import broadcast_event

class PredictionController:
    async def predict(self, patient_id: UUID, db):
        prediction = await prediction_service.run_prediction(db, patient_id)
        # Auto-create alert if needed
        new_alert = await alert_service.create_from_prediction(db, prediction)
        patient = await db.patients.find_one({"id": str(patient_id)})
        latest_vital = await db.vitals.find_many({"patient_id": str(patient_id)}, sort=[("recorded_at", -1)], limit=1)
        await broadcast_event(
            {
                "type": "patient_updated",
                "patient": patient,
                "latest_vitals": latest_vital[0] if latest_vital else None,
                "prediction": prediction,
            }
        )
        if new_alert is not None:
            await broadcast_event({"type": "new_alert", "alert": new_alert})
        # Send SMS for critical
        if prediction["risk_level"] == "CRITICAL":
            await notification_service.send_critical_alert(
                patient_name=str(patient_id),
                risk_score=prediction["risk_score"],
                phone_numbers=[],
            )
        return {
            "prediction": PredictionResponse.model_validate(prediction),
            "alert_created": new_alert is not None,
            "alert_severity": new_alert["severity"] if new_alert else None,
        }

    async def get_history(self, patient_id: UUID, limit: int, db):
        predictions = await prediction_service.get_history(db, patient_id, limit)
        return [PredictionResponse.model_validate(p) for p in predictions]

prediction_controller = PredictionController()
