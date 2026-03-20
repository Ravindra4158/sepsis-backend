from __future__ import annotations

from datetime import UTC, datetime
from typing import List
from uuid import UUID

from fastapi import HTTPException, status

from app.database.document import ensure_document, normalize_payload
from app.ml.predict import predict_sepsis_risk
from app.services.patient_service import patient_service


class PredictionService:
    async def run_prediction(self, db, patient_id: UUID) -> dict:
        patient = await db.patients.find_one({"id": str(patient_id)})
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        vitals = await db.vitals.find_many({"patient_id": str(patient_id)}, sort=[("recorded_at", -1)], limit=1)
        if not vitals:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No vitals available for prediction")

        latest_vital = vitals[0]
        vitals_dict = {
            "heart_rate": latest_vital.get("heart_rate"),
            "systolic_bp": latest_vital.get("systolic_bp"),
            "diastolic_bp": latest_vital.get("diastolic_bp"),
            "temperature": latest_vital.get("temperature"),
            "respiratory_rate": latest_vital.get("respiratory_rate"),
            "spo2": latest_vital.get("spo2"),
            "wbc": latest_vital.get("wbc"),
            "lactate": latest_vital.get("lactate"),
            "creatinine": latest_vital.get("creatinine"),
        }
        result = predict_sepsis_risk(vitals_dict)
        prediction = ensure_document(
            normalize_payload(
                {
                    "patient_id": str(patient_id),
                    "predicted_at": datetime.now(UTC),
                    "risk_score": result["risk_score"],
                    "risk_level": result["risk_level"],
                    "lstm_probability": result.get("lstm_probability"),
                    "xgb_probability": result.get("xgb_probability"),
                    "ensemble_probability": result.get("ensemble_probability"),
                    "sirs_score": result.get("sirs_score"),
                    "sofa_score": result.get("sofa_score"),
                    "top_features": result.get("top_features"),
                    "feature_snapshot": vitals_dict,
                    "model_version": result.get("model_version", "v1.0"),
                }
            )
        )
        await db.predictions.insert_one(prediction)
        await patient_service.apply_prediction_snapshot(db, str(patient_id), prediction["risk_score"])
        return prediction

    async def get_history(self, db, patient_id: UUID, limit: int = 24) -> List[dict]:
        return await db.predictions.find_many({"patient_id": str(patient_id)}, sort=[("predicted_at", -1)], limit=limit)


prediction_service = PredictionService()
