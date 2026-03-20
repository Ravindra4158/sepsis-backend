from __future__ import annotations

from datetime import UTC, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.database.document import ensure_document, normalize_payload, prepare_update
from app.ml.predict import score_to_level
from app.schemas.patient_schema import PatientCreate, PatientUpdate


class PatientService:
    ICU_CAPACITY = 12

    async def create(self, db, data: PatientCreate) -> dict:
        if await db.patients.find_one({"mrn": data.mrn}):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"MRN {data.mrn} already exists")
        patient = ensure_document(
            normalize_payload(
                {
                    **data.model_dump(),
                    "risk_score": 0,
                    "risk_level": "LOW",
                }
            )
        )
        await db.patients.insert_one(patient)
        return patient

    async def get_all(
        self,
        db,
        skip: int = 0,
        limit: int = 20,
        ward: Optional[str] = None,
        risk_level: Optional[str] = None,
    ) -> tuple[List[dict], int]:
        query = {}
        if ward:
            query["ward"] = ward
        if risk_level:
            query["risk_level"] = risk_level
        total = await db.patients.count_documents(query)
        patients = await db.patients.find_many(query, sort=[("created_at", -1)], skip=skip, limit=limit)
        return patients, total

    async def get_by_id(self, db, patient_id: UUID) -> dict:
        patient = await db.patients.find_one({"id": str(patient_id)})
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        return patient

    async def search(self, db, q: str) -> List[dict]:
        query = q.lower()
        patients = await db.patients.find_many({}, sort=[("created_at", -1)])
        matches = []
        for patient in patients:
            full_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip().lower()
            if query in full_name or query in str(patient.get("mrn", "")).lower():
                matches.append(patient)
            if len(matches) == 10:
                break
        return matches

    async def update(self, db, patient_id: UUID, data: PatientUpdate) -> dict:
        patient = await self.get_by_id(db, patient_id)
        patient.update(prepare_update(normalize_payload(data.model_dump(exclude_unset=True))))
        await db.patients.replace_one({"id": patient["id"]}, patient)
        return patient

    async def delete(self, db, patient_id: UUID) -> None:
        patient = await self.get_by_id(db, patient_id)
        await db.patients.delete_one({"id": patient["id"]})
        await db.vitals.delete_many({"patient_id": patient["id"]})
        await db.labs.delete_many({"patient_id": patient["id"]})
        await db.predictions.delete_many({"patient_id": patient["id"]})
        await db.alerts.delete_many({"patient_id": patient["id"]})

    async def get_dashboard_stats(self, db) -> dict:
        patients = await db.patients.find_many({}, sort=[("created_at", -1)])
        now = datetime.now(UTC)
        counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0}
        ward_counts: dict[str, int] = {}
        active_patients = 0
        discharged_today = 0
        new_today = 0
        sepsis_confirmed = 0
        total_risk_score = 0
        for patient in patients:
            discharged_at = patient.get("discharged_at")
            admitted_at = patient.get("admitted_at") or patient.get("created_at")
            is_active = discharged_at is None

            risk_level = patient.get("risk_level", "LOW")
            counts[risk_level] = counts.get(risk_level, 0) + 1
            total_risk_score += int(patient.get("risk_score") or 0)
            ward = patient.get("ward") or "Unassigned"
            ward_counts[ward] = ward_counts.get(ward, 0) + 1
            diagnosis = str(patient.get("primary_diagnosis") or "").lower()

            if is_active:
                active_patients += 1
            if admitted_at and admitted_at.date() == now.date():
                new_today += 1
            if discharged_at and discharged_at.date() == now.date():
                discharged_today += 1
            if "sepsis" in diagnosis or risk_level in {"CRITICAL", "HIGH"}:
                sepsis_confirmed += 1

        predictions = await db.predictions.find_many({}, sort=[("predicted_at", -1)], limit=24)
        risk_trend = [
            {
                "timestamp": prediction["predicted_at"],
                "risk_score": prediction["risk_score"],
                "risk_level": prediction["risk_level"],
            }
            for prediction in reversed(predictions)
        ]
        avg_risk_score = round(total_risk_score / len(patients), 1) if patients else 0
        icu_occupancy_pct = round((active_patients / self.ICU_CAPACITY) * 100) if self.ICU_CAPACITY else 0
        return {
            "total": active_patients,
            "total_records": len(patients),
            "critical": counts["CRITICAL"],
            "high": counts["HIGH"],
            "moderate": counts["MODERATE"],
            "low": counts["LOW"],
            "by_ward": ward_counts,
            "avg_risk_score": avg_risk_score,
            "icu_occupancy_pct": icu_occupancy_pct,
            "discharged_today": discharged_today,
            "new_today": new_today,
            "sepsis_confirmed": sepsis_confirmed,
            "risk_trend": risk_trend,
            "last_updated": now,
        }

    async def apply_prediction_snapshot(self, db, patient_id: str, risk_score: int) -> None:
        patient = await db.patients.find_one({"id": patient_id})
        if not patient:
            return
        patient["risk_score"] = risk_score
        patient["risk_level"] = score_to_level(risk_score)
        patient["updated_at"] = datetime.now(UTC)
        await db.patients.replace_one({"id": patient_id}, patient)


patient_service = PatientService()
