from __future__ import annotations

from datetime import UTC, datetime

from app.database.document import ensure_document, normalize_payload
from app.services.audit_service import audit_service
from app.services.mock_vitals_service import mock_vitals_service
from app.utils.password_hash import hash_password


DEFAULT_USERS = [
    {
        "name": "Dr. Maya Patel",
        "email": "doctor@sepsis.ai",
        "password": "Doctor@123",
        "role": "doctor",
        "ward": "ICU-A",
        "phone": "+15551001001",
    },
    {
        "name": "Nurse Daniel Kim",
        "email": "nurse@sepsis.ai",
        "password": "Nurse@123",
        "role": "nurse",
        "ward": "ICU-A",
        "phone": "+15551001002",
    },
    {
        "name": "Avery Brooks",
        "email": "admin@sepsis.ai",
        "password": "Admin@123",
        "role": "admin",
        "ward": None,
        "phone": "+15551001003",
    },
]

DEFAULT_PATIENTS = [
    {
        "mrn": "ICU-1001",
        "first_name": "Lena",
        "last_name": "Hart",
        "date_of_birth": "1978-04-21",
        "gender": "F",
        "ward": "ICU-A",
        "bed_number": 3,
        "primary_diagnosis": "Post-operative monitoring",
        "comorbidities": ["hypertension"],
        "physician_name": "Dr. Maya Patel",
        "risk_score": 72,
        "risk_level": "CRITICAL",
    },
    {
        "mrn": "ICU-1002",
        "first_name": "Owen",
        "last_name": "Reed",
        "date_of_birth": "1969-09-09",
        "gender": "M",
        "ward": "ICU-A",
        "bed_number": 7,
        "primary_diagnosis": "Pneumonia",
        "comorbidities": ["type 2 diabetes"],
        "physician_name": "Dr. Maya Patel",
        "risk_score": 44,
        "risk_level": "HIGH",
    },
]

DEFAULT_SYSTEM_SETTINGS = {
    "id": "default",
    "notifications": {
        "emailAlerts": True,
        "smsAlerts": False,
        "pagerAlerts": True,
        "autoEscalateMin": 10,
    },
    "model": {
        "criticalThreshold": 65,
        "highThreshold": 40,
        "moderateThreshold": 20,
        "pollingInterval": 5,
    },
    "operations": {
        "dataRetentionDays": 365,
        "maintenanceMode": False,
    },
}


async def seed_database(db) -> None:
    if await db.users.count_documents({}) == 0:
        for user in DEFAULT_USERS:
            await db.users.insert_one(
                ensure_document(
                    normalize_payload(
                        {
                            "name": user["name"],
                            "email": user["email"],
                            "password_hash": hash_password(user["password"]),
                            "role": user["role"],
                            "ward": user["ward"],
                            "phone": user["phone"],
                            "is_active": True,
                            "last_login": None,
                        }
                    )
                )
            )

    if await db.patients.count_documents({}) == 0:
        now = datetime.now(UTC)
        for patient in DEFAULT_PATIENTS:
            doc = ensure_document(
                normalize_payload(
                    {
                        **patient,
                        "admitted_at": now,
                        "discharged_at": None,
                    }
                )
            )
            await db.patients.insert_one(doc)

    if await db.vitals.count_documents({}) == 0:
        patients = await db.patients.find_many({}, sort=[("created_at", 1)])
        for index, patient in enumerate(patients):
            reading_count = 6
            for reading_index in range(reading_count):
                critical = patient.get("risk_level") == "CRITICAL" and reading_index >= reading_count - 2
                recorded_at = datetime.now(UTC)
                payload = mock_vitals_service.generate(
                    critical=critical if critical else (patient.get("risk_level") == "HIGH" and reading_index == reading_count - 1),
                    source="seed_mock",
                )
                await db.vitals.insert_one(
                    ensure_document(
                        normalize_payload(
                            {
                                "patient_id": patient["id"],
                                **payload,
                                "recorded_at": recorded_at,
                            }
                        )
                    )
                )

    if await db.system_settings.count_documents({}) == 0:
        await db.system_settings.insert_one(
            ensure_document(normalize_payload(DEFAULT_SYSTEM_SETTINGS), doc_id="default")
        )

    if await db.audit_logs.count_documents({}) == 0:
        await audit_service.log_event(
            db,
            action="seed",
            resource="database",
            actor={"name": "System Seeder", "role": "system"},
            details={"users": len(DEFAULT_USERS), "patients": len(DEFAULT_PATIENTS)},
        )
