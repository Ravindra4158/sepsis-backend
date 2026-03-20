from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status

from app.database.document import ensure_document, normalize_payload
from app.schemas.lab_schema import LabCreate


class LabService:
    async def get_by_patient(self, db, patient_id: UUID, limit: int = 50) -> list[dict]:
        return await db.labs.find_many({"patient_id": str(patient_id)}, sort=[("collected_at", -1)], limit=limit)

    async def create(self, db, patient_id: UUID, data: LabCreate) -> dict:
        patient = await db.patients.find_one({"id": str(patient_id)})
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        lab = ensure_document(
            normalize_payload(
                {
                    "patient_id": str(patient_id),
                    **data.model_dump(),
                    "collected_at": data.collected_at or datetime.now(UTC),
                }
            )
        )
        await db.labs.insert_one(lab)
        return lab


lab_service = LabService()
