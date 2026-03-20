from __future__ import annotations

from datetime import UTC, datetime
from typing import List
from uuid import UUID

from fastapi import HTTPException, status

from app.database.document import ensure_document, normalize_payload
from app.schemas.vital_schema import VitalCreate
from app.services.mock_vitals_service import mock_vitals_service


class VitalsService:
    async def create(self, db, patient_id: UUID, data: VitalCreate) -> dict:
        patient = await db.patients.find_one({"id": str(patient_id)})
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        vital = ensure_document(
            normalize_payload(
                {
                    "patient_id": str(patient_id),
                    **data.model_dump(),
                    "recorded_at": datetime.now(UTC),
                }
            )
        )
        await db.vitals.insert_one(vital)
        return vital

    async def create_mock(self, db, patient_id: UUID, critical: bool | None = None) -> dict:
        mock_payload = mock_vitals_service.generate(critical=critical)
        return await self.create(db, patient_id, VitalCreate(**mock_payload))

    async def get_latest(self, db, patient_id: UUID) -> dict:
        vitals = await db.vitals.find_many({"patient_id": str(patient_id)}, sort=[("recorded_at", -1)], limit=1)
        if not vitals:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No vitals found for this patient")
        return vitals[0]

    async def get_history(self, db, patient_id: UUID, limit: int = 50) -> List[dict]:
        return await db.vitals.find_many({"patient_id": str(patient_id)}, sort=[("recorded_at", -1)], limit=limit)


vitals_service = VitalsService()
