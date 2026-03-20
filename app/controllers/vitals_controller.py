from uuid import UUID
from app.services.vitals_service import vitals_service
from app.schemas.vital_schema import VitalCreate, VitalResponse

class VitalsController:
    async def add_vital(self, patient_id: UUID, data: VitalCreate, db):
        vital = await vitals_service.create(db, patient_id, data)
        return {"message": "Vitals recorded", "vital": VitalResponse.model_validate(vital)}

    async def add_mock_vital(self, patient_id: UUID, db, critical: bool | None = None):
        vital = await vitals_service.create_mock(db, patient_id, critical=critical)
        return {"message": "Mock vitals recorded", "vital": VitalResponse.model_validate(vital)}

    async def get_latest(self, patient_id: UUID, db):
        vital = await vitals_service.get_latest(db, patient_id)
        return VitalResponse.model_validate(vital)

    async def get_history(self, patient_id: UUID, limit: int, db):
        vitals = await vitals_service.get_history(db, patient_id, limit)
        return [VitalResponse.model_validate(v) for v in vitals]

vitals_controller = VitalsController()
