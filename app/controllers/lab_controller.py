from uuid import UUID
from app.services.lab_service import lab_service
from app.schemas.lab_schema import LabResponse, LabCreate

class LabController:
    async def get_by_patient(self, patient_id: UUID, db):
        labs = await lab_service.get_by_patient(db, patient_id)
        return [LabResponse.model_validate(lab) for lab in labs]

    async def create(self, patient_id: UUID, data: LabCreate, db):
        lab = await lab_service.create(db, patient_id, data)
        return LabResponse.model_validate(lab)

lab_controller = LabController()
