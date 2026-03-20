from typing import Optional
from uuid import UUID
from app.services.patient_service import patient_service
from app.schemas.patient_schema import PatientCreate, PatientUpdate, PatientResponse

class PatientController:
    async def create_patient(self, data: PatientCreate, db):
        patient = await patient_service.create(db, data)
        return {"message": "Patient created", "patient": PatientResponse.model_validate(patient)}

    async def get_patients(self, skip: int, limit: int,
                           ward: Optional[str],
                           db):
        patients, total = await patient_service.get_all(db, skip, limit, ward)
        return {
            "total": total, "skip": skip, "limit": limit,
            "patients": [PatientResponse.model_validate(p) for p in patients],
        }

    async def get_patient(self, patient_id: UUID, db):
        patient = await patient_service.get_by_id(db, patient_id)
        return PatientResponse.model_validate(patient)

    async def search_patients(self, q: str, db):
        patients = await patient_service.search(db, q)
        return [PatientResponse.model_validate(p) for p in patients]

    async def update_patient(self, patient_id: UUID, data: PatientUpdate, db):
        patient = await patient_service.update(db, patient_id, data)
        return {"message": "Patient updated", "patient": PatientResponse.model_validate(patient)}

    async def delete_patient(self, patient_id: UUID, db):
        await patient_service.delete(db, patient_id)
        return {"message": "Patient deleted"}

    async def dashboard_stats(self, db):
        return await patient_service.get_dashboard_stats(db)

patient_controller = PatientController()
