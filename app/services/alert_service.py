from __future__ import annotations

from datetime import UTC, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.database.document import ensure_document, normalize_payload


class AlertService:
    async def _enrich_alert(self, db, alert: dict) -> dict:
        patient = await db.patients.find_one({"id": alert["patient_id"]})
        if not patient:
            return alert

        enriched = dict(alert)
        enriched["patient_name"] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or patient.get("mrn")
        enriched["ward"] = patient.get("ward")
        enriched["bed"] = f"Bed {patient['bed_number']}" if patient.get("bed_number") is not None else None
        enriched["patient_mrn"] = patient.get("mrn")
        return enriched

    async def create_from_prediction(self, db, prediction: dict) -> Optional[dict]:
        if prediction["risk_level"] == "LOW":
            return None
        messages = {
            "CRITICAL": "Septic shock pattern detected; immediate intervention required",
            "HIGH": "Severe sepsis indicators; physician notification sent",
            "MODERATE": "Early sepsis warning; increased monitoring recommended",
        }
        alert = ensure_document(
            normalize_payload(
                {
                    "patient_id": prediction["patient_id"],
                    "prediction_id": prediction["id"],
                    "severity": prediction["risk_level"],
                    "risk_score": str(prediction["risk_score"]),
                    "message": messages.get(prediction["risk_level"], ""),
                    "flags": [feature["name"] for feature in (prediction.get("top_features") or [])],
                    "status": "active",
                    "triggered_at": datetime.now(UTC),
                    "acknowledged_at": None,
                    "acknowledged_by": None,
                    "resolved_at": None,
                    "escalated": False,
                }
            )
        )
        await db.alerts.insert_one(alert)
        return await self._enrich_alert(db, alert)

    async def get_all(self, db, status_filter: Optional[str] = None, severity: Optional[str] = None, limit: int = 50) -> List[dict]:
        query = {}
        if status_filter:
            query["status"] = status_filter
        if severity:
            query["severity"] = severity
        alerts = await db.alerts.find_many(query, sort=[("triggered_at", -1)], limit=limit)
        return [await self._enrich_alert(db, alert) for alert in alerts]

    async def get_by_patient(self, db, patient_id: UUID) -> List[dict]:
        alerts = await db.alerts.find_many({"patient_id": str(patient_id)}, sort=[("triggered_at", -1)])
        return [await self._enrich_alert(db, alert) for alert in alerts]

    async def acknowledge(self, db, alert_id: UUID, user_id: UUID) -> dict:
        alert = await db.alerts.find_one({"id": str(alert_id)})
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        alert["status"] = "acknowledged"
        alert["acknowledged_at"] = datetime.now(UTC)
        alert["acknowledged_by"] = str(user_id)
        alert["updated_at"] = datetime.now(UTC)
        await db.alerts.replace_one({"id": alert["id"]}, alert)
        return await self._enrich_alert(db, alert)

    async def resolve(self, db, alert_id: UUID) -> dict:
        alert = await db.alerts.find_one({"id": str(alert_id)})
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        alert["status"] = "resolved"
        alert["resolved_at"] = datetime.now(UTC)
        alert["updated_at"] = datetime.now(UTC)
        await db.alerts.replace_one({"id": alert["id"]}, alert)
        return await self._enrich_alert(db, alert)

    async def escalate(self, db, alert_id: UUID) -> dict:
        alert = await db.alerts.find_one({"id": str(alert_id)})
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        alert["escalated"] = True
        alert["updated_at"] = datetime.now(UTC)
        await db.alerts.replace_one({"id": alert["id"]}, alert)
        return await self._enrich_alert(db, alert)

    async def get_stats(self, db) -> dict:
        alerts = await db.alerts.find_many({}, sort=[("triggered_at", -1)])
        now = datetime.now(UTC).date()
        active = 0
        acknowledged = 0
        resolved = 0
        total_today = 0
        by_severity: dict[str, int] = {}

        for alert in alerts:
            status = alert.get("status")
            severity = alert.get("severity", "UNKNOWN")
            triggered_at = alert.get("triggered_at")

            if status == "active":
                active += 1
                by_severity[severity] = by_severity.get(severity, 0) + 1
            elif status == "acknowledged":
                acknowledged += 1
            elif status == "resolved":
                resolved += 1

            if triggered_at and triggered_at.date() == now:
                total_today += 1

        return {
            "active": active,
            "acknowledged": acknowledged,
            "resolved": resolved,
            "total_today": total_today,
            "active_by_severity": by_severity,
        }


alert_service = AlertService()
